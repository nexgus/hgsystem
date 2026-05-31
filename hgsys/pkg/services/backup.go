// Package services 封裝 mongodump / mongorestore 與基於 git 的 self-updater.
package services

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"

	"hgsys/pkg/repository"
)

// RequiredRestoreFiles 列出 mongodump 會產生, 且於 restore 前必須存在的檔案,
// 對齊舊版程式.
var RequiredRestoreFiles = []string{
	"customers.bson",
	"customers.metadata.json",
	"worksheets.bson",
	"worksheets.metadata.json",
}

// ResolveRestoreDir 允許使用者選擇 dump 的上層目錄: 若 `chosen` 之下有
// `hgsystem/` 子目錄, 則自動下鑽進去.
func ResolveRestoreDir(chosen string) string {
	nested := filepath.Join(chosen, repository.DatabaseName)
	if info, err := os.Stat(nested); err == nil && info.IsDir() {
		return nested
	}
	return chosen
}

// MissingRestoreFiles 回傳 `savepath` 中缺少的 RequiredRestoreFiles 子集.
// 空 slice 表示可直接執行 restore.
func MissingRestoreFiles(savepath string) []string {
	var missing []string
	for _, name := range RequiredRestoreFiles {
		if _, err := os.Stat(filepath.Join(savepath, name)); err != nil {
			missing = append(missing, name)
		}
	}
	return missing
}

// containerDumpDir / containerRestoreDir 為 docker 備援路徑在容器內使用的暫存
// 目錄. 每次使用前都會先清空, 用後即刪.
const (
	containerDumpDir    = "/tmp/hgsystem-dump"
	containerRestoreDir = "/tmp/hgsystem-restore"
)

// MongoPort 為偵測 MongoDB 容器時比對的發佈 port. 與 mongodump / mongorestore
// 的預設連線 port 一致 (備份目前不帶 -H / -p, 固定走預設值).
const MongoPort = 27017

// backupMetaFile 為備份資訊檔名. 寫在使用者選的備份目錄下, 與 dump 產生的
// hgsystem/ 夾同層 — 不在 mongorestore --dir 指向的目錄之內, 因此不影響還原.
const backupMetaFile = "backup-info.json"

// MetaInfo 由 app 層提供 services 層無從得知的資訊 (MongoDB server 版本與
// hgsystem 版本), 一併寫入備份 metadata. 取不到時可為空字串.
type MetaInfo struct {
	MongoDBVersion string
	AppVersion     string
}

// BackupMeta 為寫入 <savepath>/backup-info.json 的內容, 記錄此次備份的時間,
// 來源工具與各 collection 筆數, 供日後辨識與驗證備份用.
type BackupMeta struct {
	Database       string         `json:"database"`
	BackupTime     string         `json:"backup_time"`     // RFC3339, 本地時區
	MongoDBVersion string         `json:"mongodb_version"` // 取自 server buildInfo; 未知時為空字串
	BackupTool     string         `json:"backup_tool"`     // "mongodump (host)" 或 "mongodump (container <name>)"
	AppVersion     string         `json:"app_version"`     // hgsystem 版本
	Collections    map[string]int `json:"collections"`     // collection 名稱 -> 文件數, 取自 mongodump 輸出
}

// dumpCountRe 比對 mongodump 的 "done dumping <db>.<collection> (N documents)"
// 輸出行 (tab 已由 forwardLines 換成空白), 取出 collection 名稱與筆數.
var dumpCountRe = regexp.MustCompile(`done dumping ` + regexp.QuoteMeta(repository.DatabaseName) + `\.(\S+) \((\d+) document`)

// Dump 將 hgsystem 資料庫匯出至 host 的 <savepath>. 優先使用 host 上的 mongodump;
// 若 host 未安裝, 則退回在 MongoDB 容器內執行 mongodump, 再以 `docker cp` 把結果
// 複製回 host. 每一行 stderr 會轉發給 onLine; 直到完成才回傳 (blocking).
func Dump(ctx context.Context, savepath string, info MetaInfo, onLine func(string)) error {
	// 邊備份邊解析 mongodump 輸出的各 collection 筆數, 同時照常逐行轉發前端.
	counts := map[string]int{}
	record := func(line string) {
		scanDumpCount(line, counts)
		emit(onLine, line)
	}

	var tool string
	if _, err := exec.LookPath("mongodump"); err == nil {
		if err := runStreamed(ctx, "mongodump", []string{"-d", repository.DatabaseName, "-o", savepath}, record); err != nil {
			return err
		}
		tool = "mongodump (host)"
	} else {
		container := MongoContainer(MongoPort)
		if container == "" {
			return fmt.Errorf("找不到 mongodump, 也找不到發佈 %d port 的 MongoDB 容器 (請安裝 MongoDB Database Tools, 或確認 docker 容器已啟動)", MongoPort)
		}
		if err := dumpViaDocker(ctx, container, savepath, record); err != nil {
			return err
		}
		tool = fmt.Sprintf("mongodump (container %s)", container)
	}

	// 備份本身已完成; metadata 寫檔失敗不視為備份失敗, 僅在對話框提示.
	if err := writeBackupMeta(savepath, info, tool, counts); err != nil {
		emit(onLine, fmt.Sprintf("警告: 寫入備份資訊檔失敗: %v", err))
	}
	return nil
}

// scanDumpCount 解析單行 mongodump 輸出, 若為某 collection 的完成行則記下筆數.
func scanDumpCount(line string, counts map[string]int) {
	m := dumpCountRe.FindStringSubmatch(line)
	if m == nil {
		return
	}
	n, err := strconv.Atoi(m[2])
	if err != nil {
		return
	}
	counts[m[1]] = n
}

// writeBackupMeta 將此次備份的 metadata 以縮排 JSON 寫入 <savepath>/backup-info.json.
// savepath 於兩條 dump 路徑執行至此時均已存在 (host: mongodump -o 建立; docker:
// dumpViaDocker 內以 MkdirAll 建立).
func writeBackupMeta(savepath string, info MetaInfo, tool string, counts map[string]int) error {
	meta := BackupMeta{
		Database:       repository.DatabaseName,
		BackupTime:     time.Now().Format(time.RFC3339),
		MongoDBVersion: info.MongoDBVersion,
		BackupTool:     tool,
		AppVersion:     info.AppVersion,
		Collections:    counts,
	}
	data, err := json.MarshalIndent(meta, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(filepath.Join(savepath, backupMetaFile), data, 0o644)
}

// Restore 從 host 的 <savepath> 還原 hgsystem 資料庫. 工具挑選邏輯與 Dump 相同:
// host mongorestore 優先, 否則退回容器內的 mongorestore (先以 `docker cp` 把 dump
// 送進容器).
func Restore(ctx context.Context, savepath string, onLine func(string)) error {
	if _, err := exec.LookPath("mongorestore"); err == nil {
		return runStreamed(ctx, "mongorestore", []string{"-d", repository.DatabaseName, "--dir", savepath}, onLine)
	}
	container := MongoContainer(MongoPort)
	if container == "" {
		return fmt.Errorf("找不到 mongorestore, 也找不到發佈 %d port 的 MongoDB 容器 (請安裝 MongoDB Database Tools, 或確認 docker 容器已啟動)", MongoPort)
	}
	return restoreViaDocker(ctx, container, savepath, onLine)
}

// MongoContainer 找出本機 docker 中發佈了 port 的容器名稱, 供 Dump / Restore 的
// docker 備援路徑使用. 本機無 docker CLI, 查詢失敗, 或查無容器時一律回傳 "".
// 同一 port 有多個容器時取第一個.
func MongoContainer(port int) string {
	if _, err := exec.LookPath("docker"); err != nil {
		return ""
	}
	out, err := exec.Command("docker", "ps",
		"--filter", fmt.Sprintf("publish=%d", port),
		"--format", "{{.Names}}").Output()
	if err != nil {
		return ""
	}
	name := strings.TrimSpace(string(out))
	if i := strings.IndexByte(name, '\n'); i >= 0 {
		name = name[:i]
	}
	return name
}

// dumpViaDocker 在容器內執行 mongodump, 再把結果複製回 host 的 savepath, 使最終
// 佈局 (<savepath>/hgsystem/*) 與 host 直接 mongodump 一致.
func dumpViaDocker(ctx context.Context, container, savepath string, onLine func(string)) error {
	emit(onLine, fmt.Sprintf("host 未安裝 mongodump, 改用容器 %s 內的工具", container))
	if err := runQuiet(ctx, "docker", "exec", container, "rm", "-rf", containerDumpDir); err != nil {
		return err
	}
	if err := runStreamed(ctx, "docker",
		[]string{"exec", container, "mongodump", "-d", repository.DatabaseName, "-o", containerDumpDir}, onLine); err != nil {
		return err
	}
	// docker cp 的目的目錄必須存在, 容器內的 hgsystem 才會被放進去成為子目錄.
	if err := os.MkdirAll(savepath, 0o755); err != nil {
		return fmt.Errorf("建立 %s: %w", savepath, err)
	}
	src := fmt.Sprintf("%s:%s/%s", container, containerDumpDir, repository.DatabaseName)
	if err := runQuiet(ctx, "docker", "cp", src, savepath); err != nil {
		return err
	}
	_ = runQuiet(ctx, "docker", "exec", container, "rm", "-rf", containerDumpDir) // 清理失敗不致命.
	return nil
}

// restoreViaDocker 先把 host 的 dump 內容複製進容器, 再於容器內執行 mongorestore.
func restoreViaDocker(ctx context.Context, container, savepath string, onLine func(string)) error {
	emit(onLine, fmt.Sprintf("host 未安裝 mongorestore, 改用容器 %s 內的工具", container))
	if err := runQuiet(ctx, "docker", "exec", container, "sh", "-c",
		"rm -rf "+containerRestoreDir+" && mkdir -p "+containerRestoreDir); err != nil {
		return err
	}
	// savepath/. 表示複製目錄內容 (而非目錄本身) 進入 containerRestoreDir.
	if err := runQuiet(ctx, "docker", "cp", savepath+"/.", container+":"+containerRestoreDir); err != nil {
		return err
	}
	if err := runStreamed(ctx, "docker",
		[]string{"exec", container, "mongorestore", "-d", repository.DatabaseName, "--dir", containerRestoreDir}, onLine); err != nil {
		return err
	}
	_ = runQuiet(ctx, "docker", "exec", container, "rm", "-rf", containerRestoreDir) // 清理失敗不致命.
	return nil
}

// runQuiet 執行不需串流的輔助指令 (docker cp / rm 等), 失敗時把合併輸出一併帶回.
func runQuiet(ctx context.Context, name string, args ...string) error {
	out, err := exec.CommandContext(ctx, name, args...).CombinedOutput()
	if err != nil {
		return fmt.Errorf("%s %s: %w: %s", name, strings.Join(args, " "), err, strings.TrimSpace(string(out)))
	}
	return nil
}

// emit 在 onLine 非 nil 時送出一行訊息.
func emit(onLine func(string), line string) {
	if onLine != nil {
		onLine(line)
	}
}

func runStreamed(ctx context.Context, name string, args []string, onLine func(string)) error {
	cmd := exec.CommandContext(ctx, name, args...)
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("create stderr pipe: %w", err)
	}
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("start %s: %w", name, err)
	}
	go forwardLines(stderr, onLine)
	if err := cmd.Wait(); err != nil {
		var exitErr *exec.ExitError
		if errors.As(err, &exitErr) {
			return fmt.Errorf("%s exited with %d", name, exitErr.ExitCode())
		}
		return err
	}
	return nil
}

func forwardLines(r io.Reader, onLine func(string)) {
	sc := bufio.NewScanner(r)
	sc.Buffer(make([]byte, 64*1024), 1024*1024)
	for sc.Scan() {
		// 對齊舊版行為: 將 tab 換為空白, 並去除換行 (Scanner 已順帶處理掉換行).
		line := strings.ReplaceAll(sc.Text(), "\t", " ")
		if onLine != nil {
			onLine(line)
		}
	}
}

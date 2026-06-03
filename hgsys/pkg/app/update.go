package app

import (
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/wailsapp/wails/v3/pkg/application"
	"golang.org/x/mod/semver"

	"hgsys/pkg/repo"
	"hgsys/pkg/version"
)

// updateRepo 為檢查新版本的來源儲存庫 (owner/repo).
const updateRepo = "nexgus/hgsystem"

// downloadTimeout 為下載新版 binary / MSI 的總逾時上限. 取較寬鬆值以容納
// 數十 MB 的下載; 連線真的停滯時仍會中止而非無限等待.
const downloadTimeout = 10 * time.Minute

// UpdateService 提供「檢查更新」綁定: 查詢 GitHub release、比較語意化版本,
// 並在使用者確認後下載新版 (邊下載邊以 "update:progress" event 回報百分比)、
// 釋出內嵌的 hgupgrade、啟動它後關閉自己. 實際的換檔 / 安裝由 hgupgrade
// 於本程式結束後進行.
type UpdateService struct {
	app *application.App

	// upgrader 為內嵌的 hgupgrade 執行檔位元組, 由 main.go 經 SetUpgrader 注入
	// (embed 宣告位於 cmd/hgsystem, 與本套件不同包, 故用注入而非直接 embed).
	// upgraderName 為釋出到暫存目錄時使用的檔名 (Windows 須含 .exe).
	upgrader     []byte
	upgraderName string

	// mu 保護 pending. CheckForUpdate 解析出的下載目標暫存於此, 供後續
	// StartUpgrade 取用, 免去再查一次 release.
	mu      sync.Mutex
	pending *pendingUpdate
}

// pendingUpdate 為 CheckForUpdate 解析出、待安裝的版本與其平台對應 asset.
type pendingUpdate struct {
	version   string // 顯示用版本字串 (不含 v 前綴)
	assetURL  string
	assetName string
	assetSize int64
}

// UpdateInfo 為 CheckForUpdate 回傳給前端的結果.
type UpdateInfo struct {
	HasUpdate      bool   `json:"hasUpdate"`      // 是否有可安裝的新版本
	CurrentVersion string `json:"currentVersion"` // 目前版本 (不含 v 前綴)
	LatestVersion  string `json:"latestVersion"`  // 最新正式版 (不含 v 前綴); 無新版時與 current 相同
}

func NewUpdateService() *UpdateService {
	return &UpdateService{}
}

// SetApp 於 application.New 之後注入 Wails *App (與 BackupService 相同作法),
// 供發送進度 event 與關閉應用程式.
func (s *UpdateService) SetApp(app *application.App) {
	s.app = app
}

// SetUpgrader 注入內嵌的 hgupgrade 執行檔位元組與其釋出檔名. 由 main.go 於
// 建立 service 後呼叫 (位元組來自 cmd/hgsystem 的平台 embed).
func (s *UpdateService) SetUpgrader(bin []byte, name string) {
	s.upgrader = bin
	s.upgraderName = name
}

// CheckForUpdate 查詢來源儲存庫的所有 release, 略過 draft / prerelease, 以
// 語意化版本挑出最大的正式版, 並與目前版本比較. 若有新版且存在對應本平台的
// asset, 將下載目標暫存供 StartUpgrade 使用.
func (s *UpdateService) CheckForUpdate() (UpdateInfo, error) {
	current := normSemver(version.String)
	info := UpdateInfo{
		CurrentVersion: strings.TrimPrefix(current, "v"),
		LatestVersion:  strings.TrimPrefix(current, "v"),
	}

	finder, err := repo.NewRepoFinder(repo.SourceGitHub, nil, nil, nil)
	if err != nil {
		return info, err
	}
	report, err := finder.GetAllReleases(updateRepo)
	if err != nil {
		return info, fmt.Errorf("查詢版本失敗: %w", err)
	}

	rel, latest, ok := pickLatestRelease(report)
	if !ok {
		// 查不到任何有效的正式版; 視為已是最新.
		return info, nil
	}
	info.LatestVersion = strings.TrimPrefix(latest, "v")

	if semver.Compare(latest, current) <= 0 {
		// 目前已是最新 (或更新). 不視為錯誤.
		return info, nil
	}

	asset, found := pickAsset(rel)
	if !found {
		// 有新版本, 但沒有對應本平台的下載檔, 無法更新.
		slog.Warn("發現新版本但缺少對應本平台的 asset", "version", info.LatestVersion, "platform", runtime.GOOS+"/"+runtime.GOARCH)
		return info, nil
	}

	s.mu.Lock()
	s.pending = &pendingUpdate{
		version:   info.LatestVersion,
		assetURL:  asset.BrowserDownloadURL,
		assetName: asset.Name,
		assetSize: asset.Size,
	}
	s.mu.Unlock()

	info.HasUpdate = true
	return info, nil
}

// StartUpgrade 下載 CheckForUpdate 解析出的新版 asset (邊下載邊回報進度),
// 驗證大小後釋出內嵌的 hgupgrade 並啟動它, 然後關閉本應用程式. 下載或釋出
// 階段失敗時回傳 error (此時應用程式仍在執行, 由前端顯示錯誤); 成功啟動
// hgupgrade 後即關閉自己, 後續換檔 / 安裝與重啟由 hgupgrade 負責.
func (s *UpdateService) StartUpgrade() error {
	s.mu.Lock()
	p := s.pending
	s.mu.Unlock()
	if p == nil {
		return errors.New("尚未檢查更新或無可用更新")
	}
	if len(s.upgrader) == 0 {
		return errors.New("內建的更新程式不存在, 無法更新")
	}

	launchPath, err := os.Executable()
	if err != nil {
		return fmt.Errorf("無法取得自身路徑: %w", err)
	}

	dest, err := s.downloadAsset(p)
	if err != nil {
		return err
	}

	upPath, err := s.extractUpgrader()
	if err != nil {
		return fmt.Errorf("準備更新程式失敗: %w", err)
	}

	args := []string{
		"-pid", strconv.Itoa(os.Getpid()),
		"-launch-path", launchPath,
		"-file", dest,
		"-version", p.version,
	}
	cmd := exec.Command(upPath, args...)
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("啟動更新程式失敗: %w", err)
	}
	_ = cmd.Process.Release()

	slog.Info("已啟動 hgupgrade, 即將關閉以進行更新", "version", p.version)
	if s.app != nil {
		s.app.Quit()
	}
	return nil
}

// downloadAsset 將 p 對應的 asset 下載至目的路徑, 邊下載邊以 "update:progress"
// event 回報百分比, 完成後比對大小. 回傳已下載完成的檔案路徑.
func (s *UpdateService) downloadAsset(p *pendingUpdate) (string, error) {
	dest := downloadDestPath(p.assetName)
	partial := dest + ".partial"

	client := &http.Client{Timeout: downloadTimeout}
	resp, err := client.Get(p.assetURL)
	if err != nil {
		return "", fmt.Errorf("下載失敗: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("下載失敗: 伺服器回應 %s", resp.Status)
	}

	out, err := os.Create(partial)
	if err != nil {
		return "", fmt.Errorf("建立暫存檔失敗: %w", err)
	}

	total := p.assetSize
	var read int64
	lastPct := -1
	buf := make([]byte, 64*1024)
	for {
		n, rerr := resp.Body.Read(buf)
		if n > 0 {
			if _, werr := out.Write(buf[:n]); werr != nil {
				out.Close()
				_ = os.Remove(partial)
				return "", fmt.Errorf("寫入暫存檔失敗: %w", werr)
			}
			read += int64(n)
			if total > 0 {
				if pct := int(read * 100 / total); pct != lastPct {
					lastPct = pct
					s.emitProgress(pct)
				}
			}
		}
		if rerr == io.EOF {
			break
		}
		if rerr != nil {
			out.Close()
			_ = os.Remove(partial)
			return "", fmt.Errorf("下載中斷: %w", rerr)
		}
	}
	if err := out.Close(); err != nil {
		_ = os.Remove(partial)
		return "", fmt.Errorf("關閉暫存檔失敗: %w", err)
	}

	if total > 0 && read != total {
		_ = os.Remove(partial)
		return "", fmt.Errorf("下載大小不符 (預期 %d 位元組, 實得 %d)", total, read)
	}

	if err := os.Rename(partial, dest); err != nil {
		_ = os.Remove(partial)
		return "", fmt.Errorf("完成下載失敗: %w", err)
	}
	s.emitProgress(100)
	return dest, nil
}

// extractUpgrader 將內嵌的 hgupgrade 位元組寫入新建的暫存目錄, 回傳可執行的
// 路徑. 寫入時即賦予執行權限 (Windows 無作用, 但檔名帶 .exe).
func (s *UpdateService) extractUpgrader() (string, error) {
	dir, err := os.MkdirTemp("", "hgupgrade-")
	if err != nil {
		return "", err
	}
	path := filepath.Join(dir, s.upgraderName)
	if err := os.WriteFile(path, s.upgrader, 0o755); err != nil {
		return "", err
	}
	return path, nil
}

func (s *UpdateService) emitProgress(pct int) {
	if s.app != nil {
		s.app.Event.Emit("update:progress", pct)
	}
}

// downloadDestPath 決定下載目的路徑. Windows 下載 .msi 至暫存目錄 (交由
// msiexec 安裝); 其他平台 (macOS) 將新版 binary 下載至執行檔同目錄, 供
// hgupgrade 以原子換 symlink 指向它.
func downloadDestPath(assetName string) string {
	if runtime.GOOS == "windows" {
		return filepath.Join(os.TempDir(), assetName)
	}
	dir := os.TempDir()
	if exe, err := os.Executable(); err == nil {
		dir = filepath.Dir(exe)
	}
	return filepath.Join(dir, assetName)
}

// pickLatestRelease 自 report 中略過 draft / prerelease, 以語意化版本挑出最大
// 的正式版. 回傳該 release、其正規化版本字串 (含 v 前綴), 與是否找到.
func pickLatestRelease(report *repo.ReleaseReport) (repo.Release, string, bool) {
	var best repo.Release
	bestVer := ""
	for _, r := range report.Releases {
		if r.Draft || r.Prerelease {
			continue
		}
		v := normSemver(r.TagName)
		if !semver.IsValid(v) {
			continue
		}
		if bestVer == "" || semver.Compare(v, bestVer) > 0 {
			best = r
			bestVer = v
		}
	}
	return best, bestVer, bestVer != ""
}

// pickAsset 自 release 的 assets 中挑出對應本平台的下載檔: Windows 取 .msi,
// 其他平台取結尾為 -GOOS-GOARCH (例如 -darwin-arm64) 的檔.
func pickAsset(rel repo.Release) (repo.Asset, bool) {
	suffix := assetSuffix()
	for _, a := range rel.Assets {
		if strings.HasSuffix(a.Name, suffix) {
			return a, true
		}
	}
	return repo.Asset{}, false
}

func assetSuffix() string {
	if runtime.GOOS == "windows" {
		return ".msi"
	}
	return "-" + runtime.GOOS + "-" + runtime.GOARCH
}

// normSemver 將 tag 正規化為帶單一小寫 v 前綴的語意化版本字串, 供
// golang.org/x/mod/semver 使用 (線上 tag 有 v0.1.1 也有 0.7.0 兩種寫法).
func normSemver(tag string) string {
	tag = strings.TrimSpace(tag)
	if tag == "" {
		return ""
	}
	if tag[0] == 'v' || tag[0] == 'V' {
		tag = tag[1:]
	}
	return "v" + tag
}

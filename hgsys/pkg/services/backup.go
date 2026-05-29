// Package services 封裝 mongodump / mongorestore 與基於 git 的 self-updater.
package services

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

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

// Dump 執行 `mongodump -d hgsystem -o <savepath>`, 並將每一行 stderr 轉發給
// `onLine`. 直到指令結束才回傳 (blocking).
func Dump(ctx context.Context, savepath string, onLine func(string)) error {
	return runStreamed(ctx, "mongodump", []string{"-d", repository.DatabaseName, "-o", savepath}, onLine)
}

// Restore 執行 `mongorestore -d hgsystem --dir <savepath>`, 並將每一行 stderr
// 轉發給 `onLine`. 直到指令結束才回傳 (blocking).
func Restore(ctx context.Context, savepath string, onLine func(string)) error {
	return runStreamed(ctx, "mongorestore", []string{"-d", repository.DatabaseName, "--dir", savepath}, onLine)
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

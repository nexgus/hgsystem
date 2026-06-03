//go:build darwin

package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
)

// applyUpdate 設定新版 binary 的執行權限, 並以原子方式將 launchPath (通常為
// 指向版本化 binary 的 symlink) 換成指向新版的 symlink. 先建立暫存 symlink
// 再 rename 蓋過, 避免「舊的已移除、新的尚未建立」的空窗; 換檔前的任何失敗
// 都不動既有 binary. 不刪除舊版本檔, 以保留退回的可能.
func applyUpdate(launchPath, file string) error {
	if err := os.Chmod(file, 0o755); err != nil {
		return fmt.Errorf("設定執行權限失敗: %w", err)
	}
	dir := filepath.Dir(launchPath)
	tmp := filepath.Join(dir, ".hgsystem.new")
	_ = os.Remove(tmp)
	// 以相對目標建立 symlink, 與 build.sh 的 ln -s 行為一致 (同目錄相對連結).
	if err := os.Symlink(filepath.Base(file), tmp); err != nil {
		return fmt.Errorf("建立連結失敗: %w", err)
	}
	if err := os.Rename(tmp, launchPath); err != nil {
		_ = os.Remove(tmp)
		return fmt.Errorf("替換連結失敗: %w", err)
	}
	return nil
}

// processAlive 回傳 pid 對應的行程是否仍存在.
func processAlive(pid int) bool {
	if pid <= 0 {
		return false
	}
	// signal 0 不送出訊號, 僅用於偵測行程是否存在; EPERM 代表行程存在但無權限.
	err := syscall.Kill(pid, 0)
	return err == nil || err == syscall.EPERM
}

// launchDetached 以脫離本行程 session 的方式啟動 path, 使其在本程式結束後存活.
func launchDetached(path string) error {
	cmd := exec.Command(path)
	cmd.SysProcAttr = &syscall.SysProcAttr{Setsid: true}
	if err := cmd.Start(); err != nil {
		return err
	}
	return cmd.Process.Release()
}

// showError 以 osascript 顯示原生對話框, 阻塞至使用者按下「確認」.
func showError(msg string) {
	script := `tell application "System Events" to display dialog ` + asQuote(msg) +
		` with title "更新" buttons {"確認"} default button "確認" with icon stop`
	_ = exec.Command("osascript", "-e", script).Run()
}

// asQuote 將字串轉為 AppleScript 字串字面值 (跳脫反斜線與雙引號, 換行轉空白).
func asQuote(s string) string {
	s = strings.ReplaceAll(s, `\`, `\\`)
	s = strings.ReplaceAll(s, `"`, `\"`)
	s = strings.ReplaceAll(s, "\n", " ")
	return `"` + s + `"`
}

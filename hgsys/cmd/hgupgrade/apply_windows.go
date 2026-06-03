//go:build windows

package main

import (
	"fmt"
	"os/exec"
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
)

// applyUpdate 以 msiexec 安裝已下載的新版 MSI. MSI 為 MajorUpgrade, 會自動移除
// 舊版再裝新版; /qb! 顯示無法取消的基本進度 UI; per-machine 安裝會觸發一次
// UAC 提權. 安裝失敗時 Windows Installer 一般會自動回滾為舊版.
func applyUpdate(launchPath, file string) error {
	cmd := exec.Command("msiexec", "/i", file, "/qb!")
	err := cmd.Run()
	if err == nil {
		return nil
	}
	if ee, ok := err.(*exec.ExitError); ok {
		// 3010 = ERROR_SUCCESS_REBOOT_REQUIRED, 視為安裝成功 (僅需重開機).
		if ee.ExitCode() == 3010 {
			return nil
		}
		return fmt.Errorf("安裝程式回傳錯誤碼 %d", ee.ExitCode())
	}
	return fmt.Errorf("執行安裝程式失敗: %w", err)
}

// processAlive 回傳 pid 對應的行程是否仍存在.
func processAlive(pid int) bool {
	if pid <= 0 {
		return false
	}
	h, err := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION, false, uint32(pid))
	if err != nil {
		return false
	}
	defer windows.CloseHandle(h)
	var code uint32
	if err := windows.GetExitCodeProcess(h, &code); err != nil {
		return false
	}
	return code == 259 // STILL_ACTIVE
}

// launchDetached 以脫離本行程的方式啟動 path, 使其在本程式結束後存活.
func launchDetached(path string) error {
	cmd := exec.Command(path)
	cmd.SysProcAttr = &syscall.SysProcAttr{
		CreationFlags: windows.DETACHED_PROCESS | windows.CREATE_NEW_PROCESS_GROUP,
	}
	if err := cmd.Start(); err != nil {
		return err
	}
	return cmd.Process.Release()
}

var (
	user32         = windows.NewLazySystemDLL("user32.dll")
	procMessageBox = user32.NewProc("MessageBoxW")
)

// showError 以原生 MessageBox 顯示錯誤, 阻塞至使用者按下「確定」.
func showError(msg string) {
	const (
		mbOK            = 0x00000000
		mbIconError     = 0x00000010
		mbSetForeground = 0x00010000
		mbTopMost       = 0x00040000
	)
	title, _ := windows.UTF16PtrFromString("更新")
	text, _ := windows.UTF16PtrFromString(msg)
	procMessageBox.Call(
		0,
		uintptr(unsafe.Pointer(text)),
		uintptr(unsafe.Pointer(title)),
		uintptr(mbOK|mbIconError|mbSetForeground|mbTopMost),
	)
}

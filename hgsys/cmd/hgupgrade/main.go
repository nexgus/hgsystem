// Command hgupgrade 是 hgsystem 的隨附更新程式. 它由 hgsystem 在使用者確認
// 更新、且新版檔已下載完成後啟動 (hgsystem 隨即關閉自己), 負責 hgsystem 仍在
// 執行時無法自行完成的部分:
//
//   - macOS: 將指向版本化 binary 的 symlink 原子換成指向新版.
//   - Windows: 以 msiexec 安裝新版 MSI (MajorUpgrade 自動替換舊版).
//
// 完成後重新啟動 hgsystem 並結束自己. 任何 (換檔 / 安裝前的) 失敗都會彈出
// 原生對話框告知使用者, 並重啟仍可用的舊版.
//
// hgupgrade 以 //go:embed 內嵌於 hgsystem, 由 hgsystem 釋出到暫存目錄後執行,
// 因此本身不留在安裝目錄, 也不會在更新時鎖住自己.
package main

import (
	"flag"
	"fmt"
	"time"
)

// waitTimeout 為等待原 hgsystem 行程結束的上限. 正常情況下 hgsystem 在啟動
// 本程式後隨即關閉, 數秒內即結束; 逾時代表卡住, 此時中止更新並回報.
const waitTimeout = 30 * time.Second

func main() {
	pid := flag.Int("pid", 0, "要等待結束的原 hgsystem 行程 PID")
	launchPath := flag.String("launch-path", "", "原 hgsystem 的啟動路徑 (macOS 為 symlink, Windows 為 exe)")
	file := flag.String("file", "", "已下載的新版檔案路徑 (macOS 為 binary, Windows 為 .msi)")
	ver := flag.String("version", "", "新版本字串 (僅供訊息顯示)")
	flag.Parse()

	err := run(*pid, *launchPath, *file)
	if err != nil {
		showError(fmt.Sprintf("更新到 %s 失敗:\n%v\n\n將繼續使用目前的版本。", displayVersion(*ver), err))
	}

	// 不論成功或 (換檔 / 安裝前) 失敗, 都重啟 launch-path 指向的 hgsystem:
	// 成功時它已指向新版, 失敗時仍為舊版.
	if *launchPath != "" {
		if rerr := launchDetached(*launchPath); rerr != nil {
			showError(fmt.Sprintf("重新啟動失敗:\n%v", rerr))
		}
	}
}

// run 等待原行程結束後套用更新. 換檔 / 安裝前的任何失敗都回傳 error, 且不動
// 既有安裝, 由呼叫端重啟舊版.
func run(pid int, launchPath, file string) error {
	if launchPath == "" || file == "" {
		return fmt.Errorf("缺少必要參數")
	}
	if pid > 0 {
		if err := waitForExit(pid, waitTimeout); err != nil {
			return err
		}
	}
	return applyUpdate(launchPath, file)
}

// waitForExit 輪詢直到 pid 對應行程消失, 或超過 timeout 為止.
func waitForExit(pid int, timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	for {
		if !processAlive(pid) {
			return nil
		}
		if time.Now().After(deadline) {
			return fmt.Errorf("等待原程式結束逾時 (%s)", timeout)
		}
		time.Sleep(200 * time.Millisecond)
	}
}

func displayVersion(v string) string {
	if v == "" {
		return "新版本"
	}
	return v
}

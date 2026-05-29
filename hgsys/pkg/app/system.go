package app

import (
	"path/filepath"
	"runtime"

	"github.com/wailsapp/wails/v3/pkg/application"

	"hgsys/pkg/services"
	"hgsys/pkg/version"
)

// UpdateMarkerFilename 為自我更新重啟前寫入 repo 根目錄的標記檔, 讓下次啟動時
// 能顯示"已由 X 更新為 Y".
const UpdateMarkerFilename = "updated"

// SystemService 為主選單所用之 version / update / about 動作的 binding.
type SystemService struct {
	app      *application.App
	repoRoot string
	testMode bool
}

func NewSystemService(app *application.App, repoRoot string, testMode bool) *SystemService {
	return &SystemService{app: app, repoRoot: repoRoot, testMode: testMode}
}

// SetApp 於 `application.New` 回傳後注入 Wails *App. 參見 BackupService.SetApp.
func (s *SystemService) SetApp(app *application.App) {
	s.app = app
}

// Version 回傳應用程式版本字串.
func (s *SystemService) Version() string {
	return version.String
}

// Platform 回傳目前執行的作業系統 (runtime.GOOS), 例如 "darwin", "windows".
// frontend 依此決定 menu 渲染方式: Mac 使用原生選單列, 其他平台則沿用視窗內
// MenuBar.vue.
func (s *SystemService) Platform() string {
	return runtime.GOOS
}

// TestMode 回報是否帶有 -T 旗標 (即使"已是最新"也強制重啟).
func (s *SystemService) TestMode() bool {
	return s.testMode
}

// PendingUpdateMessage 於標記檔存在 (前次啟動曾進行更新) 時回傳前一版的版本字串,
// 並順帶清除該標記. 無待處理訊息時回傳 "".
func (s *SystemService) PendingUpdateMessage() (string, error) {
	return services.ReadAndClearMarker(filepath.Join(s.repoRoot, UpdateMarkerFilename))
}

// UpdateResult 對應舊版"更新"選單呈現的四種結果: 已是最新版 (test mode → 重啟),
// 已 fast-forward (一律重啟), 錯誤, 或非預期的合併情況 (顯示細節).
type UpdateResult struct {
	State   string `json:"state"`   // "uptodate" | "fastforward" | "unexpected" | "error"
	Detail  string `json:"detail"`  // 給人看的細節 (僅 unexpected / error 使用)
	Version string `json:"version"` // 目前版本, 供顯示用
}

// Update 執行 git fetch + fast-forward + `go install`. 若 fast-forward 成功,
// 會寫入標記檔並重啟 process (該情況下本函式不會回傳). test mode 下, 即使結果
// 為"已是最新版", 也會重啟.
func (s *SystemService) Update() (UpdateResult, error) {
	res := UpdateResult{Version: version.String}
	repoRoot := s.repoRoot
	if repoRoot == "" {
		root, err := services.FindRepoRoot(".")
		if err != nil {
			res.State = "error"
			res.Detail = err.Error()
			return res, nil
		}
		repoRoot = root
	}

	outcome, detail, err := services.PullAndInstall(repoRoot, "origin", "main")
	if err != nil {
		res.State = "error"
		res.Detail = err.Error()
		return res, nil
	}

	switch outcome {
	case services.PullUpToDate:
		if s.testMode {
			s.doRestart(repoRoot)
		}
		res.State = "uptodate"
	case services.PullFastForward:
		s.doRestart(repoRoot)
		// doRestart 不應回傳; 若真的回傳, 則 fall through:
		res.State = "fastforward"
	default:
		res.State = "unexpected"
		res.Detail = detail
	}
	return res, nil
}

func (s *SystemService) doRestart(repoRoot string) {
	_ = services.WriteMarker(filepath.Join(repoRoot, UpdateMarkerFilename), version.String)
	// Unix 下 syscall.Exec 會置換 process. Windows 下會回傳 error, caller 應將此
	// 情況視為"請手動重啟".
	_ = services.Restart(nil)
}

// Exit 關閉應用程式.
func (s *SystemService) Exit() {
	if s.app != nil {
		s.app.Quit()
	}
}

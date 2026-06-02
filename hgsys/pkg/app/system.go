package app

import (
	"runtime"

	"github.com/wailsapp/wails/v3/pkg/application"

	"hgsys/pkg/version"
)

// SystemService 為主選單所用之 version / about / exit 動作的 binding.
type SystemService struct {
	app *application.App
}

func NewSystemService(app *application.App) *SystemService {
	return &SystemService{app: app}
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

// Exit 關閉應用程式.
func (s *SystemService) Exit() {
	if s.app != nil {
		s.app.Quit()
	}
}

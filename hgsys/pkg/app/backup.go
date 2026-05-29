package app

import (
	"context"

	"github.com/wailsapp/wails/v3/pkg/application"

	"hgsys/pkg/services"
)

// BackupService 為 mongodump / mongorestore 的 binding, 透過 Wails event 將
// stderr 逐行送至 frontend. 對話框會監聽 "backup:line" / "backup:done".
type BackupService struct {
	app *application.App
}

func NewBackupService(app *application.App) *BackupService {
	return &BackupService{app: app}
}

// SetApp 在 `application.New` 回傳後, 將 Wails *App 注入 service. binding
// 產生器要求 service 必須於 Options 中傳入, 因此需要 app 參考的 service 改在
// 此處拿回.
func (s *BackupService) SetApp(app *application.App) {
	s.app = app
}

// ResolveRestoreDir 讓對話框可接受 dump 目錄的上層目錄作為輸入.
func (s *BackupService) ResolveRestoreDir(chosen string) string {
	return services.ResolveRestoreDir(chosen)
}

// MissingRestoreFiles 回傳 `savepath` 中缺少的 mongorestore 必要檔案清單.
// 空 slice 表示可直接執行 restore.
func (s *BackupService) MissingRestoreFiles(savepath string) []string {
	return services.MissingRestoreFiles(savepath)
}

// Dump 啟動 mongodump, 並於指令結束時回傳. 每一行 stderr 會以 "backup:line"
// event 送出; 結束時觸發 "backup:done", 內容為錯誤字串或空字串.
func (s *BackupService) Dump(savepath string) error {
	err := services.Dump(context.Background(), savepath, s.emitLine)
	s.emitDone(err)
	return err
}

// Restore 啟動 mongorestore. event 機制與 Dump 相同.
func (s *BackupService) Restore(savepath string) error {
	err := services.Restore(context.Background(), savepath, s.emitLine)
	s.emitDone(err)
	return err
}

func (s *BackupService) emitLine(line string) {
	if s.app != nil {
		s.app.Event.Emit("backup:line", line)
	}
}

func (s *BackupService) emitDone(err error) {
	msg := ""
	if err != nil {
		msg = err.Error()
	}
	if s.app != nil {
		s.app.Event.Emit("backup:done", msg)
	}
}

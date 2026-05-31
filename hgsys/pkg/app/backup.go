package app

import (
	"context"
	"log/slog"
	"time"

	"github.com/wailsapp/wails/v3/pkg/application"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"

	"hgsys/pkg/repository"
	"hgsys/pkg/services"
	"hgsys/pkg/version"
)

// BackupService 為 mongodump / mongorestore 的 binding, 透過 Wails event 將
// stderr 逐行送至 frontend. 對話框會監聽 "backup:line" / "backup:done".
type BackupService struct {
	app *application.App
	// client 僅用於備份時查詢 MongoDB server 版本寫入 metadata; 可為 nil
	// (查不到版本不影響備份).
	client *mongo.Client
}

func NewBackupService(app *application.App, client *mongo.Client) *BackupService {
	return &BackupService{app: app, client: client}
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
	ctx := context.Background()
	info := services.MetaInfo{
		MongoDBVersion: s.serverVersion(ctx),
		AppVersion:     version.String,
	}
	err := services.Dump(ctx, savepath, info, s.emitLine)
	s.emitDone(err)
	return err
}

// serverVersion 透過 buildInfo 取得 MongoDB server 版本字串, 供備份 metadata 使用.
// 連線不存在或查詢失敗時回傳空字串 (metadata 記為未知), 不影響備份本身.
func (s *BackupService) serverVersion(ctx context.Context) string {
	if s.client == nil {
		return ""
	}
	queryCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	var res struct {
		Version string `bson:"version"`
	}
	cmd := bson.D{{Key: "buildInfo", Value: 1}}
	if err := s.client.Database(repository.DatabaseName).RunCommand(queryCtx, cmd).Decode(&res); err != nil {
		slog.Warn("查詢 MongoDB 版本失敗", "err", err)
		return ""
	}
	return res.Version
}

// Restore 啟動 mongorestore. event 機制與 Dump 相同.
func (s *BackupService) Restore(savepath string) error {
	err := services.Restore(context.Background(), savepath, s.emitLine)
	s.emitDone(err)
	return err
}

// LastBackupDir 回傳上次選取的備份目錄, 供前端對話框作為起始目錄; 從未選過時
// 回傳 "".
func (s *BackupService) LastBackupDir() string {
	return services.LoadSettings().BackupDir
}

// LastRestoreDir 回傳上次選取的還原目錄, 供前端對話框作為起始目錄; 從未選過時
// 回傳 "".
func (s *BackupService) LastRestoreDir() string {
	return services.LoadSettings().RestoreDir
}

// SetLastBackupDir 記住備份對話框選取的目錄. 由前端在使用者選完目錄當下呼叫
// (不論之後備份是否成功).
func (s *BackupService) SetLastBackupDir(dir string) {
	if err := services.SaveBackupDir(dir); err != nil {
		slog.Warn("記住備份目錄失敗", "err", err)
	}
}

// SetLastRestoreDir 記住還原對話框選取的目錄. 由前端在使用者選完目錄當下呼叫.
func (s *BackupService) SetLastRestoreDir(dir string) {
	if err := services.SaveRestoreDir(dir); err != nil {
		slog.Warn("記住還原目錄失敗", "err", err)
	}
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

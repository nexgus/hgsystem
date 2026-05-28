package app

import (
	"context"

	"github.com/wailsapp/wails/v3/pkg/application"

	"hgsys/pkg/services"
)

// BackupService binds mongodump / mongorestore and streams stderr lines to the
// frontend via a Wails event. The dialog listens for "backup:line" / "backup:done".
type BackupService struct {
	app *application.App
}

func NewBackupService(app *application.App) *BackupService {
	return &BackupService{app: app}
}

// SetApp wires the Wails *App after `application.New` returns (the binding
// generator requires services to be passed in Options, but services that need
// the app reference get it back here).
func (s *BackupService) SetApp(app *application.App) {
	s.app = app
}

// ResolveRestoreDir lets the dialog accept the parent of a dump directory.
func (s *BackupService) ResolveRestoreDir(chosen string) string {
	return services.ResolveRestoreDir(chosen)
}

// MissingRestoreFiles returns the list of mongorestore-required files absent
// from `savepath`. Empty slice means restore can proceed.
func (s *BackupService) MissingRestoreFiles(savepath string) []string {
	return services.MissingRestoreFiles(savepath)
}

// Dump starts mongodump and returns when the command exits. Each stderr line
// is emitted as the "backup:line" event; "backup:done" fires on completion
// with either an error string or empty.
func (s *BackupService) Dump(savepath string) error {
	err := services.Dump(context.Background(), savepath, s.emitLine)
	s.emitDone(err)
	return err
}

// Restore starts mongorestore. Same eventing as Dump.
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

package app

import (
	"path/filepath"

	"github.com/wailsapp/wails/v3/pkg/application"

	"hgsys/pkg/services"
	"hgsys/pkg/version"
)

// UpdateMarkerFilename is dropped into the repo root before a self-update
// restart so the next launch can display "已由 X 更新為 Y".
const UpdateMarkerFilename = "updated"

// SystemService binds version / update / about actions used by the main menu.
type SystemService struct {
	app      *application.App
	repoRoot string
	testMode bool
}

func NewSystemService(app *application.App, repoRoot string, testMode bool) *SystemService {
	return &SystemService{app: app, repoRoot: repoRoot, testMode: testMode}
}

// SetApp wires the Wails *App after `application.New` returns. See BackupService.SetApp.
func (s *SystemService) SetApp(app *application.App) {
	s.app = app
}

// Version returns the application version string.
func (s *SystemService) Version() string {
	return version.String
}

// TestMode reports whether the -T flag was supplied (forces restart on "up to date").
func (s *SystemService) TestMode() bool {
	return s.testMode
}

// PendingUpdateMessage returns the previous version string if a marker is
// present (the prior launch performed an update). Clears the marker as a side
// effect. Returns "" when there is no pending message.
func (s *SystemService) PendingUpdateMessage() (string, error) {
	return services.ReadAndClearMarker(filepath.Join(s.repoRoot, UpdateMarkerFilename))
}

// UpdateResult mirrors the four outcomes the legacy "更新" menu surfaces:
// up-to-date (test mode → restart), fast-forwarded (always restart), error,
// or unexpected merge analysis (shows detail).
type UpdateResult struct {
	State   string `json:"state"`   // "uptodate" | "fastforward" | "unexpected" | "error"
	Detail  string `json:"detail"`  // human-readable detail (only for unexpected/error)
	Version string `json:"version"` // current version for display
}

// Update runs git fetch + fast-forward + `go install`. On fast-forward it
// writes the marker and restarts the process (this function does not return
// in that path). In test mode an "up to date" result also restarts.
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
		// doRestart should not return; if it does, fall through:
		res.State = "fastforward"
	default:
		res.State = "unexpected"
		res.Detail = detail
	}
	return res, nil
}

func (s *SystemService) doRestart(repoRoot string) {
	_ = services.WriteMarker(filepath.Join(repoRoot, UpdateMarkerFilename), version.String)
	// On Unix syscall.Exec replaces the process. On Windows it returns an error
	// and the caller should treat that as "please restart manually".
	_ = services.Restart(nil)
}

// Exit closes the app.
func (s *SystemService) Exit() {
	if s.app != nil {
		s.app.Quit()
	}
}

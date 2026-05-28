// Command hgsystem is the entry point for the Wails desktop app. It parses
// CLI flags, opens MongoDB, sets up logging, and hands control to Wails.
package main

import (
	"context"
	"embed"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"path/filepath"

	"github.com/wailsapp/wails/v3/pkg/application"

	"hgsys/pkg/app"
	"hgsys/pkg/applog"
	"hgsys/pkg/services"
	"hgsys/pkg/version"
)

// frontend assets. build.sh copies frontend/dist into ./dist before `go build`
// so Go's embed (which cannot use `..`) finds them alongside this file.
//
//go:embed all:dist
var assets embed.FS

func main() {
	var (
		host    = flag.String("H", "localhost", "MongoDB host address (also --host).")
		port    = flag.Int("p", 27017, "MongoDB port number (also --port).")
		test    = flag.Bool("T", false, "Test mode: auto-restart instead of \"up to date\" dialog on Update (also --test).")
		debug   = flag.Bool("d", false, "Enable DEBUG-level console output (also --debug).")
		showVer = flag.Bool("version", false, "Print version and exit.")
	)
	flag.StringVar(host, "host", "localhost", "MongoDB host address.")
	flag.IntVar(port, "port", 27017, "MongoDB port number.")
	flag.BoolVar(test, "test", false, "Test mode.")
	flag.BoolVar(debug, "debug", false, "Enable DEBUG-level console output.")
	flag.Parse()

	if *showVer {
		fmt.Printf("HG System %s\n", version.String)
		return
	}

	if logPath, err := applog.Setup(*debug); err != nil {
		fmt.Fprintf(os.Stderr, "warning: setup logging failed: %v\n", err)
	} else {
		slog.Info("logging initialised", "file", logPath)
	}

	ctx := context.Background()
	client, err := app.Connect(ctx, app.Config{Host: *host, Port: *port})
	if err != nil {
		slog.Error("mongo connect failed", "err", err)
		os.Exit(1)
	}
	defer func() { _ = client.Disconnect(ctx) }()

	repos, err := app.PrepareRepositories(ctx, client)
	if err != nil {
		slog.Error("prepare repositories failed", "err", err)
		os.Exit(1)
	}

	repoRoot := detectRepoRoot()

	customerSvc := app.NewCustomerService(repos)
	worksheetSvc := app.NewWorksheetService(repos)
	searchSvc := app.NewSearchService(repos)
	// Backup/System services need the *App for events / Quit; injected after New.
	backupSvc := app.NewBackupService(nil)
	systemSvc := app.NewSystemService(nil, repoRoot, *test)

	wailsApp := application.New(application.Options{
		Name:        "hgsystem",
		Description: fmt.Sprintf("豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統 (%s)", version.String),
		Services: []application.Service{
			application.NewService(customerSvc),
			application.NewService(worksheetSvc),
			application.NewService(searchSvc),
			application.NewService(backupSvc),
			application.NewService(systemSvc),
		},
		Assets: application.AssetOptions{
			Handler: application.AssetFileServerFS(assets),
		},
		Mac: application.MacOptions{
			ApplicationShouldTerminateAfterLastWindowClosed: true,
		},
	})

	// Now that we have *App, hand it to services that need to emit events / quit.
	backupSvc.SetApp(wailsApp)
	systemSvc.SetApp(wailsApp)

	wailsApp.Window.NewWithOptions(application.WebviewWindowOptions{
		Title: fmt.Sprintf("豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統 (%s)", version.String),
		Mac: application.MacWindow{
			InvisibleTitleBarHeight: 50,
			Backdrop:                application.MacBackdropTranslucent,
			TitleBar:                application.MacTitleBarHiddenInset,
		},
		BackgroundColour: application.NewRGB(255, 255, 255),
		URL:              "/",
		Width:            1400,
		Height:           900,
	})

	if err := wailsApp.Run(); err != nil {
		slog.Error("application exited with error", "err", err)
		os.Exit(1)
	}
}

// detectRepoRoot finds the source repo root so the updater can pull the right
// directory. Falls back to the executable's directory when running from an
// installed binary outside the source tree.
func detectRepoRoot() string {
	if exe, err := os.Executable(); err == nil {
		if root, err := services.FindRepoRoot(filepath.Dir(exe)); err == nil {
			return root
		}
	}
	if cwd, err := os.Getwd(); err == nil {
		if root, err := services.FindRepoRoot(cwd); err == nil {
			return root
		}
	}
	return ""
}

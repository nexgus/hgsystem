// Command hgsystem 為 Wails 桌面應用程式的進入點. 它會解析
// 命令列旗標, 開啟 MongoDB 連線, 設定 logging, 並把控制權交給 Wails.
package main

import (
	"context"
	"embed"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"path/filepath"
	"runtime"

	"github.com/wailsapp/wails/v3/pkg/application"

	"hgsys/pkg/app"
	"hgsys/pkg/applog"
	"hgsys/pkg/repository"
	"hgsys/pkg/services"
	"hgsys/pkg/version"
)

// 前端 assets. build.sh 會在執行 `go build` 之前先把 frontend/dist 複製到 ./dist,
// 這樣 Go 的 embed (不支援 `..`) 才能在這個檔案旁邊找到它們.
//
//go:embed all:dist
var assets embed.FS

func main() {
	var (
		host    = flag.String("H", "localhost", "MongoDB host address (also --host).")
		port    = flag.Int("p", 27017, "MongoDB port number (also --port).")
		test    = flag.Bool("T", false, "Test mode: auto-restart instead of \"up to date\" dialog on Update (also --test).")
		debug   = flag.Bool("d", false, "Enable DEBUG-level console output (also --debug).")
		nodb    = flag.Bool("nodb", false, "Skip MongoDB connection on startup (GUI-only mode, faster start).")
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
	client, err := app.Connect(ctx, app.Config{Host: *host, Port: *port, NoDB: *nodb})
	if err != nil {
		slog.Warn("無法連線到 MongoDB, 以僅檢視 GUI 模式啟動 (資料操作將失敗)", "err", err)
	}
	if client == nil {
		slog.Error("無法建立 mongo client", "err", err)
		os.Exit(1)
	}
	defer func() { _ = client.Disconnect(ctx) }()

	var repos *repository.Repositories
	if *nodb {
		// --nodb 模式下不嘗試清空 search history (該操作也會 5 秒 timeout).
		repos = repository.New(client)
	} else {
		repos, err = app.PrepareRepositories(ctx, client)
		if err != nil {
			slog.Warn("初始化 repository 失敗, 以僅檢視 GUI 模式繼續", "err", err)
			repos = repository.New(client)
		}
	}

	repoRoot := detectRepoRoot()

	customerSvc := app.NewCustomerService(repos)
	worksheetSvc := app.NewWorksheetService(repos)
	searchSvc := app.NewSearchService(repos)
	// Backup / System service 需要 *App 來發送事件 / 結束程式; 在 New 之後再注入.
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

	// 現在有了 *App, 把它交給需要發送事件 / 結束程式的 service.
	backupSvc.SetApp(wailsApp)
	systemSvc.SetApp(wailsApp)

	// macOS 上以原生選單列取代視窗內 MenuBar.vue (前端依 SystemService.Platform()
	// 決定不渲染 MenuBar). 其他平台維持視窗內 menu, 不在此處建立原生 menu.
	if runtime.GOOS == "darwin" {
		setupMacMenu(wailsApp)
	}

	wailsApp.Window.NewWithOptions(application.WebviewWindowOptions{
		Title: fmt.Sprintf("豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統 (%s)", version.String),
		// 不指定 BackgroundColour, 讓 native window 透出 → 由前端 CSS 的
		// color-scheme + Canvas 系統色決定亮 / 暗主題, 與 macOS 系統設定一致.
		URL:    "/",
		Width:  1400,
		Height: 900,
	})

	if err := wailsApp.Run(); err != nil {
		slog.Error("application exited with error", "err", err)
		os.Exit(1)
	}
}

// setupMacMenu 建立 macOS 原生選單列. 「系統」「資料」項目對應視窗內 MenuBar.vue
// 的功能, click 時透過 event 通知前端, 由前端共用同一組 handler.
//
// Edit / Window 為 Mac 標準角色 (剪下 / 複製 / 貼上 / Minimize / Zoom 等),
// AppMenu 角色提供 About / Quit / Hide 等系統慣例項目.
func setupMacMenu(app *application.App) {
	menu := app.NewMenu()
	menu.AddRole(application.AppMenu)

	sys := menu.AddSubmenu("系統")
	sys.Add("更新").OnClick(func(*application.Context) { app.Event.Emit("menu:update") })
	sys.Add("有關").OnClick(func(*application.Context) { app.Event.Emit("menu:about") })
	sys.AddSeparator()
	sys.Add("離開").OnClick(func(*application.Context) { app.Event.Emit("menu:exit") })

	data := menu.AddSubmenu("資料")
	data.Add("備份").OnClick(func(*application.Context) { app.Event.Emit("menu:backup") })
	data.Add("還原").OnClick(func(*application.Context) { app.Event.Emit("menu:restore") })

	menu.AddRole(application.EditMenu)
	menu.AddRole(application.WindowMenu)

	app.Menu.SetApplicationMenu(menu)
}

// detectRepoRoot 找出原始碼 repo 的根目錄, 讓 updater 可以對正確的目錄做 pull.
// 若是從原始碼樹之外的已安裝執行檔執行, 則回退到執行檔所在的目錄.
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

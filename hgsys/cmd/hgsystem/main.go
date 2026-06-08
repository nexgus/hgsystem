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

	"github.com/wailsapp/wails/v3/pkg/application"

	"hgsys/pkg/app"
	"hgsys/pkg/applog"
	"hgsys/pkg/repository"
	"hgsys/pkg/version"
)

// 前端 assets. build.sh 會在執行 `go build` 之前先把 frontend/dist 複製到 ./dist,
// 這樣 Go 的 embed (不支援 `..`) 才能在這個檔案旁邊找到它們.
//
//go:embed all:dist
var assets embed.FS

// iconBytes 為應用程式圖示, 取自 Noto Emoji 的 eyeglasses (U+1F453), SIL OFL 1.1
// 授權. 傳給 application.Options.Icon 供視窗 / 工作列使用; Windows exe 的檔案
// 圖示另由 build.sh 產生的 rsrc_windows_amd64.syso 提供 (同一張 icon).
//
//go:embed icon.png
var iconBytes []byte

func main() {
	// macOS 應用程式選單的粗體標題取自主 bundle 的 CFBundleName; 於建立
	// application 前先設為應用顯示名稱, 使其顯示「HGSystem」而非裸執行檔的
	// 檔名. 非 darwin 平台為 no-op. 參見 appname_darwin.go.
	setAppName(appDisplayName)

	var (
		host    = flag.String("H", "localhost", "MongoDB host address (also --host).")
		port    = flag.Int("p", 27017, "MongoDB port number (also --port).")
		debug   = flag.Bool("d", false, "Enable DEBUG-level console output (also --debug).")
		nodb    = flag.Bool("nodb", false, "Skip MongoDB connection on startup (GUI-only mode, faster start).")
		showVer = flag.Bool("version", false, "Print version and exit.")
	)
	flag.StringVar(host, "host", "localhost", "MongoDB host address.")
	flag.IntVar(port, "port", 27017, "MongoDB port number.")
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

	customerSvc := app.NewCustomerService(repos)
	worksheetSvc := app.NewWorksheetService(repos)
	searchSvc := app.NewSearchService(repos)
	titleSvc := app.NewTitleService(repos)
	// BackupService 需要 *App 來發送事件; 在 New 之後再注入.
	backupSvc := app.NewBackupService(nil, client)
	systemSvc := app.NewSystemService()
	// UpdateService 需要 *App (發送進度事件 / 關閉應用程式) 與內嵌的 hgupgrade;
	// 同樣在 New 之後注入.
	updateSvc := app.NewUpdateService()

	wailsApp := application.New(application.Options{
		Name:        "hgsystem",
		Description: "豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統",
		Icon:        iconBytes,
		Services: []application.Service{
			application.NewService(customerSvc),
			application.NewService(worksheetSvc),
			application.NewService(searchSvc),
			application.NewService(titleSvc),
			application.NewService(backupSvc),
			application.NewService(systemSvc),
			application.NewService(updateSvc),
		},
		Assets: application.AssetOptions{
			Handler: application.AssetFileServerFS(assets),
		},
		Mac: application.MacOptions{
			ApplicationShouldTerminateAfterLastWindowClosed: true,
		},
	})

	// 現在有了 *App, 把它交給需要發送事件的 service.
	backupSvc.SetApp(wailsApp)
	updateSvc.SetApp(wailsApp)
	updateSvc.SetUpgrader(hgupgradeBinary, hgupgradeName)

	// 依平台慣例建立原生應用程式選單 (macOS / Windows 皆然). 參見 menu.go.
	wailsApp.Menu.SetApplicationMenu(buildAppMenu(wailsApp))

	wailsApp.Window.NewWithOptions(application.WebviewWindowOptions{
		Title: "豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統",
		// 不指定 BackgroundColour, 讓 native window 透出 → 由前端 CSS 的
		// color-scheme + Canvas 系統色決定亮 / 暗主題, 與 macOS 系統設定一致.
		URL:    "/",
		// 啟動時即最大化視窗 (macOS 為 zoom 填滿可用區域, Windows 為最大化).
		// Width / Height 在此情況下作為使用者取消最大化後的還原尺寸.
		StartState: application.WindowStateMaximised,
		Width:      1600,
		Height:     900,
		// macOS 的 application menu 一律為全域選單列, 但 Windows / Linux 預設不會
		// 把它掛到視窗上, 需視窗明確選用. 開啟此旗標讓上方以 SetApplicationMenu
		// 設定的選單在 Windows / Linux 顯示為視窗選單列; macOS 為 no-op.
		UseApplicationMenu: true,
	})

	if err := wailsApp.Run(); err != nil {
		slog.Error("application exited with error", "err", err)
		os.Exit(1)
	}
}

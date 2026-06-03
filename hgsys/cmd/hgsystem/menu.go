package main

import (
	"embed"
	"runtime"

	"github.com/wailsapp/wails/v3/pkg/application"
)

// appDisplayName 為選單與「關於」視窗使用的應用顯示名稱. 不同於
// application.Options.Name; 全名 (豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統) 過長,
// 不適合放入選單, 故另取此短名.
const appDisplayName = "HGSystem"

// aboutWindowName 為「關於」視窗的 window name, 用以確保同時只有一個此視窗.
// 視窗以 URL hash #about 載入; 前端 (main.ts / About.vue) 據此掛載「關於」元件.
// 第三方授權為視窗內的分頁, 不另設選單項.
const aboutWindowName = "about"

// menuIconFS 內嵌 Windows 主選單各子項的圖示. Windows 的子選單會在項目左側預留一欄
// 放置圖示, 未設定時該欄留白而顯得突兀, 故為每個子項填入對應圖示 (見 buildDefaultMenu).
// 圖示為 16x16 PNG, 取自 Google Material Symbols (google/material-design-icons,
// Apache-2.0), 以填滿樣式 (fill1) 渲染為寶藍色 #3B82F6. 選此色因 Windows 深色模式下
// Wails 會將選單背景改為深色 (約 #212121), 純黑圖示會看不見; #3B82F6 於淺色與深色選單
// 背景下對比皆達圖形可辨標準. 檔名對應的字符:
//
//	quit=logout          backup=save         restore=settings_backup_restore
//	undo=undo            redo=redo           cut=content_cut
//	copy=content_copy    paste=content_paste selectall=select_all
//	actualsize=search    zoomin=zoom_in      zoomout=zoom_out
//	fullscreen=fullscreen update=update      about=info
//
// macOS 依平台慣例不於選單放圖示, 故僅 buildDefaultMenu 會用到這些圖示; 授權標示見
// frontend/src/licenses.ts.
//
//go:embed menuicons/*.png
var menuIconFS embed.FS

// menuIcon 讀取 menuicons/ 內指定名稱的選單圖示 (PNG). 圖示於編譯期內嵌, 正常情況下
// 必定存在; 萬一讀取失敗則回傳 nil (SetBitmap(nil) 為無作用), 不影響選單其餘運作.
func menuIcon(name string) []byte {
	b, err := menuIconFS.ReadFile("menuicons/" + name + ".png")
	if err != nil {
		return nil
	}
	return b
}

// buildAppMenu 依平台慣例組裝應用程式選單.
//
// macOS 採 App / 資料 / 編輯 / 顯示 / 視窗 結構, 「關於」與「檢查更新…」置於
// App 選單; 第三方授權於「關於」視窗內以分頁呈現, 依 macOS 慣例 (授權 / 致謝
// 放在 About 視窗) 不另設說明選單. 其他平台 (Windows) 採 檔案 / 資料 / 編輯 /
// 顯示 / 說明 結構, 「檢查更新…」與「關於」置於說明選單. 「檢查更新…」以
// menu:update event 通知前端執行檢查流程 (見 frontend 的 App.vue). 選單文案
// 全為繁體中文.
//
// Arg(s):
//
//	app: 已建立的 application, 供選單動作開啟「關於」視窗與通知前端.
//
// Return(s):
//
//	組裝完成的應用程式選單
func buildAppMenu(app *application.App) *application.Menu {
	menu := application.NewMenu()
	if runtime.GOOS == "darwin" {
		buildDarwinMenu(app, menu)
	} else {
		buildDefaultMenu(app, menu)
	}
	return menu
}

// buildDarwinMenu 組裝 macOS 慣例的應用程式選單.
func buildDarwinMenu(app *application.App, menu *application.Menu) {
	// 應用程式選單 (標題為應用顯示名稱), 含「關於」與標準的服務 / 隱藏 / 結束.
	appSub := menu.AddSubmenu(appDisplayName)
	appSub.Add("關於 " + appDisplayName).OnClick(func(*application.Context) {
		showAbout(app)
	})
	// macOS 慣例: 「檢查更新…」置於 App 選單「關於」下方.
	appSub.Add("檢查更新…").OnClick(func(*application.Context) {
		app.Event.Emit("menu:update")
	})
	appSub.AddSeparator()
	appSub.AddRole(application.ServicesMenu)
	appSub.AddSeparator()
	appSub.AddRole(application.Hide)
	appSub.AddRole(application.HideOthers)
	appSub.AddRole(application.UnHide)
	appSub.AddSeparator()
	appSub.AddRole(application.Quit)
	setRoleLabel(appSub, application.ServicesMenu, "服務")
	setRoleLabel(appSub, application.Hide, "隱藏 "+appDisplayName)
	setRoleLabel(appSub, application.HideOthers, "隱藏其他")
	setRoleLabel(appSub, application.UnHide, "全部顯示")
	setRoleLabel(appSub, application.Quit, "結束 "+appDisplayName)

	addDataMenu(app, menu)
	addEditMenu(menu)
	addViewMenu(menu)

	// 視窗選單.
	winSub := menu.AddSubmenu("視窗")
	winSub.AddRole(application.Minimise)
	winSub.AddRole(application.Zoom)
	winSub.AddSeparator()
	winSub.AddRole(application.Front)
	setRoleLabel(winSub, application.Minimise, "最小化")
	setRoleLabel(winSub, application.Zoom, "縮放")
	setRoleLabel(winSub, application.Front, "全部移至最前")
}

// buildDefaultMenu 組裝 Windows (及其他非 macOS 平台) 慣例的應用程式選單.
func buildDefaultMenu(app *application.App, menu *application.Menu) {
	fileSub := menu.AddSubmenu("檔案")
	fileSub.AddRole(application.Quit)
	setRoleLabel(fileSub, application.Quit, "結束")

	backup, restore := addDataMenu(app, menu)
	editSub := addEditMenu(menu)
	viewSub := addViewMenu(menu)

	helpSub := menu.AddSubmenu("說明")
	// Windows 慣例: 「檢查更新…」與「關於」同置於「說明」選單.
	update := helpSub.Add("檢查更新…")
	update.OnClick(func(*application.Context) { app.Event.Emit("menu:update") })
	helpSub.AddSeparator()
	about := helpSub.Add("關於 " + appDisplayName)
	about.OnClick(func(*application.Context) { showAbout(app) })

	// Windows 子選單會在項目左側預留圖示欄; 逐項填入對應圖示, 避免該欄留白而顯得突兀.
	// 沿用內建 role 的標準項目以 setRoleBitmap 透過 role 定位, 其餘項目直接設定.
	setRoleBitmap(fileSub, application.Quit, menuIcon("quit"))
	backup.SetBitmap(menuIcon("backup"))
	restore.SetBitmap(menuIcon("restore"))
	setRoleBitmap(editSub, application.Undo, menuIcon("undo"))
	setRoleBitmap(editSub, application.Redo, menuIcon("redo"))
	setRoleBitmap(editSub, application.Cut, menuIcon("cut"))
	setRoleBitmap(editSub, application.Copy, menuIcon("copy"))
	setRoleBitmap(editSub, application.Paste, menuIcon("paste"))
	setRoleBitmap(editSub, application.SelectAll, menuIcon("selectall"))
	setRoleBitmap(viewSub, application.ResetZoom, menuIcon("actualsize"))
	setRoleBitmap(viewSub, application.ZoomIn, menuIcon("zoomin"))
	setRoleBitmap(viewSub, application.ZoomOut, menuIcon("zoomout"))
	setRoleBitmap(viewSub, application.ToggleFullscreen, menuIcon("fullscreen"))
	update.SetBitmap(menuIcon("update"))
	about.SetBitmap(menuIcon("about"))
}

// addDataMenu 加入「資料」選單. 備份 / 還原需主視窗前端的目錄挑選與對話框流程,
// 故以 event 通知前端 (App.vue 的 menu:backup / menu:restore handler) 處理. 回傳
// 備份 / 還原兩個項目, 供 Windows 主選單為其加上圖示; 其他平台呼叫端可忽略回傳值.
func addDataMenu(app *application.App, menu *application.Menu) (backup, restore *application.MenuItem) {
	dataSub := menu.AddSubmenu("資料")
	backup = dataSub.Add("備份")
	backup.OnClick(func(*application.Context) { app.Event.Emit("menu:backup") })
	restore = dataSub.Add("還原")
	restore.OnClick(func(*application.Context) { app.Event.Emit("menu:restore") })
	return
}

// addEditMenu 加入編輯選單. 各項目沿用 Wails 內建 role 以保有對應的系統行為
// (例如 macOS 上的剪下 / 複製 / 貼上 / 全選與標準快捷鍵), 僅將標籤改為中文.
func addEditMenu(menu *application.Menu) *application.Menu {
	editSub := menu.AddSubmenu("編輯")
	editSub.AddRole(application.Undo)
	editSub.AddRole(application.Redo)
	editSub.AddSeparator()
	editSub.AddRole(application.Cut)
	editSub.AddRole(application.Copy)
	editSub.AddRole(application.Paste)
	editSub.AddRole(application.SelectAll)
	setRoleLabel(editSub, application.Undo, "復原")
	setRoleLabel(editSub, application.Redo, "重做")
	setRoleLabel(editSub, application.Cut, "剪下")
	setRoleLabel(editSub, application.Copy, "複製")
	setRoleLabel(editSub, application.Paste, "貼上")
	setRoleLabel(editSub, application.SelectAll, "全選")
	return editSub
}

// addViewMenu 加入顯示選單. 僅提供縮放與全螢幕, 刻意不放重新載入 / 開發者工具,
// 避免重載前端後因單次查詢語意而顯示空白且不再查詢.
func addViewMenu(menu *application.Menu) *application.Menu {
	viewSub := menu.AddSubmenu("顯示")
	viewSub.AddRole(application.ResetZoom)
	viewSub.AddRole(application.ZoomIn)
	viewSub.AddRole(application.ZoomOut)
	viewSub.AddSeparator()
	viewSub.AddRole(application.ToggleFullscreen)
	setRoleLabel(viewSub, application.ResetZoom, "實際大小")
	setRoleLabel(viewSub, application.ZoomIn, "放大")
	setRoleLabel(viewSub, application.ZoomOut, "縮小")
	setRoleLabel(viewSub, application.ToggleFullscreen, "切換全螢幕")
	return viewSub
}

// setRoleLabel 將選單內指定 role 的項目標籤改為中文; 找不到時靜默略過.
func setRoleLabel(m *application.Menu, role application.Role, label string) {
	if item := m.FindByRole(role); item != nil {
		item.SetLabel(label)
	}
}

// setRoleBitmap 為選單內指定 role 的項目設定圖示; 找不到 role 或 png 為 nil 時靜默
// 略過. 供 Windows 主選單為沿用內建 role 的標準項目 (剪下 / 複製 / 放大等) 加圖示.
func setRoleBitmap(m *application.Menu, role application.Role, png []byte) {
	if png == nil {
		return
	}
	if item := m.FindByRole(role); item != nil {
		item.SetBitmap(png)
	}
}

// showAbout 開啟 (或聚焦既有的)「關於」視窗.
//
// 以 window name 確保同時只有一個「關於」視窗: 已存在則聚焦, 否則新建一個
// 小尺寸視窗. 第三方授權為視窗內的分頁, 由使用者於視窗內切換.
func showAbout(app *application.App) {
	if w, ok := app.Window.GetByName(aboutWindowName); ok {
		w.Focus()
		return
	}

	app.Window.NewWithOptions(application.WebviewWindowOptions{
		Name:  aboutWindowName,
		Title: "關於 " + appDisplayName,
		// 寬度取能舒適完整顯示「第三方授權」表格之值; 表格採固定佈局 (見
		// About.vue), 內容會自動換行, 故任何寬度皆不會出現水平捲軸, 此值僅為易讀.
		Width:     600,
		Height:    600,
		MinWidth:  380,
		MinHeight: 420,
		URL:       "/#" + aboutWindowName,
	})
}

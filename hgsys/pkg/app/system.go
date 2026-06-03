package app

import (
	"runtime"
	"strings"

	"github.com/wailsapp/wails/v3/pkg/application"

	"hgsys/pkg/version"
)

// SystemService 提供「關於」視窗所需的版本與環境資訊綁定.
type SystemService struct{}

func NewSystemService() *SystemService {
	return &SystemService{}
}

// AboutInfo 為「關於」視窗顯示的版本與環境資訊.
//
// 由 GetAbout 於 Go 端組裝; WebView 引擎字串另由前端讀取 navigator.userAgent
// 取得, 不在此結構內. WebView2 僅 Windows 平台有值.
type AboutInfo struct {
	AppName   string `json:"appName"`   // 顯示用名稱 (HGSystem)
	FullName  string `json:"fullName"`  // 應用全名
	Version   string `json:"version"`   // 語意化版本號
	Commit    string `json:"commit"`    // git commit hash, 未注入時為替代文字
	BuildDate string `json:"buildDate"` // 編譯機器當地時間 (含時區 offset), 未注入時為替代文字
	GoVersion string `json:"goVersion"` // 編譯用 Go 版本
	OS        string `json:"os"`        // 人類可讀的作業系統名稱與版本
	Platform  string `json:"platform"`  // GOOS/GOARCH (例如 darwin/arm64)
	WebView2  string `json:"webView2"`  // Windows WebView2 runtime 版本, 其他平台為空字串
	Copyright string `json:"copyright"` // 著作權字樣
}

// GetAbout 組裝並回傳「關於」視窗所需的版本與環境資訊.
//
// 版本欄位取自 version 套件 (編譯期注入); 未注入 (例如直接以 go run 啟動)
// 時改填替代文字. 作業系統與 WebView2 版本取自 Wails 的 Environment.Info.
func (s *SystemService) GetAbout() AboutInfo {
	const devPlaceholder = "(開發版本)"

	commit := version.GitCommitHash
	if !version.Injected(commit) {
		commit = devPlaceholder
	}
	buildDate := version.BuildDate
	if !version.Injected(buildDate) {
		buildDate = devPlaceholder
	}
	goVer := version.GoVersion
	if !version.Injected(goVer) {
		// 直接以 go run 啟動時改用執行期的 Go 版本.
		goVer = runtime.Version()
	}

	info := application.Get().Env.Info()
	osName := runtime.GOOS
	webView2 := ""
	if info.OSInfo != nil {
		osName = formatOS(info.OSInfo.Branding, info.OSInfo.Name, info.OSInfo.Version)
	}
	if v, ok := info.PlatformInfo["WebView2"].(string); ok {
		webView2 = v
	}

	return AboutInfo{
		AppName:   "HGSystem",
		FullName:  "豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統",
		Version:   version.String,
		Commit:    commit,
		BuildDate: buildDate,
		GoVersion: goVer,
		OS:        osName,
		Platform:  runtime.GOOS + "/" + runtime.GOARCH,
		WebView2:  webView2,
		Copyright: "© 2026 豪格鐘錶隱形眼鏡公司",
	}
}

// formatOS 將作業系統資訊組成單一人類可讀字串.
//
// 以 branding (品牌名, 例如 macOS Tahoe) 為主, 缺少時退回 name; 若該字串
// 尚未包含版本號, 再附加 version. 藉此避免 "MacOS 26.0 26.0" 之類的重複.
func formatOS(branding, name, version string) string {
	base := strings.TrimSpace(branding)
	if base == "" {
		base = strings.TrimSpace(name)
	}
	version = strings.TrimSpace(version)
	if version != "" && version != "Unknown" && !strings.Contains(base, version) {
		base = strings.TrimSpace(base + " " + version)
	}
	return base
}

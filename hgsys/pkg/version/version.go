package version

// String 為給人看的應用程式版本字串. 用於視窗標題與「關於」視窗.
const String = "0.9.0"

// GitCommitHash, GoVersion 與 BuildDate 由 build.sh 於建置時透過 -ldflags 注入.
// 以 `go run` 臨時執行時, 預設為空字串. BuildDate 為編譯機器當地時間
// (ISO 8601 含時區 offset, 形如 2026-06-03T08:19:01+0800).
var (
	GitCommitHash string
	GoVersion     string
	BuildDate     string
)

// Injected 回傳 s 是否已於編譯期由 build.sh 以 -ldflags 注入實際值. 未注入時
// (例如直接以 go run 啟動) 維持空字串, 此時回傳 false, 供呼叫端改顯示替代文字.
func Injected(s string) bool {
	return s != ""
}

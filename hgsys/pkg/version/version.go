package version

// String 為給人看的應用程式版本字串. 用於視窗標題, "有關"對話框, 以及自我
// 更新標記檔.
const String = "0.7.0"

// GitCommitHash 與 GoVersion 由 build.sh 於建置時透過 -ldflags 注入.
// 以 `go run` 臨時執行時, 預設為空字串.
var (
	GitCommitHash string
	GoVersion     string
)

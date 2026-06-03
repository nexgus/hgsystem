// Package repo 透過各程式碼託管平台的 API 查詢儲存庫資訊.
// 使用前須先以 NewRepoFinder 建立 RepoFinder; 目前 source 僅支援 "github",
// 且僅讀取 public repo.
package repo

import (
	"fmt"
	"net/http"
	"time"
)

// SourceGitHub 為目前唯一支援的 source.
const SourceGitHub = "github"

// httpTimeout 為單一 HTTP 請求的逾時上限.
const httpTimeout = 30 * time.Second

// Asset 對應 release 內單一可下載檔案.
type Asset struct {
	Name               string
	Size               int64
	BrowserDownloadURL string
}

// Release 為單一 release 的彙整結果.
type Release struct {
	Name       string   // release 名稱
	TagName    string   // release 對應的 tag
	Draft      bool     // 是否為草稿
	Prerelease bool     // 是否為預先發行
	CommitHash string   // TagName 所指向 commit 的 hash; 找不到對應 tag 時為空字串
	Tags       []string // 指向同一 commit 的所有 tag
	Assets     []Asset  // 可供下載的檔案
}

// ReleaseReport 為 GetAllReleases 的回傳結構, 涵蓋一個儲存庫的所有 release.
type ReleaseReport struct {
	Owner    string
	Repo     string
	Releases []Release
}

// authMethod 表示 RepoFinder 實際採用的認證方式.
type authMethod int

const (
	authNone     authMethod = iota // 不認證
	authPassword                   // 以 password 認證
	authKeyfile                    // 以 keyfile 認證
)

// RepoFinder 封裝對單一 source 的存取設定與認證.
type RepoFinder struct {
	source   string
	username string
	password string
	keyfile  string
	auth     authMethod
	client   *http.Client
}

// NewRepoFinder 建立 RepoFinder. source 目前僅接受 "github"; username / password /
// keyfile 為 source 的認證資訊, 各自可為 nil 或 string. 若 keyfile 與 password
// 皆有指定, 則 keyfile 優先.
func NewRepoFinder(source string, username, password, keyfile any) (*RepoFinder, error) {
	if source != SourceGitHub {
		return nil, fmt.Errorf("不支援的 source %q, 目前僅支援 %q", source, SourceGitHub)
	}

	u, err := normalizeCred("username", username)
	if err != nil {
		return nil, err
	}
	p, err := normalizeCred("password", password)
	if err != nil {
		return nil, err
	}
	k, err := normalizeCred("keyfile", keyfile)
	if err != nil {
		return nil, err
	}

	f := &RepoFinder{
		source:   source,
		username: u,
		password: p,
		keyfile:  k,
		client:   &http.Client{Timeout: httpTimeout},
	}

	// keyfile 與 password 都有時 keyfile 優先.
	switch {
	case k != "":
		f.auth = authKeyfile
	case p != "":
		f.auth = authPassword
	default:
		f.auth = authNone
	}

	return f, nil
}

// GetAllReleases 回傳 repo 的所有 release. repo 須為 "owner/repo" 格式
// (例: "nexgus/hgsystem").
func (f *RepoFinder) GetAllReleases(repo string) (*ReleaseReport, error) {
	switch f.source {
	case SourceGitHub:
		return f.githubGetAllReleases(repo)
	default:
		return nil, fmt.Errorf("不支援的 source %q", f.source)
	}
}

// normalizeCred 將認證參數正規化為 string. nil 視為未指定 (空字串);
// 非 nil 且非 string 則回 error.
func normalizeCred(name string, v any) (string, error) {
	switch t := v.(type) {
	case nil:
		return "", nil
	case string:
		return t, nil
	default:
		return "", fmt.Errorf("%s 必須為 string 或 nil, 但收到 %T", name, v)
	}
}

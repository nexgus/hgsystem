package repo

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

const (
	githubAPIBase = "https://api.github.com"
	githubPerPage = 100
	githubAPIVer  = "2022-11-28"
	githubUA      = "hgsystem-repo-finder"

	// githubOverallTimeout 限制單次 GetAllReleases 的總耗時 (含分頁與多個端點).
	githubOverallTimeout = 60 * time.Second
)

// ghAsset / ghRelease / ghTag 對應 GitHub REST API 的回應, 僅取用到的欄位.
type ghAsset struct {
	Name               string `json:"name"`
	Size               int64  `json:"size"`
	BrowserDownloadURL string `json:"browser_download_url"`
}

type ghRelease struct {
	Name       string    `json:"name"`
	TagName    string    `json:"tag_name"`
	Draft      bool      `json:"draft"`
	Prerelease bool      `json:"prerelease"`
	Assets     []ghAsset `json:"assets"`
}

// ghTag 的 commit.sha 對 annotated tag 已解參考到實際 commit, 即所要的 hash.
type ghTag struct {
	Name   string `json:"name"`
	Commit struct {
		SHA string `json:"sha"`
	} `json:"commit"`
}

// githubGetAllReleases 以 GitHub REST API 彙整 repo 的所有 release.
func (f *RepoFinder) githubGetAllReleases(repo string) (*ReleaseReport, error) {
	owner, name, err := splitOwnerRepo(repo)
	if err != nil {
		return nil, err
	}

	ctx, cancel := context.WithTimeout(context.Background(), githubOverallTimeout)
	defer cancel()

	releases, err := f.githubFetchReleases(ctx, owner, name)
	if err != nil {
		return nil, fmt.Errorf("取得 releases 失敗: %w", err)
	}
	tags, err := f.githubFetchTags(ctx, owner, name)
	if err != nil {
		return nil, fmt.Errorf("取得 tags 失敗: %w", err)
	}

	// 建立 tag 名稱 -> commit sha, 以及 commit sha -> 多個 tag 名稱的對照.
	tagToSHA := make(map[string]string, len(tags))
	shaToTags := make(map[string][]string, len(tags))
	for _, t := range tags {
		tagToSHA[t.Name] = t.Commit.SHA
		shaToTags[t.Commit.SHA] = append(shaToTags[t.Commit.SHA], t.Name)
	}

	report := &ReleaseReport{Owner: owner, Repo: name}
	for _, r := range releases {
		rel := Release{
			Name:       r.Name,
			TagName:    r.TagName,
			Draft:      r.Draft,
			Prerelease: r.Prerelease,
		}
		if sha, ok := tagToSHA[r.TagName]; ok {
			rel.CommitHash = sha
			rel.Tags = shaToTags[sha]
		}
		for _, a := range r.Assets {
			rel.Assets = append(rel.Assets, Asset{
				Name:               a.Name,
				Size:               a.Size,
				BrowserDownloadURL: a.BrowserDownloadURL,
			})
		}
		report.Releases = append(report.Releases, rel)
	}
	return report, nil
}

// githubFetchReleases 取得所有 release, 自動處理分頁.
func (f *RepoFinder) githubFetchReleases(ctx context.Context, owner, name string) ([]ghRelease, error) {
	var all []ghRelease
	for page := 1; ; page++ {
		url := fmt.Sprintf("%s/repos/%s/%s/releases?per_page=%d&page=%d", githubAPIBase, owner, name, githubPerPage, page)
		var batch []ghRelease
		if err := f.githubGetJSON(ctx, url, &batch); err != nil {
			return nil, err
		}
		all = append(all, batch...)
		if len(batch) < githubPerPage {
			break
		}
	}
	return all, nil
}

// githubFetchTags 取得所有 tag, 自動處理分頁.
func (f *RepoFinder) githubFetchTags(ctx context.Context, owner, name string) ([]ghTag, error) {
	var all []ghTag
	for page := 1; ; page++ {
		url := fmt.Sprintf("%s/repos/%s/%s/tags?per_page=%d&page=%d", githubAPIBase, owner, name, githubPerPage, page)
		var batch []ghTag
		if err := f.githubGetJSON(ctx, url, &batch); err != nil {
			return nil, err
		}
		all = append(all, batch...)
		if len(batch) < githubPerPage {
			break
		}
	}
	return all, nil
}

// githubGetJSON 對指定 URL 發出 GET 請求並將 JSON 解碼至 out.
func (f *RepoFinder) githubGetJSON(ctx context.Context, url string, out any) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	req.Header.Set("User-Agent", githubUA)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("X-GitHub-Api-Version", githubAPIVer)
	// keyfile 屬 SSH 用途, REST/HTTPS 用不到; 僅當有效認證為 password (視為 token)
	// 時才帶 Authorization, 以提高未認證的速率上限.
	if f.auth == authPassword {
		req.Header.Set("Authorization", "Bearer "+f.password)
	}

	resp, err := f.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("GET %s 回傳 %s", url, resp.Status)
	}

	if err := json.NewDecoder(resp.Body).Decode(out); err != nil {
		return fmt.Errorf("解析回應失敗: %w", err)
	}
	return nil
}

// splitOwnerRepo 將 "owner/repo" 拆成兩段, 格式不符則回 error.
func splitOwnerRepo(s string) (owner, name string, err error) {
	parts := strings.Split(s, "/")
	if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
		return "", "", fmt.Errorf("repo 需為 \"owner/repo\" 格式, 但收到 %q", s)
	}
	return parts[0], parts[1], nil
}

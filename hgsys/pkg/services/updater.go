package services

import (
	"errors"
	"fmt"
	"log/slog"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"

	"github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/plumbing"
)

// PullResult 列舉 `PullAndInstall` 實際執行的結果.
type PullResult int

const (
	PullUpToDate     PullResult = 0 // 已位於 remote tip; 不需重啟
	PullFastForward  PullResult = 1 // 已 fast-forward; caller 應呼叫 Restart
	PullUnexpected   PullResult = 2 // 非 fast-forward, 或找不到 remote
)

// FindRepoRoot 從 `startDir` 往上搜尋, 尋找含 `.git` 目錄的位置.
func FindRepoRoot(startDir string) (string, error) {
	cur, err := filepath.Abs(startDir)
	if err != nil {
		return "", err
	}
	for {
		if info, err := os.Stat(filepath.Join(cur, ".git")); err == nil && info.IsDir() {
			return cur, nil
		}
		parent := filepath.Dir(cur)
		if parent == cur {
			return "", fmt.Errorf("no git repository found above %s", startDir)
		}
		cur = parent
	}
}

// PullAndInstall 從 `remoteName` fetch, 並對 `branch` 進行 fast-forward;
// 若 `main` 不存在則退回 `master` (對齊舊版行為).
// 僅能乾淨處理「已是最新」與「fast-forward」兩種情況; 其他情況一律回傳
// PullUnexpected 並附上 detail 字串.
//
// fast-forward 完成後, 會以 `go install` 重新編譯 Go 執行檔, 讓下次 exec 載入
// 新版程式碼. 若 PATH 中沒有 Go toolchain, 則跳過編譯步驟, caller 仍會收到
// PullFastForward — 此時 Restart 會 re-exec 原本的執行檔.
func PullAndInstall(repoRoot, remoteName, branch string) (PullResult, string, error) {
	logger := slog.Default()
	if remoteName == "" {
		remoteName = "origin"
	}
	if branch == "" {
		branch = "main"
	}

	repo, err := git.PlainOpen(repoRoot)
	if err != nil {
		return PullUnexpected, "", fmt.Errorf("open repo: %w", err)
	}

	remote, err := repo.Remote(remoteName)
	if err != nil {
		return PullUnexpected, fmt.Sprintf("remote '%s' not found", remoteName), nil
	}
	if err := remote.Fetch(&git.FetchOptions{RemoteName: remoteName}); err != nil && !errors.Is(err, git.NoErrAlreadyUpToDate) {
		return PullUnexpected, "", fmt.Errorf("fetch: %w", err)
	}

	refName, remoteHash, err := resolveRemoteRef(repo, remoteName, branch)
	if err != nil {
		return PullUnexpected, fmt.Sprintf("cannot find %s/%s or %s/master", remoteName, branch, remoteName), nil
	}
	logger.Info("update: resolved remote ref", "ref", refName)

	head, err := repo.Head()
	if err != nil {
		return PullUnexpected, "", fmt.Errorf("read HEAD: %w", err)
	}

	if head.Hash() == remoteHash {
		return PullUpToDate, "", nil
	}

	localCommit, err := repo.CommitObject(head.Hash())
	if err != nil {
		return PullUnexpected, "", fmt.Errorf("local commit: %w", err)
	}
	remoteCommit, err := repo.CommitObject(remoteHash)
	if err != nil {
		return PullUnexpected, "", fmt.Errorf("remote commit: %w", err)
	}
	isAncestor, err := localCommit.IsAncestor(remoteCommit)
	if err != nil {
		return PullUnexpected, "", fmt.Errorf("ancestor check: %w", err)
	}
	if !isAncestor {
		return PullUnexpected, "remote diverged (not fast-forward)", nil
	}

	// 套用 fast-forward: 移動 local branch ref, 並 checkout 該 tree.
	wt, err := repo.Worktree()
	if err != nil {
		return PullUnexpected, "", fmt.Errorf("worktree: %w", err)
	}
	if err := wt.Checkout(&git.CheckoutOptions{Hash: remoteHash, Force: true}); err != nil {
		return PullUnexpected, "", fmt.Errorf("checkout: %w", err)
	}
	branchRef := plumbing.NewBranchReferenceName(branch)
	if _, err := repo.Reference(branchRef, false); err != nil {
		// 本地沒有此 branch — 建立之.
		if err := repo.Storer.SetReference(plumbing.NewHashReference(branchRef, remoteHash)); err != nil {
			return PullUnexpected, "", fmt.Errorf("create branch: %w", err)
		}
	} else {
		if err := repo.Storer.SetReference(plumbing.NewHashReference(branchRef, remoteHash)); err != nil {
			return PullUnexpected, "", fmt.Errorf("update branch: %w", err)
		}
	}
	if err := repo.Storer.SetReference(plumbing.NewSymbolicReference(plumbing.HEAD, branchRef)); err != nil {
		return PullUnexpected, "", fmt.Errorf("update HEAD: %w", err)
	}

	if err := goInstall(repoRoot); err != nil {
		logger.Warn("go install skipped", "err", err)
	}

	return PullFastForward, "", nil
}

func resolveRemoteRef(repo *git.Repository, remoteName, branch string) (string, plumbing.Hash, error) {
	tryBranches := []string{branch}
	if branch == "main" {
		tryBranches = append(tryBranches, "master")
	}
	for _, b := range tryBranches {
		refName := plumbing.NewRemoteReferenceName(remoteName, b)
		ref, err := repo.Reference(refName, true)
		if err == nil {
			return refName.String(), ref.Hash(), nil
		}
	}
	return "", plumbing.ZeroHash, errors.New("remote branch not found")
}

func goInstall(repoRoot string) error {
	if _, err := exec.LookPath("go"); err != nil {
		return fmt.Errorf("go toolchain not on PATH: %w", err)
	}
	cmd := exec.Command("go", "install", "./cmd/hgsystem")
	cmd.Dir = repoRoot
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// MarkerFile 寫入目前的版本字串, 讓下次啟動時能顯示「已由 X 更新為 Y」.
// 搭配 Restart 一起使用.
func WriteMarker(path, version string) error {
	return os.WriteFile(path, []byte(version), 0o644)
}

// ReadAndClearMarker 若標記檔存在, 回傳前一版版本字串並一併刪除標記檔.
// 找不到標記檔時回傳 "".
func ReadAndClearMarker(path string) (string, error) {
	data, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return "", nil
	}
	if err != nil {
		return "", err
	}
	_ = os.Remove(path)
	return string(data), nil
}

// Restart 就地 re-exec 目前的執行檔 (不會產生新 process). Windows 下無法使用
// syscall.Exec, caller 應改以另起新 process 後結束自身的方式處理.
func Restart(args []string) error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	env := os.Environ()
	argv := append([]string{exe}, args...)
	return syscall.Exec(exe, argv, env)
}


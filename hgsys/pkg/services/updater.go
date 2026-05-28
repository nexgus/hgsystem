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

// PullResult enumerates what `PullAndInstall` ended up doing.
type PullResult int

const (
	PullUpToDate     PullResult = 0 // already on the remote tip; no restart needed
	PullFastForward  PullResult = 1 // fast-forwarded; caller should Restart
	PullUnexpected   PullResult = 2 // not fast-forward, or remote not found
)

// FindRepoRoot walks up from `startDir` looking for a `.git` directory.
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

// PullAndInstall fetches from `remoteName` and fast-forwards to `branch`,
// falling back to `master` if `main` is missing (matches legacy behavior).
// Only handles up-to-date and fast-forward cases cleanly; anything else
// returns PullUnexpected with a detail string.
//
// After a fast-forward, the Go binary is rebuilt via `go install` so the
// next exec picks up the new code. If no Go toolchain is on PATH the build
// step is skipped and the caller still gets PullFastForward — Restart will
// re-exec the existing binary in that case.
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

	// Apply fast-forward: move local branch ref + checkout the tree.
	wt, err := repo.Worktree()
	if err != nil {
		return PullUnexpected, "", fmt.Errorf("worktree: %w", err)
	}
	if err := wt.Checkout(&git.CheckoutOptions{Hash: remoteHash, Force: true}); err != nil {
		return PullUnexpected, "", fmt.Errorf("checkout: %w", err)
	}
	branchRef := plumbing.NewBranchReferenceName(branch)
	if _, err := repo.Reference(branchRef, false); err != nil {
		// Branch doesn't exist locally — create it.
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

// MarkerFile writes the current version so the next launch can show
// "已由 X 更新為 Y". Used together with Restart.
func WriteMarker(path, version string) error {
	return os.WriteFile(path, []byte(version), 0o644)
}

// ReadAndClearMarker returns the previous version if a marker exists and then
// removes the marker. Returns "" if no marker was found.
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

// Restart re-execs the current binary in place (no new process). On Windows
// syscall.Exec is unavailable so the caller should fall back to spawning a
// new process and exiting.
func Restart(args []string) error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	env := os.Environ()
	argv := append([]string{exe}, args...)
	return syscall.Exec(exe, argv, env)
}


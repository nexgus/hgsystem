// Package services wraps mongodump/mongorestore and the git-based self-updater.
package services

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"hgsys/pkg/repository"
)

// RequiredRestoreFiles enumerates the files mongodump produces that must be
// present before a restore is attempted. Matches the legacy app.
var RequiredRestoreFiles = []string{
	"customers.bson",
	"customers.metadata.json",
	"worksheets.bson",
	"worksheets.metadata.json",
}

// ResolveRestoreDir lets the user pick the parent of the dump: if `chosen`
// contains an `hgsystem/` subdirectory, drill into it.
func ResolveRestoreDir(chosen string) string {
	nested := filepath.Join(chosen, repository.DatabaseName)
	if info, err := os.Stat(nested); err == nil && info.IsDir() {
		return nested
	}
	return chosen
}

// MissingRestoreFiles returns the subset of RequiredRestoreFiles absent from
// `savepath`. Empty slice means restore can proceed.
func MissingRestoreFiles(savepath string) []string {
	var missing []string
	for _, name := range RequiredRestoreFiles {
		if _, err := os.Stat(filepath.Join(savepath, name)); err != nil {
			missing = append(missing, name)
		}
	}
	return missing
}

// Dump runs `mongodump -d hgsystem -o <savepath>` and forwards each stderr
// line to `onLine`. Blocks until the command finishes.
func Dump(ctx context.Context, savepath string, onLine func(string)) error {
	return runStreamed(ctx, "mongodump", []string{"-d", repository.DatabaseName, "-o", savepath}, onLine)
}

// Restore runs `mongorestore -d hgsystem --dir <savepath>` and forwards each
// stderr line to `onLine`. Blocks until the command finishes.
func Restore(ctx context.Context, savepath string, onLine func(string)) error {
	return runStreamed(ctx, "mongorestore", []string{"-d", repository.DatabaseName, "--dir", savepath}, onLine)
}

func runStreamed(ctx context.Context, name string, args []string, onLine func(string)) error {
	cmd := exec.CommandContext(ctx, name, args...)
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("create stderr pipe: %w", err)
	}
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("start %s: %w", name, err)
	}
	go forwardLines(stderr, onLine)
	if err := cmd.Wait(); err != nil {
		var exitErr *exec.ExitError
		if errors.As(err, &exitErr) {
			return fmt.Errorf("%s exited with %d", name, exitErr.ExitCode())
		}
		return err
	}
	return nil
}

func forwardLines(r io.Reader, onLine func(string)) {
	sc := bufio.NewScanner(r)
	sc.Buffer(make([]byte, 64*1024), 1024*1024)
	for sc.Scan() {
		// Match legacy: collapse tabs to spaces, strip newlines (already stripped by Scanner).
		line := strings.ReplaceAll(sc.Text(), "\t", " ")
		if onLine != nil {
			onLine(line)
		}
	}
}

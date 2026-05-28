// Package applog sets up the hgsystem logger. It writes to the OS-conventional
// log directory (~/Library/Logs/hgsystem on macOS, %LOCALAPPDATA%\hgsystem\logs
// on Windows, $XDG_STATE_HOME/hgsystem/logs elsewhere) using a per-launch file
// named YYMMDD_NNNN.log where NNNN is a same-day serial starting at 0001.
package applog

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"
)

const loggerName = "hgsystem"

// LogFile is the path of the file the logger is writing to (set by Setup).
var LogFile string

// Setup wires slog with two handlers: a console handler that respects debug
// and a file handler that always records DEBUG and up. Returns the file path
// it opened (also stored in LogFile).
func Setup(debug bool) (string, error) {
	dir, err := defaultLogDir()
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", err
	}
	path := nextLogPath(dir)
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o644)
	if err != nil {
		return "", err
	}

	consoleLevel := slog.LevelInfo
	if debug {
		consoleLevel = slog.LevelDebug
	}

	console := slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: consoleLevel})
	file := slog.NewTextHandler(f, &slog.HandlerOptions{Level: slog.LevelDebug})

	slog.SetDefault(slog.New(multiHandler{console, file}))
	LogFile = path
	return path, nil
}

func defaultLogDir() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	switch runtime.GOOS {
	case "windows":
		base := os.Getenv("LOCALAPPDATA")
		if base == "" {
			base = filepath.Join(home, "AppData", "Local")
		}
		return filepath.Join(base, loggerName, "logs"), nil
	case "darwin":
		return filepath.Join(home, "Library", "Logs", loggerName), nil
	default:
		state := os.Getenv("XDG_STATE_HOME")
		if state == "" {
			state = filepath.Join(home, ".local", "state")
		}
		return filepath.Join(state, loggerName, "logs"), nil
	}
}

func nextLogPath(dir string) string {
	prefix := time.Now().Format("060102")
	maxSeq := 0
	entries, _ := os.ReadDir(dir)
	for _, e := range entries {
		name := e.Name()
		if !strings.HasPrefix(name, prefix+"_") || !strings.HasSuffix(name, ".log") {
			continue
		}
		seqStr := strings.TrimSuffix(strings.TrimPrefix(name, prefix+"_"), ".log")
		if seq, err := strconv.Atoi(seqStr); err == nil && seq > maxSeq {
			maxSeq = seq
		}
	}
	return filepath.Join(dir, fmt.Sprintf("%s_%04d.log", prefix, maxSeq+1))
}

// multiHandler fans a slog record out to every wrapped handler.
type multiHandler []slog.Handler

func (m multiHandler) Enabled(ctx context.Context, lvl slog.Level) bool {
	for _, h := range m {
		if h.Enabled(ctx, lvl) {
			return true
		}
	}
	return false
}

func (m multiHandler) Handle(ctx context.Context, r slog.Record) error {
	for _, h := range m {
		if h.Enabled(ctx, r.Level) {
			if err := h.Handle(ctx, r.Clone()); err != nil {
				return err
			}
		}
	}
	return nil
}

func (m multiHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
	out := make(multiHandler, len(m))
	for i, h := range m {
		out[i] = h.WithAttrs(attrs)
	}
	return out
}

func (m multiHandler) WithGroup(name string) slog.Handler {
	out := make(multiHandler, len(m))
	for i, h := range m {
		out[i] = h.WithGroup(name)
	}
	return out
}


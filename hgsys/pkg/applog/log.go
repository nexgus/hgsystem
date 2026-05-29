// Package applog 為 hgsystem 設定 logger. 它會依各 OS 慣用的 log 目錄
// (macOS 為 ~/Library/Logs/hgsystem, Windows 為 %LOCALAPPDATA%\hgsystem\logs,
// 其他為 $XDG_STATE_HOME/hgsystem/logs) 寫入每次啟動一份的 log 檔, 檔名為
// YYMMDD_NNNN.log; 其中 NNNN 為當日流水號, 自 0001 起算.
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

// LogFile 為 logger 目前寫入之檔案路徑 (由 Setup 設定).
var LogFile string

// Setup 為 slog 註冊兩個 handler: 一個會依 debug 旗標調整等級的 console handler,
// 以及一個無論如何皆記錄 DEBUG 以上的 file handler. 回傳實際開啟的檔案路徑
// (同時存於 LogFile).
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

// multiHandler 將一筆 slog record 分送至所有包裹的 handler.
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


//go:build !darwin

package main

// setAppName 在非 macOS 平台為 no-op: 其他平台的選單列沒有取自應用名稱的
// 項目, 無須調整.
func setAppName(string) {}

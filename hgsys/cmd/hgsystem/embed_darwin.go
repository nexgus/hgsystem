//go:build darwin

package main

import _ "embed"

// hgupgradeBinary 為 darwin/arm64 版的 hgupgrade 執行檔, 由 build.sh 於
// `go build` 前編到 hgupgrade/ 子目錄 (見 .gitignore, 不入版控). UpdateService
// 更新時會把它釋出到暫存目錄執行.
//
//go:embed hgupgrade/hgupgrade-darwin-arm64
var hgupgradeBinary []byte

// hgupgradeName 為釋出到暫存目錄時使用的檔名.
const hgupgradeName = "hgupgrade-darwin-arm64"

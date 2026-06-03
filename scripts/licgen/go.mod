// 本目錄為獨立的開發用工具 module (自帶 go.mod), 不屬於 hgsystem 產品, 也不
// 會被 hgsys 主 module 的 `go build ./...` 納入. 由 scripts/gen-licenses.sh 以
// `go run .` 呼叫, 產生 frontend/src/licenses-go.ts.
module hgsystem-licgen

go 1.24

require github.com/google/licensecheck v0.3.1

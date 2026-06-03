#!/bin/bash
# gen-licenses.sh — 重新產生 frontend/src/licenses-go.ts 與 licenses-manual.ts.
#
# (1) Go 依賴: 掃描 hgsystem 散布物 (hgsystem 執行檔, 及其內嵌的 hgupgrade 自我
#     更新輔助程式) 於 darwin 與 windows 平台實際編譯進 binary 的 Go 依賴, 偵測
#     各自授權並取其原文, 寫入 frontend/src/licenses-go.ts. 依賴 (go.mod) 變動後
#     應重跑本腳本, 使授權揭露與實際散布的程式碼保持一致.
# (2) 手動素材: 依 scripts/licenses-manual/manifest.json 產生 licenses-manual.ts
#     (圖示等「既非 Go module、也非 npm 套件」者). 其中 embed=true 的項目需於產生
#     時抓取授權原文, 故此步需要網路 (產出已納版控, 平常 build 不需重抓).
#
# 開發工具 cmd/check 不隨產品散布, 不納入掃描.
#
# 需求: go, jq (生成器本身為獨立 module scripts/licgen/, 依賴 licensecheck);
# (2) 另需網路.

set -eo pipefail

# 切換至 hgsys/ 目錄 (Go module hgsys 的根; 本腳本位於 hgsystem/scripts/).
cd "$(dirname "${BASH_SOURCE[0]}")/../hgsys"

command -v jq >/dev/null 2>&1 || { echo "Error: 需要 jq" >&2; exit 1; }

OUT="../frontend/src/licenses-go.ts"
TSV="$(mktemp)"
DIRECT="$(mktemp)"
trap 'rm -f "$TSV" "$DIRECT"' EXIT

# collect 列出指定 GOOS 下 hgsystem 與 hgupgrade 兩執行檔的相依 module (排除
# 標準函式庫與 hgsys 自身), 每行輸出 "<path>\t<dir>\t<version>". 使用
# CGO_ENABLED=1 以涵蓋 cgo 檔內的 import (darwin/windows 的 webview 綁定);
# go list 解析 import 不需 C 編譯器.
collect() {
    CGO_ENABLED=1 GOOS="$1" go list -deps -json ./cmd/hgsystem ./cmd/hgupgrade 2>/dev/null \
        | jq -r 'select(.Standard|not)
                 | select(.Module!=null)
                 | select(.Module.Path!="hgsys")
                 | [.Module.Path, .Module.Dir, .Module.Version] | @tsv'
}

# 取 darwin + windows 兩平台的聯集, 以 module path 去重後排序.
{ collect darwin; collect windows; } | sort -u | awk -F'\t' '!seen[$1]++' | sort > "$TSV"

echo "scanned modules (darwin + windows union): $(wc -l < "$TSV" | tr -d ' ')"

# 由 go.mod 取「直接依賴」module path (require 中非 indirect 者), 供 licgen 將
# 掃描到的 module 分為直接 / 間接兩類.
go mod edit -json | jq -r '.Require[] | select(.Indirect | not) | .Path' | sort -u > "$DIRECT"

echo "direct modules (go.mod, non-indirect): $(wc -l < "$DIRECT" | tr -d ' ')"

# licgen 為獨立 module, 於其目錄內以 go run 執行; 傳入聯集清單與直接依賴清單.
( cd ../scripts/licgen && go run . "$TSV" "$DIRECT" ) > "$OUT"

echo "wrote frontend/src/licenses-go.ts ($(grep -c '    name:' "$OUT") entries)"

# 手動素材: licgen 的 -manual 模式讀 manifest, 產生 licenses-manual.ts. 一併傳入
# 兩份自動清單, 讓 licgen 依授權種類是否已涵蓋自動決定要嵌入全文或僅放著作權:
# licenses-go.ts 為上一步剛產生 (最新); licenses-frontend.ts 取既有版控檔 (npm 依賴
# 穩定, 其於 build_frontend 的 Vite 階段才重產, 此處的版控檔已足供判斷).
MANUAL_OUT="../frontend/src/licenses-manual.ts"
( cd ../scripts/licgen && go run . -manual ../licenses-manual/manifest.json \
    ../../frontend/src/licenses-go.ts ../../frontend/src/licenses-frontend.ts ) > "$MANUAL_OUT"

echo "wrote frontend/src/licenses-manual.ts ($(grep -c '    name:' "$MANUAL_OUT") entries)"

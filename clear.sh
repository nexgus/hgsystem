#!/bin/bash
# 刪除 build.sh 產出的所有 binary / intermediate / cache, 將 repo 還原到剛
# 簽出時的狀態. 不會動 git-tracked 的原始碼或設定檔.
#
# 移除清單對齊 .gitignore 中的 build artifact 條目:
#   * bin/                          — Go binaries + MSI + symlink
#   * hgsys/cmd/hgsystem/dist/      — embed 用的 frontend dist 副本
#   * frontend/dist/                — Vite 輸出
#   * frontend/bindings/            — wails3 generate bindings 產出的 TS
#   * frontend/node_modules/        — npm install 的依賴
#   * frontend/tsconfig.tsbuildinfo — vue-tsc 增量編譯快取
#   * msi/hgsystem.wxs              — sed 由 .wxs.in 生成的 MSI manifest

set -eo pipefail

# 切換到 script 所在目錄 (repo root), 使本檔可由任何位置呼叫.
cd "$(dirname "${BASH_SOURCE[0]}")"

TARGETS=(
    bin
    hgsys/cmd/hgsystem/dist
    frontend/dist
    frontend/bindings
    frontend/node_modules
    frontend/tsconfig.tsbuildinfo
    msi/hgsystem.wxs
)

for path in "${TARGETS[@]}"; do
    if [ -e "$path" ] || [ -L "$path" ]; then
        echo "Removing $path"
        rm -rf -- "$path"
    fi
done

echo "Done."

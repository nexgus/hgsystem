#!/bin/bash
# 編譯 hgsystem (darwin/arm64 + windows/amd64) Wails v3 + Vue 3 + TS 桌面 app.
#
# 流程:
#   1. (依需要) nvm use 20.
#   2. (依需要) npm install frontend 依賴.
#   3. 確保 wails3 CLI 與 mingw-w64 已安裝 (windows 交叉編譯需要).
#   4. wails3 generate bindings — 從 Go service 產生 frontend/bindings/.
#   5. npm run build — 產 frontend/dist/ (Vite 輸出).
#   6. 複製 frontend/dist 到 hgsys/cmd/hgsystem/dist (供 //go:embed 使用).
#   7. go build darwin/arm64 + windows/amd64.
#   8. wixl 將 windows/amd64 binary 打包為 hgsystem-<VER>.msi.
#
# 兩個目標皆為單一 GUI binary; macOS 用 WKWebView, Windows 用 WebView2
# (Win10/11 內建). 產出位於 bin/, 並以無後綴 / .exe / .msi 短 symlink
# 指向當前版本.

# pipefail 確保 pipeline 任一段失敗即視為失敗.
set -eo pipefail

# 切換到 script 所在目錄 (repo root), 使本檔可由任何位置以
# bash <path/to/build.sh> 執行.
cd "$(dirname "${BASH_SOURCE[0]}")"

# PKG: Go module 名稱 / 子目錄名稱 (匯入路徑 hgsys/...).
# BIN: 輸出 binary 名稱與 cmd/ 子目錄名稱 (使用者可見的應用程式名稱).
PKG=hgsys
BIN=hgsystem

COMMIT=$(git describe --match=NeVeRmAtCh --always --abbrev=8 --dirty)
GOVER=$(go version | cut -d ' ' -f 3)
VER=$(grep 'const String' "${PKG}/pkg/version/version.go" | sed -E 's/.*"([^"]+)".*/\1/')
if [ -z "$VER" ]; then
    echo "Error: failed to extract VERSION from ${PKG}/pkg/version/version.go" >&2
    exit 1
fi

# 版本資訊於編譯期注入 hgsys/pkg/version.
VERLD="-X ${PKG}/pkg/version.GitCommitHash=${COMMIT} -X ${PKG}/pkg/version.GoVersion=${GOVER}"

# Wails v3 與 Node 主版本固定; 升級需明確修改本檔.
WAILS_VERSION="v3.0.0-alpha.95"
NODE_MAJOR="20"

WAILS3="$(go env GOPATH)/bin/wails3"

# ensure_nvm_node 確保當前 shell 透過 nvm 切換到 Node ${NODE_MAJOR}.
# 不更動使用者的 nvm default; 僅於本 build session 內生效.
function ensure_nvm_node {
    export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
    if [ ! -s "$NVM_DIR/nvm.sh" ]; then
        echo "Error: nvm not found ($NVM_DIR/nvm.sh). Please install nvm first." >&2
        exit 1
    fi
    # shellcheck disable=SC1091
    . "$NVM_DIR/nvm.sh"
    if ! nvm use "${NODE_MAJOR}" >/dev/null 2>&1; then
        echo "Node ${NODE_MAJOR} not available via nvm, installing..."
        nvm install "${NODE_MAJOR}" --no-progress
        nvm use "${NODE_MAJOR}"
    fi
}

# ensure_wails3 確保 wails3 CLI 已安裝且版本為 ${WAILS_VERSION}.
function ensure_wails3 {
    local current=""
    # wails3 version 印到 stderr, 需合併 2>&1 後過濾.
    if [ -x "${WAILS3}" ]; then
        current=$("${WAILS3}" version 2>&1 | tr -d '[:space:]')
    fi
    if [ "${current}" != "${WAILS_VERSION}" ]; then
        echo "wails3 CLI not at ${WAILS_VERSION} (have: ${current:-none}), installing..."
        go install "github.com/wailsapp/wails/v3/cmd/wails3@${WAILS_VERSION}"
    fi
}

# ensure_npm_install 確保 frontend 依賴已安裝.
function ensure_npm_install {
    if [ ! -d frontend/node_modules ] || [ frontend/package.json -nt frontend/node_modules ]; then
        echo "frontend dependencies out of date or missing, running npm install..."
        (cd frontend && npm install)
    fi
}

# ensure_mingw 確保 mingw-w64 已安裝 (windows 交叉編譯所需 C 編譯器).
function ensure_mingw {
    if command -v x86_64-w64-mingw32-gcc >/dev/null 2>&1; then
        return
    fi
    echo "x86_64-w64-mingw32-gcc not found, installing mingw-w64 via Homebrew..."
    if ! command -v brew >/dev/null 2>&1; then
        echo "Error: Homebrew not found, cannot auto-install." >&2
        exit 1
    fi
    brew install mingw-w64 || { echo "Error: failed to install mingw-w64." >&2; exit 1; }
}

# ensure_wixl 確保 wixl (msitools) 已安裝, 用以打包 windows .msi.
function ensure_wixl {
    if command -v wixl >/dev/null 2>&1; then
        return
    fi
    echo "wixl not found, installing msitools via Homebrew..."
    if ! command -v brew >/dev/null 2>&1; then
        echo "Error: Homebrew not found, cannot auto-install." >&2
        exit 1
    fi
    brew install msitools || { echo "Error: failed to install msitools." >&2; exit 1; }
}

function build_frontend {
    echo "Generating Wails bindings..."
    # wails3 generate 必須在含 go.mod 的目錄跑, 故進入 ${PKG}/. cmd/${BIN}
    # 內含 application.NewService 呼叫, 指明 pattern 讓 static analyser 找到
    # 所有 Service. 輸出指向 repo root 的 frontend/bindings/.
    (cd "${PKG}" && "${WAILS3}" generate bindings -ts -silent -clean=true \
        -d "../frontend/bindings" "./cmd/${BIN}")

    echo "Building frontend (Vite)..."
    (cd frontend && npm run build)

    echo "Copying frontend/dist to ${PKG}/cmd/${BIN}/dist (for //go:embed)..."
    rm -rf "${PKG}/cmd/${BIN}/dist"
    cp -r frontend/dist "${PKG}/cmd/${BIN}/dist"
}

# build_msi 將 windows/amd64 binary 打包為 hgsystem-<VER>.msi.
#
# 安裝範圍: per-machine; 安裝目錄: %ProgramFiles%\hgsystem\;
# 並將該目錄追加至系統 PATH (HKLM, 全使用者可見). 升級語意為 MajorUpgrade,
# 允許同版本覆蓋, 拒絕降級.
#
# msi/hgsystem.wxs.in 為來源 template, 以 sed 將 @VERSION@ 替換為 $VER 後
# 寫到 msi/hgsystem.wxs (不入版控), 餵給 wixl 編譯. wixl File@Source 之
# 相對路徑以 wixl 之 CWD 為基準, 此處 CWD 即 repo root, 故 .wxs 內可寫
# bin/...exe.
#
# wixl 對 Environment 元素之 Permanent="no" 不發出對應的 MSI Name '-'
# prefix, 導致 uninstall 時不會從系統 PATH 移除 INSTALLDIR, 多次升級會
# 累積重複條目. 此處以 msiinfo / msibuild 後處理 Environment table, 將
# '=*PATH' 改為 '=-*PATH', 補上 'remove on uninstall' 語意, 使升級與
# 卸載皆能正確維護 PATH.
function build_msi {
    echo "Generating msi/${BIN}.wxs from template..."
    sed "s/@VERSION@/${VER}/g" "msi/${BIN}.wxs.in" > "msi/${BIN}.wxs"

    echo "Building bin/${BIN}-${VER}.msi..."
    wixl -a x64 -o "bin/${BIN}-${VER}.msi" "msi/${BIN}.wxs" \
        || { echo "Error: wixl failed to build MSI." >&2; exit 1; }

    echo "Patching Environment table for uninstall PATH cleanup..."
    local env_idt
    env_idt=$(mktemp)
    msiinfo export "bin/${BIN}-${VER}.msi" Environment \
        | sed 's/=\*PATH/=-*PATH/' > "$env_idt"
    msibuild "bin/${BIN}-${VER}.msi" -i "$env_idt" \
        || { echo "Error: msibuild failed to patch Environment table." >&2; rm -f "$env_idt"; exit 1; }
    rm -f "$env_idt"

    # wixl 0.106 忽略 Package@SummaryCodepage 屬性, 一律以 cp1252 寫入
    # Summary Information stream 的 PID_CODEPAGE. 我們的 Description 含中文
    # (UTF-8 bytes), 在 cp1252 解讀下會顯示為亂碼. 此處後處理 _SummaryInformation
    # 表將 codepage 由 1252 改為 65001 (UTF-8), 使 Windows installer 與
    # Programs and Features 能正確顯示中文 description / subject.
    #
    # _SummaryInformation 由 msiinfo export 輸出時行尾為 CRLF, 因此 sed 不使用
    # 行尾錨點 ($); 僅匹配開頭 "1<TAB>1252" 把 1252 改為 65001.
    echo "Patching _SummaryInformation codepage to UTF-8 (65001)..."
    local sum_idt tab
    sum_idt=$(mktemp)
    tab=$(printf '\t')
    msiinfo export "bin/${BIN}-${VER}.msi" _SummaryInformation \
        | sed "s/^1${tab}1252/1${tab}65001/" > "$sum_idt"
    msibuild "bin/${BIN}-${VER}.msi" -i "$sum_idt" \
        || { echo "Error: msibuild failed to patch _SummaryInformation." >&2; rm -f "$sum_idt"; exit 1; }
    rm -f "$sum_idt"
}

# mklink 為兩個目標平台各建一組短 symlink: 無後綴指向 darwin/arm64,
# .exe 指向 windows/amd64; 並為 MSI 建一個 hgsystem.msi 短符號.
function mklink {
    ln -fs "${BIN}-${VER}-darwin-arm64" "bin/${BIN}"
    ln -fs "${BIN}-${VER}-windows-amd64.exe" "bin/${BIN}.exe"
    ln -fs "${BIN}-${VER}.msi" "bin/${BIN}.msi"
}

mkdir -p bin
ensure_nvm_node
ensure_wails3
ensure_npm_install
ensure_mingw
ensure_wixl

# wails3 generate bindings 需要 deps 已下載.
(cd "${PKG}" && go mod download)

build_frontend

# 透過 -extldflags 傳 -mmacosx-version-min=26.0 給 external linker (clang),
# 與 Wails v3 alpha.95 內含之 prebuilt Objective-C 物件檔 (以 macOS 26 SDK
# 編譯) 一致, 消除 "built for newer 'macOS' version (26.0) than being
# linked (11.0)" 警告; 代價為產出 binary 僅能在 macOS 26+ 執行.
echo "Building darwin/arm64 ${BIN}..."
(cd "${PKG}" && \
    GOOS=darwin GOARCH=arm64 CGO_ENABLED=1 go build -trimpath \
        -o "../bin/${BIN}-${VER}-darwin-arm64" \
        -ldflags "-w -extldflags '-mmacosx-version-min=26.0' ${VERLD}" \
        "./cmd/${BIN}")

# Windows GUI subsystem 避免雙擊時跳出多餘的 console 視窗.
echo "Building windows/amd64 ${BIN}..."
(cd "${PKG}" && \
    GOOS=windows GOARCH=amd64 CGO_ENABLED=1 CC=x86_64-w64-mingw32-gcc go build -trimpath \
        -o "../bin/${BIN}-${VER}-windows-amd64.exe" \
        -ldflags "-w -H windowsgui -extldflags \"-static\" ${VERLD}" \
        "./cmd/${BIN}")

build_msi

mklink

echo
echo "Built binaries:"
for f in bin/*; do
    [ -L "$f" ] && continue
    [ -f "$f" ] && echo "  $(basename "$f")"
done

echo
echo "Symlinks:"
for f in bin/*; do
    [ -L "$f" ] || continue
    echo "  $(basename "$f") -> $(readlink "$f")"
done

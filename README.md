# hgsystem

hgsystem (豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統) 為一支 Go + Wails v3 桌面應用, 前端以 Vue 3 + TypeScript 撰寫, 經系統 webview 渲染. 提供眼鏡店之客戶資料維護與配鏡工單管理, 資料儲存於本地 MongoDB 之 `hgsystem` 資料庫, 涵蓋客戶 (`customers`), 工單 (`worksheets`), 稱謂清單 (`titles`) 與本次啟動之搜尋歷史 (`search`) 四個 collection.

本目錄之 `build.sh` 同時交叉編譯 darwin/arm64 與 windows/amd64, 並產出 Windows MSI 安裝程式.

## 1. 開發環境準備

- darwin/arm64 版限 macOS 26 以上 (執行與編譯皆需). hgsystem 連結之系統函式庫自 macOS 26 起始提供, 較舊 macOS 既無法編譯亦無法執行 darwin/arm64 版. windows/amd64 版不受此限.
- Go 1.25 以上.
- Node.js 20. `build.sh` 透過 nvm 於本次編譯過程內切換至 Node 20, 若機器尚未安裝該版則一併下載, 不更動使用者之 nvm 預設值. 因此 host 僅須先安裝 [nvm](https://github.com/nvm-sh/nvm).
- Wails v3 CLI, 版本鎖定為 `v3.0.0-alpha.95`. `build.sh` 偵測現裝版本不符時, 以 `go install` 重新安裝指定版本至 `$(go env GOPATH)/bin/wails3`.
- hgsystem 需 `CGO_ENABLED=1` 以連結 webview. macOS host 編譯 darwin/arm64 版時連結 WKWebView 由系統工具鏈處理, 無須額外安裝.
- windows/amd64 交叉編譯需要 mingw 的 C 編譯器 (`x86_64-w64-mingw32-gcc`), 用於連結 Microsoft Edge WebView2 客戶端. 若 PATH 中找不到, `build.sh` 會透過 Homebrew 自動安裝 `mingw-w64`.
- msitools (含 `wixl`), 用於產出 Windows MSI. 若 PATH 中找不到, `build.sh` 會透過 Homebrew 自動安裝.
- `jq`, 僅 `build.sh --license` (重新掃描第三方授權) 時需要; 若 PATH 中找不到, `build.sh` 會透過 Homebrew 自動安裝. 前端授權掃描所需之 `rollup-plugin-license` 為 `frontend/` 之 devDependency, 由 `npm install` 自動取得.
- 執行期 (非編譯期) 須有可連線之 MongoDB 服務. 預設連線 `localhost:27017`, 可由 `-H` / `-p` 旗標調整. 備份與還原功能另需 `mongodump` 與 `mongorestore` 於 PATH.

## 2. 編譯

以下說明假設位於 repo 根目錄:

```bash
bash build.sh             # 一般建置
bash build.sh --license   # 建置, 並先重新掃描 / 更新第三方授權清單 (詳見第 5 節)
```

不加 `--license` 的一般建置沿用既有的授權清單, 不重新掃描. `build.sh` 的行為 (以下為一般建置流程; `--license` 另於產生 bindings 前插入授權掃描步驟, 見第 5 節):

1. 透過 nvm 切換至 Node 20, 缺少時自動安裝.
1. 偵測 wails3 CLI, 版本不符 `v3.0.0-alpha.95` 時以 `go install` 重新安裝.
1. 視需要在 `frontend/` 執行 `npm install` 取得前端依賴.
1. 偵測 mingw, 缺少時透過 Homebrew 安裝.
1. 偵測 wixl (msitools), 缺少時透過 Homebrew 安裝.
1. `go mod download` 同步 Go 依賴.
1. 編譯隨附的更新程式 hgupgrade (darwin/arm64 與 windows/amd64, `CGO_ENABLED=0`; windows 版以 `-H windowsgui` 避免顯示錯誤對話框時閃出 console), 輸出至 `hgsys/cmd/hgsystem/hgupgrade/` (不入版控), 供 hgsystem 以 `//go:embed` 內嵌. 此步須早於產生 bindings 與 `go build`: `cmd/hgsystem` 對該目錄之檔有 embed 宣告, 缺檔會導致型別檢查與編譯失敗. hgupgrade 之行為詳見第 7 節.
1. 產出前端:
   - 由 `hgsys/` 內呼叫 `wails3 generate bindings -ts ./cmd/hgsystem`, 由 Go service (`pkg/app` 下之 `CustomerService`, `WorksheetService`, `SearchService`, `TitleService`, `BackupService`, `SystemService`, `UpdateService`) 反推產生 `frontend/bindings/` 之 TypeScript 綁定. 此命令須於含 `go.mod` 之目錄執行, 並指定 `./cmd/hgsystem` 為 pattern, 使 static analyser 找得到 `application.NewService(...)` 之呼叫.
   - 於 `frontend/` 執行 `npm run build`, 經 vue-tsc 型別檢查後由 Vite 輸出 `frontend/dist/`.
   - 將 `frontend/dist/` 複製為 `hgsys/cmd/hgsystem/dist/`, 供 `//go:embed all:dist` 內嵌進執行檔. Go 之 embed 不允許 `..` 跨層, 故必須以複製而非符號連結方式置入.
1. 由 `hgsys/cmd/hgsystem/icon.ico` (眼鏡圖示, 取自 Noto Emoji U+1F453, SIL OFL 1.1 授權) 以 `rsrc` 產生 `rsrc_windows_amd64.syso` (不入版控). `go build` 偵測到此檔即自動連結, 使 windows/amd64 執行檔帶有應用程式圖示 (檔案總管 / 工作列). 同一張圖示之 `icon.png` 另由 `//go:embed` 內嵌, 經 `application.Options.Icon` 供 Wails 視窗使用.
1. 依序編譯 darwin/arm64 之 hgsystem (`CGO_ENABLED=1`, 以 `-extldflags '-mmacosx-version-min=26.0'` 對齊 Wails alpha.95 內含之 Objective-C 預編譯物件) 與 windows/amd64 之 hgsystem (`CGO_ENABLED=1`, `CC=x86_64-w64-mingw32-gcc`, 以 `-H windowsgui` 指定 GUI subsystem, 避免雙擊時跳出多餘的 console 視窗).
1. 將 `msi/hgsystem.wxs.in` 之 `@VERSION@` 替換為當前版本後寫入 `msi/hgsystem.wxs` (不入版控), 再交由 wixl 編譯為 Windows MSI 安裝程式, 並對 MSI 之 Environment table 後處理, 補入解除安裝時自系統 PATH 移除安裝目錄之語意 (詳見第 6.2 節). MSI metadata (ProductName / Description) 一律為 ASCII, 不做 codepage 後處理 (原因詳見第 6.3 節).
1. 建立 `bin/hgsystem`, `bin/hgsystem.exe` 與 `bin/hgsystem.msi` 三個 symlink, 分別指向當前平台之執行檔與 MSI.

產出檔置於 `bin/`, 檔名形如:

```
bin/hgsystem-<版本>-darwin-arm64
bin/hgsystem-<版本>-windows-amd64.exe
bin/hgsystem-<版本>.msi
```

版本號定義於 [`hgsys/pkg/version/version.go`](hgsys/pkg/version/version.go) 之 `const String`. `build.sh` 依賴該行格式, 勿更動. git commit hash 與 Go 版本於編譯期以 `-ldflags -X` 注入 `hgsys/pkg/version`.

## 3. 執行與啟動參數

```bash
./bin/hgsystem                       # 預設連 MongoDB localhost:27017
./bin/hgsystem -H <host> -p <port>   # 指定 MongoDB 位址
./bin/hgsystem -d                    # console 輸出層級調至 DEBUG
./bin/hgsystem --version
```

執行期 log 寫至 OS 慣用位置, 每次啟動為一獨立檔案, 同日累計流水號:

- macOS: `~/Library/Logs/hgsystem/YYMMDD_NNNN.log`
- Windows: `%LOCALAPPDATA%\hgsystem\logs\YYMMDD_NNNN.log`
- 其餘平台: `$XDG_STATE_HOME/hgsystem/logs/` (或 `~/.local/state/hgsystem/logs/`).

原生選單依平台慣例組織 (詳見 [`hgsys/cmd/hgsystem/menu.go`](hgsys/cmd/hgsystem/menu.go)): macOS 為 應用程式 / 資料 / 編輯 / 顯示 / 視窗, Windows 為 檔案 / 資料 / 編輯 / 顯示 / 說明. 「關於」與「檢查更新…」於 macOS 置於應用程式選單, 於 Windows 置於說明選單. 「資料」選單之備份 / 還原以 `mongodump` / `mongorestore` 子程序執行, stderr 以 Wails event 串流至前端對話框; 「檢查更新…」之行為詳見第 7 節.

## 4. 清除產物

```bash
bash clear.sh
```

`clear.sh` 刪除 `build.sh` 產出之所有 binary, 中間產物與快取, 包含 `bin/`, `hgsys/cmd/hgsystem/dist/`, `frontend/dist/`, `frontend/bindings/`, `frontend/node_modules/`, `frontend/tsconfig.tsbuildinfo`, 與 `msi/hgsystem.wxs`. 不動 git-tracked 之原始碼; 可重複執行.

## 5. 開發者工作流

修改 Go 端 (`hgsys/`) 時, 凡新增 / 刪除 service method 或調整 domain struct 之欄位, 須重跑 `wails3 generate bindings` 重產 `frontend/bindings/`, 否則前端之 TypeScript 型別與實際 ABI 將不一致; 最直接的方式為再跑一次 `bash build.sh`.

修改 Vue 前端 (`frontend/src/`) 時, 由於 `//go:embed all:dist` 於編譯期固化前端產出, 純前端變更亦須重跑 `build.sh` (或至少 `npm run build` + 將 `frontend/dist` 重新複製至 `hgsys/cmd/hgsystem/dist`), 才能於下次 `go build` 時生效.

「關於」視窗的「第三方授權」分頁顯示散布物所引用之第三方開源元件授權, 分「直接引用」與「間接引用」兩表. 授權清單來自三個來源, 皆為自動產生:

- **Go 依賴** (直接 + 間接): [`scripts/gen-licenses.sh`](scripts/gen-licenses.sh) 掃描 `hgsystem` 與 `hgupgrade` 兩執行檔於 darwin + windows 編譯進 binary 的 module, 依 `hgsys/go.mod` 之 require 分直接 / 間接, 偵測授權後產出 [`frontend/src/licenses-go.ts`](frontend/src/licenses-go.ts) (需 `go` 與 `jq`).
- **前端 npm 依賴**: 由 Vite + `rollup-plugin-license` 於建置時取「實際打包進 `dist`」的套件 (經 tree-shaking, 不含僅建置期用的 TypeScript / Vue 編譯器 / Babel / postcss 等), 依 `frontend/package.json` 之 dependencies 分直接 / 間接, 產出 [`frontend/src/licenses-frontend.ts`](frontend/src/licenses-frontend.ts).
- **手動素材** (圖示等「既非 Go module、也非 npm 套件」者, 如 Noto Emoji 應用圖示、Material Symbols 選單圖示): 描述於 [`scripts/licenses-manual/manifest.json`](scripts/licenses-manual/manifest.json) (每筆含 `type` / `copyright` / `licenseUrl`), 由 [`scripts/gen-licenses.sh`](scripts/gen-licenses.sh) 產出 [`frontend/src/licenses-manual.ts`](frontend/src/licenses-manual.ts). 是否嵌入授權全文由產生器**自動**判斷: 該 `type` 已見於上述 Go / npm 自動清單者僅放著作權 (全文沿用該元件, 例: Material Symbols 的 Apache-2.0 已隨 Go 依賴顯示), 未見者則抓 `licenseUrl` 原文嵌入 (例: Noto 的 SIL OFL 1.1)。欄位與用法見 [`scripts/licenses-manual/README.md`](scripts/licenses-manual/README.md).

三份 `licenses-*.ts` 皆入版控 (`licenses.ts` 僅存共用型別 `ThirdPartyLicense`). 凡依賴或素材變動 (`hgsys/go.mod`、`frontend/package.json` 或 `scripts/licenses-manual/manifest.json`), 以 **`bash build.sh --license`** 於建置時一併重產上述三份自動清單, 使授權揭露與實際散布一致; 不加 `--license` 的 `build.sh` 沿用既有清單、不重新掃描. (亦可單獨跑 `bash scripts/gen-licenses.sh` 重產 Go 與手動素材兩份; 手動素材 `embed:true` 的抓取需網路.) 顯示時依授權種類去重 (同種授權只列一次條文), 但保留各元件著作權聲明.

domain 行為涉及與 MongoDB 中既有資料及 `mongodump` 備份檔之相容性, 變更時須留意以下不變式:

- 資料庫名 `hgsystem` 與 collection 名 (`customers`, `worksheets`, `search`, `titles`) 不可更動.
- 文件 `_id` 為以字串型態儲存的 `bson.ObjectId` (非原生 ObjectId 型別).
- 工單之客戶外鍵欄位名為 `cid`.
- ROC 民國紀年中"民國 0 年"不存在, 故 [`hgsys/pkg/domain/dates.go`](hgsys/pkg/domain/dates.go) 與 [`frontend/src/lib/rocDate.ts`](frontend/src/lib/rocDate.ts) 皆對 0 年作負偏移處理; "年份未知"以哨兵值 `YEAR_NONE = 9996` 表示. 改動其一須同步另一, 否則既有儲存之日期會誤捨入.

## 6. Windows MSI 安裝程式

`bin/hgsystem-<版本>.msi` 為 Windows 端 MSI 安裝程式, 由 wixl (msitools) 於 macOS 端交叉編譯產出, 不需 .NET 環境亦無須 Windows 主機.

安裝行為:

- **安裝範圍**: per-machine (`ALLUSERS=1`), 須系統管理員權限.
- **安裝目錄**: `%ProgramFiles%\hgsystem\`, 含 `hgsystem.exe` 一個檔案.
- **系統 PATH**: 安裝時將 `%ProgramFiles%\hgsystem\` 追加至**系統 PATH** (HKLM, 全使用者可見), 解除安裝時自動移除.

升級語意採 MajorUpgrade:

- **新版安裝於舊版之上**: 自動先移除舊版再安裝新版, 對使用者而言為"就地升級".
- **同版本重裝**: 允許直接覆蓋 (`AllowSameVersionUpgrades="yes"`), 便於開發期反覆編譯.
- **降級**: 拒絕, 顯示"已安裝較新版本"錯誤訊息.

`UpgradeCode` 為固定 GUID (`7C12F6AC-EDAB-4539-BFB3-645EDD61BA4C`), 一旦變更等同新產品, 將與舊版失去升級關係.

MSI 定義檔以範本形式存於 [`msi/hgsystem.wxs.in`](msi/hgsystem.wxs.in), `build.sh` 編譯時將 `@VERSION@` 以 `hgsys/pkg/version/version.go` 之 `String` 替換後寫出 `msi/hgsystem.wxs` (不入版控), 交由 wixl 編譯.

### 6.1 解除安裝 (Windows)

hgsystem 為 per-machine 安裝, 解除安裝同樣須系統管理員權限.

**GUI 解除**

由 Windows 設定: **設定 → 應用程式 → 已安裝的應用程式**, 搜尋 `hgsystem`, 點選 `...` → **解除安裝**.

或由控制台: 執行 `appwiz.cpl` (控制台 → 程式集 → 程式和功能), 找到 `hgsystem`, 按右鍵 → **解除安裝**.

**CLI 解除** (適用腳本與自動化)

```bat
msiexec /x hgsystem-<版本>.msi      ← 若仍留有當初安裝的 .msi 檔
msiexec /x {ProductCode}            ← 以 ProductCode 解除, 每版不同
msiexec /x {ProductCode} /qn        ← 傳入 /qn 進行靜默解除, 無 UI
```

ProductCode 可於原始 .msi 上以 `msiinfo export <當初的 .msi> Property` 取得, 或於 Windows 端以 `wmic product where name="hgsystem" get IdentifyingNumber` 查詢.

**解除後清理的項目**

- `C:\Program Files\hgsystem\` 整個目錄.
- 系統 PATH 中之 `C:\Program Files\hgsystem\` 條目 (依賴 `build.sh` 對 Environment table 之後處理, 詳見下方第 6.2 節).
- 註冊機碼 `HKLM\Software\hgsystem\installed` (Component KeyPath dummy).
- 安裝紀錄 `HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\{ProductCode}`.

**注意事項**

- **既有之 cmd / PowerShell 視窗看不到 PATH 變更**: 已開啟之 shell 已固定其環境變數快照, 須另開一個 shell 始能看到解除安裝後之新 PATH. 圖形介面 (檔案總管) 通常會收到 broadcast 即時更新.
- **per-machine 故須管理員權限**: 一般使用者帳號執行時會觸發 UAC 提示; 若為受管理帳號 (公司 AD), 可能需 IT 協助.

### 6.2 wixl 對 Environment 之異常行為

wixl (msitools 0.106) 對 `<Environment>` 元素之 `Permanent="no"` 並未發出對應之 MSI Name `-` 前綴, 導致解除安裝階段不會自動從系統 PATH 移除 `INSTALLDIR`, 多次升級會累積重複條目. `build.sh` 於 wixl 編譯後以 `msiinfo export Environment | sed | msibuild -i` 將 `=*PATH` 後處理為 `=-*PATH`, 補入"解除安裝時移除"之語意.

### 6.3 MSI metadata 一律使用 ASCII (codepage 限制)

Windows Installer 以 `IsValidCodePage` 驗證資料庫字串池與 `_SummaryInformation` stream 的 codepage, 而 UTF-8 (`65001`) 並非系統安裝之 code page (`IsValidCodePage` 回傳 false), 驗證不過時 `msiexec` 會直接拒絕開啟封裝, 顯示不是正常的 Windows installer 封裝而完全無法安裝. 因此 `Product@Name` 與 `Package@Description` 一律使用 ASCII, 不設 `SummaryCodepage`, 由 wixl 以預設 cp1252 (Summary) 與 neutral (資料庫字串池) 寫入; 內容皆 ASCII 故不會亂碼亦可正常安裝. 若日後需於 metadata 顯示繁體中文, 須改用 cp950 (Big5) 等系統實際安裝之 code page, 而非 UTF-8 (`65001` 無法通過 `IsValidCodePage`).

## 7. 軟體更新

主選單「檢查更新…」(macOS 於應用程式選單「關於」下方, Windows 於說明選單) 會連線至 GitHub 之 `nexgus/hgsystem` 儲存庫, 列出所有 release, 略過 draft 與 prerelease, 以語意化版本 (`golang.org/x/mod/semver`) 挑出最大正式版並與當前版本比較. 線上 tag 同時存在帶與不帶 `v` 前綴兩種寫法 (如 `v0.1.1` 與 `0.7.0`), 比較前一律正規化. 版本號定義於 [`hgsys/pkg/version/version.go`](hgsys/pkg/version/version.go).

發現新版且存在對應本平台之 asset 時, 詢問使用者是否更新. 確認後由 hgsystem 自身下載對應 asset (邊下載邊以 `update:progress` event 於前端顯示進度條), 驗證大小後將內嵌的 hgupgrade 釋出至暫存目錄並啟動之, 隨即關閉自己. 後續換版由 hgupgrade 進行 (hgsystem 執行中無法替換自身):

- **macOS**: 下載 `hgsystem-<版本>-darwin-arm64` 至執行檔同目錄, 設定執行權限後以「先建暫存 symlink 再 `rename`」之原子方式, 將指向版本檔之 symlink 換成指向新版; 保留舊版本檔. 以程式下載不會被加上 `com.apple.quarantine`, 且 `go build` 對 arm64 之 ad-hoc 簽章隨位元組保留, 故無 Gatekeeper 阻擋.
- **Windows**: 下載 `hgsystem-<版本>.msi` 至暫存目錄, 以 `msiexec /i ... /qb!` 安裝 (MajorUpgrade 自動替換舊版). 因屬 per-machine 安裝, 會觸發一次 UAC 提權; 安裝中斷時 Windows Installer 一般會自動回滾為舊版.

hgupgrade 先等待原 hgsystem 行程結束 (上限 30 秒, 逾時即中止) 再換版, 完成後重新啟動. 任何換版 / 安裝前的失敗皆不動既有安裝, 改以原生對話框 (macOS `osascript`, Windows `MessageBox`) 告知使用者, 待其按確認後重啟仍可用的原版本.

hgupgrade 以 `//go:embed` 內嵌於 hgsystem (見第 2 節之編譯步驟), 更新時才釋出至暫存目錄執行, 因此不留在安裝目錄, 也不會在 Windows 上因執行中而鎖住安裝目錄.

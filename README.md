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
- 執行期 (非編譯期) 須有可連線之 MongoDB 服務. 預設連線 `localhost:27017`, 可由 `-H` / `-p` 旗標調整. 備份與還原功能另需 `mongodump` 與 `mongorestore` 於 PATH.

## 2. 編譯

以下說明假設位於 repo 根目錄:

```bash
bash build.sh
```

`build.sh` 的行為:

1. 透過 nvm 切換至 Node 20, 缺少時自動安裝.
1. 偵測 wails3 CLI, 版本不符 `v3.0.0-alpha.95` 時以 `go install` 重新安裝.
1. 視需要在 `frontend/` 執行 `npm install` 取得前端依賴.
1. 偵測 mingw, 缺少時透過 Homebrew 安裝.
1. 偵測 wixl (msitools), 缺少時透過 Homebrew 安裝.
1. `go mod download` 同步 Go 依賴.
1. 產出前端:
   - 由 `hgsys/` 內呼叫 `wails3 generate bindings -ts ./cmd/hgsystem`, 由 Go service (`pkg/app` 下之 `CustomerService`, `WorksheetService`, `SearchService`, `TitleService`, `BackupService`, `SystemService`) 反推產生 `frontend/bindings/` 之 TypeScript 綁定. 此命令須於含 `go.mod` 之目錄執行, 並指定 `./cmd/hgsystem` 為 pattern, 使 static analyser 找得到 `application.NewService(...)` 之呼叫.
   - 於 `frontend/` 執行 `npm run build`, 經 vue-tsc 型別檢查後由 Vite 輸出 `frontend/dist/`.
   - 將 `frontend/dist/` 複製為 `hgsys/cmd/hgsystem/dist/`, 供 `//go:embed all:dist` 內嵌進執行檔. Go 之 embed 不允許 `..` 跨層, 故必須以複製而非符號連結方式置入.
1. 由 `hgsys/cmd/hgsystem/icon.ico` (眼鏡圖示, 取自 Noto Emoji U+1F453, Apache-2.0 授權) 以 `rsrc` 產生 `rsrc_windows_amd64.syso` (不入版控). `go build` 偵測到此檔即自動連結, 使 windows/amd64 執行檔帶有應用程式圖示 (檔案總管 / 工作列). 同一張圖示之 `icon.png` 另由 `//go:embed` 內嵌, 經 `application.Options.Icon` 供 Wails 視窗使用.
1. 依序編譯 darwin/arm64 之 hgsystem (`CGO_ENABLED=1`, 以 `-extldflags '-mmacosx-version-min=26.0'` 對齊 Wails alpha.95 內含之 Objective-C 預編譯物件) 與 windows/amd64 之 hgsystem (`CGO_ENABLED=1`, `CC=x86_64-w64-mingw32-gcc`, 以 `-H windowsgui` 指定 GUI subsystem, 避免雙擊時跳出多餘的 console 視窗).
1. 將 `msi/hgsystem.wxs.in` 之 `@VERSION@` 替換為當前版本後寫入 `msi/hgsystem.wxs` (不入版控), 再交由 wixl 編譯為 Windows MSI 安裝程式. 末對 MSI 進行三項後處理: (a) Environment table 補入"解除安裝時自系統 PATH 移除安裝目錄"之語意 (詳見第 6.2 節); (b) `_SummaryInformation` 之 codepage 由 1252 改為 65001 (UTF-8), 使 Windows 端能正確顯示中文 description (詳見第 6.3 節); (c) 將資料庫字串池 codepage 設為 65001 並補回中文 `ProductName`, 使「新增 / 移除程式」顯示正確之中文產品名稱 (詳見第 6.4 節).
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
./bin/hgsystem -T                    # 測試模式, 更新動作即使無新版亦會重啟
./bin/hgsystem -d                    # console 輸出層級調至 DEBUG
./bin/hgsystem --version
```

執行期 log 寫至 OS 慣用位置, 每次啟動為一獨立檔案, 同日累計流水號:

- macOS: `~/Library/Logs/hgsystem/YYMMDD_NNNN.log`
- Windows: `%LOCALAPPDATA%\hgsystem\logs\YYMMDD_NNNN.log`
- 其餘平台: `$XDG_STATE_HOME/hgsystem/logs/` (或 `~/.local/state/hgsystem/logs/`).

主畫面之選單分為"系統"(更新 / 有關 / 離開) 與"資料"(備份 / 還原) 兩列. 備份與還原以 `mongodump` / `mongorestore` 子程序執行, stderr 以 Wails event 串流至前端對話框. "更新"以 go-git 程式庫自遠端 fetch 後嘗試 fast-forward, 成功則執行 `go install ./cmd/hgsystem` 後以 `syscall.Exec` 原地重啟程式; 故部署機器若需自我更新, 必須具備 Go 工具鏈 (但不需 `git` CLI, fetch 由 go-git 於行程內完成).

## 4. 清除產物

```bash
bash clear.sh
```

`clear.sh` 刪除 `build.sh` 產出之所有 binary, 中間產物與快取, 包含 `bin/`, `hgsys/cmd/hgsystem/dist/`, `frontend/dist/`, `frontend/bindings/`, `frontend/node_modules/`, `frontend/tsconfig.tsbuildinfo`, `msi/hgsystem.wxs`, 與自我更新留下之 `updated` marker. 不動 git-tracked 之原始碼; 可重複執行.

## 5. 開發者工作流

修改 Go 端 (`hgsys/`) 時, 凡新增 / 刪除 service method 或調整 domain struct 之欄位, 須重跑 `wails3 generate bindings` 重產 `frontend/bindings/`, 否則前端之 TypeScript 型別與實際 ABI 將不一致; 最直接的方式為再跑一次 `bash build.sh`.

修改 Vue 前端 (`frontend/src/`) 時, 由於 `//go:embed all:dist` 於編譯期固化前端產出, 純前端變更亦須重跑 `build.sh` (或至少 `npm run build` + 將 `frontend/dist` 重新複製至 `hgsys/cmd/hgsystem/dist`), 才能於下次 `go build` 時生效.

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

### 6.3 wixl 對 SummaryCodepage 之忽略

wixl (msitools 0.106) 不處理 `Package` 元素之 `SummaryCodepage` 屬性, 一律以 `1252` 寫入 `_SummaryInformation` stream 之 PID_CODEPAGE. hgsystem 之 description 含中文, 若以 cp1252 解讀則 Windows installer 與 Programs and Features 將顯示亂碼. `build.sh` 於 wixl 編譯後以 `msiinfo export _SummaryInformation | sed | msibuild -i` 將該值由 `1252` 改為 `65001` (UTF-8), 使 Windows 端正確解碼.

### 6.4 wixl 無法寫入非 ASCII 之 ProductName

第 6.3 節修的是 Summary Information stream (description / subject); 而「新增 / 移除程式」清單顯示的名稱來自 `Property` 表的 `ProductName`, 存於另一個獨立的資料庫字串池. wixl (msitools 0.106) 之資料庫字串池 codepage 無法編碼中文, 會把 `Product@Name` 的中文直接丟成空字串 (純 ASCII 名稱則正常). 由於字串在 wixl 階段即已遺失, 事後僅改 codepage 無法救回, 故 `build.sh` 於 wixl 編譯後分兩步後處理: (1) 以 `_ForceCodepage` 將資料庫字串池 codepage 設為 `65001` (UTF-8); (2) 自渲染後的 `msi/hgsystem.wxs` 取回 `Product@Name`, 以 `msiinfo export Property | sed | msibuild -i` 將 `ProductName` 補回中文值. 兩步須照此順序, 後者方能於 UTF-8 codepage 下正確存入. `ARPPRODUCTICON` 與 `Icon` 元素 (清單圖示) 為純 ASCII, 不受此限, 由 wixl 直接寫入.

# licenses-manual

手動維護的第三方素材授權清單,涵蓋「**既非 Go module、也非 npm 套件**」、自動掃描
工具抓不到的素材 (目前為圖示)。`scripts/gen-licenses.sh` (即 `build.sh --license`)
會讀 `manifest.json`,經 `scripts/licgen` 的 `-manual` 模式產生
`frontend/src/licenses-manual.ts` 的 `MANUAL_LICENSES`,於「關於」視窗顯示。

自動掃描的 Go / npm 依賴不放這裡 (見 README 第 5 節)。

## manifest.json 欄位

每筆為一個物件,陣列形式。除 `note` 外皆必填:

| 欄位 | 必填 | 說明 |
| --- | --- | --- |
| `name` | 是 | 元件名稱 (顯示於表格)。 |
| `url` | 是 | 首頁或原始碼倉庫位址。 |
| `type` | 是 | 授權種類,**須與 `licensecheck` 對 Go 依賴判定的 SPDX 字串一致** (如 `Apache-2.0`)。同種授權會與其他元件去重,只顯示一次條文,並據此自動判斷是否需嵌入全文 (見下)。 |
| `copyright` | 是 | 著作權聲明 (如 `Copyright 2013 Example Inc`)。 |
| `licenseUrl` | 是 | 授權原文的 **raw 文字** URL (非 GitHub `/blob/` 之類的 HTML 頁面);**釘在某個 commit/tag** 以利重現。 |
| `note` | 否 | 備註 (這是什麼素材);僅作產生檔內註解,不顯示於 UI。 |

`copyright` 與 `licenseUrl` 兩者都要備妥,因為「實際用到哪個」由產生器自動決定 (見下),
在撰寫 manifest 時並不知道。

## 嵌入全文 vs 僅引用 (自動)

產生器讀入已產生的 `licenses-go.ts` / `licenses-frontend.ts`,比對每筆素材的 `type`:

- **該 `type` 已出現在自動清單中** → 該授權全文已由那個元件提供 (例:某素材是
  Apache-2.0,而專案已有 Apache-2.0 的 Go 依賴);此筆只放 `copyright`,全文由
  `About.vue` 依授權種類去重後共用,不重複嵌入。
- **該 `type` 不在自動清單中** → 抓 `licenseUrl` 的原文、攤平後嵌入,使散布物自身即
  含授權全文 (符合 MIT / BSD / Apache / OFL 等「散布須附授權」的要求)。例:Noto Emoji
  的 SIL OFL 1.1 沒有任何 Go / npm 依賴使用,故嵌入全文。

依賴變動時此判斷會自動跟著調整 (例如某 Apache 依賴被移除後,Material Symbols 會自動
改為嵌入 Apache 全文),毋須改 manifest。

## 重新產生

```sh
bash scripts/gen-licenses.sh        # 或 bash build.sh --license
```

需要網路 (抓未涵蓋者的 `licenseUrl`);產出 `licenses-manual.ts` 已納版控,平常
`build.sh` (不加 `--license`) 沿用既有產出、離線即可。

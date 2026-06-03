// 本檔僅定義第三方授權的共用型別 ThirdPartyLicense, 供「關於」視窗的「第三方
// 授權」分頁使用. 實際的授權清單分三份, 皆為自動產生 (見各檔抬頭):
//
//   - licenses-go.ts       Go 依賴 (直接 / 間接); 由 scripts/gen-licenses.sh 掃描
//                          hgsys/go.mod 與實際編譯進 binary 的 module 產生.
//   - licenses-frontend.ts 前端 npm 依賴; 由 build.sh --license 經 Vite +
//                          rollup-plugin-license 取實際打包進 dist 者產生.
//   - licenses-manual.ts   圖示等「既非 Go module、也非 npm 套件」的素材; 由
//                          scripts/gen-licenses.sh 依 scripts/licenses-manual/
//                          manifest.json 產生 (見 README 第 5 節).
//
// 三份皆以 ThirdPartyLicense[] 匯出, 由 About.vue 合併顯示; 顯示時依授權種類去重
// (同種授權只列一次條文), 但保留各元件的著作權聲明.

// ThirdPartyLicense 描述單一第三方元件的授權資訊.
export interface ThirdPartyLicense {
  // 元件名稱.
  name: string;
  // 官方網站或原始碼倉庫位址.
  url: string;
  // 授權種類 (例如 MIT, SIL OFL 1.1).
  type: string;
  // 授權條文 (含著作權聲明); 段落間以空行分隔, 於視窗寬度內自然換行. 對手動素材
  // 而言, 若該授權全文已由同視窗中其他同種授權的元件提供, 此處可僅含著作權聲明.
  text: string;
}

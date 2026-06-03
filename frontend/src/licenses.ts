// 本檔列出 hgsystem 散布物中「既非 Go module、也非 npm 套件」的第三方素材及其
// 授權條文或來源標示, 供「關於」視窗的「第三方授權」分頁顯示. 目前有應用圖示 (Noto
// Emoji) 與 Windows 主選單圖示 (Material Symbols); 這類素材沒有套件清單可掃, 故手動
// 維護於此.
//
// 其餘第三方授權均為自動產生, 不在此檔:
//   - Go 依賴 (直接 / 間接): scripts/gen-licenses.sh 依 hgsys/go.mod 與實際編譯進
//     binary 的 module 掃描, 列於 licenses-go.ts.
//   - 前端 npm 依賴: build.sh --license 經 Vite + rollup-plugin-license 取實際打包
//     進 dist 者, 列於 licenses-frontend.ts.
// 僅於建置期使用 (不隨產品散布) 的工具 (Vite / TypeScript 等) 不列入.
//
// 應用圖示 (Noto Emoji) 的條文逐字保留對應專案 LICENSE 檔的著作權聲明與授權全文, 以
// 符合 SIL OFL 等授權「散布時須保留著作權與授權聲明」的要求. 為配合視窗寬度閱讀, 原文
// 中為固定欄寬而設的段內硬換行已攤平 (段內換行改空格, 段落間保留空行), 文字內容不變.
//
// Windows 主選單圖示 (Material Symbols, 取自 Apache-2.0 的 google/material-design-icons)
// 的 Apache License 2.0 全文已隨多個同為 Apache-2.0 的 Go 依賴顯示於同一視窗, 故此處僅
// 作來源標示, 不重複附上全文.

// ThirdPartyLicense 描述單一第三方元件的授權資訊. 亦為 licenses-go.ts 與
// licenses-frontend.ts 共用的型別.
export interface ThirdPartyLicense {
  // 元件名稱.
  name: string;
  // 官方網站或原始碼倉庫位址.
  url: string;
  // 授權種類 (例如 MIT, SIL OFL 1.1).
  type: string;
  // 授權條文 (含著作權聲明); 段落間以空行分隔, 於視窗寬度內自然換行.
  text: string;
}

// NOTO_OFL 為應用圖示 (取自 Noto Emoji 的 eyeglasses, U+1F453) 之授權. noto-emoji
// 專案以 SIL Open Font License 1.1 授權 (見 repo 根目錄的 LICENSE 檔). 條文逐字
// 取自 googlefonts/noto-emoji 之 LICENSE, 著作權為 Copyright 2013 Google LLC.
const NOTO_OFL = `Copyright 2013 Google LLC

This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is copied below, and is also available with a FAQ at: https://scripts.sil.org/OFL

-----------------------------------------------------------
SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007
-----------------------------------------------------------

PREAMBLE
The goals of the Open Font License (OFL) are to stimulate worldwide development of collaborative font projects, to support the font creation efforts of academic and linguistic communities, and to provide a free and open framework in which fonts may be shared and improved in partnership with others.

The OFL allows the licensed fonts to be used, studied, modified and redistributed freely as long as they are not sold by themselves. The fonts, including any derivative works, can be bundled, embedded, redistributed and/or sold with any software provided that any reserved names are not used by derivative works. The fonts and derivatives, however, cannot be released under any other type of license. The requirement for fonts to remain under this license does not apply to any document created using the fonts or their derivatives.

DEFINITIONS
"Font Software" refers to the set of files released by the Copyright Holder(s) under this license and clearly marked as such. This may include source files, build scripts and documentation.

"Reserved Font Name" refers to any names specified as such after the copyright statement(s).

"Original Version" refers to the collection of Font Software components as distributed by the Copyright Holder(s).

"Modified Version" refers to any derivative made by adding to, deleting, or substituting -- in part or in whole -- any of the components of the Original Version, by changing formats or by porting the Font Software to a new environment.

"Author" refers to any designer, engineer, programmer, technical writer or other person who contributed to the Font Software.

PERMISSION & CONDITIONS
Permission is hereby granted, free of charge, to any person obtaining a copy of the Font Software, to use, study, copy, merge, embed, modify, redistribute, and sell modified and unmodified copies of the Font Software, subject to the following conditions:

1) Neither the Font Software nor any of its individual components, in Original or Modified Versions, may be sold by itself.

2) Original or Modified Versions of the Font Software may be bundled, redistributed and/or sold with any software, provided that each copy contains the above copyright notice and this license. These can be included either as stand-alone text files, human-readable headers or in the appropriate machine-readable metadata fields within text or binary files as long as those fields can be easily viewed by the user.

3) No Modified Version of the Font Software may use the Reserved Font Name(s) unless explicit written permission is granted by the corresponding Copyright Holder. This restriction only applies to the primary font name as presented to the users.

4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font Software shall not be used to promote, endorse or advertise any Modified Version, except to acknowledge the contribution(s) of the Copyright Holder(s) and the Author(s) or with their explicit written permission.

5) The Font Software, modified or unmodified, in part or in whole, must be distributed entirely under this license, and must not be distributed under any other license. The requirement for fonts to remain under this license does not apply to any document created using the Font Software.

TERMINATION
This license becomes null and void if any of the above conditions are not met.

DISCLAIMER
THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM OTHER DEALINGS IN THE FONT SOFTWARE.`;

// MATERIAL_SYMBOLS_NOTICE 為 Windows 主選單圖示 (取自 Google Material Symbols,
// google/material-design-icons) 的來源標示. 該專案以 Apache License 2.0 授權; 其完整
// 條文已隨多個同為 Apache-2.0 的 Go 依賴顯示於同一視窗, 故此處僅作來源標示, 不重複附上
// 全文.
const MATERIAL_SYMBOLS_NOTICE = `Windows 主選單圖示取自 Google Material Symbols (google/material-design-icons), 以 Apache License 2.0 授權.

完整 Apache License 2.0 條文同本視窗其他 Apache-2.0 元件所示, 亦可見 https://www.apache.org/licenses/LICENSE-2.0.`;

// THIRD_PARTY_LICENSES 為手動維護的素材授權清單 (應用圖示與選單圖示).
export const THIRD_PARTY_LICENSES: ThirdPartyLicense[] = [
  {
    name: "Noto Emoji",
    url: "https://github.com/googlefonts/noto-emoji",
    type: "SIL OFL 1.1",
    text: NOTO_OFL,
  },
  {
    name: "Material Symbols",
    url: "https://github.com/google/material-design-icons",
    type: "Apache-2.0",
    text: MATERIAL_SYMBOLS_NOTICE,
  },
];

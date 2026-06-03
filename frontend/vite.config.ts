import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import wails from "@wailsio/runtime/plugins/vite";
import license from "rollup-plugin-license";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));

// GEN_LICENSES=1 時 (見 build.sh --license) 啟用第三方授權蒐集: 由
// rollup-plugin-license 取「實際打包進 dist」的 npm 套件 (經 tree-shaking 後真正
// 散布者, 不含僅建置期用的 TypeScript / Babel / postcss 等), 依 package.json 的
// dependencies 分直接 / 間接, 逐字寫入 src/licenses-frontend.ts. 此檔為前端授權的
// 權威來源 (對應 Go 端的 licenses-go.ts); 圖示素材另手動維護於 licenses.ts.
const genLicenses = process.env.GEN_LICENSES === "1";

// jsStr 將字串編成 JS 字串字面量 (正確跳脫換行 / 引號等).
function jsStr(s) {
  return JSON.stringify(s ?? "");
}

// 少數套件的 npm 包未隨附 LICENSE 檔 (licenseText 會是空字串), 為其補上權威
// 授權全文. @wailsio/runtime 屬 Wails 專案, LICENSE 在 Wails 主 repo, 與 Go 端
// Wails 共用此 MIT 條文 (顯示時會依授權種類去重).
const FALLBACK_TEXT = {
  "@wailsio/runtime": `MIT License

Copyright (c) 2018-Present Lea Anthony

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.`,
};

// frontendLicensePlugin 設定 rollup-plugin-license, 將打包進 bundle 的第三方
// npm 套件授權寫成 src/licenses-frontend.ts.
function frontendLicensePlugin() {
  const pkg = JSON.parse(readFileSync(resolve(here, "package.json"), "utf-8"));
  const directDeps = new Set(Object.keys(pkg.dependencies ?? {}));

  const emit = (arr) =>
    "[\n" +
    arr
      .map(
        (e) =>
          "  {\n" +
          `    name: ${jsStr(e.name)},\n` +
          `    url: ${jsStr(e.url)},\n` +
          `    type: ${jsStr(e.type)},\n` +
          `    text: ${jsStr(e.text)},\n` +
          "  },\n",
      )
      .join("") +
    "]";

  return license({
    thirdParty: {
      includePrivate: false,
      output: {
        file: resolve(here, "src/licenses-frontend.ts"),
        template(dependencies) {
          const items = dependencies
            .map((d) => {
              const repo =
                typeof d.repository === "string"
                  ? d.repository
                  : d.repository?.url ?? "";
              const url = (d.homepage || repo || "https://www.npmjs.com/package/" + d.name)
                .replace(/^git\+/, "")
                .replace(/\.git$/, "");
              return {
                name: d.name,
                url,
                type: d.license || "",
                text: (d.licenseText || FALLBACK_TEXT[d.name] || "").trim(),
                direct: directDeps.has(d.name),
              };
            })
            .sort((a, b) =>
              a.name.toLowerCase().localeCompare(b.name.toLowerCase()),
            );
          const direct = items.filter((i) => i.direct);
          const trans = items.filter((i) => !i.direct);
          return `// 本檔為自動產生, 請勿手動編輯. 重新產生: bash build.sh --license.
//
// 內容為實際打包進前端 dist 的 npm 套件及其授權 (由 Vite + rollup-plugin-license
// 於建置時蒐集真正進入 bundle 者), 依 package.json 的 dependencies 分直接
// (FRONTEND_DIRECT_LICENSES) 與間接 (FRONTEND_TRANSITIVE_LICENSES). 僅於建置期
// 使用、經 tree-shaking 不入 bundle 的工具 (TypeScript / Vue 編譯器 / Babel /
// postcss 等) 不列入. 應用圖示素材非 npm 套件, 另列於 licenses.ts.

import type { ThirdPartyLicense } from "./licenses";

// FRONTEND_DIRECT_LICENSES 為 package.json dependencies 中、且實際打包進 dist 者.
export const FRONTEND_DIRECT_LICENSES: ThirdPartyLicense[] = ${emit(direct)};

// FRONTEND_TRANSITIVE_LICENSES 為上述套件之相依, 同樣打包進 dist.
export const FRONTEND_TRANSITIVE_LICENSES: ThirdPartyLicense[] = ${emit(trans)};
`;
        },
      },
    },
  });
}

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: Number(process.env.WAILS_VITE_PORT) || 9245,
    strictPort: true,
  },
  plugins: [vue(), wails("./bindings"), ...(genLicenses ? [frontendLicensePlugin()] : [])],
});

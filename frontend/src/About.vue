<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { Browser } from "@wailsio/runtime";
import { SystemService } from "../bindings/hgsys/pkg/app";
import type { AboutInfo } from "../bindings/hgsys/pkg/app/models";
import { MANUAL_LICENSES } from "./licenses-manual";
import type { ThirdPartyLicense } from "./licenses";
import { GO_DIRECT_LICENSES, GO_TRANSITIVE_LICENSES } from "./licenses-go";
import { FRONTEND_DIRECT_LICENSES, FRONTEND_TRANSITIVE_LICENSES } from "./licenses-frontend";

type Tab = "about" | "license";

// 初始分頁由 Go 端選單透過 URL hash 指定 (#about-license 為第三方授權分頁).
function tabFromHash(): Tab {
  return location.hash === "#about-license" ? "license" : "about";
}

const activeTab = ref<Tab>(tabFromHash());
const info = ref<AboutInfo | null>(null);
// WebView 引擎字串只能於前端取得 (macOS WKWebView Go 端無法得知版本).
const userAgent = ref(navigator.userAgent);

// 已開啟的「關於」視窗被選單再次開啟時, Go 端僅更新 hash; 監聽 hashchange
// 以同步切換分頁, 不必重新載入頁面.
function onHashChange() {
  activeTab.value = tabFromHash();
}

// rows 為「關於」分頁逐列顯示的欄位; WebView2 僅 Windows 平台有值.
const rows = computed(() => {
  const i = info.value;
  if (!i) return [] as { label: string; value: string }[];
  const list = [
    { label: "版本", value: i.version },
    { label: "Commit", value: i.commit },
    { label: "編譯日期", value: i.buildDate },
    { label: "Go 版本", value: i.goVersion },
    { label: "作業系統", value: i.os },
    { label: "平台", value: i.platform },
    { label: "WebView", value: userAgent.value },
  ];
  if (i.webView2) {
    list.push({ label: "WebView2", value: i.webView2 });
  }
  return list;
});

// 將關於資訊整理為純文字, 供「複製資訊」使用.
function aboutText(): string {
  const lines = [info.value?.fullName ?? ""];
  for (const r of rows.value) {
    lines.push(`${r.label}: ${r.value}`);
  }
  return lines.join("\n").trimEnd();
}

async function copyAbout() {
  try {
    await navigator.clipboard.writeText(aboutText());
  } catch {
    // 某些 webview 環境無 clipboard API, 降級忽略.
  }
}

// openURL 以系統預設瀏覽器開啟連結; 直接於 webview 內導航會取代「關於」頁面.
function openURL(url: string) {
  Browser.OpenURL(url);
}

// 授權分頁分三部分: 直接引用表格 / 間接引用表格 / 各授權條文. 條文依「授權
// 種類」去重 (同種授權只顯示一次條文), 但仍逐一保留各元件的著作權聲明
// (copyright notice) 以符合 MIT / BSD / Apache 等授權的散布要求; 表格的授權
// 種類為錨點, 點擊捲動至對應的條文.

// NOTICE_SEP 為 licenses-go.ts 中附加 NOTICE 段落的分隔標記.
const NOTICE_SEP = "--- NOTICE ---";

// licAnchor 由授權種類產生錨點 id (每種授權對應唯一錨點).
function licAnchor(type: string): string {
  return "lic-" + type.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

// splitNotice 將條文與其附帶的 NOTICE 段落分開.
function splitNotice(text: string): { body: string; notice: string } {
  const i = text.indexOf(NOTICE_SEP);
  if (i < 0) return { body: text, notice: "" };
  return { body: text.slice(0, i).trimEnd(), notice: text.slice(i + NOTICE_SEP.length).trim() };
}

// extractCopyrights 取出文字中所有著作權行 (行首, 無縮排的 Copyright 行).
// 比對大小寫敏感: 著作權聲明慣例為大寫起首的 "Copyright", 藉此避開 BSD 條文
// 中因換行而以小寫 "copyright notice, ..." 起首的續行 (那是條文內容, 非聲明).
function extractCopyrights(text: string): string[] {
  return (text.match(/^Copyright\b.*$/gm) ?? []).map((s) => s.trim());
}

// stripCopyrights 移除行首的著作權行 (其餘交由區塊統一彙整), 並收斂多餘空行.
// 同樣大小寫敏感, 以免誤刪 BSD 條文中以小寫 copyright 起首的續行.
function stripCopyrights(text: string): string {
  return text
    .split("\n")
    .filter((l) => !/^Copyright\b/.test(l))
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

interface LicenseBlock {
  anchor: string;
  type: string;
  copyrights: string[];
  body: string;
  notices: string[];
}

// reflow 將為固定欄寬而硬換行的條文重排為段落, 使其於視窗寬度內自然換行而
// 不致鋸齒 (硬換行 + 二次自動折行的疊加). 規則: 空行維持段落分隔; 以項目
// 符號 (* - •) 或編號項 ((a) / 1. 等) 起首的行另起一行; 其餘單一硬換行視為
// 同段續行, 併為空白. licenses-go.ts / licenses-frontend.ts 取自各 LICENSE 原檔多含
// 80 欄硬換行, 故套用此處理; licenses-manual.ts 已由產生器 (licgen) 以相同規則攤平,
// 不再於此重排 (reflowBody=false).
function reflow(text: string): string {
  const out: string[] = [];
  for (const raw of text.split("\n")) {
    if (raw.trim() === "") {
      out.push("");
      continue;
    }
    const t = raw.trim();
    const isItem = /^[*\-•]\s/.test(t) || /^\d+[.)]\s/.test(t) || /^\([0-9a-zA-Z]+\)\s/.test(t);
    if (out.length === 0 || out[out.length - 1] === "" || isItem) {
      out.push(t);
    } else {
      out[out.length - 1] += " " + t;
    }
  }
  return out.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

// buildLicenseBlocks 依授權種類彙整: 同種授權的條文僅取「首次出現」者為代表全文,
// 但收集所有元件的著作權聲明與 NOTICE. 故呼叫端須將自動掃描的 Go / npm 依賴排在
// 手動素材之前, 使代表全文為其原始 LICENSE 全文 (手動素材的 embed=false 項僅含著作
// 權聲明, 不應成為代表). reflowBody 為 true 時 (取自原始 LICENSE 檔) 對條文與
// NOTICE 套用 reflow.
function buildLicenseBlocks(items: { comp: ThirdPartyLicense; reflowBody: boolean }[]): LicenseBlock[] {
  const map = new Map<string, LicenseBlock>();
  const order: LicenseBlock[] = [];
  for (const { comp, reflowBody } of items) {
    const { body, notice } = splitNotice(comp.text);
    let blk = map.get(comp.type);
    if (!blk) {
      const b = stripCopyrights(body);
      blk = { anchor: licAnchor(comp.type), type: comp.type, copyrights: [], body: reflowBody ? reflow(b) : b, notices: [] };
      map.set(comp.type, blk);
      order.push(blk);
    }
    for (const cp of extractCopyrights(comp.text)) {
      if (!blk.copyrights.includes(cp)) blk.copyrights.push(cp);
    }
    const n = notice ? (reflowBody ? reflow(notice) : notice) : "";
    if (n && !blk.notices.includes(n)) blk.notices.push(n);
  }
  return order;
}

// blockText 組出單一授權區塊的完整顯示文字: 著作權聲明 + 條文 + NOTICE.
function blockText(b: LicenseBlock): string {
  const parts: string[] = [];
  if (b.copyrights.length) parts.push(b.copyrights.join("\n"));
  parts.push(b.body);
  for (const n of b.notices) parts.push("NOTICE\n\n" + n);
  return parts.join("\n\n");
}

// 次序重要: 自動掃描的 Go / npm 依賴在前, 手動素材在後, 使各授權的代表全文取自
// 原始 LICENSE; 手動素材中 embed=false 者僅補上著作權聲明 (其全文已由前面同種授權
// 的元件提供), 不會覆蓋代表全文.
const licenseBlocks = buildLicenseBlocks([
  ...FRONTEND_DIRECT_LICENSES.map((comp) => ({ comp, reflowBody: true })),
  ...FRONTEND_TRANSITIVE_LICENSES.map((comp) => ({ comp, reflowBody: true })),
  ...GO_DIRECT_LICENSES.map((comp) => ({ comp, reflowBody: true })),
  ...GO_TRANSITIVE_LICENSES.map((comp) => ({ comp, reflowBody: true })),
  ...MANUAL_LICENSES.map((comp) => ({ comp, reflowBody: false })),
]);

// 兩個表格逐元件列出; 授權種類連結指向去重後的對應條文區塊. 直接引用表合併
// 手動素材 (licenses-manual.ts)、前端 npm 直接依賴 (licenses-frontend.ts) 與 Go
// 直接依賴 (licenses-go.ts); 間接引用表合併前端與 Go 的間接依賴.
function toRows(comps: ThirdPartyLicense[]) {
  return comps.map((c) => ({ name: c.name, url: c.url, type: c.type, anchor: licAnchor(c.type) }));
}
const tables = [
  {
    title: "直接引用",
    rows: toRows([...MANUAL_LICENSES, ...FRONTEND_DIRECT_LICENSES, ...GO_DIRECT_LICENSES]),
  },
  {
    title: "間接引用 (transitive)",
    rows: toRows([...FRONTEND_TRANSITIVE_LICENSES, ...GO_TRANSITIVE_LICENSES]),
  },
];

// scrollToAnchor 捲動至指定錨點的條文區塊 (授權分頁的捲動容器為 .tab-body).
function scrollToAnchor(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

onMounted(async () => {
  window.addEventListener("hashchange", onHashChange);
  info.value = await SystemService.GetAbout();
  if (info.value) {
    document.title = "關於 " + info.value.appName;
  }
});

onUnmounted(() => {
  window.removeEventListener("hashchange", onHashChange);
});
</script>

<template>
  <div class="about">
    <nav class="tabs">
      <button :class="{ active: activeTab === 'about' }" @click="activeTab = 'about'">
        關於
      </button>
      <button :class="{ active: activeTab === 'license' }" @click="activeTab = 'license'">
        第三方授權
      </button>
    </nav>

    <section v-if="activeTab === 'about'" class="tab-body">
      <header class="hero">
        <div class="logo" aria-hidden="true">👓</div>
        <div class="hero-text">
          <div class="app-name">{{ info?.appName }}</div>
          <div class="full-name">{{ info?.fullName }}</div>
        </div>
      </header>

      <dl class="fields">
        <template v-for="row in rows" :key="row.label">
          <dt>{{ row.label }}</dt>
          <dd>{{ row.value }}</dd>
        </template>
      </dl>

      <footer class="about-footer">
        <span class="copyright">{{ info?.copyright }}</span>
        <button @click="copyAbout">複製資訊</button>
      </footer>
    </section>

    <section v-else class="tab-body licenses">
      <p class="intro">
        本軟體散布物中引用下列第三方開源元件, 謹此致謝, 並依各自授權條款保留其著作權聲明與授權全文.
      </p>

      <template v-for="t in tables" :key="t.title">
        <h3 class="sec-title">{{ t.title }}</h3>
        <table class="lic-table">
          <thead>
            <tr>
              <th>名稱</th>
              <th>網站</th>
              <th>授權</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in t.rows" :key="row.name">
              <td>{{ row.name }}</td>
              <td>
                <a href="#" @click.prevent="openURL(row.url)">{{ row.url }}</a>
              </td>
              <td>
                <a href="#" class="lic-link" @click.prevent="scrollToAnchor(row.anchor)">
                  {{ row.type }}
                </a>
              </td>
            </tr>
          </tbody>
        </table>
      </template>

      <h3 class="sec-title">各授權條文</h3>
      <div v-for="blk in licenseBlocks" :id="blk.anchor" :key="blk.anchor" class="lic-block">
        <h4>{{ blk.type }}</h4>
        <pre>{{ blockText(blk) }}</pre>
      </div>
    </section>
  </div>
</template>

<style scoped>
.about {
  display: grid;
  grid-template-rows: auto 1fr;
  height: 100vh;
  width: 100vw;
}

.tabs {
  display: flex;
  gap: 4px;
  padding: 8px 12px 0;
  border-bottom: 1px solid #d1d1d6;
  background-color: #ececef;
}

.tabs button {
  border: 1px solid #c6c6c8;
  border-bottom: none;
  border-radius: 6px 6px 0 0;
  background-color: transparent;
  padding: 6px 16px;
}

.tabs button.active {
  background-color: #ffffff;
  font-weight: 600;
}

.tab-body {
  min-height: 0;
  overflow: auto;
  padding: 16px;
}

.hero {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}

.logo {
  font-size: 44px;
  line-height: 1;
}

.app-name {
  font-size: 20px;
  font-weight: 700;
}

.full-name {
  color: #6c6c70;
  font-size: 13px;
}

.fields {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 6px 14px;
  margin: 0;
}

.fields dt {
  font-weight: 600;
  white-space: nowrap;
}

.fields dd {
  margin: 0;
  user-select: text;
  -webkit-user-select: text;
  word-break: break-word;
}

.about-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 20px;
  padding-top: 12px;
  border-top: 1px solid #e5e5ea;
}

.copyright {
  color: #6c6c70;
  font-size: 12px;
}

.licenses .intro {
  margin: 0 0 14px;
  color: #6c6c70;
  font-size: 12px;
}

.lic-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 18px;
  font-size: 12px;
  /* 固定佈局: 欄寬不隨內容撐大, 長 URL / module 名稱於欄內換行, 表格永不
     超出視窗 (避免授權分頁出現水平捲軸). */
  table-layout: fixed;
}

.lic-table th,
.lic-table td {
  text-align: left;
  padding: 5px 8px;
  border-bottom: 1px solid #e5e5ea;
  vertical-align: top;
  /* 覆蓋全域 style.css 的 `th, td { white-space: nowrap }`: 授權表需讓長字串
     (URL / module 路徑) 換行, 否則 nowrap 會使 word-break / overflow-wrap 失效,
     儲存格撐爆而出現水平捲軸. 授權種類欄另由 .lic-link 維持 nowrap. */
  white-space: normal;
  word-break: break-word;
  overflow-wrap: anywhere;
}

/* 名稱欄固定比例, 授權欄固定窄寬 (足以容納 "BSD-3-Clause"), 其餘留給網站欄. */
.lic-table th:first-child,
.lic-table td:first-child {
  width: 34%;
}

.lic-table th:last-child,
.lic-table td:last-child {
  width: 104px;
}

.lic-table th {
  font-weight: 600;
  border-bottom: 1px solid #d1d1d6;
}

.lic-table td a {
  color: #0a6cff;
  text-decoration: none;
  word-break: break-all;
}

.lic-table td a:hover {
  text-decoration: underline;
}

.sec-title {
  font-size: 14px;
  margin: 18px 0 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #d1d1d6;
}

.lic-link {
  white-space: nowrap;
  word-break: normal;
}

.lic-block {
  margin-top: 16px;
}

.lic-block h4 {
  font-size: 13px;
  margin: 0 0 6px;
}

.lic-block pre {
  margin: 0;
  padding: 8px 10px;
  background-color: #f5f5f7;
  border: 1px solid #e5e5ea;
  border-radius: 6px;
  font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  font-size: 11px;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: normal;
  overflow-wrap: break-word;
  user-select: text;
  -webkit-user-select: text;
}

@media (prefers-color-scheme: dark) {
  .tabs {
    background-color: #2c2c2e;
    border-color: #3a3a3c;
  }

  .tabs button {
    border-color: #48484a;
  }

  .tabs button.active {
    background-color: #1c1c1e;
  }

  .full-name,
  .copyright,
  .licenses .intro {
    color: #98989d;
  }

  .about-footer {
    border-color: #3a3a3c;
  }

  .sec-title {
    border-color: #3a3a3c;
  }

  .lic-table th,
  .lic-table td {
    border-color: #3a3a3c;
  }

  .lic-table td a {
    color: #4ea1ff;
  }

  .lic-block pre {
    background-color: #2c2c2e;
    border-color: #3a3a3c;
  }
}
</style>

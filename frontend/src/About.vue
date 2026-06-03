<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { SystemService } from "../bindings/hgsys/pkg/app";
import type { AboutInfo } from "../bindings/hgsys/pkg/app/models";

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

    <section v-else class="tab-body placeholder">
      <p>To Be Implemented</p>
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

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6c6c70;
  font-size: 14px;
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
  .placeholder {
    color: #98989d;
  }
  .about-footer {
    border-color: #3a3a3c;
  }
}
</style>

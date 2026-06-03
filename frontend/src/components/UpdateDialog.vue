<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from "vue";
import { Events } from "@wailsio/runtime";
import { UpdateService } from "../../bindings/hgsys/pkg/app";

const emit = defineEmits<{ (e: "close"): void }>();

// checking   — 正在向 GitHub 查詢最新版本
// uptodate   — 已是最新版本
// available  — 有新版, 等待使用者確認
// downloading— 下載中 (由 hgsystem 進行, 完成後關閉自己交由 hgupgrade)
// error      — 查詢或下載失敗
type Phase = "checking" | "uptodate" | "available" | "downloading" | "error";

const phase = ref<Phase>("checking");
const currentVersion = ref("");
const latestVersion = ref("");
const progress = ref(0);
const errMsg = ref("");

let stopProgress: (() => void) | null = null;

onMounted(async () => {
  // 下載進度由後端以 update:progress event 推送 (0-100).
  stopProgress = Events.On("update:progress", (event: { data: number }) => {
    progress.value = Number(event.data) || 0;
  });
  try {
    const info = await UpdateService.CheckForUpdate();
    currentVersion.value = info.currentVersion ?? "";
    latestVersion.value = info.latestVersion ?? "";
    phase.value = info.hasUpdate ? "available" : "uptodate";
  } catch (e) {
    errMsg.value = String(e);
    phase.value = "error";
  }
});

onBeforeUnmount(() => {
  stopProgress?.();
});

// startUpgrade 觸發下載. 成功時 hgsystem 會在啟動 hgupgrade 後關閉自己, 故此
// 呼叫通常不會正常返回; 僅在下載 / 準備階段失敗時 catch 並顯示錯誤.
async function startUpgrade() {
  phase.value = "downloading";
  progress.value = 0;
  try {
    await UpdateService.StartUpgrade();
  } catch (e) {
    errMsg.value = String(e);
    phase.value = "error";
  }
}
</script>

<template>
  <div class="dialog-backdrop">
    <div class="dialog update-dialog">
      <div class="dialog-title">軟體更新</div>

      <template v-if="phase === 'checking'">
        <div class="message">正在檢查是否有新版本…</div>
      </template>

      <template v-else-if="phase === 'uptodate'">
        <div class="message">目前已是最新版本 ({{ currentVersion }})。</div>
        <div class="dialog-actions">
          <button @click="emit('close')">關閉</button>
        </div>
      </template>

      <template v-else-if="phase === 'available'">
        <div class="message">
          發現新版本 {{ latestVersion }}(目前為 {{ currentVersion }})。<br />
          是否要立即下載並更新?更新過程中應用程式會重新啟動。
        </div>
        <div class="dialog-actions">
          <button @click="startUpgrade">立即更新</button>
          <button @click="emit('close')">稍後</button>
        </div>
      </template>

      <template v-else-if="phase === 'downloading'">
        <div class="message">
          {{ progress >= 100 ? "下載完成,即將重新啟動…" : "下載新版本中…" }}
        </div>
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <div class="progress-pct">{{ progress }}%</div>
      </template>

      <template v-else>
        <div class="message error">更新失敗:{{ errMsg }}</div>
        <div class="dialog-actions">
          <button @click="emit('close')">關閉</button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.update-dialog {
  min-width: 380px;
  max-width: 480px;
}
.message {
  font-size: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.message.error {
  color: var(--error-fg);
}
.progress-track {
  height: 10px;
  border-radius: 5px;
  background-color: var(--border-color);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background-color: var(--row-highlight-bg);
  transition: width 0.15s ease;
}
.progress-pct {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-size: 13px;
}
</style>

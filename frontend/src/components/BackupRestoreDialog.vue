<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from "vue";
import { Events } from "@wailsio/runtime";
import { BackupService } from "../../bindings/hgsys/pkg/app";

const props = defineProps<{
  savepath: string;
  mode: "backup" | "restore";
}>();

const emit = defineEmits<{ (e: "close"): void }>();

const lines = ref<string[]>([]);
const running = ref(false);
const done = ref(false);
const errMsg = ref("");

let stopLine: (() => void) | null = null;
let stopDone: (() => void) | null = null;

onMounted(() => {
  stopLine = Events.On("backup:line", (event: { data: string }) => {
    lines.value = [...lines.value, event.data];
  });
  stopDone = Events.On("backup:done", (event: { data: string }) => {
    errMsg.value = event.data ?? "";
    running.value = false;
    done.value = true;
  });
});

onBeforeUnmount(() => {
  stopLine?.();
  stopDone?.();
});

async function start() {
  running.value = true;
  lines.value = [];
  errMsg.value = "";
  done.value = false;
  try {
    if (props.mode === "backup") {
      await BackupService.Dump(props.savepath);
    } else {
      await BackupService.Restore(props.savepath);
    }
  } catch (e) {
    errMsg.value = String(e);
    running.value = false;
    done.value = true;
  }
}
</script>

<template>
  <div class="dialog-backdrop">
    <div class="dialog backup-dialog">
      <div class="dialog-title">{{ mode === "backup" ? "備份" : "還原" }}</div>
      <div class="row">
        <span>目錄: {{ savepath }}</span>
      </div>
      <pre class="output">{{ lines.join("\n") }}</pre>
      <div v-if="errMsg" class="error">錯誤: {{ errMsg }}</div>
      <div class="dialog-actions">
        <button v-if="!done" :disabled="running" @click="start">
          {{
            running
              ? mode === "backup"
                ? "備份中..."
                : "還原中..."
              : "開始"
          }}
        </button>
        <button v-else @click="emit('close')">完成</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.backup-dialog {
  width: 720px;
  height: 520px;
}
.output {
  flex: 1;
  margin: 0;
  background: #1c1c1c;
  color: #c8c8c8;
  font-family: "Courier New", monospace;
  font-size: 12px;
  padding: 8px;
  overflow: auto;
  white-space: pre-wrap;
  border-radius: 4px;
}
.error {
  color: red;
}
</style>

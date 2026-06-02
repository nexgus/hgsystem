<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";

defineEmits<{
  (e: "about"): void;
  (e: "exit"): void;
  (e: "backup"): void;
  (e: "restore"): void;
}>();

const open = ref<string | null>(null);
function toggle(name: string) {
  open.value = open.value === name ? null : name;
}
function close() {
  open.value = null;
}

function onDocClick(e: MouseEvent) {
  const target = e.target as HTMLElement;
  if (!target.closest(".menu-bar")) close();
}
onMounted(() => document.addEventListener("click", onDocClick));
onBeforeUnmount(() => document.removeEventListener("click", onDocClick));
</script>

<template>
  <div class="menu-bar">
    <div class="menu">
      <button class="menu-button" @click="toggle('system')">系統</button>
      <div v-if="open === 'system'" class="menu-popup">
        <button @click="() => { $emit('about'); close(); }">有關</button>
        <button @click="() => { $emit('exit'); close(); }">離開</button>
      </div>
    </div>
    <div class="menu">
      <button class="menu-button" @click="toggle('data')">資料</button>
      <div v-if="open === 'data'" class="menu-popup">
        <button @click="() => { $emit('backup'); close(); }">備份</button>
        <button @click="() => { $emit('restore'); close(); }">還原</button>
      </div>
    </div>
  </div>
</template>

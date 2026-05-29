<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{
  titles: string[];
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "add", name: string): void;
  (e: "remove", name: string): void;
}>();

const draft = ref("");

function onAdd() {
  const name = draft.value.trim();
  if (!name) return;
  if (props.titles.includes(name)) {
    draft.value = "";
    return;
  }
  emit("add", name);
  draft.value = "";
}

function onRemove(name: string) {
  emit("remove", name);
}
</script>

<template>
  <div class="dialog-backdrop" @click.self="emit('close')">
    <div class="dialog title-dialog">
      <div class="dialog-title">管理稱謂</div>

      <div class="add-row">
        <input
          v-model="draft"
          placeholder="新稱謂"
          @keydown.enter.prevent="onAdd"
        />
        <button :disabled="!draft.trim()" @click="onAdd">新增</button>
      </div>

      <div class="list">
        <div v-if="titles.length === 0" class="empty">(目前清單為空)</div>
        <div v-for="t in titles" :key="t" class="list-row">
          <span class="name">{{ t }}</span>
          <button class="remove" @click="onRemove(t)">刪除</button>
        </div>
      </div>

      <div class="dialog-actions">
        <button @click="emit('close')">關閉</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.title-dialog {
  width: 360px;
  max-height: 70vh;
}
.add-row {
  display: flex;
  gap: 6px;
}
.add-row input {
  flex: 1;
}
.list {
  flex: 1;
  overflow: auto;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  min-height: 120px;
  max-height: 300px;
}
.list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  border-bottom: 1px solid var(--border-color);
}
.list-row:last-child {
  border-bottom: none;
}
.list-row .name {
  flex: 1;
}
.list-row .remove {
  font-size: 12px;
  padding: 2px 8px;
}
.empty {
  text-align: center;
  color: var(--placeholder-fg);
  padding: 24px 0;
}
</style>

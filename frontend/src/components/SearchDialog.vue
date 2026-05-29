<script setup lang="ts">
import { ref } from "vue";
import type { Customer } from "../lib/types";
import { formatROCDate } from "../lib/rocDate";
import { SearchService } from "../../bindings/hgsys/pkg/app";
import ROCDateInput from "./ROCDateInput.vue";

const emit = defineEmits<{
  (e: "close"): void;
  (e: "accept", c: Customer): void;
}>();

const phone = ref("");
const birthdate = ref<string | null>(null);
const name = ref("");
const addr = ref("");

const results = ref<Customer[]>([]);
const selectedId = ref<string>("");

async function doSearch() {
  const list = await SearchService.Search({
    name: name.value.trim(),
    addr: addr.value.trim(),
    phone: phone.value.trim(),
    birthdate: birthdate.value,
  });
  results.value = list ?? [];
  selectedId.value = results.value[0]?.id ?? "";
}

async function doHistory() {
  const list = await SearchService.History();
  results.value = list ?? [];
  selectedId.value = results.value[0]?.id ?? "";
}

function onAccept() {
  const picked = results.value.find((c) => c.id === selectedId.value);
  if (picked) emit("accept", picked);
}
</script>

<template>
  <div class="dialog-backdrop" @click.self="emit('close')">
    <div class="dialog search-dialog">
      <div class="dialog-title">搜尋</div>
      <div class="filters">
        <div class="row">
          <label>電話</label>
          <input v-model="phone" class="edit-red" style="flex: 1" />
        </div>
        <div class="row">
          <label>生日</label>
          <ROCDateInput v-model="birthdate" mode="modify" />
        </div>
        <div class="row">
          <label>姓名</label>
          <input v-model="name" class="edit-red" style="flex: 1" />
        </div>
        <div class="row">
          <label>地址</label>
          <input v-model="addr" class="edit-red" style="flex: 1" />
        </div>
        <div class="row">
          <button @click="doSearch">(F) 搜尋</button>
          <button @click="doHistory">(H) 記錄</button>
        </div>
      </div>
      <table class="results">
        <thead>
          <tr>
            <th>姓名</th>
            <th>生日</th>
            <th>電話</th>
            <th>地址</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in results"
            :key="c.id"
            :class="{ selected: c.id === selectedId }"
            @click="selectedId = c.id"
            @dblclick="onAccept"
          >
            <td>{{ c.name }}</td>
            <td>{{ formatROCDate(c.birthdate) }}</td>
            <td>{{ c.phones }}</td>
            <td>{{ c.addr }}</td>
          </tr>
          <tr v-if="results.length === 0">
            <td colspan="4" class="empty">(無結果)</td>
          </tr>
        </tbody>
      </table>
      <div class="dialog-actions">
        <button :disabled="!selectedId" @click="onAccept">(Y) 確定</button>
        <button @click="emit('close')">(N) 取消</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-dialog {
  width: 720px;
  height: 520px;
}
.filters {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.filters label {
  width: 60px;
}
.results {
  flex: 1;
  display: block;
  overflow: auto;
  border: 1px solid var(--border-color);
}
.results tr {
  cursor: pointer;
}
td.empty {
  text-align: center;
  color: var(--placeholder-fg);
  padding: 12px;
}
</style>

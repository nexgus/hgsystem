<script setup lang="ts">
import { nextTick, ref } from "vue";
import type { Customer } from "../lib/types";
import { formatROCDate } from "../lib/rocDate";
import { SearchService, SearchResult } from "../../bindings/hgsys/pkg/app";
import ROCDateInput from "./ROCDateInput.vue";
import { nextRowIndex, rowsPerPage, scrollSelectedIntoView } from "../lib/tableNav";

const emit = defineEmits<{
  (e: "close"): void;
  (e: "accept", c: Customer): void;
}>();

const phone = ref("");
const birthdate = ref<string | null>(null);
const name = ref("");
const addr = ref("");
const dateField = ref<"order" | "deliver">("order");
const dateFrom = ref<string | null>(null);
const dateTo = ref<string | null>(null);

const results = ref<SearchResult[]>([]);
const selectedId = ref<string>("");

async function doSearch() {
  const list = await SearchService.Search({
    name: name.value.trim(),
    addr: addr.value.trim(),
    phone: phone.value.trim(),
    birthdate: birthdate.value,
    dateField: dateField.value,
    dateFrom: dateFrom.value,
    dateTo: dateTo.value,
  });
  results.value = list ?? [];
  selectedId.value = results.value[0]?.customer.id ?? "";
}

async function doHistory() {
  const list = await SearchService.History();
  results.value = list ?? [];
  selectedId.value = results.value[0]?.customer.id ?? "";
}

function onAccept() {
  const picked = results.value.find((r) => r.customer.id === selectedId.value);
  if (picked) emit("accept", picked.customer);
}

const resultsEl = ref<HTMLElement>();

// 結果表格 focus 時: 上下鍵 / PageUp,Down / Home,End 移動選取列, Enter 等同確定.
function onKeydown(e: KeyboardEvent) {
  if (results.value.length === 0) return;
  if (e.key === "Enter") {
    e.preventDefault();
    onAccept();
    return;
  }
  const current = results.value.findIndex((r) => r.customer.id === selectedId.value);
  const next = nextRowIndex(e.key, current, results.value.length, rowsPerPage(resultsEl.value));
  if (next === null) return;
  e.preventDefault();
  selectedId.value = results.value[next].customer.id;
  nextTick(() => scrollSelectedIntoView(resultsEl.value));
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
          <select v-model="dateField" class="date-field-select">
            <option value="order">收件期間</option>
            <option value="deliver">交件期間</option>
          </select>
          <ROCDateInput v-model="dateFrom" mode="modify" />
          <span class="date-sep">~</span>
          <ROCDateInput v-model="dateTo" mode="modify" />
        </div>
        <div class="row search-buttons">
          <button @click="doSearch">搜尋</button>
          <button @click="doHistory">搜尋紀錄</button>
        </div>
      </div>
      <table class="results" ref="resultsEl" tabindex="0" @keydown="onKeydown">
        <thead>
          <tr>
            <th>姓名</th>
            <th>生日</th>
            <th>電話</th>
            <th>地址</th>
            <th>OD/R SPH</th>
            <th>OS/L SPH</th>
            <th>收件日</th>
            <th>交件日</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in results"
            :key="r.customer.id"
            :class="{ selected: r.customer.id === selectedId }"
            @click="selectedId = r.customer.id"
            @dblclick="onAccept"
          >
            <td>{{ r.customer.name }}</td>
            <td>{{ formatROCDate(r.customer.birthdate) }}</td>
            <td>{{ r.customer.phones }}</td>
            <td>{{ r.customer.addr }}</td>
            <td>{{ r.lastSphR }}</td>
            <td>{{ r.lastSphL }}</td>
            <td>{{ formatROCDate(r.lastOrderTime) }}</td>
            <td>{{ formatROCDate(r.lastDeliverTime) }}</td>
          </tr>
          <tr v-if="results.length === 0">
            <td colspan="8" class="empty">(無結果)</td>
          </tr>
        </tbody>
      </table>
      <div class="dialog-actions">
        <button :disabled="!selectedId" @click="onAccept">確定</button>
        <button @click="emit('close')">取消</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-dialog {
  width: 1120px;
  height: 540px;
}
.filters {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
/* 左欄: 文字 label 與日期下拉皆對齊到同一寬度, 讓視覺上"標題欄"連成一直線. */
.filters > .row > label:first-child,
.filters > .row > .date-field-select {
  width: 100px;
  flex: 0 0 auto;
}
.date-sep {
  margin: 0 6px;
}
.search-buttons > button {
  flex: 1;
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
/* 度數與日期欄較窄且不換行, 讓八欄在加寬後的視窗內一次看完, 不必右捲. */
.results th,
.results td {
  white-space: nowrap;
}
td.empty {
  text-align: center;
  color: var(--placeholder-fg);
  padding: 12px;
}
</style>

<script setup lang="ts">
import { computed } from "vue";
import type { Worksheet } from "../lib/types";
import { formatROCDate } from "../lib/rocDate";

const props = defineProps<{
  rows: Worksheet[];
  currentId: string;
  frozen: boolean;
}>();

const emit = defineEmits<{
  (e: "select", id: string): void;
}>();

const columns = [
  { key: "order", label: "收件日" },
  { key: "deliver", label: "交件日" },
  { key: "sphR", label: "SPH(R)" },
  { key: "sphL", label: "SPH(L)" },
  { key: "cylR", label: "CYL(R)" },
  { key: "cylL", label: "CYL(L)" },
  { key: "bcR", label: "BC(R)" },
  { key: "bcL", label: "BC(L)" },
  { key: "eyesightR", label: "視力(R)" },
  { key: "eyesightL", label: "視力(L)" },
  { key: "lensR", label: "鏡片(R)" },
  { key: "lensL", label: "鏡片(L)" },
  { key: "frame", label: "鏡架" },
];

function cell(w: Worksheet, key: string): string {
  switch (key) {
    case "order":
      return formatROCDate(w.orderTime);
    case "deliver":
      return formatROCDate(w.deliverTime);
    default:
      return (w as unknown as Record<string, unknown>)[key]?.toString() ?? "";
  }
}

const visibleRows = computed(() => props.rows);
</script>

<template>
  <div :class="['history-table', { frozen }]">
    <table>
      <thead>
        <tr>
          <th v-for="c in columns" :key="c.key">{{ c.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="w in visibleRows"
          :key="w.id"
          :class="{ selected: w.id === currentId }"
          @click="frozen ? null : emit('select', w.id)"
        >
          <td v-for="c in columns" :key="c.key">{{ cell(w, c.key) }}</td>
        </tr>
        <tr v-if="visibleRows.length === 0">
          <td :colspan="columns.length" class="empty">(無工單)</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.history-table {
  border: 1px solid var(--border-color);
  border-radius: 4px;
  overflow: auto;
  max-height: 240px;
}
.history-table.frozen {
  opacity: 0.6;
  pointer-events: none;
}
td.empty {
  text-align: center;
  color: #999;
  padding: 12px;
}
tr {
  cursor: pointer;
}
</style>

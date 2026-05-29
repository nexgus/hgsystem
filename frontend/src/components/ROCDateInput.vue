<script setup lang="ts">
import { computed, watch } from "vue";
import {
  YEAR_NONE,
  toROCYear,
  fromROCParts,
  toROCParts,
  daysInMonth,
} from "../lib/rocDate";
import type { EditMode } from "../lib/editMode";
import { isEditable, editClass } from "../lib/editMode";

const props = defineProps<{
  modelValue: string | null;
  mode: EditMode;
  yearLabel?: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: string | null): void;
}>();

const minROC = toROCYear(1);
const maxROC = toROCYear(9999);

const parts = computed(() => toROCParts(props.modelValue));

function emitFromParts(year: number, month: number, day: number) {
  const d = fromROCParts(year, month, day);
  emit("update:modelValue", d ? d.toISOString() : null);
}

const days = computed(() => {
  const max = daysInMonth(parts.value.year, parts.value.month);
  return Array.from({ length: max + 1 }, (_, i) => i);
});

watch(
  () => parts.value.month,
  () => {
    // 月份變更時, 原本的日數可能超出範圍, 在此夾到合法值.
    const max = daysInMonth(parts.value.year, parts.value.month);
    if (parts.value.day > max) {
      emitFromParts(parts.value.year, parts.value.month, max);
    }
  },
);

const enabled = computed(() => isEditable(props.mode));
const klass = computed(() => editClass(props.mode));

function setYear(v: string) {
  const n = Number(v);
  emitFromParts(Number.isFinite(n) ? n : 0, parts.value.month, parts.value.day);
}
function setMonth(v: string) {
  emitFromParts(parts.value.year, Number(v), parts.value.day);
}
function setDay(v: string) {
  emitFromParts(parts.value.year, parts.value.month, Number(v));
}
</script>

<template>
  <span class="roc-date">
    <span class="era">民國</span>
    <input
      type="number"
      :min="minROC"
      :max="maxROC"
      :value="parts.year"
      :disabled="!enabled"
      :class="klass"
      style="width: 70px; text-align: right"
      @input="(e) => setYear((e.target as HTMLInputElement).value)"
    />
    <span>年</span>
    <select
      :value="parts.month"
      :disabled="!enabled"
      :class="klass"
      @change="(e) => setMonth((e.target as HTMLSelectElement).value)"
    >
      <option v-for="m in 13" :key="m - 1" :value="m - 1">{{ m - 1 }}</option>
    </select>
    <span>月</span>
    <select
      :value="parts.day"
      :disabled="!enabled"
      :class="klass"
      @change="(e) => setDay((e.target as HTMLSelectElement).value)"
    >
      <option v-for="d in days" :key="d" :value="d">{{ d }}</option>
    </select>
    <span>日</span>
  </span>
</template>

<style scoped>
.roc-date {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.era {
  font-size: 14px;
}
</style>

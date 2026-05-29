<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { YEAR_NONE, toROCYear, toROCParts } from "../lib/rocDate";
import {
  formatROCParts,
  parseROCDateInput,
  isValidROCParts,
  rocPartsErrorMessage,
  rocPartsToISO,
  type ROCDateParts,
} from "../lib/rocDateInput";
import type { EditMode } from "../lib/editMode";
import { isEditable, editClass } from "../lib/editMode";

const props = defineProps<{
  modelValue: string | null;
  mode: EditMode;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: string | null): void;
}>();

const enabled = computed(() => isEditable(props.mode));
const klass = computed(() => editClass(props.mode));

const text = ref(formatROCParts(toROCParts(props.modelValue)));
const error = ref<string | null>(null);

watch(
  () => props.modelValue,
  (v) => {
    const parsed = parseROCDateInput(text.value);
    if (parsed && isValidROCParts(parsed) && rocPartsToISO(parsed) === v) {
      // 使用者輸入剛好對應到外部更新的值, 不覆寫他正在打的字.
      return;
    }
    text.value = formatROCParts(toROCParts(v));
    error.value = null;
  },
);

function onInput(e: Event) {
  const v = (e.target as HTMLInputElement).value;
  text.value = v;
  const parsed = parseROCDateInput(v);
  if (parsed && isValidROCParts(parsed)) {
    error.value = null;
    const iso = rocPartsToISO(parsed);
    if (iso !== props.modelValue) emit("update:modelValue", iso);
  }
  // 打字途中不顯示錯誤, 等失焦再判.
}

function onBlur() {
  const v = text.value.trim();
  if (!v) {
    error.value = null;
    if (props.modelValue !== null) emit("update:modelValue", null);
    text.value = "";
    return;
  }
  const parsed = parseROCDateInput(v);
  if (!parsed) {
    error.value = "格式不正確 (例: 114/05/29、5/29、1971/05/29 或 1140529)";
    return;
  }
  if (!isValidROCParts(parsed)) {
    error.value = rocPartsErrorMessage(parsed);
    return;
  }
  error.value = null;
  text.value = formatROCParts(parsed);
  const iso = rocPartsToISO(parsed);
  if (iso !== props.modelValue) emit("update:modelValue", iso);
}

const pickerRef = ref<HTMLInputElement | null>(null);

const pickerValue = computed(() => {
  if (!props.modelValue) return "";
  const d = new Date(props.modelValue);
  if (Number.isNaN(d.getTime())) return "";
  const y = d.getUTCFullYear();
  if (y === YEAR_NONE) return "";
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(d.getUTCDate()).padStart(2, "0");
  return `${y}-${mm}-${dd}`;
});

function openPicker() {
  const el = pickerRef.value;
  if (!el) return;
  // showPicker() 在 WebView2 與較新 WebKit 上支援; 不支援時 fallback 到 focus()/click().
  if (typeof el.showPicker === "function") {
    try {
      el.showPicker();
      return;
    } catch {
      // 忽略 (例如非 user-gesture), 改用 focus.
    }
  }
  el.focus();
  el.click();
}

function onPickerChange(e: Event) {
  const v = (e.target as HTMLInputElement).value;
  if (!v) {
    text.value = "";
    error.value = null;
    if (props.modelValue !== null) emit("update:modelValue", null);
    return;
  }
  const [yyyy, mm, dd] = v.split("-").map(Number);
  const parts: ROCDateParts = { year: toROCYear(yyyy), month: mm, day: dd };
  text.value = formatROCParts(parts);
  error.value = null;
  const iso = rocPartsToISO(parts);
  if (iso !== props.modelValue) emit("update:modelValue", iso);
}
</script>

<template>
  <span class="roc-date">
    <span class="era">民國</span>
    <input
      type="text"
      :value="text"
      :disabled="!enabled"
      :class="[klass, { 'has-error': error }]"
      :title="error || ''"
      placeholder="如 114/05/29"
      inputmode="numeric"
      autocomplete="off"
      @input="onInput"
      @blur="onBlur"
    />
    <button
      v-if="enabled"
      type="button"
      class="picker-btn"
      tabindex="-1"
      title="開啟日曆選擇"
      @click="openPicker"
    >
      📅
    </button>
    <input
      ref="pickerRef"
      type="date"
      class="picker-hidden"
      :value="pickerValue"
      :disabled="!enabled"
      tabindex="-1"
      aria-hidden="true"
      @change="onPickerChange"
    />
  </span>
</template>

<style scoped>
.roc-date {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  position: relative;
}
.era {
  font-size: 14px;
}
input[type="text"] {
  width: 110px;
  text-align: right;
}
input[type="text"].has-error {
  background: #fee0e0;
  border-color: #c33;
}
.picker-btn {
  padding: 0 4px;
  cursor: pointer;
  background: transparent;
  border: 1px solid transparent;
  font-size: 14px;
  line-height: 1;
}
.picker-btn:hover {
  border-color: #888;
}
.picker-hidden {
  position: absolute;
  opacity: 0;
  pointer-events: none;
  width: 0;
  height: 0;
  border: 0;
  padding: 0;
}
</style>

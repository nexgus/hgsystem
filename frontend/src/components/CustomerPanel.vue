<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { Customer } from "../lib/types";
import { emptyCustomer, phoneList } from "../lib/types";
import type { EditMode } from "../lib/editMode";
import { editClass, isEditable } from "../lib/editMode";
import ROCDateInput from "./ROCDateInput.vue";

const props = defineProps<{
  current: Customer | null;
  mode: EditMode;
  total: number;
}>();

const emit = defineEmits<{
  (e: "append"): void;
  (e: "modify"): void;
  (e: "save", draft: Customer): void;
  (e: "cancel"): void;
  (e: "remove"): void;
  (e: "search"): void;
}>();

// Form state mirrors `props.current` when not editing. Live values are kept
// here so the user's typing is preserved across edit/cancel cycles.
const form = ref<Customer>(emptyCustomer());

function adopt(c: Customer | null) {
  form.value = c ? { ...c } : emptyCustomer();
}

watch(
  () => props.current,
  (v) => adopt(v),
  { immediate: true },
);

const phones = computed(() => phoneList(form.value));
function setPhone(idx: number, value: string) {
  const ph = [...phones.value];
  ph[idx] = value.trim();
  form.value.phones = ph.join(";");
}

const editing = computed(() => isEditable(props.mode));
const klass = computed(() => editClass(props.mode));

const groupTitle = computed(() => `客戶資料 (共有 ${props.total} 筆紀錄)`);

const canSearch = computed(
  () => props.mode === "none" && props.total > 0,
);
const canAppend = computed(() => props.mode === "none");
const canModify = computed(
  () => props.mode === "none" && props.current !== null,
);
const canRemove = computed(
  () => props.mode === "none" && props.current !== null,
);
const canSave = computed(() => editing.value && props.mode !== "inhibit");
const canCancel = computed(() => editing.value && props.mode !== "inhibit");

function onSave() {
  emit("save", { ...form.value });
}
</script>

<template>
  <fieldset class="customer-panel">
    <legend>{{ groupTitle }}</legend>
    <div class="form">
      <div class="row">
        <label>姓名</label>
        <input
          v-model="form.name"
          :disabled="!editing"
          :class="klass"
          style="flex: 1"
        />
        <input
          v-model="form.title"
          :disabled="!editing"
          :class="klass"
          style="width: 80px"
          placeholder="稱謂"
        />
      </div>
      <div class="row">
        <label>地址</label>
        <input
          v-model="form.addr"
          :disabled="!editing"
          :class="klass"
          style="flex: 1"
        />
      </div>
      <div class="row">
        <label>電話</label>
        <input
          :value="phones[0]"
          :disabled="!editing"
          :class="klass"
          style="flex: 1"
          @input="(e) => setPhone(0, (e.target as HTMLInputElement).value)"
        />
        <input
          :value="phones[1]"
          :disabled="!editing"
          :class="klass"
          style="flex: 1"
          @input="(e) => setPhone(1, (e.target as HTMLInputElement).value)"
        />
      </div>
      <div class="row">
        <label></label>
        <input
          :value="phones[2]"
          :disabled="!editing"
          :class="klass"
          style="flex: 1"
          @input="(e) => setPhone(2, (e.target as HTMLInputElement).value)"
        />
        <input
          :value="phones[3]"
          :disabled="!editing"
          :class="klass"
          style="flex: 1"
          @input="(e) => setPhone(3, (e.target as HTMLInputElement).value)"
        />
      </div>
      <div class="row">
        <label>生日</label>
        <ROCDateInput v-model="form.birthdate" :mode="mode" />
      </div>
      <div class="row">
        <label>介紹人</label>
        <input
          v-model="form.broker"
          :disabled="!editing"
          :class="klass"
          style="flex: 1"
        />
      </div>
    </div>

    <div class="controls">
      <button :disabled="!canSearch" @click="emit('search')">(F) 搜尋</button>
      <button :disabled="!canModify" @click="emit('modify')">(M) 修改</button>
      <button :disabled="!canSave" @click="onSave">(S) 儲存</button>
      <button :disabled="!canCancel" @click="emit('cancel')">(C) 取消</button>
      <button :disabled="!canRemove" @click="emit('remove')">(R) 刪除</button>
      <button :disabled="!canAppend" @click="emit('append')">(A) 新增</button>
    </div>
  </fieldset>
</template>

<style scoped>
.customer-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.row > label {
  width: var(--label-width);
  flex-shrink: 0;
}
.controls {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
</style>

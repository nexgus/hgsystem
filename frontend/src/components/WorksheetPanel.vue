<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { Worksheet } from "../lib/types";
import { emptyWorksheet } from "../lib/types";
import type { EditMode } from "../lib/editMode";
import { editClass, isEditable } from "../lib/editMode";
import ROCDateInput from "./ROCDateInput.vue";

const props = defineProps<{
  current: Worksheet | null;
  mode: EditMode;
}>();

const emit = defineEmits<{
  (e: "append"): void;
  (e: "modify"): void;
  (e: "save", draft: Worksheet): void;
  (e: "cancel"): void;
  (e: "remove"): void;
}>();

const form = ref<Worksheet>(emptyWorksheet());

watch(
  () => props.current,
  (v) => {
    form.value = v ? { ...v } : emptyWorksheet();
  },
  { immediate: true },
);

const editing = computed(() => isEditable(props.mode));
const klass = computed(() => editClass(props.mode));

const total = computed(() => form.value.lensPrice + form.value.framePrice);

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
  <fieldset class="worksheet-panel">
    <legend>配鏡資料</legend>
    <div class="dates row">
      <span class="row">
        <label>收件日</label>
        <ROCDateInput v-model="form.orderTime" :mode="mode" />
      </span>
      <span class="row">
        <label>交件日</label>
        <ROCDateInput v-model="form.deliverTime" :mode="mode" />
      </span>
    </div>

    <div class="grid">
      <fieldset class="prescription">
        <legend>處方箋</legend>
        <div class="rx">
          <div class="rx-head"></div>
          <div class="rx-head">OD/R</div>
          <div class="rx-head">OS/L</div>

          <div class="rx-label">SPH</div>
          <input v-model="form.sphR" :disabled="!editing" :class="klass" />
          <input v-model="form.sphL" :disabled="!editing" :class="klass" />

          <div class="rx-label">CYL</div>
          <input v-model="form.cylR" :disabled="!editing" :class="klass" />
          <input v-model="form.cylL" :disabled="!editing" :class="klass" />

          <div class="rx-label">AXIS</div>
          <input v-model="form.axisR" :disabled="!editing" :class="klass" />
          <input v-model="form.axisL" :disabled="!editing" :class="klass" />

          <div class="rx-label">BASE</div>
          <input v-model="form.baseR" :disabled="!editing" :class="klass" />
          <input v-model="form.baseL" :disabled="!editing" :class="klass" />

          <div class="rx-label">BC</div>
          <input v-model="form.bcR" :disabled="!editing" :class="klass" />
          <input v-model="form.bcL" :disabled="!editing" :class="klass" />

          <div class="rx-label">BC.V</div>
          <input v-model="form.bcvR" :disabled="!editing" :class="klass" />
          <input v-model="form.bcvL" :disabled="!editing" :class="klass" />

          <div class="rx-label">BC.H</div>
          <input v-model="form.bchR" :disabled="!editing" :class="klass" />
          <input v-model="form.bchL" :disabled="!editing" :class="klass" />

          <div class="rx-label">ADD</div>
          <input v-model="form.addR" :disabled="!editing" :class="klass" />
          <input v-model="form.addL" :disabled="!editing" :class="klass" />

          <div class="rx-label">PD</div>
          <input class="rx-span" v-model="form.pd" :disabled="!editing" :class="klass" />

          <div class="rx-label">來源</div>
          <input class="rx-span" v-model="form.source" :disabled="!editing" :class="klass" />
        </div>
      </fieldset>

      <fieldset class="glasses">
        <legend>眼鏡資料</legend>
        <div class="rx">
          <div class="rx-head"></div>
          <div class="rx-head">OD/R</div>
          <div class="rx-head">OS/L</div>

          <div class="rx-label">視力</div>
          <input v-model="form.eyesightR" :disabled="!editing" :class="klass" />
          <input v-model="form.eyesightL" :disabled="!editing" :class="klass" />

          <div class="rx-label">鏡片</div>
          <input v-model="form.lensR" :disabled="!editing" :class="klass" />
          <input v-model="form.lensL" :disabled="!editing" :class="klass" />

          <div class="rx-label">鏡架</div>
          <input class="rx-span" v-model="form.frame" :disabled="!editing" :class="klass" />
        </div>

        <!-- 備註: 拉出 table 作為 flex:1 的列, textarea 撐滿表格與金額之間的
             剩餘高度, 使眼鏡資料欄填滿到與處方箋欄等高. -->
        <div class="memo-row">
          <label>備註</label>
          <textarea
            v-model="form.memo"
            :disabled="!editing"
            :class="klass"
          ></textarea>
        </div>

        <fieldset class="price">
          <legend>金額</legend>
          <div class="row">
            <label>鏡片</label>
            <input
              type="number"
              v-model.number="form.lensPrice"
              :disabled="!editing"
              :class="klass"
              style="text-align: right; flex: 1"
            />
          </div>
          <div class="row">
            <label>鏡架</label>
            <input
              type="number"
              v-model.number="form.framePrice"
              :disabled="!editing"
              :class="klass"
              style="text-align: right; flex: 1"
            />
          </div>
          <div class="row">
            <label>合計</label>
            <input
              :value="total"
              readonly
              style="text-align: right; flex: 1"
            />
          </div>
        </fieldset>
      </fieldset>
    </div>

    <div class="controls">
      <button :disabled="!canAppend" @click="emit('append')">新增</button>
      <button :disabled="!canModify" @click="emit('modify')">修改</button>
      <button :disabled="!canSave" @click="onSave">儲存</button>
      <button :disabled="!canCancel" @click="emit('cancel')">取消</button>
      <button :disabled="!canRemove" @click="emit('remove')">刪除</button>
    </div>
  </fieldset>
</template>

<style scoped>
.worksheet-panel {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dates {
  gap: 20px;
}
.dates label {
  margin-right: 4px;
}
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
/* 處方箋 (10 列) 為最高欄, 決定兩欄高度. 眼鏡資料欄較矮, 經 grid stretch
   被拉到同高; 欄內表格 flex:1 撐滿, 多出來的高度全部給備註列 (memo-row),
   其餘列維持與處方箋相同的自然列距 -> 左右兩個 group box 等高. */
.glasses {
  display: flex;
  flex-direction: column;
  gap: var(--row-gap);
}
/* 處方箋 / 眼鏡資料改用 CSS Grid (取代 <table>), 讓列距與客戶區 / 金額區
   共用 --row-gap 的同一套 gap 機制, 不再靠儲存格 padding 撐.
   三欄: 60px 標籤 + 兩個等寬輸入欄; 字級 13px 沿用舊表格 (input 仍 14px). */
.rx {
  display: grid;
  grid-template-columns: 60px 1fr 1fr;
  row-gap: var(--row-gap);
  column-gap: 8px;
  font-size: 13px;
}
.glasses .rx {
  flex: none;
}
.rx-head,
.rx-label {
  display: flex;
  align-items: center;
}
/* 表頭 OD/R / OS/L 與左上空格共用底線 (取代舊 th 的 border-bottom). */
.rx-head {
  border-bottom: 1px solid var(--border-row);
  padding-bottom: 2px;
  font-weight: 600;
}
.rx-label {
  font-weight: 500;
}
.rx input {
  width: 100%;
}
/* PD / 來源 / 鏡架: 輸入框橫跨兩個輸入欄. */
.rx-span {
  grid-column: 2 / 4;
}
/* 備註列: flex:1 吃掉表格與金額之間的剩餘高度. label 對齊 grid 首欄 (寬 60px,
   文字貼左緣 x=0, 與視力/鏡片/鏡架 標籤齊頭); textarea 左邊留 8px 對齊 OD/R
   輸入框左緣, 右邊貼齊容器右緣對齊鏡架輸入框 (.rx-span) 右緣. */
.memo-row {
  display: flex;
  align-items: stretch;
  flex: 1 1 auto;
  min-height: var(--field-height);
}
.memo-row > label {
  width: 60px;
  box-sizing: border-box;
  padding-top: 2px;
  font-weight: 500;
  flex-shrink: 0;
}
.memo-row > textarea {
  flex: 1;
  height: 100%;
  margin-left: 8px;
  resize: none;
}
.rx input {
  width: 100%;
}
.rx td:first-child {
  width: 60px;
  font-weight: 500;
}
.price {
  display: flex;
  flex-direction: column;
  gap: var(--row-gap);
}
.price label {
  width: 50px;
}
.controls {
  display: flex;
  gap: 6px;
}
.controls > button {
  flex: 1;
}
</style>

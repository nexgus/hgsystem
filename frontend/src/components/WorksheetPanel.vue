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
        <table class="rx">
          <thead>
            <tr>
              <th></th>
              <th>OD/R</th>
              <th>OS/L</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>SPH</td>
              <td>
                <input v-model="form.sphR" :disabled="!editing" :class="klass" />
              </td>
              <td>
                <input v-model="form.sphL" :disabled="!editing" :class="klass" />
              </td>
            </tr>
            <tr>
              <td>CYL</td>
              <td>
                <input v-model="form.cylR" :disabled="!editing" :class="klass" />
              </td>
              <td>
                <input v-model="form.cylL" :disabled="!editing" :class="klass" />
              </td>
            </tr>
            <tr>
              <td>AXIS</td>
              <td>
                <input v-model="form.axisR" :disabled="!editing" :class="klass" />
              </td>
              <td>
                <input v-model="form.axisL" :disabled="!editing" :class="klass" />
              </td>
            </tr>
            <tr>
              <td>BASE</td>
              <td>
                <input v-model="form.baseR" :disabled="!editing" :class="klass" />
              </td>
              <td>
                <input v-model="form.baseL" :disabled="!editing" :class="klass" />
              </td>
            </tr>
            <tr>
              <td>BC</td>
              <td>
                <input v-model="form.bcR" :disabled="!editing" :class="klass" />
              </td>
              <td>
                <input v-model="form.bcL" :disabled="!editing" :class="klass" />
              </td>
            </tr>
            <tr>
              <td>BC.V</td>
              <td>
                <input v-model="form.bcvR" :disabled="!editing" :class="klass" />
              </td>
              <td>
                <input v-model="form.bcvL" :disabled="!editing" :class="klass" />
              </td>
            </tr>
            <tr>
              <td>BC.H</td>
              <td>
                <input v-model="form.bchR" :disabled="!editing" :class="klass" />
              </td>
              <td>
                <input v-model="form.bchL" :disabled="!editing" :class="klass" />
              </td>
            </tr>
            <tr>
              <td>ADD</td>
              <td>
                <input v-model="form.addR" :disabled="!editing" :class="klass" />
              </td>
              <td>
                <input v-model="form.addL" :disabled="!editing" :class="klass" />
              </td>
            </tr>
            <tr>
              <td>PD</td>
              <td colspan="2">
                <input v-model="form.pd" :disabled="!editing" :class="klass" />
              </td>
            </tr>
            <tr>
              <td>來源</td>
              <td colspan="2">
                <input v-model="form.source" :disabled="!editing" :class="klass" />
              </td>
            </tr>
          </tbody>
        </table>
      </fieldset>

      <fieldset class="glasses">
        <legend>眼鏡資料</legend>
        <table class="rx">
          <thead>
            <tr>
              <th></th>
              <th>OD/R</th>
              <th>OS/L</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>視力</td>
              <td>
                <input
                  v-model="form.eyesightR"
                  :disabled="!editing"
                  :class="klass"
                />
              </td>
              <td>
                <input
                  v-model="form.eyesightL"
                  :disabled="!editing"
                  :class="klass"
                />
              </td>
            </tr>
            <tr>
              <td>鏡片</td>
              <td>
                <input v-model="form.lensR" :disabled="!editing" :class="klass" />
              </td>
              <td>
                <input v-model="form.lensL" :disabled="!editing" :class="klass" />
              </td>
            </tr>
            <tr>
              <td>鏡架</td>
              <td colspan="2">
                <input v-model="form.frame" :disabled="!editing" :class="klass" />
              </td>
            </tr>
            <tr>
              <td>備註</td>
              <td colspan="2">
                <input v-model="form.memo" :disabled="!editing" :class="klass" />
              </td>
            </tr>
          </tbody>
        </table>

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
      <button :disabled="!canAppend" @click="emit('append')">(N) 新增</button>
      <button :disabled="!canModify" @click="emit('modify')">(E) 修改</button>
      <button :disabled="!canSave" @click="onSave">(S) 儲存</button>
      <button :disabled="!canCancel" @click="emit('cancel')">(C) 取消</button>
      <button :disabled="!canRemove" @click="emit('remove')">(D) 刪除</button>
    </div>
  </fieldset>
</template>

<style scoped>
.worksheet-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
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
  gap: 12px;
}
.rx {
  width: 100%;
}
.rx input {
  width: 100%;
}
.rx td:first-child {
  width: 60px;
  font-weight: 500;
}
.price {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.price label {
  width: 50px;
}
.controls {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
</style>

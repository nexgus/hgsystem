<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Dialogs, Events } from "@wailsio/runtime";
import {
  CustomerService,
  WorksheetService,
  SearchService,
  TitleService,
  BackupService,
} from "../bindings/hgsys/pkg/app";
import type { Customer, Worksheet } from "./lib/types";
import { emptyCustomer, emptyWorksheet } from "./lib/types";
import type { EditMode } from "./lib/editMode";
import { formatROCDate } from "./lib/rocDate";
import CustomerPanel from "./components/CustomerPanel.vue";
import WorksheetHistoryTable from "./components/WorksheetHistoryTable.vue";
import WorksheetPanel from "./components/WorksheetPanel.vue";
import SearchDialog from "./components/SearchDialog.vue";
import BackupRestoreDialog from "./components/BackupRestoreDialog.vue";
import InfoDialog from "./components/InfoDialog.vue";
import TitleManageDialog from "./components/TitleManageDialog.vue";
import UpdateDialog from "./components/UpdateDialog.vue";

// ---- customer 狀態 ---------------------------------------------------------
const currentCustomer = ref<Customer | null>(null);
const customerMode = ref<EditMode>("none");
const customerTotal = ref(0);
const customerSnapshot = ref<Customer | null>(null);

// ---- worksheet 狀態 --------------------------------------------------------
const worksheetHistory = ref<Worksheet[]>([]);
const currentWorksheet = ref<Worksheet | null>(null);
// worksheet 初始為 INHIBIT — 尚未選擇任何客戶.
const worksheetMode = ref<EditMode>("inhibit");
const worksheetSnapshot = ref<Worksheet | null>(null);

// ---- 稱謂清單 --------------------------------------------------------------
const titles = ref<string[]>([]);
async function refreshTitles() {
  const list = await TitleService.List();
  titles.value = (list ?? []).filter((t): t is string => typeof t === "string");
}

// ---- dialog 狀態 -----------------------------------------------------------
const showSearch = ref(false);
const showTitleManage = ref(false);
const showUpdate = ref(false);
const backupState = ref<{ savepath: string; mode: "backup" | "restore" } | null>(null);
const info = ref<{
  title: string;
  message: string;
  variant?: "info" | "error" | "confirm";
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm?: () => void;
} | null>(null);

// ---- 連動: customer 編輯模式 → worksheet 禁制 -----------------------------
function applyWorksheetInhibit(inhibited: boolean) {
  if (inhibited) {
    worksheetMode.value = "inhibit";
  } else {
    worksheetMode.value = currentCustomer.value ? "none" : "inhibit";
  }
}

function setCustomerMode(m: EditMode) {
  customerMode.value = m;
  if (m === "append" || m === "modify") {
    applyWorksheetInhibit(true);
  } else if (m === "none") {
    applyWorksheetInhibit(false);
  }
}

function setWorksheetMode(m: EditMode) {
  worksheetMode.value = m;
  if (m === "append" || m === "modify") {
    customerMode.value = "inhibit";
  } else if (m === "none") {
    customerMode.value = "none";
  }
}

// ---- 啟動初始化 ------------------------------------------------------------
async function refreshTotal() {
  customerTotal.value = Number(await CustomerService.Count());
}

// 取得工單收件日的時間戳; 無收件日 (或無法解析) 視為最舊.
function worksheetOrderMs(w: Worksheet): number {
  if (w.orderTime == null) return Number.NEGATIVE_INFINITY;
  const ms = new Date(w.orderTime as string | Date).getTime();
  return Number.isNaN(ms) ? Number.NEGATIVE_INFINITY : ms;
}

// 工單依收件日由新到舊排序 (最新在最上面, 最舊在最下面);
// 同一收件日則以 id (字串化 ObjectId, 內含建立時間) 由新到舊.
function sortWorksheets(list: Worksheet[]): Worksheet[] {
  return [...list].sort((a, b) => {
    const ta = worksheetOrderMs(a);
    const tb = worksheetOrderMs(b);
    if (ta !== tb) return tb - ta;
    return (b.id ?? "").localeCompare(a.id ?? "");
  });
}

async function loadHistoryFor(cid: string) {
  const list = await WorksheetService.ListForCustomer(cid);
  worksheetHistory.value = sortWorksheets(list ?? []);
  currentWorksheet.value = worksheetHistory.value[0] ?? null;
}

async function clearHistory() {
  worksheetHistory.value = [];
  currentWorksheet.value = null;
}

async function setCurrentCustomer(c: Customer | null) {
  currentCustomer.value = c;
  if (c && c.id) {
    await loadHistoryFor(c.id);
  } else {
    await clearHistory();
  }
  // 非編輯狀態下, 是否有選定客戶決定 worksheet 的禁制狀態.
  if (worksheetMode.value !== "append" && worksheetMode.value !== "modify") {
    applyWorksheetInhibit(false);
  }
}

onMounted(async () => {
  // 訂閱 Go 端原生選單「資料」項目發出的事件; 備份 / 還原需在主視窗前端跑
  // 目錄挑選與對話框流程.
  Events.On("menu:backup", () => { onMenuBackup(); });
  Events.On("menu:restore", () => { onMenuRestore(); });
  // 原生選單「檢查更新…」: 開啟更新對話框, 由其自行查詢 / 確認 / 下載.
  Events.On("menu:update", () => { showUpdate.value = true; });

  await refreshTotal();
  await refreshTitles();
});

// ---- customer 動作 ---------------------------------------------------------
function startAppendCustomer() {
  customerSnapshot.value = currentCustomer.value;
  currentCustomer.value = emptyCustomer();
  setCustomerMode("append");
}

function startModifyCustomer() {
  if (!currentCustomer.value) return;
  customerSnapshot.value = currentCustomer.value;
  setCustomerMode("modify");
}

function cancelCustomerEdit() {
  if (customerMode.value === "append" && customerSnapshot.value) {
    currentCustomer.value = customerSnapshot.value;
  } else if (customerMode.value === "modify" && customerSnapshot.value) {
    currentCustomer.value = customerSnapshot.value;
  } else if (!customerSnapshot.value) {
    currentCustomer.value = null;
  }
  customerSnapshot.value = null;
  setCustomerMode("none");
}

async function performSaveCustomer(draft: Customer) {
  try {
    if (customerMode.value === "append") {
      const newId = await CustomerService.Insert(draft);
      const stored: Customer = { ...draft, id: newId };
      await setCurrentCustomer(stored);
      await refreshTotal();
    } else if (customerMode.value === "modify") {
      const id = customerSnapshot.value?.id ?? draft.id;
      await CustomerService.Update(id, draft);
      const stored: Customer = { ...draft, id };
      await setCurrentCustomer(stored);
    }
    customerSnapshot.value = null;
    setCustomerMode("none");
  } catch (e) {
    info.value = {
      title: "輸入內容錯誤",
      message: String(e),
      variant: "error",
    };
  }
}

async function saveCustomer(draft: Customer) {
  // modify 模式下, 若稱謂既非空字串也不在 canonical 清單中, 視為舊髒資料.
  // 跳出確認框讓使用者選擇"加入清單"或"修正".
  if (
    customerMode.value === "modify" &&
    draft.title !== "" &&
    !titles.value.includes(draft.title)
  ) {
    info.value = {
      title: "稱謂不在清單中",
      message: `「${draft.title}」不在既有稱謂清單中。<br/>要將它加入清單後存檔, 還是回去修正?`,
      variant: "confirm",
      confirmLabel: "加入清單",
      cancelLabel: "修正",
      onConfirm: async () => {
        info.value = null;
        await TitleService.Add(draft.title);
        await refreshTitles();
        await performSaveCustomer(draft);
      },
    };
    return;
  }
  await performSaveCustomer(draft);
}

// ---- 稱謂管理 dialog --------------------------------------------------------
async function onAddTitle(name: string) {
  await TitleService.Add(name);
  await refreshTitles();
}

async function onRemoveTitle(name: string) {
  await TitleService.Remove(name);
  await refreshTitles();
}

function confirmDeleteCustomer() {
  if (!currentCustomer.value) return;
  const c = currentCustomer.value;
  const wsCount = worksheetHistory.value.length;
  info.value = {
    title: `刪除客戶 ${c.id}`,
    message: `確定要刪除該筆資料嗎?<br/>這會將所有該客戶的紀錄刪除 (共 ${wsCount} 筆), 無法復原!<br/>姓名: ${c.name}<br/>地址: ${c.addr}`,
    variant: "confirm",
    confirmLabel: "是",
    cancelLabel: "否",
    onConfirm: async () => {
      info.value = null;
      await CustomerService.Delete(c.id);
      await setCurrentCustomer(null);
      await refreshTotal();
    },
  };
}

// ---- worksheet 動作 --------------------------------------------------------
function startAppendWorksheet() {
  if (!currentCustomer.value) return;
  worksheetSnapshot.value = currentWorksheet.value;
  currentWorksheet.value = emptyWorksheet(currentCustomer.value.id);
  setWorksheetMode("append");
}

function startModifyWorksheet() {
  if (!currentWorksheet.value) return;
  worksheetSnapshot.value = currentWorksheet.value;
  setWorksheetMode("modify");
}

function cancelWorksheetEdit() {
  if (worksheetSnapshot.value) {
    currentWorksheet.value = worksheetSnapshot.value;
  }
  worksheetSnapshot.value = null;
  setWorksheetMode("none");
}

async function saveWorksheet(draft: Worksheet) {
  try {
    if (worksheetMode.value === "append") {
      draft.cid = currentCustomer.value?.id ?? draft.cid;
      const newId = await WorksheetService.Insert(draft);
      const stored: Worksheet = { ...draft, id: newId };
      worksheetHistory.value = sortWorksheets([...worksheetHistory.value, stored]);
      currentWorksheet.value = stored;
    } else if (worksheetMode.value === "modify") {
      const id = worksheetSnapshot.value?.id ?? draft.id;
      draft.id = id;
      draft.cid = worksheetSnapshot.value?.cid ?? draft.cid;
      await WorksheetService.Update(id, draft);
      worksheetHistory.value = sortWorksheets(
        worksheetHistory.value.map((w) => (w.id === id ? draft : w)),
      );
      currentWorksheet.value = draft;
    }
    worksheetSnapshot.value = null;
    setWorksheetMode("none");
  } catch (e) {
    info.value = {
      title: "輸入內容錯誤",
      message: String(e),
      variant: "error",
    };
  }
}

function confirmDeleteWorksheet() {
  if (!currentWorksheet.value) return;
  const w = currentWorksheet.value;
  info.value = {
    title: `刪除工單 ${w.id}`,
    message: `確定要刪除該筆資料嗎?<br/>收件日: ${formatROCDate(w.orderTime)}<br/>交件日: ${formatROCDate(w.deliverTime)}`,
    variant: "confirm",
    confirmLabel: "是",
    cancelLabel: "否",
    onConfirm: async () => {
      info.value = null;
      await WorksheetService.Delete(w.id);
      const idx = worksheetHistory.value.findIndex((x) => x.id === w.id);
      worksheetHistory.value = worksheetHistory.value.filter((x) => x.id !== w.id);
      if (worksheetHistory.value.length > 0) {
        const pick = Math.min(idx, worksheetHistory.value.length - 1);
        currentWorksheet.value = worksheetHistory.value[pick];
      } else {
        currentWorksheet.value = null;
      }
      setWorksheetMode("none");
    },
  };
}

function selectWorksheet(id: string) {
  const w = worksheetHistory.value.find((x) => x.id === id);
  if (w) currentWorksheet.value = w;
}

// ---- 選單動作 --------------------------------------------------------------
async function onMenuBackup() {
  const dir = await Dialogs.OpenFile({
    Title: "選擇備份目錄",
    CanChooseDirectories: true,
    CanChooseFiles: false,
    CanCreateDirectories: true,
    Directory: await BackupService.LastBackupDir(),
  });
  if (!dir || Array.isArray(dir)) return;
  await BackupService.SetLastBackupDir(dir);
  backupState.value = { savepath: dir, mode: "backup" };
}

async function onMenuRestore() {
  const dir = await Dialogs.OpenFile({
    Title: "選擇備份目錄",
    CanChooseDirectories: true,
    CanChooseFiles: false,
    Directory: await BackupService.LastRestoreDir(),
  });
  if (!dir || Array.isArray(dir)) return;
  await BackupService.SetLastRestoreDir(dir);
  const resolved = await BackupService.ResolveRestoreDir(dir);
  const missing = await BackupService.MissingRestoreFiles(resolved);
  if (missing && missing.length > 0) {
    info.value = {
      title: "無法還原",
      message: `檔案不完整, 無法還原. 缺少<br/>${missing.join("<br/>")}`,
      variant: "error",
    };
    return;
  }
  backupState.value = { savepath: resolved, mode: "restore" };
}

// ---- 搜尋對話框 ------------------------------------------------------------
async function onAcceptSearch(c: Customer) {
  showSearch.value = false;
  await SearchService.Remember(c);
  await setCurrentCustomer(c);
}

// 任一相鄰面板進入編輯狀態時, 將歷史列鎖死, 不接受點擊.
const historyFrozen = computed(() =>
  customerMode.value === "append" ||
  customerMode.value === "modify" ||
  worksheetMode.value === "append" ||
  worksheetMode.value === "modify",
);
</script>

<template>
  <div class="app-shell">
    <div class="app-content">
      <div class="customer-row">
        <CustomerPanel
          :current="currentCustomer"
          :mode="customerMode"
          :total="customerTotal"
          :titles="titles"
          @append="startAppendCustomer"
          @modify="startModifyCustomer"
          @save="saveCustomer"
          @cancel="cancelCustomerEdit"
          @remove="confirmDeleteCustomer"
          @search="showSearch = true"
          @manage-titles="showTitleManage = true"
        />
        <WorksheetHistoryTable
          :rows="worksheetHistory"
          :current-id="currentWorksheet?.id ?? ''"
          :frozen="historyFrozen"
          @select="selectWorksheet"
        />
      </div>
      <WorksheetPanel
        :current="currentWorksheet"
        :mode="worksheetMode"
        @append="startAppendWorksheet"
        @modify="startModifyWorksheet"
        @save="saveWorksheet"
        @cancel="cancelWorksheetEdit"
        @remove="confirmDeleteWorksheet"
      />
    </div>

    <SearchDialog
      v-if="showSearch"
      @close="showSearch = false"
      @accept="onAcceptSearch"
    />
    <TitleManageDialog
      v-if="showTitleManage"
      :titles="titles"
      @close="showTitleManage = false"
      @add="onAddTitle"
      @remove="onRemoveTitle"
    />
    <BackupRestoreDialog
      v-if="backupState"
      :savepath="backupState.savepath"
      :mode="backupState.mode"
      @close="backupState = null"
    />
    <UpdateDialog
      v-if="showUpdate"
      @close="showUpdate = false"
    />
    <InfoDialog
      v-if="info"
      :title="info.title"
      :message="info.message"
      :variant="info.variant"
      :confirm-label="info.confirmLabel"
      :cancel-label="info.cancelLabel"
      @confirm="info?.onConfirm?.()"
      @close="info = null"
    />
  </div>
</template>

<style scoped>
.customer-row {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 12px;
  margin-bottom: 12px;
}
</style>

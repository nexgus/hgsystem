// 對應 pkg/domain.EditMode, 以 string union 的形式保留, 提升可讀性.

export type EditMode = "none" | "append" | "modify" | "inhibit";

export function isEditable(m: EditMode): boolean {
  return m === "append" || m === "modify";
}

// CSS class 提示: 可編輯模式時欄位以紅色呈現, 與舊版程式風格一致.
export function editClass(m: EditMode): string {
  return isEditable(m) ? "edit-red" : "";
}

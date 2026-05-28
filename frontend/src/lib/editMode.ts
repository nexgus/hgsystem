// Mirrors pkg/domain.EditMode. Kept as a string union for readability.

export type EditMode = "none" | "append" | "modify" | "inhibit";

export function isEditable(m: EditMode): boolean {
  return m === "append" || m === "modify";
}

// CSS class hint: editable modes draw fields red, matching the legacy app.
export function editClass(m: EditMode): string {
  return isEditable(m) ? "edit-red" : "";
}

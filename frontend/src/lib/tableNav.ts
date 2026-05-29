// 清單表格 (工單歷史 / 搜尋結果) 的鍵盤導覽共用邏輯.
// 元件自己負責「設定選取」與處理 Enter; 這裡只算索引與處理 DOM 捲動.

// 計算鍵盤導覽後的新列索引. 回傳 null 表示這個按鍵不是導覽鍵, 交給瀏覽器預設處理.
// current 為 -1 (尚未選取) 時: 往下/PageDown/Home 選第一列, 往上/PageUp/End 選最後一列.
export function nextRowIndex(
  key: string,
  current: number,
  length: number,
  pageSize: number,
): number | null {
  if (length === 0) return null;
  const clamp = (i: number) => Math.min(length - 1, Math.max(0, i));
  switch (key) {
    case "ArrowDown":
      return current < 0 ? 0 : clamp(current + 1);
    case "ArrowUp":
      return current < 0 ? length - 1 : clamp(current - 1);
    case "PageDown":
      return current < 0 ? 0 : clamp(current + pageSize);
    case "PageUp":
      return current < 0 ? length - 1 : clamp(current - pageSize);
    case "Home":
      return 0;
    case "End":
      return length - 1;
    default:
      return null;
  }
}

// 依容器高度與單列高度估算一頁可見的列數 (至少 1). 用於 PageUp/PageDown.
export function rowsPerPage(container: HTMLElement | null | undefined): number {
  if (!container) return 1;
  const row = container.querySelector("tbody tr") as HTMLElement | null;
  const rowH = row?.offsetHeight ?? 0;
  if (!rowH) return 1;
  return Math.max(1, Math.floor(container.clientHeight / rowH) - 1);
}

// 把目前選中的列捲動到可見範圍 (block: nearest, 不置中以免畫面跳動).
export function scrollSelectedIntoView(container: HTMLElement | null | undefined): void {
  container?.querySelector("tr.selected")?.scrollIntoView({ block: "nearest" });
}

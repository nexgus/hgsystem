// ROCDateInput.vue 的文字解析邏輯, 抽出方便測試與重用.
// 輸入格式:
//   有分隔符 (/、-、／、－, 可混用):
//     2 段 → M/D, 年未知
//     3 段 → Y/M/D; 首段 4 碼視為西元, 轉成民國
//   純數字:
//     4 碼 → MMDD (年未知)
//     6 碼 → YYMMDD (民國)
//     7 碼 → YYYMMDD (民國)
//     8 碼 → YYYYMMDD (西元, 轉民國)

import { fromROCParts, toROCYear, daysInMonth } from "./rocDate";

export type ROCDateParts = { year: number; month: number; day: number };

const SEP_REGEX = /[/\-／－]+/;

export function formatROCParts(p: ROCDateParts): string {
  if (p.year === 0 && p.month === 0 && p.day === 0) return "";
  const mm = String(p.month).padStart(2, "0");
  const dd = String(p.day).padStart(2, "0");
  if (p.year === 0) return `${mm}/${dd}`;
  return `${p.year}/${mm}/${dd}`;
}

export function parseROCDateInput(s: string): ROCDateParts | null {
  const trimmed = s.trim();
  if (!trimmed) return { year: 0, month: 0, day: 0 };

  if (SEP_REGEX.test(trimmed)) {
    const segs = trimmed.split(SEP_REGEX).filter((x) => x !== "");
    if (segs.length === 2) {
      const m = Number(segs[0]);
      const d = Number(segs[1]);
      if (!Number.isFinite(m) || !Number.isFinite(d)) return null;
      return { year: 0, month: m, day: d };
    }
    if (segs.length === 3) {
      const y = Number(segs[0]);
      const m = Number(segs[1]);
      const d = Number(segs[2]);
      if (!Number.isFinite(y) || !Number.isFinite(m) || !Number.isFinite(d)) return null;
      const rocY = segs[0].length === 4 ? toROCYear(y) : y;
      return { year: rocY, month: m, day: d };
    }
    return null;
  }

  if (!/^\d+$/.test(trimmed)) return null;
  if (trimmed.length === 4) {
    return {
      year: 0,
      month: Number(trimmed.slice(0, 2)),
      day: Number(trimmed.slice(2, 4)),
    };
  }
  if (trimmed.length === 6) {
    return {
      year: Number(trimmed.slice(0, 2)),
      month: Number(trimmed.slice(2, 4)),
      day: Number(trimmed.slice(4, 6)),
    };
  }
  if (trimmed.length === 7) {
    return {
      year: Number(trimmed.slice(0, 3)),
      month: Number(trimmed.slice(3, 5)),
      day: Number(trimmed.slice(5, 7)),
    };
  }
  if (trimmed.length === 8) {
    return {
      year: toROCYear(Number(trimmed.slice(0, 4))),
      month: Number(trimmed.slice(4, 6)),
      day: Number(trimmed.slice(6, 8)),
    };
  }
  return null;
}

export function isValidROCParts(p: ROCDateParts): boolean {
  if (p.year === 0 && p.month === 0 && p.day === 0) return true;
  if (p.month < 1 || p.month > 12) return false;
  const maxDay = daysInMonth(p.year, p.month);
  if (p.day < 1 || p.day > maxDay) return false;
  return true;
}

export function rocPartsErrorMessage(p: ROCDateParts): string {
  if (p.month < 1 || p.month > 12) return `月份必須是 1–12 (輸入了 ${p.month})`;
  const maxDay = daysInMonth(p.year, p.month);
  return `${p.month} 月最多 ${maxDay} 日 (輸入了 ${p.day})`;
}

export function rocPartsToISO(p: ROCDateParts): string | null {
  const d = fromROCParts(p.year, p.month, p.day);
  return d ? d.toISOString() : null;
}

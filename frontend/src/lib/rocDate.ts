// 民國 (ROC) 與西元年的互轉, 對應 pkg/domain/dates.go.
// 民國紀年沒有 0 年; YEAR_NONE (9996) 為僅知月 / 日時所存放之 sentinel 值.

export const YEAR_NONE = 9996;

export function toROCYear(commonYear: number): number {
  let y = commonYear - 1911;
  if (y <= 0) y -= 1;
  return y;
}

export function toCommonYear(rocYear: number): number {
  if (rocYear === 0) return YEAR_NONE;
  if (rocYear > 0) return rocYear + 1911;
  return rocYear + 1912;
}

// 解析 "MM/DD" 或 "YYY/MM/DD". 格式錯誤或月 / 日為 0 時回傳 null.
export function parseROCDate(s: string): Date | null {
  const parts = s.split("/").map((p) => p.trim());
  let year = YEAR_NONE;
  let month = 0;
  let day = 0;
  if (parts.length === 2) {
    month = Number(parts[0]);
    day = Number(parts[1]);
  } else if (parts.length === 3) {
    year = toCommonYear(Number(parts[0]));
    month = Number(parts[1]);
    day = Number(parts[2]);
  } else {
    return null;
  }
  if (!Number.isFinite(month) || !Number.isFinite(day) || month === 0 || day === 0) return null;
  return new Date(Date.UTC(year, month - 1, day));
}

export function formatROCDate(d: Date | string | null | undefined): string {
  if (d == null) return "0/00/00";
  const date = typeof d === "string" ? new Date(d) : d;
  if (Number.isNaN(date.getTime())) return "0/00/00";
  const y = date.getUTCFullYear();
  const m = date.getUTCMonth() + 1;
  const day = date.getUTCDate();
  const pad = (n: number) => String(n).padStart(2, "0");
  if (y === YEAR_NONE) return `${pad(m)}/${pad(day)}`;
  return `${toROCYear(y)}/${pad(m)}/${pad(day)}`;
}

// 將分開的民國年 / 月 / 日輸入轉成 JS Date (UTC) 或 null.
// 年 0 + 月 0 + 日 0 → null. 年 0 搭配非 0 的月 / 日則以 YEAR_NONE 代表.
export function fromROCParts(year: number, month: number, day: number): Date | null {
  if (year === 0 && month === 0 && day === 0) return null;
  const y = year === 0 ? YEAR_NONE : toCommonYear(year);
  return new Date(Date.UTC(y, (month || 1) - 1, day || 1));
}

// fromROCParts 的反向操作 — 把儲存的 ISO / date 拆回民國年 / 月 / 日.
export function toROCParts(d: Date | string | null | undefined): {
  year: number;
  month: number;
  day: number;
} {
  if (d == null) return { year: 0, month: 0, day: 0 };
  const date = typeof d === "string" ? new Date(d) : d;
  if (Number.isNaN(date.getTime())) return { year: 0, month: 0, day: 0 };
  const y = date.getUTCFullYear();
  const m = date.getUTCMonth() + 1;
  const day = date.getUTCDate();
  return {
    year: y === YEAR_NONE ? 0 : toROCYear(y),
    month: m,
    day,
  };
}

const DAYS_PER_MONTH = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

export function daysInMonth(rocYear: number, month: number): number {
  if (month <= 0 || month > 12) return 31;
  if (month !== 2) return DAYS_PER_MONTH[month];
  // 民國 0 年 = 未知 — 採寬鬆策略, 允許到 29 日.
  if (rocYear === 0) return 29;
  const common = toCommonYear(rocYear);
  const isLeap = (common % 4 === 0 && common % 100 !== 0) || common % 400 === 0;
  return isLeap ? 29 : 28;
}

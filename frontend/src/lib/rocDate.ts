// ROC (民國) <-> Gregorian conversions, mirroring pkg/domain/dates.go.
// Year 0 does not exist in the ROC calendar; YEAR_NONE (9996) is the sentinel
// stored when only month/day are known.

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

// Parse "MM/DD" or "YYY/MM/DD". Returns null when the format is wrong or
// month/day are zero.
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

// Convert separate ROC year / month / day inputs to a JS Date (UTC) or null.
// Year 0 + month 0 + day 0 → null. Year 0 with non-zero m/d uses YEAR_NONE.
export function fromROCParts(year: number, month: number, day: number): Date | null {
  if (year === 0 && month === 0 && day === 0) return null;
  const y = year === 0 ? YEAR_NONE : toCommonYear(year);
  return new Date(Date.UTC(y, (month || 1) - 1, day || 1));
}

// Reverse of fromROCParts — split a stored ISO/date back into ROC year/m/d.
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
  // ROC year 0 = unknown — be permissive and allow 29.
  if (rocYear === 0) return 29;
  const common = toCommonYear(rocYear);
  const isLeap = (common % 4 === 0 && common % 100 !== 0) || common % 400 === 0;
  return isLeap ? 29 : 28;
}

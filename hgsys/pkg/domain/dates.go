package domain

import (
	"fmt"
	"strconv"
	"strings"
	"time"
)

// YearNone 為僅知月 / 日時所存放之 sentinel 年份.
const YearNone = 9996

// ToROCYear 將西元年轉為民國年.
// 民國曆中無第 0 年; 結果 ≤ 0 者會額外減 1, 使西元前的範圍跳過不存在的零年.
func ToROCYear(commonYear int) int {
	y := commonYear - 1911
	if y <= 0 {
		y--
	}
	return y
}

// ToCommonYear 將民國年轉為西元年. 第 0 年視為"年份未知", 回傳 YearNone sentinel.
func ToCommonYear(rocYear int) int {
	if rocYear == 0 {
		return YearNone
	}
	if rocYear > 0 {
		return rocYear + 1911
	}
	return rocYear + 1912
}

// ParseROCDate 解析 "MM/DD" 或 "YYY/MM/DD". 缺年份的格式以 YearNone 填入.
// 格式錯誤或月 / 日為零時回傳 nil.
func ParseROCDate(s string) *time.Time {
	parts := strings.Split(s, "/")
	var year, month, day int
	switch len(parts) {
	case 2:
		year = YearNone
		m, err1 := strconv.Atoi(parts[0])
		d, err2 := strconv.Atoi(parts[1])
		if err1 != nil || err2 != nil {
			return nil
		}
		month, day = m, d
	case 3:
		ry, err1 := strconv.Atoi(parts[0])
		m, err2 := strconv.Atoi(parts[1])
		d, err3 := strconv.Atoi(parts[2])
		if err1 != nil || err2 != nil || err3 != nil {
			return nil
		}
		year = ToCommonYear(ry)
		month, day = m, d
	default:
		return nil
	}
	if month == 0 || day == 0 {
		return nil
	}
	t := time.Date(year, time.Month(month), day, 0, 0, 0, 0, time.UTC)
	return &t
}

// FormatROCDate 將 time 格式化為民國日期. 年份為 YearNone 時省略年份 ("MM/DD");
// nil 則格式化為 "0/00/00", 以對齊舊版程式.
func FormatROCDate(t *time.Time) string {
	if t == nil {
		return "0/00/00"
	}
	if t.Year() == YearNone {
		return fmt.Sprintf("%02d/%02d", int(t.Month()), t.Day())
	}
	return fmt.Sprintf("%d/%02d/%02d", ToROCYear(t.Year()), int(t.Month()), t.Day())
}

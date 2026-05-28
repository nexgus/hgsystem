package domain

import (
	"fmt"
	"strconv"
	"strings"
	"time"
)

// YearNone is the sentinel year stored when only month/day are known.
const YearNone = 9996

// ToROCYear converts a Gregorian year to the ROC (民國) year.
// Year 0 does not exist in the ROC calendar; results ≤ 0 are shifted by an
// extra -1 so the BC range jumps over the non-existent year zero.
func ToROCYear(commonYear int) int {
	y := commonYear - 1911
	if y <= 0 {
		y--
	}
	return y
}

// ToCommonYear converts an ROC year to a Gregorian year. Year 0 is treated as
// "year unknown" and returns the YearNone sentinel.
func ToCommonYear(rocYear int) int {
	if rocYear == 0 {
		return YearNone
	}
	if rocYear > 0 {
		return rocYear + 1911
	}
	return rocYear + 1912
}

// ParseROCDate parses "MM/DD" or "YYY/MM/DD". Year-less form fills YearNone.
// Returns nil when the format is wrong or month/day are zero.
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

// FormatROCDate formats a time as ROC date. YearNone omits the year ("MM/DD");
// nil renders as "0/00/00" to match the legacy app.
func FormatROCDate(t *time.Time) string {
	if t == nil {
		return "0/00/00"
	}
	if t.Year() == YearNone {
		return fmt.Sprintf("%02d/%02d", int(t.Month()), t.Day())
	}
	return fmt.Sprintf("%d/%02d/%02d", ToROCYear(t.Year()), int(t.Month()), t.Day())
}

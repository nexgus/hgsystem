"""ROC (民國) <-> Common Era date conversions.

Year 0 is invalid in the ROC calendar. ``YEAR_NONE`` (9996) is the sentinel
stored in MongoDB when only month/day are known.
"""
from datetime import datetime
from typing import Optional

YEAR_NONE = 9996


def to_roc_year(common_year: int) -> int:
    y = common_year - 1911
    if y <= 0:
        y -= 1
    return y


def to_common_year(roc_year: int) -> int:
    if roc_year == 0:
        return YEAR_NONE
    if roc_year > 0:
        return roc_year + 1911
    return roc_year + 1912


def to_python_datetime(roc_date: str) -> Optional[datetime]:
    parts = roc_date.split("/")
    if len(parts) == 2:
        year = YEAR_NONE
        month = int(parts[0])
        day = int(parts[1])
    elif len(parts) == 3:
        year = to_common_year(int(parts[0]))
        month = int(parts[1])
        day = int(parts[2])
    else:
        return None
    if month == 0 or day == 0:
        return None
    return datetime(year, month, day)


def to_roc_date_string(dt: Optional[datetime]) -> str:
    if dt is None:
        return "0/00/00"
    if dt.year == YEAR_NONE:
        return f"{dt.month:02d}/{dt.day:02d}"
    return f"{to_roc_year(dt.year)}/{dt.month:02d}/{dt.day:02d}"

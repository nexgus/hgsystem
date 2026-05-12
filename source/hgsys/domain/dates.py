"""ROC (民國) <-> Common Era date conversions.

Year 0 is invalid in the ROC calendar. ``YEAR_NONE`` (9996) is the sentinel
stored in MongoDB when only month/day are known.
"""

from datetime import datetime

YEAR_NONE: int = 9996


def to_roc_year(common_year: int) -> int:
    """西元年轉民國年.

    民國 0 年不存在; 結果 <= 0 時額外減 1, 將 BC 區間往負方向偏移以跳過 0.

    Arg(s):
        common_year: 西元年.

    Return(s):
        民國年 (正數為民國紀年, 負數為民國前).
    """
    y = common_year - 1911
    if y <= 0:
        y -= 1
    return y


def to_common_year(roc_year: int) -> int:
    """民國年轉西元年.

    民國 0 年 (傳入 0) 視為「年份未知」, 回傳 ``YEAR_NONE`` 哨兵值.

    Arg(s):
        roc_year: 民國年 (正/負, 0 表示年份未知).

    Return(s):
        西元年; 年份未知時為 ``YEAR_NONE``.
    """
    if roc_year == 0:
        return YEAR_NONE
    if roc_year > 0:
        return roc_year + 1911
    return roc_year + 1912


def to_python_datetime(roc_date: str) -> datetime | None:
    """將 ROC 日期字串解析為 ``datetime``.

    支援兩種格式: ``MM/DD`` (年份未知, 以 ``YEAR_NONE`` 填入) 或 ``YYY/MM/DD``.
    格式不符, 或月/日為 0 時, 回傳 ``None``.

    Arg(s):
        roc_date: ROC 日期字串.

    Return(s):
        對應的 ``datetime``, 解析失敗時為 ``None``.
    """
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


def to_roc_date_string(dt: datetime | None) -> str:
    """將 ``datetime`` 格式化為 ROC 日期字串.

    年份為 ``YEAR_NONE`` 時省略年份, 輸出 ``MM/DD``; ``None`` 時回傳 ``"0/00/00"``.

    Arg(s):
        dt: 來源 ``datetime``, 可為 ``None``.

    Return(s):
        ``YYY/MM/DD``, ``MM/DD`` 或 ``"0/00/00"``.
    """
    if dt is None:
        return "0/00/00"
    if dt.year == YEAR_NONE:
        return f"{dt.month:02d}/{dt.day:02d}"
    return f"{to_roc_year(dt.year)}/{dt.month:02d}/{dt.day:02d}"

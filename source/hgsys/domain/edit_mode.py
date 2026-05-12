"""編輯模式列舉與配套狀態查詢."""

from enum import IntEnum


class EditMode(IntEnum):
    """面板的編輯狀態.

    - ``NONE``: 非編輯狀態, 顯示既有資料.
    - ``APPEND``: 新增中, 欄位可編輯且以紅色顯示.
    - ``MODIFY``: 修改中, 欄位可編輯且以紅色顯示.
    - ``INHIBIT``: 鎖定 (例如另一面板正在編輯), 欄位禁用.
    """

    NONE = 0
    APPEND = 1
    MODIFY = 2
    INHIBIT = 3


_EDITABLE: dict[EditMode, bool] = {
    EditMode.NONE: False,
    EditMode.APPEND: True,
    EditMode.MODIFY: True,
    EditMode.INHIBIT: False,
}

_COLOR: dict[EditMode, str] = {
    EditMode.NONE: "black",
    EditMode.APPEND: "red",
    EditMode.MODIFY: "red",
    EditMode.INHIBIT: "black",
}


def is_editable(mode: EditMode) -> bool:
    """回傳該模式下欄位是否可編輯."""
    return _EDITABLE[mode]


def color_for(mode: EditMode) -> str:
    """回傳該模式下欄位文字應使用的顏色名稱."""
    return _COLOR[mode]

"""Shared GUI styling: app font, EditMode-driven stylesheet."""
from pathlib import Path

from PySide6.QtGui import QFont

from ..domain.edit_mode import EditMode, color_for

FONT: QFont = QFont("Microsoft YaHei", 12, 50)

ASSETS_DIR: Path = Path(__file__).resolve().parent.parent / "assets"


def asset(name: str) -> str:
    """回傳套件內 ``assets/<name>`` 的絕對路徑字串 (供 ``QIcon`` 等使用)."""
    return str(ASSETS_DIR / name)


def lineedit_stylesheet(mode: EditMode) -> str:
    """產生隨編輯模式變色的 ``QLineEdit`` 樣式 (文字顏色 / 白底)."""
    return f"QLineEdit {{color: {color_for(mode)}; background: white;}}"

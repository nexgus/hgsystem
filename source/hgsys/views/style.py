"""Shared GUI styling: app font, EditMode-driven stylesheet."""
from pathlib import Path

from PySide6.QtGui import QFont

from ..domain.edit_mode import EditMode, color_for

FONT = QFont("Microsoft YaHei", 12, 50)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def asset(name: str) -> str:
    return str(ASSETS_DIR / name)


def lineedit_stylesheet(mode: EditMode) -> str:
    return f"QLineEdit {{color: {color_for(mode)}; background: white;}}"

"""Shared GUI styling: app font, EditMode-driven stylesheet."""
import os

from PySide6.QtGui import QFont

from ..domain.edit_mode import EditMode, color_for

FONT = QFont("Microsoft YaHei", 12, 50)

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
)


def asset(name: str) -> str:
    return os.path.join(ASSETS_DIR, name)


def lineedit_stylesheet(mode: EditMode) -> str:
    return f"QLineEdit {{color: {color_for(mode)}; background: white;}}"

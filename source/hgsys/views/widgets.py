"""Reusable Qt widgets shared by multiple views."""
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QDate, QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from ..domain.dates import (
    YEAR_NONE,
    to_common_year,
    to_roc_date_string,
    to_roc_year,
)
from ..domain.edit_mode import EditMode, is_editable
from .style import FONT, lineedit_stylesheet


class MyLineEdit(QLineEdit):
    """QLineEdit that swallows the Enter key (so Return triggers focus moves)."""

    def event(self, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Enter:
            return True
        return super().event(event)


class MySpinBox(QSpinBox):
    """QSpinBox that emits a focusOut signal — used by MyDateWidget to refresh
    day-of-month options once the year is committed."""

    focusOut = Signal()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focusOut.emit()


class MyDateWidget(QWidget):
    """ROC-year date input (民國 / month / day).

    Year 0 means "no year known" (stored as YEAR_NONE in MongoDB).
    """

    DAYS_PER_MONTH = [31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def __init__(self, year: int = 0, month: int = 0, day: int = 0):
        super().__init__()
        self.setFont(FONT)

        labels = [QLabel(text) for text in ("民國", "年", "月", "日")]
        for lbl in labels:
            lbl.setFont(FONT)
        txt_era, txt_year, txt_month, txt_day = labels

        self.edtYear = MySpinBox()
        self.edtYear.setFont(FONT)
        self.edtYear.setMinimum(to_roc_year(1))
        self.edtYear.setMaximum(to_roc_year(9999))
        self.edtYear.setValue(year)
        self.edtYear.setAlignment(Qt.AlignRight)
        self.edtYear.setMinimumWidth(50)
        self.edtYear.setFixedHeight(25)

        self.edtMonth = QComboBox()
        self.edtMonth.setFont(FONT)
        self.edtMonth.setMinimumWidth(50)
        self.edtMonth.setEditable(True)
        for x in range(13):
            self.edtMonth.addItem(str(x))
        self.edtMonth.setCurrentIndex(month)
        self.edtMonth.setFixedHeight(25)

        self.edtDay = QComboBox()
        self.edtDay.setFont(FONT)
        self.edtDay.setMinimumWidth(50)
        self.edtDay.setEditable(True)
        self.edtDay.setFixedHeight(25)
        self._refresh_day_items(year, month, day)

        layout = QHBoxLayout()
        layout.addWidget(txt_era)
        layout.addWidget(self.edtYear)
        layout.addWidget(txt_year)
        layout.addWidget(self.edtMonth)
        layout.addWidget(txt_month)
        layout.addWidget(self.edtDay)
        layout.addWidget(txt_day)
        layout.addStretch()
        self.setLayout(layout)

        self.edtMonth.currentIndexChanged.connect(self._on_month_changed)
        self.edtYear.focusOut.connect(self._on_month_changed)

    def _refresh_day_items(self, year: int, month: int, requested_day: int) -> None:
        days = self.DAYS_PER_MONTH[month]
        if days == 28:
            common_year = to_common_year(year) if year != 0 else YEAR_NONE
            if year == 0 or QDate.isLeapYear(common_year):
                days = 29
        self.edtDay.clear()
        for x in range(days + 1):
            self.edtDay.addItem(str(x))
        self.edtDay.setCurrentIndex(min(requested_day, days))

    def _on_month_changed(self, *_):
        year = self.edtYear.value()
        month = self.edtMonth.currentIndex()
        day = self.edtDay.currentIndex()
        self._refresh_day_items(year, month, day)

    def clear(self) -> None:
        self.edtYear.setValue(0)
        self.edtMonth.setCurrentIndex(0)
        self.edtDay.setCurrentIndex(0)

    def date(self) -> Optional[datetime]:
        year = self.edtYear.value()
        month = self.edtMonth.currentIndex()
        day = self.edtDay.currentIndex()
        if year == 0:
            if month == 0 and day == 0:
                return None
            year = YEAR_NONE
        else:
            year = to_common_year(year)
        return datetime(year, month, day)

    def date_string(self) -> str:
        return to_roc_date_string(self.date())

    def set_date(self, year: int = 0, month: int = 0, day: int = 0) -> None:
        self.edtYear.setValue(year)
        self.edtMonth.setCurrentIndex(month)
        self.edtDay.setCurrentIndex(day)

    def set_date_string(self, date: str) -> None:
        parts = date.split("/")
        if len(parts) == 2:
            self.set_date(0, int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            self.set_date(int(parts[0]), int(parts[1]), int(parts[2]))

    def set_edit_mode(self, mode: EditMode) -> None:
        sheet = lineedit_stylesheet(mode)
        for obj in (self.edtYear, self.edtMonth, self.edtDay):
            obj.setEnabled(is_editable(mode))
            obj.lineEdit().setStyleSheet(sheet)

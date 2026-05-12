"""Composes the customer panel above the worksheet panel."""
from typing import Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..viewmodels.main import MainViewModel
from .customer import CustomerView
from .worksheet import WorksheetView


class MainWidget(QWidget):
    def __init__(self, vm: MainViewModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._vm = vm

        self.customer = CustomerView(vm.customer, vm.worksheet)
        self.worksheet = WorksheetView(vm.worksheet)
        self.customer.setFixedHeight(300)

        layout = QVBoxLayout()
        layout.addWidget(self.customer)
        layout.addWidget(self.worksheet)
        layout.addStretch()
        self.setLayout(layout)

        # Initial focus: search if any data, otherwise append.
        vm.customer.totalCountChanged.connect(self._set_initial_focus)

    def _set_initial_focus(self, total: int) -> None:
        edit = self.customer.edit
        if total > 0:
            edit.cmdSearch.setFocus()
        else:
            edit.cmdAppend.setFocus()
        # Only need to react once.
        try:
            self._vm.customer.totalCountChanged.disconnect(self._set_initial_focus)
        except (TypeError, RuntimeError):
            pass

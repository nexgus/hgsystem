"""Composes the customer panel above the worksheet panel."""

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..viewmodels.main import MainViewModel
from .customer import CustomerView
from .worksheet import WorksheetView


class MainWidget(QWidget):
    """主視窗的中央 widget: 上半客戶面板, 下半工單面板."""

    def __init__(self, vm: MainViewModel, parent: QWidget | None = None) -> None:
        """組好兩塊面板並排版.

        Arg(s):
            vm: 已建立的 ``MainViewModel``.
            parent: Qt parent.
        """
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
        """資料庫有客戶時將初始焦點放在搜尋, 否則放在新增 (只執行一次)."""
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

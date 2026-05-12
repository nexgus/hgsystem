"""Search dialog: filter customers + history-based search."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..domain.dates import to_roc_date_string
from ..domain.edit_mode import EditMode
from ..domain.models import Customer
from ..viewmodels.search import SearchViewModel
from .style import FONT
from .widgets import MyDateWidget, MyLineEdit


class CustomerResultsTable(QTableWidget):
    """搜尋結果表格 (僅展示, 不可編輯).

    ``HIDDEN_COLS`` 為儲存了但不顯示給使用者的欄位 (例如內部 id).
    """

    HEADERS: list[str] = ["cid", "姓名", "title", "生日", "電話", "住址", "broker"]
    HIDDEN_COLS: tuple[str, ...] = ("cid", "title", "broker")

    def __init__(self, parent: QWidget | None = None) -> None:
        """建立表頭並隱藏內部欄位."""
        super().__init__(parent)
        self.setFont(FONT)
        self._results: list[Customer] = []

        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        header = self.horizontalHeader()
        for idx in range(len(self.HEADERS) - 1):
            header.setSectionResizeMode(idx, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(len(self.HEADERS) - 1, QHeaderView.Stretch)
        for col_name in self.HIDDEN_COLS:
            self.setColumnHidden(self.HEADERS.index(col_name), True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setWordWrap(False)

        self.currentCellChanged.connect(self._on_current_cell_changed)

    def set_results(self, customers: list[Customer]) -> None:
        """以 ``customers`` 重建整張表格."""
        self._results = customers
        self.setRowCount(0)
        for c in customers:
            self._append(c)

    def selected_customer(self) -> Customer | None:
        """回傳當前選取列對應的 ``Customer``; 無選取時為 ``None``."""
        row = self.currentRow()
        if 0 <= row < len(self._results):
            return self._results[row]
        return None

    def _append(self, c: Customer) -> None:
        """在表尾新增一列, 對應 ``c`` 的欄位."""
        row = self.rowCount()
        self.insertRow(row)
        values = [
            c.id, c.name, c.title,
            to_roc_date_string(c.birthdate),
            c.phones, c.addr, c.broker,
        ]
        for col, value in enumerate(values):
            self.setItem(row, col, QTableWidgetItem(value))

    def _on_current_cell_changed(self, cur_row: int, _cc: int, prv_row: int, _pc: int) -> None:
        """切換選取時更新前後列的反白."""
        if prv_row > -1:
            self._highlight(prv_row, False)
        if cur_row > -1:
            self._highlight(cur_row, True)

    def _highlight(self, row: int, on: bool) -> None:
        """切換指定列的反白色塊."""
        if row < 0:
            return
        fg = QColor("white") if on else QColor("black")
        bg = QColor("cornflowerblue") if on else QColor("white")
        for col in range(len(self.HEADERS)):
            item = self.item(row, col)
            if item is None:
                continue
            item.setForeground(QBrush(fg))
            item.setBackground(QBrush(bg))


class SearchDialog(QDialog):
    """Modal: filter by phone/birthdate/name/addr, or browse search history."""

    def __init__(self, vm: SearchViewModel, parent: QWidget | None = None) -> None:
        """建立搜尋對話框 (條件區 + 結果表 + 確定 / 取消).

        Arg(s):
            vm: 搜尋 view-model.
            parent: Qt parent.
        """
        super().__init__(parent)
        self.setFont(FONT)
        self._vm = vm

        labels = (QLabel("電話"), QLabel("生日"), QLabel("姓名"), QLabel("地址"))
        for lbl in labels:
            lbl.setFixedWidth(50)
        txt_phone, txt_birth, txt_name, txt_addr = labels

        self.edtPhone = QLineEdit()
        self.edtBirthdate = MyDateWidget()
        self.edtName = MyLineEdit()
        self.edtAddr = QLineEdit()
        self.cmdSearch = QPushButton("(&F) 搜尋")
        self.cmdHistory = QPushButton("(&H) 記錄")

        filter_actions = QHBoxLayout()
        filter_actions.addWidget(self.cmdSearch)
        filter_actions.addWidget(self.cmdHistory)

        filters = QGridLayout()
        filters.addWidget(txt_phone, 0, 0)
        filters.addWidget(txt_birth, 1, 0)
        filters.addWidget(txt_name, 2, 0)
        filters.addWidget(txt_addr, 3, 0)
        filters.addWidget(self.edtPhone, 0, 1, 1, 2)
        filters.addWidget(self.edtBirthdate, 1, 1, 1, 2)
        filters.addWidget(self.edtName, 2, 1, 1, 2)
        filters.addWidget(self.edtAddr, 3, 1, 1, 2)
        filters.addLayout(filter_actions, 5, 0, 1, 3)
        filters.setRowMinimumHeight(4, 20)

        self.table = CustomerResultsTable()
        self.cmdAccept = QPushButton("(&Y) 確定")
        self.cmdAccept.setEnabled(False)
        self.cmdCancel = QPushButton("(&N) 取消")

        controls = QHBoxLayout()
        controls.addWidget(self.cmdAccept)
        controls.addWidget(self.cmdCancel)

        outer = QVBoxLayout()
        outer.addLayout(filters)
        outer.addWidget(self.table)
        outer.addLayout(controls)
        self.setLayout(outer)

        self.setWindowTitle("搜尋")
        self.setMinimumWidth(500)
        self.setWindowModality(Qt.ApplicationModal)
        self.setStyleSheet("QLineEdit {color: red; background: white;}")
        self.edtBirthdate.set_edit_mode(EditMode.MODIFY)
        self.edtPhone.setFocus()

        # Wiring
        self.cmdSearch.clicked.connect(self._on_search_clicked)
        self.cmdHistory.clicked.connect(self._on_history_clicked)
        self.cmdAccept.clicked.connect(self.accept)
        self.cmdCancel.clicked.connect(self.reject)
        self.table.itemDoubleClicked.connect(lambda _: self.cmdAccept.click())

        self._vm.resultsChanged.connect(self._on_results)

    def selected_customer(self) -> Customer | None:
        """回傳對話框中被選取的客戶 (供外層 ``QDialog.Accepted`` 後讀取)."""
        return self.table.selected_customer()

    def _on_search_clicked(self) -> None:
        """搜尋按鈕: 收集條件交給 view-model 執行查詢."""
        birthdate = self.edtBirthdate.date()
        self._vm.search_new(
            name=self.edtName.text().strip(),
            addr=self.edtAddr.text().strip(),
            phone=self.edtPhone.text().strip(),
            birthdate=birthdate,
        )

    def _on_history_clicked(self) -> None:
        """記錄按鈕: 改以本次啟動的搜尋歷史作為結果."""
        self._vm.search_history()

    def _on_results(self, customers: list[Customer]) -> None:
        """收到結果: 灌入表格, 有結果時聚焦於表格與啟用「確定」, 否則回到電話欄."""
        self.table.set_results(customers)
        if customers:
            self.table.setCurrentCell(0, 0)
            self.cmdAccept.setEnabled(True)
            self.table.setFocus()
        else:
            self.cmdAccept.setEnabled(False)
            self.edtPhone.setFocus()

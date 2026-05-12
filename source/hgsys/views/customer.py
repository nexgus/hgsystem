"""Customer panel: editable form + worksheet history table."""
from typing import Optional

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QGroupBox,
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
from ..domain.edit_mode import EditMode, is_editable
from ..domain.models import Customer, Worksheet
from ..viewmodels.customer import CustomerViewModel
from ..viewmodels.worksheet import WorksheetViewModel
from .style import FONT, lineedit_stylesheet
from .widgets import MyDateWidget


class CustomerEditPanel(QGroupBox):
    """Form for one Customer: name/title/addr/phones/birthdate/broker."""

    def __init__(self, vm: CustomerViewModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFont(FONT)
        self._vm = vm

        self.cmdAppend = QPushButton("(&A) 新增")
        self.cmdModify = QPushButton("(&M) 修改")
        self.cmdRemove = QPushButton("(&R) 刪除")
        self.cmdSearch = QPushButton("(&F) 搜尋")
        self.cmdSave = QPushButton("(&S) 儲存")
        self.cmdCancel = QPushButton("(&C) 取消")
        for btn in (
            self.cmdAppend, self.cmdModify, self.cmdRemove,
            self.cmdSearch, self.cmdSave, self.cmdCancel,
        ):
            btn.setFont(FONT)

        controls = QHBoxLayout()
        for btn in (
            self.cmdSearch, self.cmdModify, self.cmdSave,
            self.cmdCancel, self.cmdRemove, self.cmdAppend,
        ):
            controls.addWidget(btn)

        labels = {
            "name": QLabel("姓名"),
            "addr": QLabel("地址"),
            "phone": QLabel("電話"),
            "birthdate": QLabel("生日"),
            "broker": QLabel("介紹人"),
        }
        for lbl in labels.values():
            lbl.setFont(FONT)
            lbl.setFixedWidth(65)

        self.edtName = QLineEdit()
        self.edtTitle = QLineEdit()
        self.edtAddr = QLineEdit()
        self.edtPhone1 = QLineEdit()
        self.edtPhone2 = QLineEdit()
        self.edtPhone3 = QLineEdit()
        self.edtPhone4 = QLineEdit()
        self.edtBroker = QLineEdit()
        for edt in (
            self.edtName, self.edtTitle, self.edtAddr,
            self.edtPhone1, self.edtPhone2, self.edtPhone3, self.edtPhone4,
            self.edtBroker,
        ):
            edt.setFont(FONT)

        self.edtBirthdate = MyDateWidget()
        self.edtBirthdate.setFixedHeight(40)

        form = QGridLayout()
        form.addWidget(labels["name"], 0, 0)
        form.addWidget(labels["addr"], 1, 0)
        form.addWidget(labels["phone"], 2, 0)
        form.addWidget(labels["birthdate"], 4, 0)
        form.addWidget(labels["broker"], 5, 0)
        form.addWidget(self.edtName, 0, 1)
        form.addWidget(self.edtTitle, 0, 2)
        form.addWidget(self.edtAddr, 1, 1, 1, 2)
        form.addWidget(self.edtPhone1, 2, 1)
        form.addWidget(self.edtPhone2, 2, 2)
        form.addWidget(self.edtPhone3, 3, 1)
        form.addWidget(self.edtPhone4, 3, 2)
        form.addWidget(self.edtBirthdate, 4, 1, 1, 2)
        form.addWidget(self.edtBroker, 5, 1, 1, 2)

        outer = QVBoxLayout()
        outer.addLayout(form)
        outer.addLayout(controls)
        outer.addStretch()
        self.setLayout(outer)

        self._editable_widgets = (
            self.edtName, self.edtTitle, self.edtAddr,
            self.edtPhone1, self.edtPhone2, self.edtPhone3, self.edtPhone4,
            self.edtBirthdate, self.edtBroker,
        )

        self._wire_internal()
        self._wire_vm()
        self._apply_customer(None)
        self._apply_mode(EditMode.NONE)

    # ---- wiring -----------------------------------------------------------
    def _wire_internal(self) -> None:
        self.edtName.returnPressed.connect(self.edtAddr.setFocus)
        self.edtAddr.returnPressed.connect(self.edtPhone1.setFocus)
        self.edtPhone1.returnPressed.connect(self.edtPhone2.setFocus)
        self.edtPhone2.returnPressed.connect(self.edtPhone3.setFocus)
        self.edtPhone3.returnPressed.connect(self.edtPhone4.setFocus)
        self.edtPhone4.returnPressed.connect(self.edtBirthdate.edtYear.setFocus)

        self.cmdAppend.clicked.connect(self._on_append_clicked)
        self.cmdModify.clicked.connect(self._on_modify_clicked)
        self.cmdSave.clicked.connect(self._on_save_clicked)
        self.cmdCancel.clicked.connect(self._vm.cancel_edit)

    def _wire_vm(self) -> None:
        self._vm.currentChanged.connect(self._apply_customer)
        self._vm.editModeChanged.connect(self._apply_mode_int)
        self._vm.totalCountChanged.connect(self._apply_total)

    # ---- VM → view --------------------------------------------------------
    def _apply_total(self, total: int) -> None:
        self.setTitle(f"客戶資料 (共有 {total} 筆紀錄)")

    def _apply_customer(self, customer: Optional[Customer]) -> None:
        if customer is None:
            self.edtName.clear()
            self.edtTitle.clear()
            self.edtAddr.clear()
            self.edtPhone1.clear()
            self.edtPhone2.clear()
            self.edtPhone3.clear()
            self.edtPhone4.clear()
            self.edtBirthdate.clear()
            self.edtBroker.clear()
            return
        self.edtName.setText(customer.name)
        self.edtTitle.setText(customer.title)
        self.edtAddr.setText(customer.addr)
        phones = customer.phone_list()
        self.edtPhone1.setText(phones[0])
        self.edtPhone2.setText(phones[1])
        self.edtPhone3.setText(phones[2])
        self.edtPhone4.setText(phones[3])
        self.edtBirthdate.set_date_string(to_roc_date_string(customer.birthdate))
        self.edtBroker.setText(customer.broker)

    def _apply_mode_int(self, mode: int) -> None:
        self._apply_mode(EditMode(mode))

    def _apply_mode(self, mode: EditMode) -> None:
        editing = is_editable(mode)
        has_current = self._vm.current is not None
        has_data = self._vm.total > 0

        if mode == EditMode.NONE:
            self.cmdAppend.setEnabled(True)
            self.cmdSave.setEnabled(False)
            self.cmdCancel.setEnabled(False)
            self.cmdSearch.setEnabled(has_data)
            self.cmdModify.setEnabled(has_current)
            self.cmdRemove.setEnabled(has_current)
        else:
            self.cmdAppend.setEnabled(False)
            self.cmdRemove.setEnabled(False)
            self.cmdModify.setEnabled(False)
            self.cmdSearch.setEnabled(False)
            if mode == EditMode.INHIBIT:
                self.cmdSave.setEnabled(False)
                self.cmdCancel.setEnabled(False)
            else:
                self.cmdSave.setEnabled(editing)
                self.cmdCancel.setEnabled(editing)

        for obj in self._editable_widgets:
            if isinstance(obj, MyDateWidget):
                obj.set_edit_mode(mode)
            obj.setEnabled(editing)

        self.setStyleSheet(lineedit_stylesheet(mode))

        if mode == EditMode.APPEND:
            self.edtName.setFocus()

    # ---- view → VM --------------------------------------------------------
    def _on_append_clicked(self) -> None:
        self._vm.start_append()

    def _on_modify_clicked(self) -> None:
        self._vm.start_modify()
        self.edtName.setFocus()

    def _on_save_clicked(self) -> None:
        draft = self._collect()
        self._vm.save(draft)

    def _collect(self) -> Customer:
        phones = ";".join(
            edt.text().strip()
            for edt in (self.edtPhone1, self.edtPhone2, self.edtPhone3, self.edtPhone4)
        )
        return Customer(
            id=self._vm.current.id if self._vm.current else "",
            name=self.edtName.text().strip(),
            title=self.edtTitle.text().strip(),
            addr=self.edtAddr.text().strip(),
            phones=phones,
            birthdate=self.edtBirthdate.date(),
            broker=self.edtBroker.text().strip(),
        )


class WorksheetHistoryTable(QTableWidget):
    """Table listing worksheets for the current customer.

    Bound to ``WorksheetViewModel`` — refreshes on ``historyChanged`` and emits
    ``select_row`` to the VM when the selection moves.
    """

    HEADERS = [
        "wid", "cid", "收件日", "交件日",
        "SPH(R)", "SPH(L)", "CYL(R)", "CYL(L)",
        "AXIS(R)", "AXIS(L)", "BASE(R)", "BASE(L)",
        "BC(R)", "BC(L)", "BC.V(R)", "BC.V(L)",
        "BC.H(R)", "BC.H(L)", "ADD(R)", "ADD(L)", "PD", "source",
        "視力(R)", "視力(L)", "鏡片(R)", "鏡片(L)", "鏡架", "memo",
        "priceLens", "priceFrame",
    ]
    HIDDEN_COLS = (
        "cid", "wid", "AXIS(R)", "AXIS(L)", "BASE(R)", "BASE(L)",
        "BC.V(R)", "BC.V(L)", "BC.H(R)", "BC.H(L)", "ADD(R)", "ADD(L)",
        "PD", "source", "memo", "priceLens", "priceFrame",
    )

    def __init__(self, vm: WorksheetViewModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFont(FONT)
        self._vm = vm
        self._frozen = False

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
        self._vm.historyChanged.connect(self._on_history_changed)
        self._vm.historyRowAppended.connect(self._on_row_appended)
        self._vm.historyRowReplaced.connect(self._on_row_replaced)
        self._vm.historyRowRemoved.connect(self._on_row_removed)
        self._vm.editModeChanged.connect(self._on_mode_changed)

    # ---- freeze / event filter -------------------------------------------
    def freeze(self, frozen: bool) -> None:
        self._frozen = frozen
        if frozen:
            self.installEventFilter(self)
        else:
            self.removeEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.KeyPress, QEvent.MouseButtonPress):
            return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if not self._frozen:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._frozen:
            super().mousePressEvent(event)

    # ---- VM → view --------------------------------------------------------
    def _on_history_changed(self, history: list) -> None:
        self.blockSignals(True)
        self.setRowCount(0)
        for ws in history:
            self._append_row(ws)
        self.blockSignals(False)
        if self.rowCount() > 0:
            self.setCurrentCell(0, 0)

    def _on_row_appended(self, ws: Worksheet) -> None:
        self._append_row(ws)
        self.setCurrentCell(self.rowCount() - 1, 0)

    def _on_row_replaced(self, row: int, ws: Worksheet) -> None:
        self._set_row(row, ws)

    def _on_row_removed(self, row: int) -> None:
        self.removeRow(row)

    def _on_mode_changed(self, mode: int) -> None:
        # When customer is being edited, customer-VM marks worksheet INHIBIT.
        # Conversely when worksheet is being edited, MainVM tells customer.
        # Either way, freeze the table while a sibling is editing.
        editing = EditMode(mode) in (EditMode.APPEND, EditMode.MODIFY, EditMode.INHIBIT)
        self.freeze(editing)

    def _append_row(self, ws: Worksheet) -> None:
        row = self.rowCount()
        self.insertRow(row)
        self._set_row(row, ws)

    def _set_row(self, row: int, ws: Worksheet) -> None:
        values = [
            ws.id, ws.cid,
            to_roc_date_string(ws.order_time),
            to_roc_date_string(ws.deliver_time),
            ws.sph_r, ws.sph_l, ws.cyl_r, ws.cyl_l,
            ws.axis_r, ws.axis_l, ws.base_r, ws.base_l,
            ws.bc_r, ws.bc_l, ws.bcv_r, ws.bcv_l,
            ws.bch_r, ws.bch_l, ws.add_r, ws.add_l,
            ws.pd, ws.source,
            ws.eyesight_r, ws.eyesight_l,
            ws.lens_r, ws.lens_l, ws.frame, ws.memo,
            str(ws.lens_price), str(ws.frame_price),
        ]
        for col, value in enumerate(values):
            self.setItem(row, col, QTableWidgetItem(value))

    # ---- view → VM --------------------------------------------------------
    def _on_current_cell_changed(self, cur_row, _cur_col, prv_row, _prv_col) -> None:
        if prv_row > -1:
            self._set_row_highlight(prv_row, False)
        if cur_row > -1:
            self._set_row_highlight(cur_row, True)
            self._vm.select_row(cur_row)

    def _set_row_highlight(self, row: int, on: bool) -> None:
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


class CustomerView(QWidget):
    """Composes the customer edit form and the worksheet history table."""

    def __init__(
        self,
        customer_vm: CustomerViewModel,
        worksheet_vm: WorksheetViewModel,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.edit = CustomerEditPanel(customer_vm)
        self.history = WorksheetHistoryTable(worksheet_vm)

        layout = QGridLayout()
        layout.addWidget(self.edit, 0, 0)
        layout.addWidget(self.history, 0, 1)
        self.setLayout(layout)

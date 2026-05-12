"""Worksheet panel: prescription form + glasses + price + actions."""
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from ..domain.edit_mode import EditMode, is_editable
from ..domain.models import Worksheet
from ..viewmodels.worksheet import WorksheetViewModel
from .style import FONT, lineedit_stylesheet
from .widgets import MyDateWidget


class MedicalRecordPanel(QGroupBox):
    """Prescription fields (SPH/CYL/AXIS/BASE/BC/BC.V/BC.H/ADD per eye + PD + 來源)."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFont(FONT)
        self.setTitle("處方箋")

        labels_top = QLabel("OD/R"), QLabel("OS/L")
        for lbl in labels_top:
            lbl.setFont(FONT)
        txt_right, txt_left = labels_top

        row_labels_text = ("SPH", "CYL", "AXIS", "BASE", "BC", "BC.V", "BC.H", "ADD", "PD", "來源")
        row_labels = [QLabel(t) for t in row_labels_text]
        for lbl in row_labels:
            lbl.setMaximumWidth(50)
            lbl.setFont(FONT)

        self.edtSphR = QLineEdit(parent=self)
        self.edtSphL = QLineEdit(parent=self)
        self.edtCylR = QLineEdit(parent=self)
        self.edtCylL = QLineEdit(parent=self)
        self.edtAxisR = QLineEdit(parent=self)
        self.edtAxisL = QLineEdit(parent=self)
        self.edtBaseR = QLineEdit(parent=self)
        self.edtBaseL = QLineEdit(parent=self)
        self.edtBCR = QLineEdit(parent=self)
        self.edtBCL = QLineEdit(parent=self)
        self.edtBCVR = QLineEdit(parent=self)
        self.edtBCVL = QLineEdit(parent=self)
        self.edtBCHR = QLineEdit(parent=self)
        self.edtBCHL = QLineEdit(parent=self)
        self.edtAddR = QLineEdit(parent=self)
        self.edtAddL = QLineEdit(parent=self)
        self.edtPd = QLineEdit(parent=self)
        self.edtSource = QLineEdit(parent=self)

        for edt in (
            self.edtSphR, self.edtSphL, self.edtCylR, self.edtCylL,
            self.edtAxisR, self.edtAxisL, self.edtBaseR, self.edtBaseL,
            self.edtBCR, self.edtBCL, self.edtBCVR, self.edtBCVL,
            self.edtBCHR, self.edtBCHL, self.edtAddR, self.edtAddL, self.edtPd,
        ):
            edt.setAlignment(Qt.AlignHCenter)
            edt.setFont(FONT)
        self.edtSource.setFont(FONT)

        self.setTabOrder(self.edtSphR, self.edtCylR)
        self.setTabOrder(self.edtCylR, self.edtAxisR)
        self.setTabOrder(self.edtAxisR, self.edtBaseR)
        self.setTabOrder(self.edtBaseR, self.edtBCVR)
        self.setTabOrder(self.edtBCVR, self.edtBCHR)
        self.setTabOrder(self.edtBCHR, self.edtAddR)
        self.setTabOrder(self.edtAddR, self.edtSphL)
        self.setTabOrder(self.edtCylL, self.edtAxisL)
        self.setTabOrder(self.edtAxisL, self.edtBaseL)
        self.setTabOrder(self.edtBaseL, self.edtBCVL)
        self.setTabOrder(self.edtBCVL, self.edtBCHL)
        self.setTabOrder(self.edtBCHL, self.edtAddL)
        self.setTabOrder(self.edtAddL, self.edtPd)

        layout = QGridLayout()
        layout.addWidget(txt_right, 0, 1, Qt.AlignHCenter)
        layout.addWidget(txt_left, 0, 2, Qt.AlignHCenter)
        for row_idx, lbl in enumerate(row_labels, start=1):
            layout.addWidget(lbl, row_idx, 0)
        layout.addWidget(self.edtSphR, 1, 1)
        layout.addWidget(self.edtSphL, 1, 2)
        layout.addWidget(self.edtCylR, 2, 1)
        layout.addWidget(self.edtCylL, 2, 2)
        layout.addWidget(self.edtAxisR, 3, 1)
        layout.addWidget(self.edtAxisL, 3, 2)
        layout.addWidget(self.edtBaseR, 4, 1)
        layout.addWidget(self.edtBaseL, 4, 2)
        layout.addWidget(self.edtBCR, 5, 1)
        layout.addWidget(self.edtBCL, 5, 2)
        layout.addWidget(self.edtBCVR, 6, 1)
        layout.addWidget(self.edtBCVL, 6, 2)
        layout.addWidget(self.edtBCHR, 7, 1)
        layout.addWidget(self.edtBCHL, 7, 2)
        layout.addWidget(self.edtAddR, 8, 1)
        layout.addWidget(self.edtAddL, 8, 2)
        layout.addWidget(self.edtPd, 9, 1, 1, 2)
        layout.addWidget(self.edtSource, 10, 1, 1, 2)
        self.setLayout(layout)

        self._editable_widgets = (
            self.edtSphR, self.edtSphL, self.edtCylR, self.edtCylL,
            self.edtAxisR, self.edtAxisL, self.edtBaseR, self.edtBaseL,
            self.edtBCR, self.edtBCL, self.edtBCVR, self.edtBCVL,
            self.edtBCHR, self.edtBCHL, self.edtAddR, self.edtAddL,
            self.edtPd, self.edtSource,
        )

    def clear(self) -> None:
        for edt in self._editable_widgets:
            edt.clear()

    def fill(self, ws: Worksheet) -> None:
        self.edtSphR.setText(ws.sph_r)
        self.edtSphL.setText(ws.sph_l)
        self.edtCylR.setText(ws.cyl_r)
        self.edtCylL.setText(ws.cyl_l)
        self.edtAxisR.setText(ws.axis_r)
        self.edtAxisL.setText(ws.axis_l)
        self.edtBaseR.setText(ws.base_r)
        self.edtBaseL.setText(ws.base_l)
        self.edtBCR.setText(ws.bc_r)
        self.edtBCL.setText(ws.bc_l)
        self.edtBCVR.setText(ws.bcv_r)
        self.edtBCVL.setText(ws.bcv_l)
        self.edtBCHR.setText(ws.bch_r)
        self.edtBCHL.setText(ws.bch_l)
        self.edtAddR.setText(ws.add_r)
        self.edtAddL.setText(ws.add_l)
        self.edtPd.setText(ws.pd)
        self.edtSource.setText(ws.source)

    def apply_to(self, ws: Worksheet) -> None:
        ws.sph_r = self.edtSphR.text().strip()
        ws.sph_l = self.edtSphL.text().strip()
        ws.cyl_r = self.edtCylR.text().strip()
        ws.cyl_l = self.edtCylL.text().strip()
        ws.axis_r = self.edtAxisR.text().strip()
        ws.axis_l = self.edtAxisL.text().strip()
        ws.base_r = self.edtBaseR.text().strip()
        ws.base_l = self.edtBaseL.text().strip()
        ws.bc_r = self.edtBCR.text().strip()
        ws.bc_l = self.edtBCL.text().strip()
        ws.bcv_r = self.edtBCVR.text().strip()
        ws.bcv_l = self.edtBCVL.text().strip()
        ws.bch_r = self.edtBCHR.text().strip()
        ws.bch_l = self.edtBCHL.text().strip()
        ws.add_r = self.edtAddR.text().strip()
        ws.add_l = self.edtAddL.text().strip()
        ws.pd = self.edtPd.text().strip()
        ws.source = self.edtSource.text().strip()

    def set_edit_mode(self, mode: EditMode) -> None:
        self.setStyleSheet(lineedit_stylesheet(mode))
        for edt in self._editable_widgets:
            edt.setEnabled(is_editable(mode))


class GlassesRecordPanel(QGroupBox):
    """Glasses-side fields: 視力 / 鏡片 / 鏡架 / 備註."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFont(FONT)
        self.setTitle("眼鏡資料")

        txt_right = QLabel("OD/R")
        txt_left = QLabel("OS/L")
        for lbl in (txt_right, txt_left):
            lbl.setFont(FONT)

        labels_text = ("視力", "鏡片", "鏡架", "備註")
        labels = [QLabel(t) for t in labels_text]
        for lbl in labels:
            lbl.setFixedWidth(50)
            lbl.setFont(FONT)

        self.edtSightR = QLineEdit()
        self.edtSightL = QLineEdit()
        self.edtLensR = QLineEdit()
        self.edtLensL = QLineEdit()
        self.edtFrame = QLineEdit()
        self.edtMemo = QLineEdit()

        for edt in (self.edtSightR, self.edtSightL):
            edt.setAlignment(Qt.AlignHCenter)
        for edt in (
            self.edtSightR, self.edtSightL,
            self.edtLensR, self.edtLensL,
            self.edtFrame, self.edtMemo,
        ):
            edt.setFont(FONT)

        layout = QGridLayout()
        layout.addWidget(txt_right, 0, 1, Qt.AlignHCenter)
        layout.addWidget(txt_left, 0, 2, Qt.AlignHCenter)
        for row_idx, lbl in enumerate(labels, start=1):
            layout.addWidget(lbl, row_idx, 0)
        layout.addWidget(self.edtSightR, 1, 1)
        layout.addWidget(self.edtSightL, 1, 2)
        layout.addWidget(self.edtLensR, 2, 1)
        layout.addWidget(self.edtLensL, 2, 2)
        layout.addWidget(self.edtFrame, 3, 1, 1, 2)
        layout.addWidget(self.edtMemo, 4, 1, 1, 2)
        layout.setRowStretch(5, 1)
        self.setLayout(layout)

        self._editable_widgets = (
            self.edtSightR, self.edtSightL,
            self.edtLensR, self.edtLensL,
            self.edtFrame, self.edtMemo,
        )

    def clear(self) -> None:
        for edt in self._editable_widgets:
            edt.clear()

    def fill(self, ws: Worksheet) -> None:
        self.edtSightR.setText(ws.eyesight_r)
        self.edtSightL.setText(ws.eyesight_l)
        self.edtLensR.setText(ws.lens_r)
        self.edtLensL.setText(ws.lens_l)
        self.edtFrame.setText(ws.frame)
        self.edtMemo.setText(ws.memo)

    def apply_to(self, ws: Worksheet) -> None:
        ws.eyesight_r = self.edtSightR.text().strip()
        ws.eyesight_l = self.edtSightL.text().strip()
        ws.lens_r = self.edtLensR.text().strip()
        ws.lens_l = self.edtLensL.text().strip()
        ws.frame = self.edtFrame.text().strip()
        ws.memo = self.edtMemo.text().strip()

    def set_edit_mode(self, mode: EditMode) -> None:
        self.setStyleSheet(lineedit_stylesheet(mode))
        for edt in self._editable_widgets:
            edt.setEnabled(is_editable(mode))


class PriceRecordPanel(QGroupBox):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFont(FONT)
        self.setTitle("金額")

        labels_text = ("鏡片", "鏡架", "合計")
        labels = [QLabel(t) for t in labels_text]
        for lbl in labels:
            lbl.setFixedWidth(40)
            lbl.setFont(FONT)

        self.edtLens = QSpinBox()
        self.edtFrame = QSpinBox()
        for sp in (self.edtLens, self.edtFrame):
            sp.setRange(0, 100_000_000)
            sp.setAlignment(Qt.AlignRight)
            sp.setFont(FONT)
        self.edtTotal = QLineEdit()
        self.edtTotal.setAlignment(Qt.AlignRight)
        self.edtTotal.setReadOnly(True)
        self.edtTotal.setFont(FONT)

        layout = QGridLayout()
        for row_idx, lbl in enumerate(labels, start=1):
            layout.addWidget(lbl, row_idx, 0)
        layout.addWidget(self.edtLens, 1, 1, 1, 2)
        layout.addWidget(self.edtFrame, 2, 1, 1, 2)
        layout.addWidget(self.edtTotal, 3, 1, 1, 2)
        self.setLayout(layout)

        self.edtLens.valueChanged.connect(self._recompute)
        self.edtFrame.valueChanged.connect(self._recompute)
        self._recompute()

    def _recompute(self, *_) -> None:
        self.edtTotal.setText(str(self.edtLens.value() + self.edtFrame.value()))

    def clear(self) -> None:
        self.edtLens.setValue(0)
        self.edtFrame.setValue(0)

    def fill(self, ws: Worksheet) -> None:
        self.edtLens.setValue(ws.lens_price)
        self.edtFrame.setValue(ws.frame_price)

    def apply_to(self, ws: Worksheet) -> None:
        ws.lens_price = self.edtLens.value()
        ws.frame_price = self.edtFrame.value()

    def set_edit_mode(self, mode: EditMode) -> None:
        sheet = lineedit_stylesheet(mode)
        self.setStyleSheet(sheet)
        for sp in (self.edtLens, self.edtFrame):
            sp.setEnabled(is_editable(mode))
            sp.lineEdit().setStyleSheet(sheet)
        self.edtTotal.setEnabled(is_editable(mode))


class WorksheetView(QGroupBox):
    """Top-level worksheet panel: dates + Medical/Glasses/Price + actions."""

    def __init__(self, vm: WorksheetViewModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFont(FONT)
        self.setTitle("配鏡資料")
        self._vm = vm

        txt_accept = QLabel("收件日")
        txt_accept.setFont(FONT)
        self.edtAccept = MyDateWidget()
        layout_accept = QHBoxLayout()
        layout_accept.addWidget(txt_accept)
        layout_accept.addWidget(self.edtAccept)
        layout_accept.addStretch()

        txt_deliver = QLabel("交件日")
        txt_deliver.setFont(FONT)
        self.edtDeliver = MyDateWidget()
        layout_deliver = QHBoxLayout()
        layout_deliver.addWidget(txt_deliver)
        layout_deliver.addWidget(self.edtDeliver)
        layout_deliver.addStretch()

        self.cmdAppend = QPushButton("(&N) 新增")
        self.cmdModify = QPushButton("(&E) 修改")
        self.cmdRemove = QPushButton("(&D) 刪除")
        self.cmdSave = QPushButton("(&S) 儲存")
        self.cmdCancel = QPushButton("(&C) 取消")
        for btn in (self.cmdAppend, self.cmdModify, self.cmdRemove,
                    self.cmdSave, self.cmdCancel):
            btn.setFont(FONT)
        controls = QHBoxLayout()
        for btn in (self.cmdAppend, self.cmdModify, self.cmdSave,
                    self.cmdCancel, self.cmdRemove):
            controls.addWidget(btn)

        self.medical = MedicalRecordPanel()
        self.glasses = GlassesRecordPanel()
        self.price = PriceRecordPanel()

        layout = QGridLayout()
        layout.setColumnMinimumWidth(1, 20)
        layout.addLayout(layout_accept, 0, 0)
        layout.addLayout(layout_deliver, 0, 2)
        layout.addWidget(self.medical, 1, 0, 2, 1)
        layout.addWidget(self.glasses, 1, 2, 1, 1)
        layout.addWidget(self.price, 2, 2, 1, 1)
        layout.addLayout(controls, 3, 0, 1, 3)
        self.setLayout(layout)

        self.cmdAppend.clicked.connect(self._on_append_clicked)
        self.cmdModify.clicked.connect(self._on_modify_clicked)
        self.cmdSave.clicked.connect(self._on_save_clicked)
        self.cmdCancel.clicked.connect(self._vm.cancel_edit)

        self._vm.currentChanged.connect(self._apply_current)
        self._vm.editModeChanged.connect(self._apply_mode_int)
        self._apply_current(None)
        self._apply_mode(EditMode.INHIBIT)

    # ---- VM → view --------------------------------------------------------
    def _apply_current(self, ws: Optional[Worksheet]) -> None:
        if ws is None:
            self.edtAccept.clear()
            self.edtDeliver.clear()
            self.medical.clear()
            self.glasses.clear()
            self.price.clear()
            return
        from ..domain.dates import to_roc_date_string
        self.edtAccept.set_date_string(to_roc_date_string(ws.order_time))
        self.edtDeliver.set_date_string(to_roc_date_string(ws.deliver_time))
        self.medical.fill(ws)
        self.glasses.fill(ws)
        self.price.fill(ws)

    def _apply_mode_int(self, mode: int) -> None:
        self._apply_mode(EditMode(mode))

    def _apply_mode(self, mode: EditMode) -> None:
        editing = is_editable(mode)
        has_current = self._vm.current is not None

        if mode == EditMode.NONE:
            self.cmdAppend.setEnabled(True)
            self.cmdSave.setEnabled(False)
            self.cmdCancel.setEnabled(False)
            self.cmdModify.setEnabled(has_current)
            self.cmdRemove.setEnabled(has_current)
        else:
            self.cmdAppend.setEnabled(False)
            self.cmdRemove.setEnabled(False)
            self.cmdModify.setEnabled(False)
            if mode == EditMode.INHIBIT:
                self.cmdSave.setEnabled(False)
                self.cmdCancel.setEnabled(False)
            else:
                self.cmdSave.setEnabled(editing)
                self.cmdCancel.setEnabled(editing)

        self.medical.set_edit_mode(mode)
        self.glasses.set_edit_mode(mode)
        self.price.set_edit_mode(mode)
        self.edtAccept.set_edit_mode(mode)
        self.edtDeliver.set_edit_mode(mode)

        if mode in (EditMode.APPEND, EditMode.MODIFY):
            self.edtAccept.edtYear.setFocus()
            self.edtAccept.edtYear.selectAll()

    # ---- view → VM --------------------------------------------------------
    def _on_append_clicked(self) -> None:
        self._vm.start_append()

    def _on_modify_clicked(self) -> None:
        self._vm.start_modify()

    def _on_save_clicked(self) -> None:
        draft = self._collect()
        self._vm.save(draft)

    def _collect(self) -> Worksheet:
        ws = Worksheet(
            id=self._vm.current.id if self._vm.current else "",
            cid=self._vm.current.cid if self._vm.current else "",
            order_time=self.edtAccept.date(),
            deliver_time=self.edtDeliver.date(),
        )
        self.medical.apply_to(ws)
        self.glasses.apply_to(ws)
        self.price.apply_to(ws)
        return ws

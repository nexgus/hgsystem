# pylint: disable=no-name-in-module
import hgsystem as hg

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDateEdit
from PySide2.QtWidgets import QGridLayout
from PySide2.QtWidgets import QGroupBox
from PySide2.QtWidgets import QHBoxLayout
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QLineEdit
from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import QSpinBox
from PySide2.QtWidgets import QVBoxLayout
from PySide2.QtWidgets import QWidget
from widgets import MyDateWidget

#######################################################################################################################
class MedicalRecord(QGroupBox):
    def __init__(self):
        super(MedicalRecord, self).__init__()
        self.setFont(hg.FONT)
        self.setTitle('處方箋')

        """
        sph_r , sph_l ,
        cyl_r , cyl_l ,
        axis_r, axis_l,
        base_r, base_l,
        bcv_r , bcv_l ,
        bch_r , bch_l ,
        add_r , add_l ,
        pd, '
        source
        """
        txtRight = QLabel('OD/R', parent=self)
        txtLeft = QLabel('OS/L', parent=self)
        txtRight.setFont(hg.FONT)
        txtLeft.setFont(hg.FONT)

        txtSph = QLabel('SPH', parent=self)
        txtCyl = QLabel('CYL', parent=self)
        txtAxis = QLabel('AXIS', parent=self)
        txtBase = QLabel('BASE', parent=self)
        txtBC = QLabel('BC', parent=self)
        txtBCV = QLabel('BC.V', parent=self)
        txtBCH = QLabel('BC.H', parent=self)
        txtAdd = QLabel('ADD', parent=self)
        txtPd = QLabel('PD', parent=self)
        txtSource = QLabel('來源', parent=self)

        for obj in (txtSph, txtCyl, txtAxis, txtBase, txtBC, txtBCV, txtBCH, txtAdd, txtPd, txtSource):
            obj.setMaximumWidth(50)
            obj.setFont(hg.FONT)

        self.edtSource = QLineEdit(parent=self)
        self.edtSource.setFont(hg.FONT)
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
        for obj in (self.edtSphR, self.edtSphL, self.edtCylR, 
                    self.edtCylL, self.edtAxisR, self.edtAxisL, self.edtBaseR, self.edtBaseL, self.edtBCR, self.edtBCL, self.edtBCVR, 
                    self.edtBCVL, self.edtBCHR, self.edtBCHL, self.edtAddR, self.edtAddL, self.edtPd):
            obj.setAlignment(Qt.AlignHCenter)
            obj.setFont(hg.FONT)

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
        layout.addWidget(txtRight,          0, 1, Qt.AlignHCenter)
        layout.addWidget(txtLeft,           0, 2, Qt.AlignHCenter)
        layout.addWidget(txtSph,            1, 0)
        layout.addWidget(txtCyl,            2, 0)
        layout.addWidget(txtAxis,           3, 0)
        layout.addWidget(txtBase,           4, 0)
        layout.addWidget(txtBC,             5, 0)
        layout.addWidget(txtBCV,            6, 0)
        layout.addWidget(txtBCH,            7, 0)
        layout.addWidget(txtAdd,            8, 0)
        layout.addWidget(txtPd,             9, 0)
        layout.addWidget(txtSource,        10, 0)
        layout.addWidget(self.edtSphR,      1, 1)
        layout.addWidget(self.edtSphL,      1, 2)
        layout.addWidget(self.edtCylR,      2, 1)
        layout.addWidget(self.edtCylL,      2, 2)
        layout.addWidget(self.edtAxisR,     3, 1)
        layout.addWidget(self.edtAxisL,     3, 2)
        layout.addWidget(self.edtBaseR,     4, 1)
        layout.addWidget(self.edtBaseL,     4, 2)
        layout.addWidget(self.edtBCR,       5, 1)
        layout.addWidget(self.edtBCL,       5, 2)
        layout.addWidget(self.edtBCVR,      6, 1)
        layout.addWidget(self.edtBCVL,      6, 2)
        layout.addWidget(self.edtBCHR,      7, 1)
        layout.addWidget(self.edtBCHL,      7, 2)
        layout.addWidget(self.edtAddR,      8, 1)
        layout.addWidget(self.edtAddL,      8, 2)
        layout.addWidget(self.edtPd,        9, 1, 1, 2)
        layout.addWidget(self.edtSource,   10, 1, 1, 2)
        self.setLayout(layout)

        self._edits = (self.edtSphR, self.edtSphL, self.edtCylR, self.edtCylL, 
                       self.edtAxisR, self.edtAxisL, self.edtBaseR, self.edtBaseL, 
                       self.edtBCR, self.edtBCL, self.edtBCVR, self.edtBCVL, 
                       self.edtBCHR, self.edtBCHL, self.edtAddR, self.edtAddL, 
                       self.edtPd, self.edtSource)

    def clear(self):
        for obj in self._edits:
            obj.clear()

    def getContents(self):
        contents = []
        for obj in self._edits:
            contents.append(obj.text().strip())
        return tuple(contents)

    def setContents(self, contents):
        for obj, text in zip(self._edits, contents):
            obj.setText(text)

    def setEditMode(self, mode):
        stylesheet = hg.EditMode.stylesheetQLineEdit(mode)
        self.setStyleSheet(stylesheet)
        for obj in self._edits:
            obj.setEnabled(hg.EditMode.editing[mode])

#######################################################################################################################
class GlassesRecord(QGroupBox):
    def __init__(self):
        super(GlassesRecord, self).__init__()
        self.setFont(hg.FONT)
        self.setTitle('眼鏡資料')

        txtRight = QLabel('OD/R')
        txtLeft = QLabel('OS/L')
        txtRight.setFont(hg.FONT)
        txtLeft.setFont(hg.FONT)

        txtSightSee = QLabel('視力')
        txtLens = QLabel('鏡片')
        txtGlasses = QLabel('鏡架')
        txtMemo = QLabel('備註')
        for obj in (txtSightSee, txtLens, txtGlasses, txtMemo):
            obj.setFixedWidth(50)
            obj.setFont(hg.FONT)

        self.edtSightSeeR = QLineEdit()
        self.edtSightSeeL = QLineEdit()
        self.edtLensR = QLineEdit()
        self.edtLensL = QLineEdit()
        self.edtGlasses = QLineEdit()
        self.edtMemo = QLineEdit()

        for obj in (self.edtSightSeeR, self.edtSightSeeL):
            obj.setAlignment(Qt.AlignHCenter)
        for obj in (self.edtSightSeeR, self.edtSightSeeL, self.edtLensR, self.edtLensL, self.edtGlasses, self.edtMemo):
            obj.setFont(hg.FONT)

        layout = QGridLayout()
        layout.addWidget(txtRight,          0, 1, Qt.AlignHCenter)
        layout.addWidget(txtLeft,           0, 2, Qt.AlignHCenter)
        layout.addWidget(txtSightSee,       1, 0)
        layout.addWidget(txtLens,           2, 0)
        layout.addWidget(txtGlasses,        3, 0)
        layout.addWidget(txtMemo,           4, 0)
        layout.addWidget(self.edtSightSeeR, 1, 1)
        layout.addWidget(self.edtSightSeeL, 1, 2)
        layout.addWidget(self.edtLensR,     2, 1)
        layout.addWidget(self.edtLensL,     2, 2)
        layout.addWidget(self.edtGlasses,   3, 1, 1, 2)
        layout.addWidget(self.edtMemo,      4, 1, 1, 2)
        layout.setRowStretch(5, 1)
        self.setLayout(layout)
        self._createConnection()

        self._edits = (self.edtSightSeeR, self.edtSightSeeL, self.edtLensR, self.edtLensL, self.edtGlasses, self.edtMemo)

    def _createConnection(self):
        pass

    def clear(self):
        for obj in self._edits:
            obj.clear()

    def getContents(self):
        contents = []
        for obj in self._edits:
            contents.append(obj.text().strip())
        return tuple(contents)

    def setContents(self, contents):
        for obj, text in zip(self._edits, contents):
            obj.setText(text)

    def setEditMode(self, mode):
        stylesheet = hg.EditMode.stylesheetQLineEdit(mode)
        self.setStyleSheet(stylesheet)
        for obj in self._edits:
            obj.setEnabled(hg.EditMode.editing[mode])

#######################################################################################################################
class PriceRecord(QGroupBox):
    def __init__(self):
        super(PriceRecord, self).__init__()
        self.setFont(hg.FONT)
        self.setTitle('金額')

        txtLens = QLabel('鏡片')
        txtGlasses = QLabel('鏡架')
        txtTotal = QLabel('合計')
        for obj in (txtLens, txtGlasses, txtTotal):
            obj.setFixedWidth(40)
            obj.setFont(hg.FONT)
        self.edtGlasses = QSpinBox()
        self.edtLensR = QSpinBox()
        for obj in (self.edtGlasses, self.edtLensR):
            obj.setRange(0, 100000000)
            obj.setAlignment(Qt.AlignRight)
            obj.setFont(hg.FONT)
        self.edtTotal = QLineEdit()
        self.edtTotal.setAlignment(Qt.AlignRight)
        self.edtTotal.setAlignment(Qt.AlignRight)
        self.edtTotal.setReadOnly(True)
        self.edtTotal.setFont(hg.FONT)

        layout = QGridLayout()
        layout.addWidget(txtLens,         1, 0)
        layout.addWidget(txtGlasses,      2, 0)
        layout.addWidget(txtTotal,        3, 0)
        layout.addWidget(self.edtLensR,   1, 1, 1, 2)
        layout.addWidget(self.edtGlasses, 2, 1, 1, 2)
        layout.addWidget(self.edtTotal,   3, 1, 1, 2)
        self.setLayout(layout)
        self._createConnection()

        self._edits = (self.edtLensR, self.edtGlasses)

        self.calculateTotal()

    def _createConnection(self):
        self.edtGlasses.valueChanged.connect(self.calculateTotal)
        self.edtLensR.valueChanged.connect(self.calculateTotal)

    def calculateTotal(self, dontCare=None):
        total = 0
        for obj in self._edits:
            total = total + obj.value()
        self.edtTotal.setText(str(total))

    def clear(self):
        for obj in self._edits:
            obj.setValue(0)

    def getContents(self):
        contents = []
        for obj in self._edits:
            contents.append(obj.value())
        return tuple(contents)

    def setContents(self, contents):
        for obj, val in zip(self._edits, contents):
            obj.setValue(val)

    def setEditMode(self, mode):
        stylesheet = hg.EditMode.stylesheetQLineEdit(mode)
        self.setStyleSheet(stylesheet)
        for obj in self._edits:
            obj.setEnabled(hg.EditMode.editing[mode])
            obj.lineEdit().setStyleSheet(stylesheet)
        self.edtTotal.setEnabled(hg.EditMode.editing[mode])

#######################################################################################################################
class WorkSheet(QGroupBox):
    def __init__(self):
        super(WorkSheet, self).__init__()
        self.setFont(hg.FONT)
        self.setTitle('配鏡資料')
        self._beforeEdit = {'wid': '', 'cid': ''}
        self._wid = ''
        self._cid = ''

        txtAcceptDate = QLabel('收件日')
        #txtAcceptDate.setFixedWidth(50)
        txtAcceptDate.setFont(hg.FONT)
        self.edtAccept = MyDateWidget()
        layoutAccept = QHBoxLayout()
        layoutAccept.addWidget(txtAcceptDate)
        layoutAccept.addWidget(self.edtAccept)
        layoutAccept.addStretch()

        txtDeliverDate = QLabel('交件日')
        #txtDeliverDate.setFixedWidth(50)
        txtDeliverDate.setFont(hg.FONT)
        self.edtDeliver = MyDateWidget()
        layoutDeliver = QHBoxLayout()
        layoutDeliver.addWidget(txtDeliverDate)
        layoutDeliver.addWidget(self.edtDeliver)
        layoutDeliver.addStretch()

        self.cmdAppend = QPushButton('(&N) 新增')
        self.cmdModify = QPushButton('(&E) 修改')
        self.cmdRemove = QPushButton('(&D) 刪除')
        self.cmdSave   = QPushButton('(&S) 儲存')
        self.cmdCancel = QPushButton('(&C) 取消')
        for obj in (self.cmdAppend, self.cmdModify, self.cmdRemove, self.cmdSave, self.cmdCancel):
            obj.setFont(hg.FONT)
        layoutControl  = QHBoxLayout()
        layoutControl.addWidget(self.cmdAppend)
        layoutControl.addWidget(self.cmdModify)
        layoutControl.addWidget(self.cmdSave)
        layoutControl.addWidget(self.cmdCancel)
        layoutControl.addWidget(self.cmdRemove)

        self.medicalRecord = MedicalRecord()
        self.glassesRecord = GlassesRecord()
        self.priceRecord = PriceRecord()

        layout = QGridLayout()
        layout.setColumnMinimumWidth(1, 20)
        layout.addLayout(layoutAccept,  0, 0)
        layout.addLayout(layoutDeliver, 0, 2)
        # row, column, rowSpan, columnSpan
        layout.addWidget(self.medicalRecord,   1, 0, 2, 1)
        layout.addWidget(self.glassesRecord,   1, 2, 1, 1)
        layout.addWidget(self.priceRecord,     2, 2, 1, 1)
        layout.addLayout(layoutControl,        3, 0, 1, 3)

        self.setLayout(layout)
        self._createConnection()

    def _createConnection(self):
        pass

    def clear(self):
        self._wid = ''
        self._cid = ''
        self.edtAccept.clear()
        self.edtDeliver.clear()
        self.medicalRecord.clear()
        self.glassesRecord.clear()
        self.priceRecord.clear()

    def getBeforeEdit(self):
        return self._beforeEdit

    def getContents(self):
        date = (self.edtAccept.dateString(), self.edtDeliver.dateString())
        medicalRecord = self.medicalRecord.getContents()
        glassesRecord = self.glassesRecord.getContents()
        priceRecord   = self.priceRecord.getContents()
        return self._wid, self._cid, date, medicalRecord, glassesRecord, priceRecord

    def getContentsEx(self):
        return {
            "_id": self._wid,
            "cid": self._cid,
            "order_time": hg.toPythonDatetime(self.edtAccept.dateString()),
            "deliver_time": hg.toPythonDatetime(self.edtDeliver.dateString()),
            "sph_r": self.medicalRecord.edtSphR.text().strip(),
            "sph_l": self.medicalRecord.edtSphL.text().strip(),
            "cyl_r": self.medicalRecord.edtCylR.text().strip(),
            "cyl_l": self.medicalRecord.edtCylL.text().strip(),
            "axis_r": self.medicalRecord.edtAxisR.text().strip(),
            "axis_l": self.medicalRecord.edtAxisL.text().strip(),
            "base_r": self.medicalRecord.edtBaseR.text().strip(),
            "base_l": self.medicalRecord.edtBaseL.text().strip(),
            "bc_r": self.medicalRecord.edtBCR.text().strip(),
            "bc_l": self.medicalRecord.edtBCL.text().strip(),
            "bcv_r": self.medicalRecord.edtBCVR.text().strip(),
            "bcv_l": self.medicalRecord.edtBCVL.text().strip(),
            "bch_r": self.medicalRecord.edtBCHR.text().strip(),
            "bch_l": self.medicalRecord.edtBCHL.text().strip(),
            "add_r": self.medicalRecord.edtAddR.text().strip(),
            "add_l": self.medicalRecord.edtAddL.text().strip(),
            "pd": self.medicalRecord.edtPd.text().strip(),
            "source": self.medicalRecord.edtSource.text().strip(),
            "eyesight_r": self.glassesRecord.edtSightSeeR.text().strip(),
            "eyesight_l": self.glassesRecord.edtSightSeeL.text().strip(),
            "lens_r": self.glassesRecord.edtLensR.text().strip(),
            "lens_l": self.glassesRecord.edtLensL.text().strip(),
            "frame": self.glassesRecord.edtGlasses.text().strip(),
            "memo": self.glassesRecord.edtMemo.text().strip(),
            "lens_price": self.priceRecord.edtLensR.value(),
            "frame_price": self.priceRecord.edtGlasses.value()
        }

    def getWID(self):
        return self._wid

    def setContents(self, wid, cid, date, medicalRecord, glassesRecord, priceRecord):
        self._wid = wid
        self._cid = cid
        self.edtAccept.setDateString(date[0])   # 收件日
        self.edtDeliver.setDateString(date[1])  # 交件日
        self.medicalRecord.setContents(medicalRecord)
        self.glassesRecord.setContents(glassesRecord)
        self.priceRecord.setContents(priceRecord)

    def setEditMode(self, mode):
        if not hg.EditMode.inRange(mode): raise ValueError('Invalid edit mode ({})'.format(mode))

        if mode == hg.EditMode.append or mode == hg.EditMode.modify or mode == hg.EditMode.inhibit:
            self._beforeEdit['wid'] = self._wid
            self._beforeEdit['cid'] = self._cid
            if mode == hg.EditMode.append or mode == hg.EditMode.inhibit: self.clear()

        if mode == hg.EditMode.none:
            self.cmdAppend.setEnabled(True)
            self.cmdSave.setEnabled(False)
            self.cmdCancel.setEnabled(False)
            if self._wid == '':
                self.cmdModify.setEnabled(False)
                self.cmdRemove.setEnabled(False)
            else:
                self.cmdModify.setEnabled(True)
                self.cmdRemove.setEnabled(True)
        else:
            self.cmdAppend.setEnabled(False)
            self.cmdRemove.setEnabled(False)
            self.cmdModify.setEnabled(False)
            if mode == hg.EditMode.inhibit:
                self.cmdSave.setEnabled(False)
                self.cmdCancel.setEnabled(False)
            else:
                self.cmdSave.setEnabled(hg.EditMode.editing[mode])
                self.cmdCancel.setEnabled(hg.EditMode.editing[mode])

        for obj in (self.medicalRecord, self.glassesRecord, self.priceRecord, self.edtAccept, self.edtDeliver):
            obj.setEditMode(mode)

    def setCID(self, cid):
        self._cid = cid

    def setWID(self, wid):
        self._wid = wid

    def unwrap(self, record):
        wid           = record[0]
        cid           = record[1]
        date          = record[2:4]
        medicalRecord = record[4:20]
        glassesRecord = record[20:-2]
        priceRecord   = record[-2:]
        return wid, cid, date, medicalRecord, glassesRecord, priceRecord

    def wrap(self, wid, cid, date, medicalRecord, glassesRecord, priceRecord):
        record = ([wid, cid, date[0], date[1]] + 
                  list(medicalRecord) + 
                  list(glassesRecord) + 
                  [str(price) for price in priceRecord])
        return record

    def wrapEx(self, doc):
        return [
            doc["_id"],
            doc["cid"],
            hg.toROCDateString(doc["order_time"]),
            hg.toROCDateString(doc["deliver_time"]),
            doc["sph_r"],
            doc["sph_l"],
            doc["cyl_r"],
            doc["cyl_l"],
            doc["axis_r"],
            doc["axis_l"],
            doc["base_r"],
            doc["base_l"],
            doc["bc_r"],
            doc["bc_l"],
            doc["bcv_r"],
            doc["bcv_l"],
            doc["bch_r"],
            doc["bch_l"],
            doc["add_r"],
            doc["add_l"],
            doc["pd"],
            doc["source"],
            doc["eyesight_r"],
            doc["eyesight_l"],
            doc["lens_r"],
            doc["lens_l"],
            doc["frame"],
            doc["memo"],
            str(doc["lens_price"]),
            str(doc["frame_price"])
        ]


#######################################################################################################################
if __name__ == '__main__':
    from PySide2.QtWidgets import QApplication
    app = QApplication([])
    gui = WorkSheet()
    gui.show()
    app.exec_()
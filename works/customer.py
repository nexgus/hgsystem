# pylint: disable=no-name-in-module
import hgsystem as hg
import inspect

from datetime import datetime
from PySide2.QtCore import Qt
from PySide2.QtCore import QEvent
from PySide2.QtGui import QBrush
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QAbstractItemView
from PySide2.QtWidgets import QDialog
from PySide2.QtWidgets import QGridLayout
from PySide2.QtWidgets import QGroupBox
from PySide2.QtWidgets import QHBoxLayout
from PySide2.QtWidgets import QHeaderView
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QLineEdit
from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem
from PySide2.QtWidgets import QVBoxLayout
from PySide2.QtWidgets import QWidget
from widgets import MyDateWidget
from widgets import MyLineEdit

##############################################################################################################
class Customer(QWidget):
    def __init__(self):
        super(Customer, self).__init__()

        self.edit = Edit()
        self.history = History()

        layout = QGridLayout()
        layout.addWidget(self.edit,     0, 0)
        layout.addWidget(self.history,  0, 1)
        self.setLayout(layout)

##############################################################################################################
class Edit(QGroupBox):
    BlankDate = (0, 0, 0)

    def __init__(self):
        super(Edit, self).__init__()
        self._cid = ''
        self._total = 0
        self._beforeEdit = {
            'cid': ''
        }

        self.cmdAppend = QPushButton('(&A) 新增')
        self.cmdModify = QPushButton('(&M) 修改')
        self.cmdRemove = QPushButton('(&R) 刪除')
        self.cmdSearch = QPushButton('(&F) 搜尋')
        self.cmdSave   = QPushButton('(&S) 儲存')
        self.cmdCancel = QPushButton('(&C) 取消')
        layoutControl  = QHBoxLayout()
        layoutControl.addWidget(self.cmdSearch)
        layoutControl.addWidget(self.cmdModify)
        layoutControl.addWidget(self.cmdSave)
        layoutControl.addWidget(self.cmdCancel)
        layoutControl.addWidget(self.cmdRemove)
        layoutControl.addWidget(self.cmdAppend)

        txtName = QLabel('姓名')
        txtAddr = QLabel('地址')
        txtPhone = QLabel('電話')
        txtBirthdate = QLabel('生日')
        txtBroker = QLabel('介紹人')
        for obj in (txtName, txtAddr, txtPhone, txtBirthdate, txtBroker):
            obj.setFixedWidth(45)
        self.edtName   = QLineEdit()
        self.edtTitle  = QLineEdit()
        self.edtAddr   = QLineEdit()
        self.edtPhone1 = QLineEdit()
        self.edtPhone2 = QLineEdit()
        self.edtPhone3 = QLineEdit()
        self.edtPhone4 = QLineEdit()
        self.edtBirthdate = MyDateWidget()
        self.edtBroker = QLineEdit()

        layoutEdit = QGridLayout()
        layoutEdit.addWidget(txtName,        0, 0)
        layoutEdit.addWidget(txtAddr,        1, 0)
        layoutEdit.addWidget(txtPhone,       2, 0)
        layoutEdit.addWidget(txtBirthdate,   4, 0)
        layoutEdit.addWidget(txtBroker,      5, 0)
        layoutEdit.addWidget(self.edtName,   0, 1)
        layoutEdit.addWidget(self.edtTitle,  0, 2)
        layoutEdit.addWidget(self.edtAddr,   1, 1, 1, 2)
        layoutEdit.addWidget(self.edtPhone1, 2, 1)
        layoutEdit.addWidget(self.edtPhone2, 2, 2)
        layoutEdit.addWidget(self.edtPhone3, 3, 1)
        layoutEdit.addWidget(self.edtPhone4, 3, 2)
        layoutEdit.addWidget(self.edtBirthdate, 4, 1, 1, 2)
        layoutEdit.addWidget(self.edtBroker, 5, 1, 1, 2)

        layout = QVBoxLayout()
        layout.addLayout(layoutEdit)
        layout.addLayout(layoutControl)
        layout.addStretch()
        self.setLayout(layout)
        self.setTotalCount(0)
        self._createConnection()

        self._edits = (self.edtName, self.edtTitle, self.edtAddr, self.edtPhone1, 
                       self.edtPhone2, self.edtPhone3, self.edtPhone4, self.edtBirthdate, 
                       self.edtBroker)

    def _createConnection(self):
        self.edtName.returnPressed.connect(self.edtAddr.setFocus)
        self.edtAddr.returnPressed.connect(self.edtPhone1.setFocus)
        self.edtPhone1.returnPressed.connect(self.edtPhone2.setFocus)
        self.edtPhone2.returnPressed.connect(self.edtPhone3.setFocus)
        self.edtPhone3.returnPressed.connect(self.edtPhone4.setFocus)
        self.edtPhone4.returnPressed.connect(self.edtBirthdate.edtYear.setFocus)
        #self.edtBirthdate.returnPressed.connect(self.edt)
        #self.edtBroker.returnPressed.connect(self.edt)

    def clear(self):
        self._cid = ''
        for obj in self._edits:
            obj.clear()

    def getBeforeEdit(self):
        return self._beforeEdit

    def getCID(self):
        return self._cid

    def getContents(self, mergePhoneString=False):
        cid   = self._cid
        name  = self.edtName.text().strip()
        title = self.edtTitle.text().strip()
        addr  = self.edtAddr.text().strip()
        date = self.edtBirthdate.date()
        birthdate = f"{date.year}/{date.month}/{date.day}"
        phone1 = self.edtPhone1.text().strip()
        phone2 = self.edtPhone2.text().strip()
        phone3 = self.edtPhone3.text().strip()
        phone4 = self.edtPhone4.text().strip()
        broker = self.edtBroker.text().strip()
        if mergePhoneString:
            phones = ';'.join([phone1, phone2, phone3, phone4])
            return cid, name, title, birthdate, phones, addr, broker
        else:
            return cid, name, title, birthdate, phone1, phone2, phone3, phone4, addr, broker

    def getTotalCount(self):
        return self._total

    def setCID(self, cid):
        self._cid = cid

    def setContents(self, cid='', name='', title='', birthdate=(0, 0, 0), phones=('', '', '', ''), addr='', broker=''):
        calframe = inspect.getouterframes(inspect.currentframe(), 2)
        print(f"caller: {calframe[1][3]}")
        self._cid = cid
        self.edtName.setText(name)
        self.edtTitle.setText(title)
        self.edtAddr.setText(addr)
        self.edtPhone1.setText(phones[0])
        self.edtPhone2.setText(phones[1])
        self.edtPhone3.setText(phones[2])
        self.edtPhone4.setText(phones[3])
        if isinstance(birthdate, str):
            self.edtBirthdate.setDateString(birthdate)
        else:
            year, month, day = birthdate
            self.edtBirthdate.setDate(year, month, day)
        self.edtBroker.setText(broker)

    def setContentsEx(self, customer):
        self._cid = customer["_id"]
        self.edtName.setText(customer["name"])
        self.edtTitle.setText(customer["title"])
        self.edtAddr.setText(customer["addr"])

        phones = customer["phones"].split(";")
        while len(phones) < 4:
            phones.append("")
        self.edtPhone1.setText(phones[0])
        self.edtPhone2.setText(phones[1])
        self.edtPhone3.setText(phones[2])
        self.edtPhone4.setText(phones[3])

        self.edtBirthdate.setDateString(hg.toROCDateString(customer["birthdate"]))
        self.edtBroker.setText(customer["broker"])

    def setEditMode(self, mode):
        if not hg.EditMode.inRange(mode): 
            raise ValueError(f"Invalid edit mode ({mode})")

        if mode == hg.EditMode.append or mode == hg.EditMode.modify:
            self._beforeEdit['cid'] = self._cid
            if mode == hg.EditMode.append: self.clear()

        if mode == hg.EditMode.none:
            self.cmdAppend.setEnabled(True)
            self.cmdSave.setEnabled(False)
            self.cmdCancel.setEnabled(False)
            if self._total > 0:
                self.cmdSearch.setEnabled(True)
            else:
                self.cmdSearch.setEnabled(False)
            if self._cid == '':
                self.cmdModify.setEnabled(False)
                self.cmdRemove.setEnabled(False)
            else:
                self.cmdModify.setEnabled(True)
                self.cmdRemove.setEnabled(True)
        else:
            self.cmdAppend.setEnabled(False)
            self.cmdRemove.setEnabled(False)
            self.cmdModify.setEnabled(False)
            self.cmdSearch.setEnabled(False)
            if mode == hg.EditMode.inhibit:
                self.cmdSave.setEnabled(False)
                self.cmdCancel.setEnabled(False)
            else:
                self.cmdSave.setEnabled(hg.EditMode.editing[mode])
                self.cmdCancel.setEnabled(hg.EditMode.editing[mode])

        for obj in self._edits:
            if obj == self.edtBirthdate: obj.setEditMode(mode)
            obj.setEnabled(hg.EditMode.editing[mode])

        stylesheet = hg.EditMode.stylesheetQLineEdit(mode)
        self.setStyleSheet(stylesheet)

    def setTotalCount(self, total):
        self.setTitle('客戶資料 (共有 {} 筆紀錄)'.format(total))
        self._total = total

##############################################################################################################
class History(QTableWidget):
    HEADERS = ['wid', 'cid', '收件日', '交件日', 'SPH(R)', 'SPH(L)', 'CYL(R)', 'CYL(L)', 
               'AXIS(R)', 'AXIS(L)', 'BASE(R)', 'BASE(L)', 'BC.V(R)', 'BC.V(L)', 'BC.H(R)', 'BC.H(L)', 
               'ADD(R)', 'ADD(L)', 'PD', 'source', '視力(R)', '視力(L)', '鏡片(R)', '鏡片(L)', '鏡架', 'memo',
               'priceLens', 'priceFrame']
    _isFrozen = False

    def __init__(self):
        super(History, self).__init__()

        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        header = self.horizontalHeader()
        for idx in range(len(self.HEADERS)-1):
            header.setSectionResizeMode(idx, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(len(self.HEADERS)-1, QHeaderView.Stretch)
        for hiddenHeader in ('cid', 'wid', 'AXIS(R)', 'AXIS(L)', 'BASE(R)', 'BASE(L)', 'BC.V(R)', 'BC.V(L)', 
                             'BC.H(R)', 'BC.H(L)', 'ADD(R)', 'ADD(L)', 'PD', 'source', 'memo', 
                             'priceLens', 'priceFrame'):
            self.setColumnHidden(self.HEADERS.index(hiddenHeader), True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setWordWrap(False)

        self._createConnection()

    def _createConnection(self):
        self.currentCellChanged.connect(self.tableCurrentCellChanged)

    def append(self, record):
        """Append a record to History.

        Args:
            record (dict): A document from a MongoDB collection.
        """
        record_ = [
            record["_id"], record["cid"], 
            hg.toROCDateString(record["order_time"]), hg.toROCDateString(record["deliver_time"]),
            record["sph_r"], record["sph_l"], record["cyl_r"], record["cyl_l"],
            record["axis_r"], record["axis_l"], record["base_r"], record["base_l"],
            record["bcv_r"], record["bcv_l"], record["bch_r"], record["bch_l"],
            record["add_r"], record["add_l"], record["pd"], record["source"],
            record["sight_see_r"], record["sight_see_r"], record["lens_r"], record["lens_l"],
            record["frame"], record["memo"], str(record["lens_price"]), str(record["frame_price"]),
        ]
        row = self.rowCount()
        self.insertRow(row)
        self.setRowItems(row, record_)

    def freeze(self, isFrozen):
        self._isFrozen = isFrozen
        if isFrozen:
            self.installEventFilter(self)
        else:
            self.removeEventFilter(self)

    def getIDByRow(self, row):
        if row >= 0 and row < self.rowCount():
            return self.item(row, self.HEADERS.index('wid')).text()
        else:
            return ''

    def getRowContents(self, row):
        """Return the current row values.

        Args:
            row (int): Row number/index (starts from 0).

        Returns:
            tuple: The row content in table header sequence.
        """
        record = [self.item(row, idx).text() for idx in range(len(self.HEADERS))]
        record[-2] = int(record[-2])  # lens_price
        record[-1] = int(record[-1])  # frame_price
        return tuple(record)

    def getRowByID(self, wid):
        row = -1
        matchItems = self.findItems(wid, Qt.MatchFixedString) # Qt.MatchFixedString, Qt.MatchExactly
        if len(matchItems) > 0:
            row = self.row(matchItems[0])
        return row

    def remove(self, wid):
        row = self.getRowByID(wid)
        if row >= 0:
            self.removeRow(row)
        return row

    def setRowHighLight(self, row, isHighLight):
        if row < 0: return
        if isHighLight:
            foregroundColor = QColor('white')
            backgroundColor = QColor('cornflowerblue')
        else:
            foregroundColor = QColor('black')
            backgroundColor = QColor('white')
        for col in range(len(self.HEADERS)):
            item = self.item(row, col)
            item.setForeground(QBrush(foregroundColor))
            item.setBackground(QBrush(backgroundColor))

    def setCurrentRow(self, row):
        if row < 0: return
        col = self.currentColumn()
        if col < 0: col = 0
        self.setCurrentCell(row, col)

    def setCurrentRowByID(self, pid):
        row = self.getRowByID(pid)
        self.setCurrentRow(row)

    def setRowItems(self, row, items):
        if len(items) > len(self.HEADERS):
            items = items[:len(self.HEADERS)]
        for col, item in enumerate(items):
            tableWidgetItem = QTableWidgetItem(item)
            self.setItem(row, col, tableWidgetItem)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            return True
        elif event.type() == QEvent.Type.MouseButtonPress:
            return True
        else:
            return QWidget.eventFilter(self, obj, event)

    def tableCurrentCellChanged(self, curRow, curCol, prvRow=-1, prvCol=-1):
        if prvRow > -1:
            self.setRowHighLight(prvRow, False)
        if curRow > -1:
            self.setRowHighLight(curRow, True)

    def mousePressEvent(self, event):
        if not self._isFrozen:
            QTableWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if not self._isFrozen:
            QTableWidget.mousePressEvent(self, event)

#######################################################################################################################
class TableWidget(QTableWidget):
    HEADERS = ['cid', '姓名', 'title', '生日', '電話', '住址', 'broker']
    _isFrozen = False

    def __init__(self):
        super(TableWidget, self).__init__()

        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        header = self.horizontalHeader()
        for idx in range(len(self.HEADERS)-1):
            header.setSectionResizeMode(idx, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(len(self.HEADERS)-1, QHeaderView.Stretch)
        for hiddenHeader in ('cid', 'title', 'broker'):
            self.setColumnHidden(self.HEADERS.index(hiddenHeader), True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setWordWrap(False)

        self._createConnection()

    def _createConnection(self):
        self.currentCellChanged.connect(self.tableCurrentCellChanged)

    def _splitBirthdate(self, birthdate):
        """
        split a birthdate string
        return: year, month, day in integer
        """
        birthdate = birthdate.split('/')
        lenBirthdate = len(birthdate)
        year, month, day = 0, 0, 0
        if lenBirthdate == 2:
            month = int(birthdate[0])
            day   = int(birthdate[1])
        elif lenBirthdate == 3:
            year  = int(birthdate[0])
            month = int(birthdate[1])
            day   = int(birthdate[2])
        return year, month, day

    def _splitPhones(self, phones):
        """
        split the phone string
        return: four phone strings
        """
        phones_ = phones.split(';')
        for _ in range(4-len(phones_)):
            phones_.append('')
        return tuple(phones_)

    def _mergeBirthdate(self, birthdate):
        """
        merge a three-integer-tuple/list to a string
        """
        year, month, day = birthdate
        if month == 0 or day == 0:
            return ''
        elif year == 0:
            return '{:02d}/{:02d}'.format(month, day)
        else:
            return '{}/{:02d}/{:02d}'.format(year%10000, month, day)

    def _mergePhones(self, phones):
        """
        merge a phone list/tuple to a string
        """
        phones = list(phones)
        return ';'.join(phones)

    def append(self, customer):
        row = self.rowCount()
        self.insertRow(row)
        items = (
            customer["_id"],
            customer["name"],
            customer["title"],
            hg.toROCDateString(customer["birthdate"]),
            customer["phones"],
            customer["addr"],
            customer["broker"],
        )
        self.setRowItems(row, items)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            return True
        elif event.type() == QEvent.Type.MouseButtonPress:
            return True
        else:
            return QWidget.eventFilter(self, obj, event)

    def freeze(self, isFrozen):
        self._isFrozen = isFrozen
        if isFrozen:
            self.installEventFilter(self)
        else:
            self.removeEventFilter(self)

    def getIDByRow(self, row):
        if row >= 0 and row < self.rowCount():
            return self.item(row, self.HEADERS.index('cid')).text()
        else:
            return ''

    def getRowByID(self, cid):
        row = -1
        matchItems = self.findItems(cid, Qt.MatchFixedString) # Qt.MatchFixedString, Qt.MatchExactly
        if len(matchItems) > 0:
            row = self.row(matchItems[0])
        return row

    def remove(self, cid):
        row = self.getRowByID(cid)
        if row >= 0:
            self.removeRow(row)
        return row

    def getRowContents(self, row):
        customer = list()
        for col in range(len(self.HEADERS)):
            customer.append(self.item(row, col).text())
        customer = tuple(customer)
        return customer

    def getRowContentsEx(self, row):
        return {
            "_id": self.item(row, 0).text(),
            "name": self.item(row, 1).text(),
            "title": self.item(row, 2).text(),
            "birthdate": hg.toPythonDatetime(self.item(row, 3).text()),
            "phones": self.item(row, 4).text(),
            "addr": self.item(row, 5).text(),
            "broker": self.item(row, 6).text(),
        }

    def setCurrentRow(self, row):
        if row < 0: return
        col = self.currentColumn()
        if col < 0: col = 0
        self.setCurrentCell(row, col)

    def setCurrentRowByID(self, cid):
        row = self.getRowByID(cid)
        self.setCurrentRow(row)

    def setRowHighLight(self, row, isHighLight):
        if row < 0: return
        if isHighLight:
            foregroundColor = QColor('white')
            backgroundColor = QColor('cornflowerblue')
        else:
            foregroundColor = QColor('black')
            backgroundColor = QColor('white')
        for col in range(len(self.HEADERS)):
            item = self.item(row, col)
            item.setForeground(QBrush(foregroundColor))
            item.setBackground(QBrush(backgroundColor))

    def setRowItems(self, row, items):
        if len(items) > len(self.HEADERS):
            items = items[:len(self.HEADERS)]
        for col, item in enumerate(items):
            try:
                tableWidgetItem = QTableWidgetItem(item)
            except TypeError:
                # This sould be an bson.objectid.ObjectId instance.
                tableWidgetItem = QTableWidgetItem(item.__str__())
            self.setItem(row, col, tableWidgetItem)

    def tableCurrentCellChanged(self, curRow, curCol, prvRow=-1, prvCol=-1):
        if prvRow > -1:
            self.setRowHighLight(prvRow, False)
        if curRow > -1:
            self.setRowHighLight(curRow, True)

    def mousePressEvent(self, event):
        if not self._isFrozen:
            QTableWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if not self._isFrozen:
            QTableWidget.mousePressEvent(self, event)

##############################################################################################################
class Search(QDialog):
    def __init__(self, db, parent=None):
        super(Search, self).__init__(parent)
        self._db = db
        self._row = -1

        txtPhone = QLabel('電話')
        txtBirth = QLabel('生日')
        txtName = QLabel('姓名')
        txtAddr = QLabel('地址')
        for obj in (txtName, txtAddr, txtPhone, txtBirth):
            obj.setFixedWidth(40)
        self.edtName = MyLineEdit()
        self.edtAddr = QLineEdit()
        self.edtPhone = QLineEdit()
        self.edtBirthdate = MyDateWidget()
        self.cmdSearch = QPushButton('(&F) 搜尋')

        #self.cmdClrName = QPushButton('X')
        #self.cmdClrAddr = QPushButton('X')
        #self.cmdClrPhone = QPushButton('X')
        #self.cmdClrBirthdate = QPushButton('X')
        #for obj in (self.cmdClrName, self.cmdClrAddr, self.cmdClrPhone, self.cmdClrBirthdate):
        #    obj.setFixedWidth(15)

        layoutFilter = QGridLayout()
        layoutFilter.addWidget(txtPhone,             0, 0)
        layoutFilter.addWidget(txtBirth,             1, 0)
        layoutFilter.addWidget(txtName,              2, 0)
        layoutFilter.addWidget(txtAddr,              3, 0)
        layoutFilter.addWidget(self.edtPhone,        0, 1, 1, 2)
        layoutFilter.addWidget(self.edtBirthdate,    1, 1, 1, 2)
        layoutFilter.addWidget(self.edtName,         2, 1, 1, 2)
        layoutFilter.addWidget(self.edtAddr,         3, 1, 1, 2)
        #layoutFilter.addWidget(self.cmdClrPhone,     0, 3)
        #layoutFilter.addWidget(self.cmdClrBirthdate, 1, 3)
        #layoutFilter.addWidget(self.cmdClrName,      2, 3)
        #layoutFilter.addWidget(self.cmdClrAddr,      3, 3)
        layoutFilter.addWidget(self.cmdSearch,       5, 0, 1, 3)
        layoutFilter.setRowMinimumHeight(4, 20)

        self.table = TableWidget()
        self.table.freeze(False)
        self.cmdAccept = QPushButton('(&Y) 確定')
        self.cmdAccept.setEnabled(False)
        self.cmdCancel = QPushButton('(&N) 取消')

        layoutControl = QHBoxLayout()
        layoutControl.addWidget(self.cmdAccept)
        layoutControl.addWidget(self.cmdCancel)

        layout = QVBoxLayout()
        layout.addLayout(layoutFilter)
        layout.addWidget(self.table)
        layout.addLayout(layoutControl)
        self.setLayout(layout)
        self._create_connection()
        self.setWindowTitle('搜尋')
        self.setMinimumWidth(500)
        self.setWindowModality(Qt.ApplicationModal)

        self.setStyleSheet('QLineEdit {color: red; background: white;}')
        self.edtBirthdate.setEditMode(hg.EditMode.modify)

        self.edtPhone.setFocus()

    def _create_connection(self):
        self.table.itemDoubleClicked.connect(self.tableDoubleClicked)
        self.cmdSearch.clicked.connect(self.search)
        self.cmdAccept.clicked.connect(self.accept)
        self.cmdCancel.clicked.connect(self.reject)
        #self.cmdClrName.clicked.connect(self.edtName.clear)
        #self.cmdClrAddr.clicked.connect(self.edtAddr.clear)
        #self.cmdClrPhone.clicked.connect(self.edtPhone.clear)
        #self.cmdClrBirthdate.clicked.connect(self.edtBirthdate.clear)

    def search(self):
        self.cmdAccept.setEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(0)

        
        filter_ = dict()
        if len(self.edtName.text()) > 0:
            filter_["name"] = {"$regex": f".*{self.edtName.text()}.*"}
        if len(self.edtAddr.text()) > 0:
            filter_["addr"] = {"$regex": f".*{self.edtAddr.text()}.*"}
        if len(self.edtPhone.text()) > 0:
            filter_["phones"] = {"$regex": f".*{self.edtPhone.text()}.*"}
        if self.edtBirthdate.dateString() != "0/00/00":
            filter_["birthdate"] = self.edtBirthdate.date()
        customers = self._db.customers.find(
            filter=filter_,
            allow_disk_use=True
        )

        for customer in customers:
            self.table.append(customer)

        if self.table.rowCount() > 0:
            self.table.setCurrentCell(0, 0)
            self.cmdAccept.setEnabled(True)
            self.table.setFocus()
        else:
            self.cmdAccept.setEnabled(False)
            self.edtPhone.setFocus()

    def tableDoubleClicked(self, item):
        self.cmdAccept.click()

##############################################################################################################
if __name__ == '__main__':
    from PySide2.QtWidgets import QApplication
    app = QApplication([])
    gui = Customer()
    gui.show()
    app.exec_()

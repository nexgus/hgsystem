# pylint: disable=no-name-in-module
import customer as cust
import hgsystem as hg
import worksheet as ws

from bson.objectid import ObjectId
from copy import deepcopy
from datetime import datetime
from PySide2.QtWidgets import QDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QVBoxLayout
from PySide2.QtWidgets import QWidget

####################################################################################################
class MainWidget(QWidget):
    def __init__(self, mongodb):
        super(MainWidget, self).__init__()

        self.db = mongodb.hgsystem
        self._isCustomerAppendMode = False
        self._isWorksheetAppendMode = False

        self.customer = cust.Customer()
        self.worksheet = ws.WorkSheet()
        self.customer.setFixedHeight(300)

        layout = QVBoxLayout()
        layout.addWidget(self.customer)
        layout.addWidget(self.worksheet)
        layout.addStretch()
        self.setLayout(layout)
        self._createConnection()

        customerCount = self.db.customers.count_documents({})
        self.customer.edit.setTotalCount(customerCount)
        self.customer.edit.setEditMode(hg.EditMode.none)
        self.worksheet.setEditMode(hg.EditMode.inhibit)
        if customerCount > 0:
            self.customer.edit.cmdSearch.setFocus()
        else:
            self.customer.edit.cmdAppend.setFocus()

    #-----------------------------------------------------------------------------------------------
    def _createConnection(self):
        self.customer.edit.cmdAppend.clicked.connect(self.customerAppend)
        self.customer.edit.cmdModify.clicked.connect(self.customerModify)
        self.customer.edit.cmdRemove.clicked.connect(self.customerRemove)
        self.customer.edit.cmdSearch.clicked.connect(self.customerSearch)
        self.customer.edit.cmdSave.clicked.connect(self.customerSave)
        self.customer.edit.cmdCancel.clicked.connect(self.customerCancel)
        self.customer.history.currentCellChanged.connect(self.historyCurrentCellChanged)
        self.worksheet.cmdAppend.clicked.connect(self.worksheetAppend)
        self.worksheet.cmdModify.clicked.connect(self.worksheetModify)
        self.worksheet.cmdRemove.clicked.connect(self.worksheetRemove)
        self.worksheet.cmdSave.clicked.connect(self.worksheetSave)
        self.worksheet.cmdCancel.clicked.connect(self.worksheetCancel)

    #-----------------------------------------------------------------------------------------------
    def customerAppend(self):
        """Be triggered while the (客戶)新增 button is clicked."""
        hg.logger.debug("Append a new customer.")
        self._isCustomerAppendMode = True
        self.customer.edit.setEditMode(hg.EditMode.append)
        self.customer.history.setRowCount(0)
        self.worksheet.setEditMode(hg.EditMode.inhibit)
        self.customer.edit.edtName.setFocus()

    #-----------------------------------------------------------------------------------------------
    def customerCancel(self):
        """Be triggered while the (客戶)取消 button is clicked."""
        beforeEdit = self.customer.edit.getBeforeEdit()
        if beforeEdit['cid'] == '':
            self.customer.edit.clear()
            hg.logger.debug("Cancel customer append.")
        else:
            customer = self.db.customers.find_one({"_id": beforeEdit["cid"]})
            self.customer.edit.setContentsEx(customer)
            if self._isCustomerAppendMode:
                worksheets = self.db.worksheets.find(filter={"cid": customer["_id"]})
                for worksheet in worksheets:
                    self.customer.history.append(worksheet)
                self.customer.history.setCurrentRow(0)
                self._isCustomerAppendMode = False
            cid = self.customer.edit.getCID()
            name = self.customer.edit.edtName.text().strip()
            hg.logger.debug(f"Cancel customer modification: {cid}/{name}.")
        self.customer.edit.setEditMode(hg.EditMode.none)
        self.customer.history.freeze(False)
        if self.customer.history.rowCount() > 0:
            worksheet = self.customer.history.getRowContentsEx(0)
            self.worksheet.setContentsEx(worksheet)
        if self.customer.edit.getCID() == '':
            self.worksheet.setEditMode(hg.EditMode.inhibit)
        else:
            self.worksheet.setEditMode(hg.EditMode.none)
        self.customer.history.setFocus()

    #-----------------------------------------------------------------------------------------------
    def customerModify(self):
        """Be triggered while the (客戶)修改 button is clicked."""
        cid = self.customer.edit.getCID()
        name = self.customer.edit.edtName.text().strip()
        hg.logger.debug(f"Modify customer data: {cid}/{name}.")

        self.customer.edit.setEditMode(hg.EditMode.modify)
        self.customer.history.freeze(True)
        self.worksheet.setEditMode(hg.EditMode.inhibit)
        self.customer.edit.edtName.setFocus()

    #-----------------------------------------------------------------------------------------------
    def customerRemove(self):
        """Be triggered while the (客戶)刪除 button is clicked."""
        cid = self.customer.edit.getCID()

        worksheet_count = self.customer.history.rowCount()
        name = self.customer.edit.edtName.text().strip()
        birthdate = self.customer.edit.edtBirthdate.dateString()
        addr = self.customer.edit.edtAddr.text().strip()
        selection = QMessageBox.question(
            self, 
            f"刪除客戶 {cid}",
            f"<font size='+1'><b>確定要刪除該筆資料嗎?<br>這會將所有該客戶的紀錄刪除 "
            f"(共 {worksheet_count} 筆), 無法復原!<br>姓名: {name}<br>生日: {birthdate}<br>"
            f"地址: {addr}</b></font>",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)
        if selection == QMessageBox.StandardButton.No: return

        result = self.db.customers.delete_one({"_id": cid})
        result = self.db.worksheets.delete_many({"cid": cid})
        hg.logger.debug(f"Delete customer {cid}/{name} and {result.deleted_count} worksheet(s).")

        self.customer.edit.clear()
        self.customer.history.setRowCount(0)
        self.worksheet.clear()
        self.customer.edit.setTotalCount(self.db.customers.count_documents({}))
        self.customer.edit.setEditMode(hg.EditMode.none)
        self.worksheet.setEditMode(hg.EditMode.inhibit)

    #-----------------------------------------------------------------------------------------------
    def customerSave(self):
        data = self.customer.edit.getContents(mergePhoneString=True)
        cid, name, title, birthdate, phones, addr, broker = data
        if name == "":
            QMessageBox.critical(self, "輸入內容錯誤", "<font size='+1'><b>姓名不得為空白</b></font>")
            self.customer.edit.edtName.setFocus()
            return

        if self._isCustomerAppendMode:
            document = {
                "_id": ObjectId().__str__(),
                "name": name,
                "title": title,
                "birthdate": hg.toPythonDatetime(birthdate),
                "phones": phones,
                "addr": addr,
                "broker": broker,
            }
            # to-do: what if fail to write?
            self.db.customers.insert_one(document=document)
            hg.logger.debug(f"Append customer and save: {document}.")

            self.customer.edit.setCID(document['_id'])
            self.customer.history.setRowCount(0)
            self.customer.edit.setTotalCount(self.db.customers.count_documents({}))
            self._isCustomerAppendMode = False

        else:
            document = {
                "name": name,
                "title": title,
                "birthdate": hg.toPythonDatetime(birthdate),
                "phones": phones,
                "addr": addr,
                "broker": broker,
            }
            # to-do: what if fail to write?
            self.db.customers.find_one_and_replace(
                filter={"_id": cid},
                replacement=document,
            )
            hg.logger.debug(f"Edit customer and save: {document}.")

        self.customer.edit.setEditMode(hg.EditMode.none)
        self.customer.history.freeze(False)
        self.worksheet.setEditMode(hg.EditMode.none)
        self.customer.history.setFocus()

    #-----------------------------------------------------------------------------------------------
    def customerSearch(self):
        searcher = cust.Search(self.db, self)
        if searcher.exec_() == QDialog.Accepted:
            row = searcher.table.currentRow()
            if row < 0: return

            self.worksheet.clear()
            customer = searcher.table.getRowContentsEx(row)

            # Save search history
            if self.db.search.find_one(filter=customer['_id']) is None:
                self.db.search.insert_one(customer)

            self.customer.edit.setContentsEx(customer)

            self.customer.history.setRowCount(0)
            worksheets = self.db.worksheets.find(filter={"cid":customer['_id']})
            for worksheet in worksheets:
                self.customer.history.append(worksheet)
            self.customer.history.setCurrentRow(0)
            self.customer.edit.setEditMode(hg.EditMode.none)
            self.worksheet.setEditMode(hg.EditMode.none)
            self.customer.history.setFocus()

    #-----------------------------------------------------------------------------------------------
    def historyCurrentCellChanged(self, curRow, curCol, prvRow=-1, prvCol=-1):
        if curRow < 0: return
        worksheet = self.customer.history.getRowContentsEx(curRow)
        self.worksheet.setContentsEx(worksheet)

    #-----------------------------------------------------------------------------------------------
    def worksheetAppend(self):
        cid = self.customer.edit.getCID()
        name = self.customer.edit.edtName.text().strip()
        hg.logger.debug(f"Append a new worksheet for {cid}/{name}.")

        self.customer.edit.setEditMode(hg.EditMode.inhibit)
        self.customer.history.freeze(True)
        self.worksheet.setEditMode(hg.EditMode.append)
        self._isWorksheetAppendMode = True
        self.worksheet.edtAccept.edtYear.setFocus()
        self.worksheet.edtAccept.edtYear.selectAll()

    #-----------------------------------------------------------------------------------------------
    def worksheetCancel(self):
        beforeEdit = self.worksheet.getBeforeEdit()
        if beforeEdit['wid'] == '' or self.customer.history.rowCount() == 0:
            self.worksheet.clear()
            hg.logger.debug(f"Cancel worksheet append.")
        else:
            row = self.customer.history.currentRow()
            worksheet = self.customer.history.getRowContentsEx(row)
            self.worksheet.setContentsEx(worksheet)
            hg.logger.debug(f"Cancel worksheet modify.")
        
        self.customer.edit.setEditMode(hg.EditMode.none)
        self.customer.history.freeze(False)
        self.worksheet.setEditMode(hg.EditMode.none)
        self._isWorksheetAppendMode = False

    #-----------------------------------------------------------------------------------------------
    def worksheetModify(self):
        cid = self.customer.edit.getCID()
        name = self.customer.edit.edtName.text().strip()
        wid = self.worksheet.getWID()
        hg.logger.debug(f"Append a new worksheet for {cid}/{name}/{wid}.")

        self.customer.edit.setEditMode(hg.EditMode.inhibit)
        self.customer.history.freeze(True)
        self.worksheet.setEditMode(hg.EditMode.modify)
        self.worksheet.edtAccept.edtYear.setFocus()
        self.worksheet.edtAccept.edtYear.selectAll()

    #-----------------------------------------------------------------------------------------------
    def worksheetRemove(self):
        wid = self.worksheet.getWID()
        date1 = self.worksheet.edtAccept.dateString()
        date2 = self.worksheet.edtDeliver.dateString()
        selection = QMessageBox.question(
            self, 
            f"刪除工單 {wid}",
            f"<font size='+1'><b>確定要刪除該筆資料嗎?<br>收件日: {date1}<br>交件日: {date2}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)
        if selection == QMessageBox.StandardButton.No: return

        self.db.worksheets.delete_one({"_id": wid})
        row = self.customer.history.currentRow()
        self.customer.history.removeRow(row)
        if self.customer.history.rowCount() == 0:
            self.worksheet.clear()
        else:
            row = self.customer.history.currentRow()
            self.customer.history.tableCurrentCellChanged(row, 0)
            worksheet = self.customer.history.getRowContentsEx(row)
            self.worksheet.setContentsEx(worksheet)
        hg.logger.debug(f"Delete worksheet {wid}.")

        self.customer.edit.setEditMode(hg.EditMode.none)
        self.customer.history.freeze(False)
        self.worksheet.setEditMode(hg.EditMode.none)

    #-----------------------------------------------------------------------------------------------
    def worksheetSave(self):
        doc = self.worksheet.getContentsEx()
        if doc["order_time"] is None:
            QMessageBox.critical(self, "輸入內容錯誤", "收件日不得為空白")
            self.worksheet.edtAccept.edtYear.setFocus()
            self.worksheet.edtAccept.edtYear.selectAll()
            return

        name = self.customer.edit.edtName.text().strip()
        if self._isWorksheetAppendMode:
            doc['_id'] = ObjectId().__str__()
            doc['cid'] = self.customer.edit.getCID()
            self.db.worksheets.insert_one(doc)
            self.worksheet.setWID(doc['_id'])
            self.worksheet.setCID(doc['cid'])
            self.customer.history.append(doc)
            self.customer.history.setCurrentRow(self.customer.history.rowCount()-1)
            self._isWorksheetAppendMode = False
            hg.logger.debug(f"Append and save worksheet {doc['_id']} for {doc['cid']}/{name}")
        else:
            doc_ = deepcopy(doc)
            doc_.pop("_id")
            self.db.worksheets.find_one_and_replace(
                filter={"_id": doc["_id"]},
                replacement=doc_
            )
            row = self.customer.history.currentRow()
            self.customer.history.setRowItems(row, self.worksheet.wrapEx(doc))
            hg.logger.debug(f"Append and save worksheet {doc['_id']} for {doc['cid']}/{name}")

        self.customer.edit.setEditMode(hg.EditMode.none)
        self.customer.history.freeze(False)
        self.worksheet.setEditMode(hg.EditMode.none)
        self.customer.history.setFocus()

####################################################################################################
if __name__ == '__main__':
    from pymongo import MongoClient
    from PySide2.QtWidgets import QApplication

    mongo = MongoClient("localhost", 27017)
    app = QApplication([])
    gui = MainWidget(mongo)
    gui.show()
    app.exec_()
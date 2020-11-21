# pylint: disable=no-name-in-module
import hgsystem as hg

from main_widget import MainWidget
from pymongo import MongoClient
from PySide2.QtWidgets import QAction
from PySide2.QtWidgets import QMainWindow

####################################################################################################
class MainWindow(QMainWindow):
    def __init__(self, mongo_host="localhost", mongo_port=27017):
        super(MainWindow, self).__init__()
        self.setWindowTitle(f"豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統 ({hg.VER_STRING})")

        self.mongodb = MongoClient(mongo_host, mongo_port)
        self.setCentralWidget(MainWidget(self.mongodb))

        #self.createAction()
        #self.createMenu()

    def __del__(self):
        self.mongodb.close()

    #def createAction(self):
    #    self.actCustomerNew = QAction(
    #        '&New', self, triggered=self.centralWidget().customer.edit.cmdAppend.click)

    #def createMenu(self):
    #    self.menuCustomer = self.menuBar().addMenu('&Customer')
    #    self.menuCustomer.addAction(self.actCustomerNew)

####################################################################################################
if __name__ == "__main__":
    import argparse
    from PySide2.QtWidgets import QApplication

    parser = argparse.ArgumentParser(
        description="HG System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--version", action="version", version=f"HG System {hg.VER_STRING}")
    parser.add_argument("-H", "--host", default="localhost", help="MongoDB host address.")
    parser.add_argument("-p", "--port", default=27017, help="MongoDB port number.")
    args = parser.parse_args()

    app = QApplication([])
    gui = MainWindow(mongo_host=args.host, mongo_port=args.port)
    gui.showMaximized()
    gui.show()
    app.exec_()

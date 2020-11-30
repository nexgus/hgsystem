# pylint: disable=no-name-in-module
import hgsystem as hg
import os
import pygit2
import sys

from main_widget import MainWidget
from pymongo import MongoClient
from PySide2.QtWidgets import QAction
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QMessageBox

####################################################################################################
class MainWindow(QMainWindow):
    def __init__(self, mongo_host="localhost", mongo_port=27017):
        super(MainWindow, self).__init__()
        self.setWindowTitle(f"豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統 ({hg.VER_STRING})")

        self.create_menu()

        self.mongodb = MongoClient(mongo_host, mongo_port)
        self.setCentralWidget(MainWidget(self.mongodb))

    def __del__(self):
        self.mongodb.close()

    def about(self):
        msgbox = QMessageBox()
        msgbox.setWindowTitle("有關於")
        msgbox.setText(f"豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統 ({hg.VER_STRING})")
        msgbox.exec_()

    def create_menu(self):
        mainMenu = self.menuBar()
        systemMenu = mainMenu.addMenu("系統")

        updateAction = QAction("更新", self)
        updateAction.triggered.connect(self.update_app)

        aboutAction = QAction("有關於", self)
        aboutAction.triggered.connect(self.about)

        exitAction = QAction("離開", self)
        exitAction.triggered.connect(self.exit_app)

        systemMenu.addAction(updateAction)
        systemMenu.addAction(aboutAction)
        systemMenu.addAction(exitAction)

    def exit_app(self):
        self.close()

    def update_app(self):
        dirname = os.path.dirname(os.path.abspath(__file__))
        dirname = os.path.join(dirname, "..")
        dirname = os.path.abspath(dirname)

        repo = pygit2.Repository(dirname)
        self.git_pull(repo)

    def git_pull(self, repo, remote_name="origin", branch="main"):
        # pylint: disable=no-member
        # https://www.ithome.com.tw/news/140094
        # GitHub 2020/10 起將以 main 取代 master 作為新 git 儲存庫預設名稱
        for remote in repo.remotes:
            if remote.name != remote_name: continue
            remote.fetch()
            try:
                remote_master_id = repo.lookup_reference(f"refs/remotes/origin/{branch}").target
            except KeyError:
                if branch == "main":
                    branch = "master"
                    remote_master_id = repo.lookup_reference(f"refs/remotes/origin/master").target
                else:
                    raise

            restart = False
            msgbox = QMessageBox()
            msgbox.setWindowTitle("更新結果")
            merge_result, _ = repo.merge_analysis(remote_master_id)
            if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                msgbox.setText("已為最新版本\n(未更新)")
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                repo.checkout_tree(repo.get(remote_master_id))
                try:
                    master_ref = repo.lookup_reference(f"refs/heads/{branch}")
                    master_ref.set_target(remote_master_id)
                except KeyError:
                    repo.create_branch(branch, repo.get(remote_master_id))
                repo.head.set_target(remote_master_id)
                msgbox.setText("已更新為最新版本\n(GIT_MERGE_ANALYSIS_FASTFORWARD)")
                restart = True
            else:
                msgbox.setText(f"產生不明錯誤:\n{merge_result}")
            msgbox.exec_()
            if restart:
                os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)

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

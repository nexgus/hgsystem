# pylint: disable=no-name-in-module
import hgsystem as hg
import os
import pygit2
import subprocess
import sys

from main_widget import MainWidget
from pymongo import MongoClient
from PySide2.QtWidgets import QAction
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QMessageBox

####################################################################################################
class MainWindow(QMainWindow):
    def __init__(self, mongo_host="localhost", mongo_port=27017, test=False):
        super(MainWindow, self).__init__()
        self._test = test
        self.setWindowTitle(f"豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統 ({hg.VER_STRING})")

        self.create_menu()

        self.mongodb = MongoClient(mongo_host, mongo_port)
        self.setCentralWidget(MainWidget(self.mongodb))

        # Check if file updated
        dirname = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(dirname, "updated")
        if os.path.isfile(filepath):
            with open(filepath, "r") as fp:
                old_verstr = fp.read()
            os.remove(filepath)
            QMessageBox.information(self, "更新結果", 
                f"<font size='+2'><b>已由 {old_verstr} 更新為 {hg.VER_STRING}</b></font>")

        # Clear search history
        self.mongodb.hgsystem.search.delete_many(filter={})

    def __del__(self):
        self.mongodb.close()

    def about(self):
        msgbox = QMessageBox()
        msgbox.setWindowTitle("有關於")
        msgbox.setFont(hg.FONT)
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
        hg.logger.info(f"Update application: workdir={repo.workdir}")
        for remote in repo.remotes:
            if remote.name != remote_name: continue
            remote.fetch()
            try:
                ref = repo.lookup_reference(f"refs/remotes/{remote_name}/{branch}")
            except KeyError as ex:
                if branch == "main": 
                    branch = "master"
                    ref = repo.lookup_reference(f"refs/remotes/{remote_name}/{branch}")
                else:
                    hg.logger.exception(ex)
                    raise
            except Exception as ex:
                hg.logger.exception(ex)
                raise

            remote_master_id = ref.target
            hg.logger.debug(f"URL - {remote.url}/{ref.shorthand}")

            merge_result, _ = repo.merge_analysis(remote_master_id)
            MERGE_RESULT = {
                0: "GIT_MERGE_ANALYSIS_NONE",
                1: "GIT_MERGE_ANALYSIS_NORMAL",
                2: "GIT_MERGE_ANALYSIS_UP_TO_DATE",
                4: "GIT_MERGE_ANALYSIS_FASTFORWARD",
                8: "GIT_MERGE_ANALYSIS_UNBORN",
            }
            if merge_result in MERGE_RESULT:
                hg.logger.debug(
                    f"Merge analysis result: {MERGE_RESULT[merge_result]} ({merge_result})")
            else:
                hg.logger.warning(f"Unexpected merge result: {merge_result}")

            if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                hg.logger.info("hgsystem is up to date. Do nothing.")
                if self._test:
                    self.restart()
                else:
                    QMessageBox.information(self, "更新結果", 
                        f"<font size='+2'><b>已為最新版本 ({hg.VER_STRING})</b></font>")

            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                hg.logger.info("Start to update hgsystem.")
                repo.checkout_tree(repo.get(remote_master_id))
                try:
                    master_ref = repo.lookup_reference(f"refs/heads/{branch}")
                    master_ref.set_target(remote_master_id)
                except KeyError:
                    repo.create_branch(branch, repo.get(remote_master_id))
                repo.head.set_target(remote_master_id)

                # Install dependencies
                command = f"-m pip install -r {repo.workdir}/requirements.txt".split()
                command = [sys.executable] + command
                subprocess.check_call(command)

                self.restart()

            else:
                QMessageBox.warning(self, "更新結果", 
                    f"<font size='+2'><b>發生錯誤</b></font>\n"
                    f"{MERGE_RESULT[merge_result]} ({merge_result})")

    def restart(self):
        # Write current version info to a file so after restart hgsystem detects.
        dirname = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(dirname, "updated")
        with open(filepath, "w") as fp:
            fp.write(hg.VER_STRING)

        hg.logger.info("hgsystem is updated. Restart hgsystem.")
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
    parser.add_argument("-T", "--test", action="store_true", help="Test.")
    args = parser.parse_args()

    app = QApplication([])
    gui = MainWindow(mongo_host=args.host, mongo_port=args.port, test=args.test)
    gui.showMaximized()
    gui.show()
    app.exec_()

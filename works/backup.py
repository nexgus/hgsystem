# pylint: disable=no-name-in-module
import os
import sys
import subprocess
import traceback

from PySide2 import QtCore
from PySide2.QtWidgets import QDialog
from PySide2.QtWidgets import QHBoxLayout
from PySide2.QtWidgets import QProgressBar
from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import QTextEdit
from PySide2.QtWidgets import QVBoxLayout

####################################################################################################
class WorkerSignals(QtCore.QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data
    error
        `tuple` (exctype, value, traceback.format_exc() )
    result
        `object` data returned from processing, anything
    """
    finished = QtCore.Signal()
    error = QtCore.Signal(tuple)
    result = QtCore.Signal(object)
    message = QtCore.Signal(str)

####################################################################################################
class Worker(QtCore.QRunnable):
    """Worker thread for running background tasks."""

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['message_callback'] = self.signals.message

    @QtCore.Slot()
    def run(self):
        try:
            result = self.fn(
                *self.args, **self.kwargs,
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

####################################################################################################
class BackupRestore(QDialog):
    """GUI Application using PySide2 widgets"""
    def __init__(self, savepath, mode, parent=None):
        super(BackupRestore, self).__init__(parent)
        self._savepath = savepath
        self._mode = mode
        self.threadpool = QtCore.QThreadPool()

        self.setWindowTitle("備份/還原")
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.cmdStart = QPushButton("開始")
        self.cmdCancel = QPushButton("取消")
        self.progressbar = QProgressBar(self)
        self.info = QTextEdit(self)

        layout1 = QHBoxLayout()
        layout1.addWidget(self.cmdStart)
        layout1.addWidget(self.cmdCancel)

        layout = QVBoxLayout()
        layout.addLayout(layout1)
        layout.addWidget(self.progressbar)
        layout.addWidget(self.info)
        self.setLayout(layout)

        self.cmdStart.clicked.connect(self.run)
        self.cmdCancel.clicked.connect(self.close)

    def backup(self, message_callback):
        command = f"mongodump -d hgsystem -o {self._savepath}"
        p = subprocess.Popen(command, stderr=subprocess.PIPE, shell=True)
        for line in p.stderr:
            line = line.decode("utf-8")
            line = line.replace("\n", "").replace("\t", " ")
            message_callback.emit(line)

    def completed(self):
        self.progressbar.setRange(0, 1)
        self.cmdStart.setText("完成")
        self.cmdStart.setEnabled(True)

    def on_message(self, msg):
        """Update progress"""
        self.info.append(f"<p style=\"font-family:'Courier New'\">{msg}</p>")        

    def restore(self, message_callback):
        command = f"mongorestore -d hgsystem --dir {self._savepath}"
        p = subprocess.Popen(command, stderr=subprocess.PIPE, shell=True)
        for line in p.stderr:
            line = line.decode("utf-8")
            line = line.replace("\n", "").replace("\t", " ")
            message_callback.emit(line)

    def run(self):
        """call process"""
        if self.cmdStart.text() == "開始":
            self.cmdStart.setEnabled(False)
            self.cmdCancel.setEnabled(False)
            if self._mode == "backup":
                self.cmdStart.setText("備份中...")
                self.run_threaded_process(self.backup, self.on_message, self.completed)
            else:
                self.cmdStart.setText("還原中...")
                self.run_threaded_process(self.restore, self.on_message, self.completed)
        else:
            self.close()

    def run_threaded_process(self, process, on_message, on_complete):
        """Execute a function in the background with a worker"""
        worker = Worker(fn=process)
        worker.signals.finished.connect(on_complete)
        worker.signals.message.connect(on_message)
        self.threadpool.start(worker)
        self.progressbar.setRange(0, 0)

####################################################################################################
if __name__ == "__main__":
    from PySide2.QtWidgets import QApplication
    app = QApplication([])
    gui = BackupRestore("D:\\", "backup")
    gui.show()
    app.exec_()

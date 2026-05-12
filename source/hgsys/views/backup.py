"""Backup / restore dialog. Spawns mongodump/mongorestore in a worker thread
and streams stderr lines to a QTextEdit."""
import sys
import traceback
from typing import Callable

from PySide6 import QtCore
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..services import backup as backup_svc


class _Signals(QtCore.QObject):
    finished = QtCore.Signal()
    error = QtCore.Signal(tuple)
    message = QtCore.Signal(str)


class _Worker(QtCore.QRunnable):
    def __init__(self, target: Callable, savepath: str):
        super().__init__()
        self._target = target
        self._savepath = savepath
        self.signals = _Signals()

    @QtCore.Slot()
    def run(self) -> None:
        try:
            for line in self._target(self._savepath):
                self.signals.message.emit(line)
        except Exception:  # noqa: BLE001 — surfaced to the dialog
            traceback.print_exc()
            exc_type, value = sys.exc_info()[:2]
            self.signals.error.emit((exc_type, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()


class BackupRestoreDialog(QDialog):
    def __init__(self, savepath: str, mode: str, parent: QWidget = None):
        super().__init__(parent)
        assert mode in ("backup", "restore")
        self._savepath = savepath
        self._mode = mode
        self._pool = QtCore.QThreadPool()

        self.setWindowTitle("備份/還原")
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.cmdStart = QPushButton("開始")
        self.cmdCancel = QPushButton("取消")
        self.progress = QProgressBar()
        self.info = QTextEdit()

        controls = QHBoxLayout()
        controls.addWidget(self.cmdStart)
        controls.addWidget(self.cmdCancel)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(self.progress)
        layout.addWidget(self.info)
        self.setLayout(layout)

        self.cmdStart.clicked.connect(self._on_start)
        self.cmdCancel.clicked.connect(self.close)

    def _on_start(self) -> None:
        if self.cmdStart.text() == "開始":
            self.cmdStart.setEnabled(False)
            self.cmdCancel.setEnabled(False)
            if self._mode == "backup":
                self.cmdStart.setText("備份中...")
                target = backup_svc.dump
            else:
                self.cmdStart.setText("還原中...")
                target = backup_svc.restore
            self._spawn(target)
        else:
            self.close()

    def _spawn(self, target: Callable) -> None:
        worker = _Worker(target, self._savepath)
        worker.signals.message.connect(self._on_message)
        worker.signals.finished.connect(self._on_complete)
        self._pool.start(worker)
        self.progress.setRange(0, 0)

    def _on_message(self, msg: str) -> None:
        self.info.append(f"<p style=\"font-family:'Courier New'\">{msg}</p>")

    def _on_complete(self) -> None:
        self.progress.setRange(0, 1)
        self.cmdStart.setText("完成")
        self.cmdStart.setEnabled(True)

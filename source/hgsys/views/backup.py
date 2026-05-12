"""Backup / restore dialog. Spawns mongodump/mongorestore in a worker thread
and streams stderr lines to a QTextEdit."""

import sys
import traceback
from collections.abc import Callable

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
    """worker thread 用以與主 thread 通訊的訊號 (finished / error / message)."""

    finished = QtCore.Signal()
    error = QtCore.Signal(tuple)
    message = QtCore.Signal(str)


class _Worker(QtCore.QRunnable):
    """執行 mongodump / mongorestore 的背景 worker.

    將 ``target`` (產生 stderr 字串的 generator) 一行一行透過 ``message`` 訊號
    送出, 結束時送 ``finished``; 任何例外則以 ``error`` 送 traceback.
    """

    def __init__(self, target: Callable[[str], object], savepath: str) -> None:
        """以 ``target`` 與 ``savepath`` 建立 worker."""
        super().__init__()
        self._target: Callable[[str], object] = target
        self._savepath: str = savepath
        self.signals: _Signals = _Signals()

    @QtCore.Slot()
    def run(self) -> None:
        """thread pool 入口: 跑 ``target(savepath)`` 並轉送 stderr 行."""
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
    """備份 / 還原進度對話框.

    對話框啟動時尚未開跑; 使用者按下「開始」才呼叫 ``mongodump`` /
    ``mongorestore``, 過程中其 stderr 會以類 console 的方式即時顯示.
    """

    def __init__(self, savepath: str, mode: str, parent: QWidget | None = None) -> None:
        """建立對話框.

        Arg(s):
            savepath: 備份目錄路徑.
            mode: ``"backup"`` 或 ``"restore"``.
            parent: Qt parent.
        """
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
        """主動作按鈕: 首次按下啟動工作, 完成後按下則關閉對話框."""
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

    def _spawn(self, target: Callable[[str], object]) -> None:
        """在 thread pool 啟動 worker, 並把進度條設為「不定長度」忙碌狀態."""
        worker = _Worker(target, self._savepath)
        worker.signals.message.connect(self._on_message)
        worker.signals.finished.connect(self._on_complete)
        self._pool.start(worker)
        self.progress.setRange(0, 0)

    def _on_message(self, msg: str) -> None:
        """worker 傳來一行 stderr: 以等寬字型 append 到輸出區."""
        self.info.append(f"<p style=\"font-family:'Courier New'\">{msg}</p>")

    def _on_complete(self) -> None:
        """worker 結束: 收掉忙碌進度條, 將按鈕改為「完成」."""
        self.progress.setRange(0, 1)
        self.cmdStart.setText("完成")
        self.cmdStart.setEnabled(True)

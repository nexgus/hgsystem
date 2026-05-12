"""Top-level QMainWindow: menus + central widget + dialog plumbing."""
import logging
from pathlib import Path

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from ..log import get_logger
from ..services import backup as backup_svc
from ..services import updater
from ..version import VER_STRING
from ..viewmodels.main import MainViewModel
from .backup import BackupRestoreDialog
from .main_widget import MainWidget
from .search import SearchDialog
from .style import FONT, asset

logger: logging.Logger = get_logger()

UPDATE_MARKER_FILENAME: str = "updated"


class MainWindow(QMainWindow):
    """應用程式主視窗: 選單 + 中央 widget + 跨面板 dialog 處理.

    所有 dialog (搜尋 / 刪除確認 / 備份還原 / 關於 / 更新訊息) 都收斂在這層,
    讓底下的面板維持純 UI / view-model 邏輯.
    """

    def __init__(self, vm: MainViewModel, test_mode: bool = False, parent: QWidget | None = None) -> None:
        """建立主視窗.

        Arg(s):
            vm: 已建立的 ``MainViewModel``.
            test_mode: ``True`` 時, 「更新」即使無更新可用也會直接重啟程式 (供 ``-T`` 旗標).
            parent: Qt parent.
        """
        super().__init__(parent)
        self._vm = vm
        self._test_mode = test_mode

        self.setWindowTitle(f"豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統 ({VER_STRING})")
        self.setWindowIcon(QIcon(asset("app.png")))

        self._build_menu()

        widget = MainWidget(vm)
        self.setCentralWidget(widget)

        # Search button on the customer panel triggers our search dialog.
        widget.customer.edit.cmdSearch.clicked.connect(self._open_search)
        # Delete confirmations live at this level so the panels stay UI-only.
        widget.customer.edit.cmdRemove.clicked.connect(self._delete_customer)
        widget.worksheet.cmdRemove.clicked.connect(self._delete_worksheet)
        # Surface validation errors to the user.
        vm.customer.validationFailed.connect(self._show_validation_error)
        vm.worksheet.validationFailed.connect(self._show_validation_error)

        self._maybe_show_update_message()
        vm.bootstrap()

    # ---- menu construction ----------------------------------------------
    def _build_menu(self) -> None:
        """建立 系統 / 資料 兩個選單與其底下動作."""
        menubar = self.menuBar()
        system_menu = menubar.addMenu("系統")
        data_menu = menubar.addMenu("資料")

        update_action = QAction(QIcon(asset("update.png")), "更新", self)
        about_action = QAction(QIcon(asset("about.png")), "有關", self)
        exit_action = QAction(QIcon(asset("exit.png")), "離開", self)
        backup_action = QAction(QIcon(asset("backup.png")), "備份", self)
        restore_action = QAction(QIcon(asset("restore.png")), "還原", self)

        for act in (update_action, about_action, exit_action):
            system_menu.addAction(act)
        for act in (backup_action, restore_action):
            data_menu.addAction(act)

        update_action.triggered.connect(self._update_app)
        about_action.triggered.connect(self._show_about)
        exit_action.triggered.connect(self.close)
        backup_action.triggered.connect(self._backup_database)
        restore_action.triggered.connect(self._restore_database)

    # ---- dialogs ---------------------------------------------------------
    def _open_search(self) -> None:
        """開啟搜尋對話框; 選定結果後將其推入 main VM 作為當前客戶."""
        search_vm = self._vm.make_search_viewmodel()
        dialog = SearchDialog(search_vm, parent=self)
        if dialog.exec() == QDialog.Accepted:
            customer = dialog.selected_customer()
            if customer is not None:
                self._vm.adopt_search_result(customer)

    def _delete_customer(self) -> None:
        """跳出確認對話框, 確認後刪除當前客戶 (連同名下工單)."""
        current = self._vm.customer.current
        if current is None:
            return
        worksheet_count = len(self._vm.worksheet.history)
        selection = QMessageBox.question(
            self,
            f"刪除客戶 {current.id}",
            f"<font size='+1'><b>確定要刪除該筆資料嗎?<br>"
            f"這會將所有該客戶的紀錄刪除 (共 {worksheet_count} 筆), 無法復原!<br>"
            f"姓名: {current.name}<br>"
            f"地址: {current.addr}</b></font>",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if selection == QMessageBox.StandardButton.No:
            return
        self._vm.delete_current_customer()

    def _delete_worksheet(self) -> None:
        """跳出確認對話框, 確認後刪除當前工單."""
        from ..domain.dates import to_roc_date_string

        current = self._vm.worksheet.current
        if current is None:
            return
        date1 = to_roc_date_string(current.order_time)
        date2 = to_roc_date_string(current.deliver_time)
        selection = QMessageBox.question(
            self,
            f"刪除工單 {current.id}",
            f"<font size='+1'><b>確定要刪除該筆資料嗎?<br>"
            f"收件日: {date1}<br>交件日: {date2}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if selection == QMessageBox.StandardButton.No:
            return
        self._vm.worksheet.delete()

    def _backup_database(self) -> None:
        """選擇備份目錄後開啟 ``BackupRestoreDialog`` 執行 mongodump."""
        savepath = str(QFileDialog.getExistingDirectory(self, "選擇備份目錄"))
        if not savepath:
            return
        BackupRestoreDialog(savepath, mode="backup", parent=self).exec()

    def _restore_database(self) -> None:
        """選擇備份目錄後驗證必要檔, 通過才開啟還原對話框."""
        chosen = str(QFileDialog.getExistingDirectory(self, "選擇備份目錄"))
        if not chosen:
            return
        savepath = backup_svc.resolve_restore_dir(chosen)
        missing = backup_svc.missing_files(savepath)
        if missing:
            QMessageBox.critical(
                self,
                "無法還原",
                "<font size='+1'><b>檔案不完整, 無法還原. 缺少<br>"
                + "<br>".join(missing)
                + "</b></font>",
            )
            return
        BackupRestoreDialog(savepath, mode="restore", parent=self).exec()

    def _show_about(self) -> None:
        """顯示「有關」對話框 (應用程式名稱 + 版本)."""
        msg = QMessageBox()
        msg.setWindowTitle("有關")
        msg.setFont(FONT)
        msg.setText(f"豪格鐘錶隱形眼鏡公司眼鏡客戶管理系統 ({VER_STRING})")
        msg.exec()

    def _show_validation_error(self, message: str, _focus_hint: str) -> None:
        """將 view-model 的 ``validationFailed`` 訊息以錯誤對話框呈現."""
        QMessageBox.critical(
            self, "輸入內容錯誤",
            f"<font size='+1'><b>{message}</b></font>",
        )

    # ---- self-update -----------------------------------------------------
    def _update_app(self) -> None:
        """執行自我更新: ``git pull`` + 必要時 ``pip install`` + 重啟.

        測試模式下即使「已是最新版本」也會直接重啟, 方便觀察更新流程.
        """
        try:
            repo_root = updater.find_repo_root(Path(__file__).resolve().parent)
            result, detail = updater.pull_and_install(repo_root)
        except Exception as ex:  # noqa: BLE001
            logger.exception(ex)
            QMessageBox.critical(self, "更新結果", f"<font size='+2'><b>更新失敗: {ex}</b></font>")
            return

        if result == updater.PullResult.UP_TO_DATE:
            if self._test_mode:
                self._restart()
            else:
                QMessageBox.information(
                    self, "更新結果",
                    f"<font size='+2'><b>已為最新版本 ({VER_STRING})</b></font>",
                )
        elif result == updater.PullResult.FAST_FORWARDED:
            self._restart()
        else:
            QMessageBox.warning(
                self, "更新結果",
                f"<font size='+2'><b>發生錯誤</b></font>\n{detail}",
            )

    def _restart(self) -> None:
        """寫入版本 marker 並以 ``os.execl`` 重啟本程式."""
        marker = (Path(__file__).resolve().parent.parent / UPDATE_MARKER_FILENAME)
        updater.restart(marker, VER_STRING)

    def _maybe_show_update_message(self) -> None:
        """若上次啟動後有 marker, 顯示「已由 X 更新為 Y」並清除 marker."""
        marker = Path(__file__).resolve().parent.parent / UPDATE_MARKER_FILENAME
        if not marker.is_file():
            return
        old_ver = marker.read_text()
        marker.unlink()
        QMessageBox.information(
            self, "更新結果",
            f"<font size='+2'><b>已由 {old_ver} 更新為 {VER_STRING}</b></font>",
        )

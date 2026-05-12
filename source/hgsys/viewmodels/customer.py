import logging
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal

from ..domain.edit_mode import EditMode
from ..domain.models import Customer
from ..log import get_logger
from ..repository.customers import CustomerRepository

logger: logging.Logger = get_logger()


class CustomerViewModel(QObject):
    """客戶面板的 view-model.

    維護「當前客戶」與編輯狀態, 對 view 提供新增 / 修改 / 取消 / 儲存 / 刪除指令,
    並透過訊號通知 view 更新. ``validationFailed`` 由 view 接收後彈窗.
    """

    currentChanged = Signal(object)      # Optional[Customer]
    editModeChanged = Signal(int)        # EditMode
    totalCountChanged = Signal(int)
    validationFailed = Signal(str, str)  # (message, focus_hint)

    def __init__(self, repo: CustomerRepository, parent: QObject | None = None) -> None:
        """以客戶 repository 建立 view-model.

        Arg(s):
            repo: ``CustomerRepository`` 實例.
            parent: Qt parent.
        """
        super().__init__(parent)
        self._repo: CustomerRepository = repo
        self._current: Customer | None = None
        self._snapshot: Customer | None = None
        self._mode: EditMode = EditMode.NONE
        self._total: int = 0

    # ---- read accessors ---------------------------------------------------
    @property
    def current(self) -> Customer | None:
        """目前選定的客戶 (尚未選擇或新增中時為 ``None``)."""
        return self._current

    @property
    def mode(self) -> EditMode:
        """當前編輯模式."""
        return self._mode

    @property
    def total(self) -> int:
        """客戶總筆數 (僅在 ``refresh_total`` / 新增 / 刪除後更新)."""
        return self._total

    # ---- public commands --------------------------------------------------
    def refresh_total(self) -> None:
        """重新查詢客戶總筆數並廣播 ``totalCountChanged``."""
        self._total = self._repo.count()
        self.totalCountChanged.emit(self._total)

    def set_current(self, customer: Customer | None) -> None:
        """將 ``customer`` 設為當前客戶並廣播 ``currentChanged``."""
        self._current = customer
        self.currentChanged.emit(customer)

    def start_append(self) -> None:
        """進入新增模式: 暫存當前客戶, 清空欄位等待輸入."""
        self._snapshot = self._current
        self._current = None
        self._mode = EditMode.APPEND
        logger.debug("Append a new customer.")
        self.currentChanged.emit(None)
        self.editModeChanged.emit(self._mode)

    def start_modify(self) -> None:
        """對當前客戶進入修改模式; 沒有當前客戶時 no-op."""
        if self._current is None:
            return
        self._snapshot = self._current
        self._mode = EditMode.MODIFY
        logger.debug(f"Modify customer data: {self._current.id}/{self._current.name}.")
        self.editModeChanged.emit(self._mode)

    def cancel_edit(self) -> None:
        """取消編輯: 還原為 snapshot (修改時) 或舊客戶 (新增時)."""
        was_appending = self._mode == EditMode.APPEND
        if was_appending and self._snapshot is not None:
            self._current = self._snapshot
        elif self._mode == EditMode.MODIFY and self._snapshot is not None:
            # re-fetch in case underlying data drifted; preserves legacy behavior
            fresh = self._repo.get(self._snapshot.id) or self._snapshot
            self._current = fresh
        elif self._snapshot is None:
            self._current = None
        self._snapshot = None
        self._mode = EditMode.NONE
        logger.debug("Cancel customer edit.")
        self.currentChanged.emit(self._current)
        self.editModeChanged.emit(self._mode)

    def save(self, draft: Customer) -> bool:
        """儲存當前編輯; 姓名為空則發出 ``validationFailed`` 並回傳 ``False``.

        Arg(s):
            draft: 由 view 收集而來的草稿 ``Customer``.

        Return(s):
            是否成功儲存.
        """
        if not draft.name.strip():
            self.validationFailed.emit("姓名不得為空白", "name")
            return False
        if self._mode == EditMode.APPEND:
            self._repo.insert(draft)
            self._current = draft
            self.refresh_total()
            logger.debug(f"Append customer and save: {draft.id}/{draft.name}.")
        elif self._mode == EditMode.MODIFY:
            cid = self._snapshot.id if self._snapshot else draft.id
            draft.id = cid
            self._repo.replace(cid, draft)
            self._current = draft
            logger.debug(f"Edit customer and save: {draft.id}/{draft.name}.")
        else:
            return False
        self._snapshot = None
        self._mode = EditMode.NONE
        self.currentChanged.emit(self._current)
        self.editModeChanged.emit(self._mode)
        return True

    def delete(self, on_worksheets_deleted: Callable[[str], int] | None = None) -> bool:
        """刪除當前客戶; 透過 ``on_worksheets_deleted`` 連動刪除其工單.

        Arg(s):
            on_worksheets_deleted: callable, 收到 cid 後刪除該客戶名下工單並回傳刪除筆數.

        Return(s):
            是否真的執行刪除 (當前客戶為 ``None`` 時回傳 ``False``).
        """
        if self._current is None:
            return False
        cid = self._current.id
        name = self._current.name
        self._repo.delete(cid)
        deleted = on_worksheets_deleted(cid) if on_worksheets_deleted else 0
        logger.debug(f"Delete customer {cid}/{name} and {deleted} worksheet(s).")
        self._current = None
        self.refresh_total()
        self._mode = EditMode.NONE
        self.currentChanged.emit(None)
        self.editModeChanged.emit(self._mode)
        return True

    def set_inhibited(self, inhibited: bool) -> None:
        """由主協調者呼叫: 鎖定 / 解鎖此面板 (對應 ``INHIBIT`` / ``NONE``)."""
        target = EditMode.INHIBIT if inhibited else EditMode.NONE
        if target == self._mode:
            return
        self._mode = target
        self.editModeChanged.emit(self._mode)

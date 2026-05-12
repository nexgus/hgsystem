import logging

from PySide6.QtCore import QObject, Signal

from ..domain.edit_mode import EditMode
from ..domain.models import Worksheet
from ..log import get_logger
from ..repository.worksheets import WorksheetRepository

logger: logging.Logger = get_logger()


class WorksheetViewModel(QObject):
    """工單面板的 view-model.

    維護當前客戶名下的工單列表 (``history``), 當前選中的工單 (``current``) 與
    編輯狀態. 工單須附著於客戶, 因此預設狀態為 ``INHIBIT``, 直到 ``load_history``
    收到有效的 cid 才解鎖.
    """

    currentChanged = Signal(object)  # Optional[Worksheet]
    editModeChanged = Signal(int)  # EditMode
    historyChanged = Signal(list)  # list[Worksheet]
    historyRowReplaced = Signal(int, object)  # (row, Worksheet)
    historyRowAppended = Signal(object)  # Worksheet
    historyRowRemoved = Signal(int)  # row
    validationFailed = Signal(str, str)

    def __init__(
        self, repo: WorksheetRepository, parent: QObject | None = None
    ) -> None:
        """以工單 repository 建立 view-model.

        Arg(s):
            repo: ``WorksheetRepository`` 實例.
            parent: Qt parent.
        """
        super().__init__(parent)
        self._repo: WorksheetRepository = repo
        self._current: Worksheet | None = None
        self._snapshot: Worksheet | None = None
        self._mode: EditMode = EditMode.INHIBIT
        self._history: list[Worksheet] = []
        self._current_cid: str = ""

    # ---- read accessors ---------------------------------------------------
    @property
    def current(self) -> Worksheet | None:
        """目前選中的工單 (歷史為空時為 ``None``)."""
        return self._current

    @property
    def mode(self) -> EditMode:
        """當前編輯模式."""
        return self._mode

    @property
    def history(self) -> list[Worksheet]:
        """當前客戶名下的工單列表 (回傳副本)."""
        return list(self._history)

    # ---- public commands --------------------------------------------------
    def load_history(self, cid: str) -> None:
        """重新載入 ``cid`` 客戶的所有工單, 自動選中第一筆."""
        self._current_cid = cid
        self._history = self._repo.find_for_customer(cid) if cid else []
        self.historyChanged.emit(self._history)
        self._current = self._history[0] if self._history else None
        self.currentChanged.emit(self._current)

    def clear_history(self) -> None:
        """清空歷史 (沒有當前客戶時)."""
        self._current_cid = ""
        self._history = []
        self._current = None
        self.historyChanged.emit(self._history)
        self.currentChanged.emit(None)

    def select_row(self, row: int) -> None:
        """以列號切換當前工單; 範圍外 no-op."""
        if row < 0 or row >= len(self._history):
            return
        self._current = self._history[row]
        self.currentChanged.emit(self._current)

    def start_append(self) -> None:
        """進入新增模式; 沒有當前客戶 (``cid``) 時 no-op."""
        if not self._current_cid:
            return
        self._snapshot = self._current
        self._mode = EditMode.APPEND
        logger.debug(f"Append a new worksheet for {self._current_cid}.")
        self.editModeChanged.emit(self._mode)

    def start_modify(self) -> None:
        """對當前工單進入修改模式; 沒有當前工單時 no-op."""
        if self._current is None:
            return
        self._snapshot = self._current
        self._mode = EditMode.MODIFY
        logger.debug(f"Modify worksheet for {self._current.cid}/{self._current.id}.")
        self.editModeChanged.emit(self._mode)

    def cancel_edit(self) -> None:
        """取消編輯, 還原為 snapshot."""
        if self._snapshot is not None:
            self._current = self._snapshot
        self._snapshot = None
        self._mode = EditMode.NONE
        logger.debug("Cancel worksheet edit.")
        self.currentChanged.emit(self._current)
        self.editModeChanged.emit(self._mode)

    def save(self, draft: Worksheet) -> bool:
        """儲存當前編輯; 收件日空白則發出 ``validationFailed`` 並回傳 ``False``.

        Arg(s):
            draft: 由 view 收集而來的草稿 ``Worksheet``.

        Return(s):
            是否成功儲存.
        """
        if draft.order_time is None:
            self.validationFailed.emit("收件日不得為空白", "order_time")
            return False
        if self._mode == EditMode.APPEND:
            draft.cid = self._current_cid
            self._repo.insert(draft)
            self._history.append(draft)
            self._current = draft
            self.historyRowAppended.emit(draft)
            logger.debug(f"Append and save worksheet {draft.id} for {draft.cid}")
        elif self._mode == EditMode.MODIFY:
            wid = self._snapshot.id if self._snapshot else draft.id
            draft.id = wid
            draft.cid = self._snapshot.cid if self._snapshot else draft.cid
            self._repo.replace(wid, draft)
            row = self._row_of(wid)
            if row >= 0:
                self._history[row] = draft
                self.historyRowReplaced.emit(row, draft)
            self._current = draft
            logger.debug(f"Edit and save worksheet {draft.id} for {draft.cid}")
        else:
            return False
        self._snapshot = None
        self._mode = EditMode.NONE
        self.currentChanged.emit(self._current)
        self.editModeChanged.emit(self._mode)
        return True

    def delete(self) -> bool:
        """刪除當前工單; 沒有當前工單時回傳 ``False``.

        刪除後若歷史仍有資料, 選中靠近原位置的下一筆.
        """
        if self._current is None:
            return False
        wid = self._current.id
        row = self._row_of(wid)
        self._repo.delete(wid)
        if row >= 0:
            self._history.pop(row)
            self.historyRowRemoved.emit(row)
        if self._history:
            new_row = min(row, len(self._history) - 1)
            self._current = self._history[new_row]
        else:
            self._current = None
        self._mode = EditMode.NONE
        logger.debug(f"Delete worksheet {wid}.")
        self.currentChanged.emit(self._current)
        self.editModeChanged.emit(self._mode)
        return True

    def set_inhibited(self, inhibited: bool) -> None:
        """由主協調者呼叫: 鎖定 / 解鎖此面板; 解鎖時若無當前客戶仍維持 ``INHIBIT``."""
        if inhibited:
            target = EditMode.INHIBIT
        else:
            target = EditMode.NONE if self._current_cid else EditMode.INHIBIT
        if target == self._mode:
            return
        self._mode = target
        self.editModeChanged.emit(self._mode)

    # ---- internals --------------------------------------------------------
    def _row_of(self, wid: str) -> int:
        """於歷史中找出 ``wid`` 工單所在列號; 不存在時回傳 -1."""
        for idx, ws in enumerate(self._history):
            if ws.id == wid:
                return idx
        return -1

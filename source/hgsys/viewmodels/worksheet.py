from typing import Optional

from PySide6.QtCore import QObject, Signal

from ..domain.edit_mode import EditMode
from ..domain.models import Worksheet
from ..log import get_logger
from ..repository.worksheets import WorksheetRepository

logger = get_logger()


class WorksheetViewModel(QObject):
    currentChanged = Signal(object)      # Optional[Worksheet]
    editModeChanged = Signal(int)        # EditMode
    historyChanged = Signal(list)        # list[Worksheet]
    historyRowReplaced = Signal(int, object)  # (row, Worksheet)
    historyRowAppended = Signal(object)  # Worksheet
    historyRowRemoved = Signal(int)      # row
    validationFailed = Signal(str, str)

    def __init__(self, repo: WorksheetRepository, parent=None):
        super().__init__(parent)
        self._repo = repo
        self._current: Optional[Worksheet] = None
        self._snapshot: Optional[Worksheet] = None
        self._mode = EditMode.INHIBIT
        self._history: list[Worksheet] = []
        self._current_cid = ""

    # ---- read accessors ---------------------------------------------------
    @property
    def current(self) -> Optional[Worksheet]:
        return self._current

    @property
    def mode(self) -> EditMode:
        return self._mode

    @property
    def history(self) -> list[Worksheet]:
        return list(self._history)

    # ---- public commands --------------------------------------------------
    def load_history(self, cid: str) -> None:
        self._current_cid = cid
        self._history = self._repo.find_for_customer(cid) if cid else []
        self.historyChanged.emit(self._history)
        self._current = self._history[0] if self._history else None
        self.currentChanged.emit(self._current)

    def clear_history(self) -> None:
        self._current_cid = ""
        self._history = []
        self._current = None
        self.historyChanged.emit(self._history)
        self.currentChanged.emit(None)

    def select_row(self, row: int) -> None:
        if row < 0 or row >= len(self._history):
            return
        self._current = self._history[row]
        self.currentChanged.emit(self._current)

    def start_append(self) -> None:
        if not self._current_cid:
            return
        self._snapshot = self._current
        self._mode = EditMode.APPEND
        logger.debug(f"Append a new worksheet for {self._current_cid}.")
        self.editModeChanged.emit(self._mode)

    def start_modify(self) -> None:
        if self._current is None:
            return
        self._snapshot = self._current
        self._mode = EditMode.MODIFY
        logger.debug(
            f"Modify worksheet for {self._current.cid}/{self._current.id}."
        )
        self.editModeChanged.emit(self._mode)

    def cancel_edit(self) -> None:
        if self._snapshot is not None:
            self._current = self._snapshot
        self._snapshot = None
        self._mode = EditMode.NONE
        logger.debug("Cancel worksheet edit.")
        self.currentChanged.emit(self._current)
        self.editModeChanged.emit(self._mode)

    def save(self, draft: Worksheet) -> bool:
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
        for idx, ws in enumerate(self._history):
            if ws.id == wid:
                return idx
        return -1

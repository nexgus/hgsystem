from typing import Optional

from PySide6.QtCore import QObject, Signal

from ..domain.edit_mode import EditMode
from ..domain.models import Customer
from ..log import get_logger
from ..repository.customers import CustomerRepository

logger = get_logger()


class CustomerViewModel(QObject):
    currentChanged = Signal(object)      # Optional[Customer]
    editModeChanged = Signal(int)        # EditMode
    totalCountChanged = Signal(int)
    validationFailed = Signal(str, str)  # (message, focus_hint)

    def __init__(self, repo: CustomerRepository, parent=None):
        super().__init__(parent)
        self._repo = repo
        self._current: Optional[Customer] = None
        self._snapshot: Optional[Customer] = None
        self._mode = EditMode.NONE
        self._total = 0

    # ---- read accessors ---------------------------------------------------
    @property
    def current(self) -> Optional[Customer]:
        return self._current

    @property
    def mode(self) -> EditMode:
        return self._mode

    @property
    def total(self) -> int:
        return self._total

    # ---- public commands --------------------------------------------------
    def refresh_total(self) -> None:
        self._total = self._repo.count()
        self.totalCountChanged.emit(self._total)

    def set_current(self, customer: Optional[Customer]) -> None:
        self._current = customer
        self.currentChanged.emit(customer)

    def start_append(self) -> None:
        self._snapshot = self._current
        self._current = None
        self._mode = EditMode.APPEND
        logger.debug("Append a new customer.")
        self.currentChanged.emit(None)
        self.editModeChanged.emit(self._mode)

    def start_modify(self) -> None:
        if self._current is None:
            return
        self._snapshot = self._current
        self._mode = EditMode.MODIFY
        logger.debug(f"Modify customer data: {self._current.id}/{self._current.name}.")
        self.editModeChanged.emit(self._mode)

    def cancel_edit(self) -> None:
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

    def delete(self, on_worksheets_deleted=None) -> bool:
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
        target = EditMode.INHIBIT if inhibited else EditMode.NONE
        if target == self._mode:
            return
        self._mode = target
        self.editModeChanged.emit(self._mode)

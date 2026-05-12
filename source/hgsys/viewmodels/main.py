from pymongo import MongoClient
from PySide6.QtCore import QObject

from ..domain.edit_mode import EditMode
from ..domain.models import Customer
from ..repository.customers import CustomerRepository
from ..repository.search_history import SearchHistoryRepository
from ..repository.worksheets import WorksheetRepository
from .customer import CustomerViewModel
from .search import SearchViewModel
from .worksheet import WorksheetViewModel


class MainViewModel(QObject):
    """Owns sub-VMs and coordinates inter-panel state.

    Coordination rules (preserved from the legacy app):
      * Editing the customer panel inhibits the worksheet panel and vice versa.
      * When the customer panel returns to a no-current state, the worksheet
        panel stays inhibited (you can't edit a worksheet without a customer).
      * Whenever ``customer.current`` changes, worksheet history is reloaded
        and the worksheet panel jumps to row 0.
    """

    def __init__(self, mongo_client: MongoClient, parent: QObject | None = None) -> None:
        """建立 sub-VM, 串接資料層, 並清空本次啟動的搜尋記錄.

        Arg(s):
            mongo_client: 已連線的 ``pymongo.MongoClient`` (取其 ``hgsystem`` db).
            parent: Qt parent.
        """
        super().__init__(parent)
        self._mongo = mongo_client
        db = mongo_client.hgsystem
        self._customer_repo = CustomerRepository(db)
        self._worksheet_repo = WorksheetRepository(db)
        self._search_history_repo = SearchHistoryRepository(db)

        self.customer = CustomerViewModel(self._customer_repo, parent=self)
        self.worksheet = WorksheetViewModel(self._worksheet_repo, parent=self)

        # Search history is cleared on every startup, matching legacy behavior.
        self._search_history_repo.clear()

        self._wire_coordination()

    # ---- exposed helpers --------------------------------------------------
    def make_search_viewmodel(self) -> SearchViewModel:
        """為搜尋對話框建立一個新的 ``SearchViewModel`` (共用 repo)."""
        return SearchViewModel(self._customer_repo, self._search_history_repo)

    def adopt_search_result(self, customer: Customer) -> None:
        """搜尋結果被使用者選定時呼叫: 寫入歷史並切換為當前客戶."""
        self._search_history_repo.remember(customer)
        self.customer.set_current(customer)

    def delete_current_customer(self) -> bool:
        """刪除目前客戶及其名下所有工單; 沒有當前客戶時 no-op."""
        return self.customer.delete(
            on_worksheets_deleted=self._worksheet_repo.delete_for_customer
        )

    # ---- bootstrap --------------------------------------------------------
    def bootstrap(self) -> None:
        """View 連接完成後呼叫一次, 觸發初始狀態 (目前僅刷新客戶總筆數)."""
        self.customer.refresh_total()

    # ---- internals --------------------------------------------------------
    def _wire_coordination(self) -> None:
        """將 sub-VM 的訊號串接成兩面板互鎖的協調邏輯."""
        self.customer.currentChanged.connect(self._on_customer_current_changed)
        self.customer.editModeChanged.connect(self._on_customer_mode_changed)
        self.worksheet.editModeChanged.connect(self._on_worksheet_mode_changed)

    def _on_customer_current_changed(self, customer: Customer | None) -> None:
        """當前客戶切換: 重新載入工單歷史 (清空 / 載入)."""
        if customer is None or not customer.id:
            self.worksheet.clear_history()
        else:
            self.worksheet.load_history(customer.id)

    def _on_customer_mode_changed(self, mode: int) -> None:
        """客戶面板進入編輯時鎖住工單面板; 離開編輯則依當前客戶決定是否解鎖."""
        mode = EditMode(mode)
        if mode in (EditMode.APPEND, EditMode.MODIFY):
            self.worksheet.set_inhibited(True)
        elif mode == EditMode.NONE:
            self.worksheet.set_inhibited(self.customer.current is None)

    def _on_worksheet_mode_changed(self, mode: int) -> None:
        """工單面板進入編輯時鎖住客戶面板; 離開編輯則解鎖客戶面板."""
        mode = EditMode(mode)
        if mode in (EditMode.APPEND, EditMode.MODIFY):
            self.customer.set_inhibited(True)
        elif mode == EditMode.NONE:
            self.customer.set_inhibited(False)

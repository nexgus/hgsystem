from datetime import datetime

from PySide6.QtCore import QObject, Signal

from ..domain.models import Customer
from ..repository.customers import CustomerRepository
from ..repository.search_history import SearchHistoryRepository


class SearchViewModel(QObject):
    """搜尋對話框的 view-model.

    把使用者輸入的條件轉成 pymongo 查詢, 或回放本次啟動的搜尋歷史.
    """

    resultsChanged = Signal(list)  # list[Customer]

    def __init__(
        self,
        customers: CustomerRepository,
        history: SearchHistoryRepository,
        parent: QObject | None = None,
    ) -> None:
        """建立 view-model.

        Arg(s):
            customers: 客戶 repository (用於條件搜尋).
            history: 搜尋歷史 repository (用於回放).
            parent: Qt parent.
        """
        super().__init__(parent)
        self._customers: CustomerRepository = customers
        self._history: SearchHistoryRepository = history
        self._results: list[Customer] = []

    @property
    def results(self) -> list[Customer]:
        """目前搜尋結果 (回傳副本)."""
        return list(self._results)

    def search_new(
        self,
        name: str = "",
        addr: str = "",
        phone: str = "",
        birthdate: datetime | None = None,
    ) -> None:
        """以條件 (姓名 / 地址 / 電話模糊比對 + 生日完全比對) 查詢客戶並廣播結果.

        所有條件皆 optional; 空字串 / ``None`` 代表不限.
        """
        filter_: dict = {}
        if name:
            filter_["name"] = {"$regex": f".*{name}.*"}
        if addr:
            filter_["addr"] = {"$regex": f".*{addr}.*"}
        if phone:
            filter_["phones"] = {"$regex": f".*{phone}.*"}
        if birthdate is not None:
            filter_["birthdate"] = birthdate
        self._results = self._customers.find(filter_)
        self.resultsChanged.emit(self._results)

    def search_history(self) -> None:
        """改以本次啟動的搜尋歷史作為結果並廣播."""
        self._results = self._history.list()
        self.resultsChanged.emit(self._results)

    def remember(self, customer: Customer) -> None:
        """將 ``customer`` 寫入搜尋歷史 (已存在時略過)."""
        self._history.remember(customer)

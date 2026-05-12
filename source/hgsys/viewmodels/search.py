from datetime import datetime
from typing import Optional

from PySide6.QtCore import QObject, Signal

from ..domain.models import Customer
from ..repository.customers import CustomerRepository
from ..repository.search_history import SearchHistoryRepository


class SearchViewModel(QObject):
    resultsChanged = Signal(list)  # list[Customer]

    def __init__(
        self,
        customers: CustomerRepository,
        history: SearchHistoryRepository,
        parent=None,
    ):
        super().__init__(parent)
        self._customers = customers
        self._history = history
        self._results: list[Customer] = []

    @property
    def results(self) -> list[Customer]:
        return list(self._results)

    def search_new(
        self,
        name: str = "",
        addr: str = "",
        phone: str = "",
        birthdate: Optional[datetime] = None,
    ) -> None:
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
        self._results = self._history.list()
        self.resultsChanged.emit(self._results)

    def remember(self, customer: Customer) -> None:
        self._history.remember(customer)

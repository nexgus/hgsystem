"""``search`` collection 的 MongoDB 存取層 (本次啟動的搜尋記錄)."""

from pymongo.collection import Collection
from pymongo.database import Database

from ..domain.models import Customer


class SearchHistoryRepository:
    """``hgsystem.search`` collection 的存取層.

    每次程式啟動時清空; 使用者透過搜尋對話框選中的客戶會被記錄, 之後可供「記錄」
    按鈕快速重看本次工作階段內看過的客戶.
    """

    _coll: Collection

    def __init__(self, db: Database) -> None:
        """以 pymongo Database 物件建立 repository (取 ``db.search``)."""
        self._coll = db.search

    def clear(self) -> None:
        """清空所有歷史記錄 (在程式啟動時呼叫)."""
        self._coll.delete_many(filter={})

    def list(self) -> list[Customer]:
        """回傳目前所有歷史記錄."""
        return [
            Customer.from_doc(d)
            for d in self._coll.find(filter={}, allow_disk_use=True)
        ]

    def remember(self, customer: Customer) -> None:
        """記錄客戶到歷史 (依 ``_id`` 去重, 已存在則略過)."""
        if self._coll.find_one(filter={"_id": customer.id}) is None:
            self._coll.insert_one(customer.to_doc())

"""``customers`` collection 的 MongoDB 存取層."""
from bson.objectid import ObjectId
from pymongo.collection import Collection
from pymongo.database import Database

from ..domain.models import Customer


class CustomerRepository:
    """``hgsystem.customers`` collection 的 CRUD 包裝."""

    _coll: Collection

    def __init__(self, db: Database) -> None:
        """以 pymongo Database 物件建立 repository (取 ``db.customers``)."""
        self._coll = db.customers

    def count(self) -> int:
        """回傳客戶總筆數."""
        return self._coll.count_documents({})

    def find(self, filter_: dict | None = None) -> list[Customer]:
        """依 ``filter_`` 撈出客戶並轉為 ``Customer`` 物件 (預設撈全部).

        Arg(s):
            filter_: pymongo 風格的查詢條件; ``None`` 視為無條件.
        """
        return [
            Customer.from_doc(d)
            for d in self._coll.find(filter_ or {}, allow_disk_use=True)
        ]

    def get(self, cid: str) -> Customer | None:
        """以 ``_id`` 取得單一客戶, 不存在時回傳 ``None``."""
        doc = self._coll.find_one({"_id": cid})
        return Customer.from_doc(doc) if doc else None

    def insert(self, customer: Customer) -> str:
        """新增客戶; 若未指定 ``id`` 則自動以新 ``ObjectId`` 填入.

        Return(s):
            寫入後的 ``_id`` 字串.
        """
        if not customer.id:
            customer.id = str(ObjectId())
        self._coll.insert_one(customer.to_doc())
        return customer.id

    def replace(self, cid: str, customer: Customer) -> None:
        """以 ``customer`` 整筆覆寫 ``_id == cid`` 的客戶 (``_id`` 不受改動)."""
        self._coll.find_one_and_replace(
            filter={"_id": cid},
            replacement=customer.to_doc(include_id=False),
        )

    def delete(self, cid: str) -> None:
        """刪除 ``_id == cid`` 的客戶 (相關工單不在此處理)."""
        self._coll.delete_one({"_id": cid})

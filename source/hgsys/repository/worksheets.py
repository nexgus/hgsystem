"""``worksheets`` collection 的 MongoDB 存取層."""
from bson.objectid import ObjectId
from pymongo.collection import Collection
from pymongo.database import Database

from ..domain.models import Worksheet


class WorksheetRepository:
    """``hgsystem.worksheets`` collection 的 CRUD 包裝.

    工單透過 ``cid`` 對應到客戶; 不存在「客戶」概念的 cascade, 由呼叫端負責.
    """

    _coll: Collection

    def __init__(self, db: Database) -> None:
        """以 pymongo Database 物件建立 repository (取 ``db.worksheets``)."""
        self._coll = db.worksheets

    def find_for_customer(self, cid: str) -> list[Worksheet]:
        """回傳指定客戶 ``cid`` 的所有工單 (依儲存順序)."""
        return [
            Worksheet.from_doc(d)
            for d in self._coll.find({"cid": cid})
        ]

    def insert(self, worksheet: Worksheet) -> str:
        """新增工單; 若未指定 ``id`` 則自動以新 ``ObjectId`` 填入.

        Return(s):
            寫入後的 ``_id`` 字串.
        """
        if not worksheet.id:
            worksheet.id = str(ObjectId())
        self._coll.insert_one(worksheet.to_doc())
        return worksheet.id

    def replace(self, wid: str, worksheet: Worksheet) -> None:
        """以 ``worksheet`` 整筆覆寫 ``_id == wid`` 的工單."""
        self._coll.find_one_and_replace(
            filter={"_id": wid},
            replacement=worksheet.to_doc(include_id=False),
        )

    def delete(self, wid: str) -> int:
        """刪除 ``_id == wid`` 的工單.

        Return(s):
            實際刪除筆數 (0 或 1).
        """
        result = self._coll.delete_one({"_id": wid})
        return result.deleted_count

    def delete_for_customer(self, cid: str) -> int:
        """刪除指定客戶 ``cid`` 名下所有工單 (用於客戶刪除時 cascade).

        Return(s):
            實際刪除筆數.
        """
        result = self._coll.delete_many({"cid": cid})
        return result.deleted_count

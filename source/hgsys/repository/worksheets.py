from typing import Optional

from bson.objectid import ObjectId

from ..domain.models import Worksheet


class WorksheetRepository:
    def __init__(self, db):
        self._coll = db.worksheets

    def find_for_customer(self, cid: str) -> list[Worksheet]:
        return [
            Worksheet.from_doc(d)
            for d in self._coll.find({"cid": cid})
        ]

    def insert(self, worksheet: Worksheet) -> str:
        if not worksheet.id:
            worksheet.id = str(ObjectId())
        self._coll.insert_one(worksheet.to_doc())
        return worksheet.id

    def replace(self, wid: str, worksheet: Worksheet) -> None:
        self._coll.find_one_and_replace(
            filter={"_id": wid},
            replacement=worksheet.to_doc(include_id=False),
        )

    def delete(self, wid: str) -> int:
        result = self._coll.delete_one({"_id": wid})
        return result.deleted_count

    def delete_for_customer(self, cid: str) -> int:
        result = self._coll.delete_many({"cid": cid})
        return result.deleted_count

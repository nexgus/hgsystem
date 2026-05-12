from typing import Optional

from bson.objectid import ObjectId

from ..domain.models import Customer


class CustomerRepository:
    def __init__(self, db):
        self._coll = db.customers

    def count(self) -> int:
        return self._coll.count_documents({})

    def find(self, filter_: Optional[dict] = None) -> list[Customer]:
        return [
            Customer.from_doc(d)
            for d in self._coll.find(filter_ or {}, allow_disk_use=True)
        ]

    def get(self, cid: str) -> Optional[Customer]:
        doc = self._coll.find_one({"_id": cid})
        return Customer.from_doc(doc) if doc else None

    def insert(self, customer: Customer) -> str:
        if not customer.id:
            customer.id = str(ObjectId())
        self._coll.insert_one(customer.to_doc())
        return customer.id

    def replace(self, cid: str, customer: Customer) -> None:
        self._coll.find_one_and_replace(
            filter={"_id": cid},
            replacement=customer.to_doc(include_id=False),
        )

    def delete(self, cid: str) -> None:
        self._coll.delete_one({"_id": cid})

from ..domain.models import Customer


class SearchHistoryRepository:
    def __init__(self, db):
        self._coll = db.search

    def clear(self) -> None:
        self._coll.delete_many(filter={})

    def list(self) -> list[Customer]:
        return [
            Customer.from_doc(d)
            for d in self._coll.find(filter={}, allow_disk_use=True)
        ]

    def remember(self, customer: Customer) -> None:
        if self._coll.find_one(filter={"_id": customer.id}) is None:
            self._coll.insert_one(customer.to_doc())

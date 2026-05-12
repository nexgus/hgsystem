"""Domain models. Pure Python — no Qt, no Mongo."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Customer:
    id: str = ""
    name: str = ""
    title: str = ""
    birthdate: Optional[datetime] = None
    phones: str = ""  # ';'-separated raw string, as stored historically
    addr: str = ""
    broker: str = ""

    @classmethod
    def from_doc(cls, doc: dict) -> "Customer":
        return cls(
            id=doc.get("_id", ""),
            name=doc.get("name", ""),
            title=doc.get("title", ""),
            birthdate=doc.get("birthdate"),
            phones=doc.get("phones", ""),
            addr=doc.get("addr", ""),
            broker=doc.get("broker", ""),
        )

    def to_doc(self, include_id: bool = True) -> dict:
        doc = {
            "name": self.name,
            "title": self.title,
            "birthdate": self.birthdate,
            "phones": self.phones,
            "addr": self.addr,
            "broker": self.broker,
        }
        if include_id and self.id:
            doc["_id"] = self.id
        return doc

    def phone_list(self) -> list[str]:
        parts = self.phones.split(";") if self.phones else []
        while len(parts) < 4:
            parts.append("")
        return parts


@dataclass
class Worksheet:
    id: str = ""
    cid: str = ""
    order_time: Optional[datetime] = None
    deliver_time: Optional[datetime] = None
    sph_r: str = ""
    sph_l: str = ""
    cyl_r: str = ""
    cyl_l: str = ""
    axis_r: str = ""
    axis_l: str = ""
    base_r: str = ""
    base_l: str = ""
    bc_r: str = ""
    bc_l: str = ""
    bcv_r: str = ""
    bcv_l: str = ""
    bch_r: str = ""
    bch_l: str = ""
    add_r: str = ""
    add_l: str = ""
    pd: str = ""
    source: str = ""
    eyesight_r: str = ""
    eyesight_l: str = ""
    lens_r: str = ""
    lens_l: str = ""
    frame: str = ""
    memo: str = ""
    lens_price: int = 0
    frame_price: int = 0

    @classmethod
    def from_doc(cls, doc: dict) -> "Worksheet":
        return cls(
            id=doc.get("_id", ""),
            cid=doc.get("cid", ""),
            order_time=doc.get("order_time"),
            deliver_time=doc.get("deliver_time"),
            sph_r=doc.get("sph_r", ""),
            sph_l=doc.get("sph_l", ""),
            cyl_r=doc.get("cyl_r", ""),
            cyl_l=doc.get("cyl_l", ""),
            axis_r=doc.get("axis_r", ""),
            axis_l=doc.get("axis_l", ""),
            base_r=doc.get("base_r", ""),
            base_l=doc.get("base_l", ""),
            bc_r=doc.get("bc_r", ""),
            bc_l=doc.get("bc_l", ""),
            bcv_r=doc.get("bcv_r", ""),
            bcv_l=doc.get("bcv_l", ""),
            bch_r=doc.get("bch_r", ""),
            bch_l=doc.get("bch_l", ""),
            add_r=doc.get("add_r", ""),
            add_l=doc.get("add_l", ""),
            pd=doc.get("pd", ""),
            source=doc.get("source", ""),
            eyesight_r=doc.get("eyesight_r", ""),
            eyesight_l=doc.get("eyesight_l", ""),
            lens_r=doc.get("lens_r", ""),
            lens_l=doc.get("lens_l", ""),
            frame=doc.get("frame", ""),
            memo=doc.get("memo", ""),
            lens_price=int(doc.get("lens_price", 0) or 0),
            frame_price=int(doc.get("frame_price", 0) or 0),
        )

    def to_doc(self, include_id: bool = True) -> dict:
        doc = asdict(self)
        doc["_id"] = doc.pop("id")
        if not include_id:
            doc.pop("_id", None)
        return doc

"""
CatalogIQ â€“ SQLAlchemy 2.0 Async ORM Models
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProductRecord(Base):
    """Persisted enriched product row."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default="RAW")
    enrichment_source: Mapped[str] = mapped_column(String(20), default="DETERMINISTIC")

    # Raw input fields
    mfg_part_num: Mapped[str | None] = mapped_column(String(120), index=True)
    part_desc: Mapped[str | None] = mapped_column(Text)
    part_manuf_raw: Mapped[str | None] = mapped_column(String(200))
    e1_brand: Mapped[str | None] = mapped_column(String(120))
    unilog_brand: Mapped[str | None] = mapped_column(String(120))
    dib_brand: Mapped[str | None] = mapped_column(String(120))

    # Enriched fields
    manufacturer_name: Mapped[str | None] = mapped_column(String(120), index=True)
    brand_name: Mapped[str | None] = mapped_column(String(80))
    part_number: Mapped[str | None] = mapped_column(String(80))
    class_name: Mapped[str | None] = mapped_column(String(100))
    fine_class: Mapped[str | None] = mapped_column(String(100))

    # Descriptions
    short_description: Mapped[str | None] = mapped_column(String(60))
    invoice_description: Mapped[str | None] = mapped_column(String(30))
    mobile_description: Mapped[str | None] = mapped_column(Text)
    marketing_description: Mapped[str | None] = mapped_column(Text)

    # Attributes & confidence stored as JSON blobs
    attributes_json: Mapped[str | None] = mapped_column(Text, default="{}")
    confidence_json: Mapped[str | None] = mapped_column(Text, default="{}")
    validation_errors_json: Mapped[str | None] = mapped_column(Text, default="[]")

    # Audit
    review_notes: Mapped[str | None] = mapped_column(Text)
    confidence_overall: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def attributes(self) -> dict:
        try:
            return json.loads(self.attributes_json or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    @attributes.setter
    def attributes(self, value: dict) -> None:
        self.attributes_json = json.dumps(value, default=str)

    @property
    def confidence(self) -> dict:
        try:
            return json.loads(self.confidence_json or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    @confidence.setter
    def confidence(self, value: dict) -> None:
        self.confidence_json = json.dumps(value, default=str)

    @property
    def validation_errors(self) -> list:
        try:
            return json.loads(self.validation_errors_json or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @validation_errors.setter
    def validation_errors(self, value: list) -> None:
        self.validation_errors_json = json.dumps(value)


"""
CatalogIQ â€“ Database Repository Layer
Provides async CRUD for ProductRecord ORM model.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_model import ProductRecord
from app.schemas.product import (
    ConfidenceMap,
    EnrichedProduct,
    ExtractedAttributes,
    RecordStatus,
)


def enriched_product_to_orm(product: EnrichedProduct) -> ProductRecord:
    """Convert an in-memory EnrichedProduct to a ProductRecord ORM object."""
    record = ProductRecord(
        id=str(product.id),
        status=product.status.value,
        enrichment_source=product.enrichment_source,
        mfg_part_num=product.mfg_part_num,
        part_desc=product.part_desc,
        part_manuf_raw=product.part_manuf_raw,
        e1_brand=product.e1_brand,
        unilog_brand=product.unilog_brand,
        dib_brand=product.dib_brand,
        manufacturer_name=product.manufacturer_name,
        brand_name=product.brand_name,
        part_number=product.part_number,
        class_name=product.class_name,
        fine_class=product.fine_class,
        short_description=product.short_description,
        invoice_description=product.invoice_description,
        mobile_description=product.mobile_description,
        marketing_description=product.marketing_description,
        attributes_json=product.attributes.model_dump_json(),
        confidence_json=product.confidence.model_dump_json(),
        validation_errors_json=json.dumps(product.validation_errors),
        review_notes=product.review_notes,
        confidence_overall=product.confidence.overall,
    )
    return record


def orm_to_dict(record: ProductRecord) -> Dict[str, Any]:
    """Convert ORM record to a serializable dict for API responses."""
    return {
        "id": record.id,
        "status": record.status,
        "enrichment_source": record.enrichment_source,
        "mfg_part_num": record.mfg_part_num,
        "part_desc": record.part_desc,
        "part_manuf_raw": record.part_manuf_raw,
        "manufacturer_name": record.manufacturer_name,
        "brand_name": record.brand_name,
        "part_number": record.part_number,
        "class_name": record.class_name,
        "fine_class": record.fine_class,
        "short_description": record.short_description,
        "invoice_description": record.invoice_description,
        "mobile_description": record.mobile_description,
        "marketing_description": record.marketing_description,
        "attributes": record.attributes,
        "confidence": record.confidence,
        "validation_errors": record.validation_errors,
        "review_notes": record.review_notes,
        "confidence_overall": record.confidence_overall,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def row_to_enriched_product(row: Dict[str, Any]) -> EnrichedProduct:
    """Reconstruct an EnrichedProduct from a repository dict row."""
    attrs_raw = row.get("attributes") or {}
    conf_raw = row.get("confidence") or {}

    try:
        attrs = ExtractedAttributes(**attrs_raw)
    except Exception:
        attrs = ExtractedAttributes()

    try:
        conf = ConfidenceMap(**conf_raw)
    except Exception:
        conf = ConfidenceMap()

    return EnrichedProduct(
        id=row.get("id", ""),
        status=RecordStatus(row.get("status", "RAW")),
        enrichment_source=row.get("enrichment_source", "DETERMINISTIC"),
        mfg_part_num=row.get("mfg_part_num"),
        part_desc=row.get("part_desc"),
        part_manuf_raw=row.get("part_manuf_raw"),
        manufacturer_name=row.get("manufacturer_name"),
        brand_name=row.get("brand_name"),
        part_number=row.get("part_number"),
        class_name=row.get("class_name"),
        fine_class=row.get("fine_class"),
        short_description=row.get("short_description"),
        invoice_description=row.get("invoice_description"),
        mobile_description=row.get("mobile_description"),
        marketing_description=row.get("marketing_description"),
        attributes=attrs,
        confidence=conf,
        validation_errors=row.get("validation_errors") or [],
        review_notes=row.get("review_notes"),
    )


class ProductRepository:
    """Async data access layer for ProductRecord."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert(self, product: EnrichedProduct) -> ProductRecord:
        """Insert or replace a product record."""
        record = enriched_product_to_orm(product)
        # Merge (upsert) using SQLAlchemy session
        merged = await self._db.merge(record)
        return merged

    async def get_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(ProductRecord).where(ProductRecord.id == product_id)
        result = await self._db.execute(stmt)
        record = result.scalar_one_or_none()
        return orm_to_dict(record) if record else None

    async def list_products(
        self,
        status: Optional[RecordStatus] = None,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
    ) -> Tuple[int, List[Dict[str, Any]]]:
        base_query = select(ProductRecord)

        if status:
            base_query = base_query.where(ProductRecord.status == status.value)

        if search:
            pattern = f"%{search}%"
            base_query = base_query.where(
                or_(
                    ProductRecord.mfg_part_num.ilike(pattern),
                    ProductRecord.part_desc.ilike(pattern),
                    ProductRecord.manufacturer_name.ilike(pattern),
                )
            )

        # Count
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self._db.execute(count_query)
        total = total_result.scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        data_query = (
            base_query
            .order_by(ProductRecord.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        data_result = await self._db.execute(data_query)
        records = data_result.scalars().all()

        return total, [orm_to_dict(r) for r in records]

    async def update_product(
        self, product_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Handle nested attributes dict
        if "attributes" in updates:
            updates["attributes_json"] = json.dumps(updates.pop("attributes"), default=str)

        stmt = (
            update(ProductRecord)
            .where(ProductRecord.id == product_id)
            .values(**updates)
            .returning(ProductRecord)
        )
        result = await self._db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError(f"Product {product_id} not found for update.")
        return orm_to_dict(record)


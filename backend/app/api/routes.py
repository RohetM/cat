"""
CatalogIQ â€“ FastAPI Route Handlers
====================================
Endpoints:
  POST /api/v1/enrich/batch        â€“ Upload & process input CSV
  GET  /api/v1/products            â€“ Paginated product list with status filter
  PUT  /api/v1/products/{id}/review â€“ Human override (HITL)
  GET  /api/v1/evaluate            â€“ Ground-truth evaluation metrics
  GET  /api/v1/export              â€“ Download 252-column delivery CSV
  GET  /api/v1/jobs/{job_id}       â€“ Async job status polling
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.db.repository import ProductRepository
from app.schemas.product import (
    BatchEnrichResponse,
    EvaluationMetrics,
    ProductListResponse,
    RecordStatus,
    ReviewRequest,
)
from app.services.hybrid_engine import HybridEnrichmentEngine
from app.services.ingestion_service import parse_input_csv
from app.services.validator import (
    GroundTruthEvaluator,
    ValidationEngine,
    build_export_csv,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["CatalogIQ"])

# ---------------------------------------------------------------------------
# Shared singletons (created once at startup, reused across requests)
# ---------------------------------------------------------------------------

_engine = HybridEnrichmentEngine()
_validator = ValidationEngine()
_evaluator = GroundTruthEvaluator()

# In-memory job tracker { job_id: { status, total, done, errors } }
_jobs: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# POST /api/v1/enrich/batch
# ---------------------------------------------------------------------------

@router.post(
    "/enrich/batch",
    response_model=BatchEnrichResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload supplier CSV and trigger async enrichment pipeline",
)
async def enrich_batch(
    file: UploadFile = File(..., description="Supplier input CSV (â‰¤6 columns)"),
    db: AsyncSession = Depends(get_db),
) -> BatchEnrichResponse:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are accepted.",
        )

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_bytes // 1_048_576} MB limit.",
        )

    records, parse_warnings = parse_input_csv(content)
    if not records:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid records found in the uploaded CSV.",
        )

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "QUEUED",
        "total": len(records),
        "done": 0,
        "errors": [],
        "warnings": parse_warnings,
    }

    # Fire-and-forget enrichment task
    asyncio.create_task(_run_enrichment_job(job_id, records, db))

    return BatchEnrichResponse(
        job_id=job_id,
        status="QUEUED",
        total_records=len(records),
        message=f"Enrichment job queued. {len(parse_warnings)} parse warning(s).",
    )


async def _run_enrichment_job(
    job_id: str,
    records: list,
    db: AsyncSession,
) -> None:
    """Background task: enrich records and persist to DB."""
    repo = ProductRepository(db)
    _jobs[job_id]["status"] = "PROCESSING"
    try:
        enriched_products = await _engine.process_batch(records, concurrency=settings.batch_concurrency)
        for product in enriched_products:
            validated = _validator.validate(product)
            await repo.upsert(validated)
            _jobs[job_id]["done"] += 1

        await db.commit()
        _jobs[job_id]["status"] = "COMPLETED"
        logger.info("Job %s completed: %d records.", job_id, len(enriched_products))

    except Exception as exc:
        logger.error("Job %s failed: %s", job_id, exc)
        _jobs[job_id]["status"] = "FAILED"
        _jobs[job_id]["errors"].append(str(exc))
        await db.rollback()


# ---------------------------------------------------------------------------
# GET /api/v1/jobs/{job_id}
# ---------------------------------------------------------------------------

@router.get(
    "/jobs/{job_id}",
    summary="Poll enrichment job status",
)
async def get_job_status(job_id: str) -> Dict[str, Any]:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {"job_id": job_id, **job}


# ---------------------------------------------------------------------------
# GET /api/v1/products
# ---------------------------------------------------------------------------

@router.get(
    "/products",
    response_model=ProductListResponse,
    summary="List enriched products with optional status filter and pagination",
)
async def list_products(
    status_filter: Optional[RecordStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None, description="Search part number or description"),
    db: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    repo = ProductRepository(db)
    total, items = await repo.list_products(
        status=status_filter,
        page=page,
        page_size=page_size,
        search=search,
    )
    return ProductListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/products/{product_id}
# ---------------------------------------------------------------------------

@router.get(
    "/products/{product_id}",
    summary="Get a single product by UUID",
)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


# ---------------------------------------------------------------------------
# PUT /api/v1/products/{product_id}/review
# ---------------------------------------------------------------------------

@router.put(
    "/products/{product_id}/review",
    summary="Human-in-the-Loop override: approve and correct a product record",
    status_code=status.HTTP_200_OK,
)
async def review_product(
    product_id: str,
    body: ReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Apply human overrides
    updates: Dict[str, Any] = {k: v for k, v in body.model_dump().items() if v is not None}
    updates["status"] = RecordStatus.APPROVED.value
    updates["enrichment_source"] = "HUMAN"

    updated = await repo.update_product(product_id, updates)
    await db.commit()
    return updated


# ---------------------------------------------------------------------------
# GET /api/v1/evaluate
# ---------------------------------------------------------------------------

@router.get(
    "/evaluate",
    response_model=EvaluationMetrics,
    summary="Evaluate enriched records against expected delivery CSV",
)
async def evaluate(
    db: AsyncSession = Depends(get_db),
) -> EvaluationMetrics:
    repo = ProductRepository(db)
    _, raw_items = await repo.list_products(page=1, page_size=10_000)

    # Reconstruct EnrichedProduct objects from DB rows for evaluation
    from app.db.repository import row_to_enriched_product
    products = [row_to_enriched_product(item) for item in raw_items]

    metrics = _evaluator.evaluate(products)
    return metrics


@router.post(
    "/evaluate/upload-expected",
    summary="Upload the expected delivery CSV for ground-truth comparison",
    status_code=status.HTTP_200_OK,
)
async def upload_expected_csv(
    file: UploadFile = File(..., description="Expected delivery format CSV"),
) -> Dict[str, Any]:
    content = await file.read()
    _evaluator.load_from_bytes(content)
    return {"message": "Expected CSV loaded successfully."}


# ---------------------------------------------------------------------------
# GET /api/v1/export
# ---------------------------------------------------------------------------

@router.get(
    "/export",
    summary="Download enriched products as 252-column delivery CSV",
)
async def export_csv(
    status_filter: Optional[RecordStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    repo = ProductRepository(db)
    _, raw_items = await repo.list_products(status=status_filter, page=1, page_size=100_000)

    from app.db.repository import row_to_enriched_product
    products = [row_to_enriched_product(item) for item in raw_items]
    csv_content = build_export_csv(products)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=catalogiq_export.csv"},
    )


# ---------------------------------------------------------------------------
# GET /api/v1/stats
# ---------------------------------------------------------------------------

@router.get(
    "/stats",
    summary="Dashboard summary statistics",
)
async def get_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    repo = ProductRepository(db)

    total_raw,      _ = await repo.list_products(status=RecordStatus.RAW,            page=1, page_size=1)
    total_enriched, _ = await repo.list_products(status=RecordStatus.ENRICHED,       page=1, page_size=1)
    total_review,   _ = await repo.list_products(status=RecordStatus.REQUIRES_REVIEW, page=1, page_size=1)
    total_approved, _ = await repo.list_products(status=RecordStatus.APPROVED,        page=1, page_size=1)
    total_all,      _ = await repo.list_products(page=1, page_size=1)

    return {
        "total": total_all,
        "raw": total_raw,
        "enriched": total_enriched,
        "requires_review": total_review,
        "approved": total_approved,
        "active_jobs": len([j for j in _jobs.values() if j["status"] in ("QUEUED", "PROCESSING")]),
    }


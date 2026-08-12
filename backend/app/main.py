"""
CatalogIQ â€“ FastAPI Application Entry Point
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import init_db
from app.api.routes import router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s â€“ %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan  (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ðŸš€ CatalogIQ starting up â€“ initialising databaseâ€¦")
    await init_db()
    logger.info("âœ… Database ready.")
    yield
    logger.info("ðŸ›‘ CatalogIQ shutting down.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Enterprise AI Product Enrichment, Validation & Governance System "
        "for B2B Distributor Catalogs."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Rate-limiting middleware (simple in-memory token bucket)
# ---------------------------------------------------------------------------

from collections import defaultdict
import time

_request_counts: Dict[str, list] = defaultdict(list)
_WINDOW_SECONDS = 60


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - _WINDOW_SECONDS

    # Clean old entries
    _request_counts[client_ip] = [
        t for t in _request_counts[client_ip] if t > window_start
    ]

    if len(_request_counts[client_ip]) >= settings.rate_limit_rpm:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please retry after 60 seconds."},
        )

    _request_counts[client_ip].append(now)
    return await call_next(request)


# ---------------------------------------------------------------------------
# Centralized exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation error", "detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": "An unexpected error occurred."},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(router)


@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    return {"status": "healthy", "version": settings.app_version}


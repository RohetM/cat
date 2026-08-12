# CatalogIQ

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat)](https://docs.pydantic.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![UniHack](https://img.shields.io/badge/Unilog-UniHack%202024-6366F1?style=flat)](https://unilog.com)

**Enterprise AI Product Enrichment, Validation & Governance System**

*Transforms sparse supplier rows into rich, standardized 252-column B2B commerce records using a Deterministic-First + LLM Fallback + Human-in-the-Loop pipeline.*

[Live Demo](#quick-start) · [API Docs](http://localhost:8000/docs) · [Architecture](#architecture) · [Endpoints](#api-reference)

</div>

---

## Problem Statement

Industrial B2B distributors receive tens of thousands of raw product records from suppliers every month. These records are:

- **Incomplete** — missing dimensions, grit, UOM, product type
- **Inconsistent** — `"Freud Inc (2435)"` vs `"FREUD"` vs `"Freud"`
- **Unstructured** — all data packed into a single `Part_Desc` free-text field

Manual enrichment is slow, error-prone, and unscalable. Raw LLM-only pipelines hallucinate values with no confidence signal and no human safety net.

**CatalogIQ solves this with a three-layer trust architecture.**

---

## Architecture

```
Supplier CSV (6 cols)
        │
        ▼
┌───────────────────┐
│  Ingestion Layer  │  CSV parse · UUID assign · CSV injection sanitize
└────────┬──────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  HYBRID ENRICHMENT ENGINE                       │
│                                                                 │
│  Layer 1 – Deterministic (always runs first)                   │
│  ├─ Regex: grit (P80/150grit), dims (WxL), qty (6pc/10pk)      │
│  ├─ RapidFuzz: manufacturer + brand entity resolution           │
│  └─ Keyword tables: product type, abrasive material             │
│                                                                 │
│  Layer 2 – LLM Fallback (triggered only when conf < 0.85)      │
│  ├─ OpenAI GPT-4o-mini  OR  Google Gemini 1.5 Flash            │
│  ├─ XML prompt-injection guard + Pydantic output schema         │
│  └─ Merges only empty / low-confidence fields                   │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌───────────────────┐
│  Validation Engine│  Length limits · UOM codes · Required fields
└────────┬──────────┘
         │
    conf ≥ 0.85?
    ┌────┴────┐
   YES        NO
    │          │
    ▼          ▼
ENRICHED   REQUIRES_REVIEW ──► HITL Queue (PUT /review → APPROVED)
    │          │
    └────┬─────┘
         ▼
┌───────────────────┐
│  Export (252-col) │  Streaming CSV · All unset cols default ""
└───────────────────┘
```

### Confidence Scoring Weights

| Field | Weight |
|---|---|
| `manufacturer_name` | 0.20 |
| `product_type` | 0.15 |
| `brand_name` | 0.10 |
| `part_number` | 0.10 |
| `grit` | 0.10 |
| `dimensions` | 0.10 |
| `short_description` | 0.10 |
| `invoice_description` | 0.10 |
| `package_quantity` | 0.05 |

Records scoring `overall < 0.85` are routed to the HITL review queue. Records approved by a human specialist are marked `APPROVED` with `enrichment_source = HUMAN`.

---

## Directory Structure

```
cat/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app · CORS · rate limiting · exception handlers
│   │   ├── core/
│   │   │   └── config.py               # pydantic-settings typed config (env-driven)
│   │   ├── schemas/
│   │   │   └── product.py              # All Pydantic v2 models + 252-column DELIVERY_COLUMNS list
│   │   ├── models/
│   │   │   └── product_model.py        # SQLAlchemy 2.0 mapped_column ORM
│   │   ├── db/
│   │   │   ├── session.py              # Async engine · AsyncSessionLocal · get_db()
│   │   │   └── repository.py           # ProductRepository CRUD + converters
│   │   ├── services/
│   │   │   ├── ingestion_service.py    # CSV parse · sanitize · header normalise
│   │   │   ├── hybrid_engine.py        # DeterministicEngine + LLMFallbackEngine + Orchestrator
│   │   │   └── validator.py            # ValidationEngine · GroundTruthEvaluator · CSV builder
│   │   └── api/
│   │       └── routes.py               # All 9 FastAPI route handlers
│   ├── _smoke_test.py                  # End-to-end pipeline smoke test
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/app/
│   │   ├── layout.tsx                  # Root layout + metadata
│   │   ├── page.tsx                    # Redirects → /dashboard
│   │   ├── globals.css                 # Tailwind base
│   │   ├── dashboard/
│   │   │   └── page.tsx               # KPI cards · Recharts · accuracy bars · pipeline diagram
│   │   └── review/
│   │       └── page.tsx               # HITL queue · upload card · slide-over review panel
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── next.config.ts
│
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI **or** Google Gemini API key (optional — pipeline runs in deterministic-only mode without one)

### Backend

```bash
# 1. Clone the repository
git clone https://github.com/RohetM/cat.git
cd cat/backend

# 2. Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — add OPENAI_API_KEY or GEMINI_API_KEY

# 5. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at **http://localhost:8000/docs**
ReDoc available at **http://localhost:8000/redoc**

### Frontend

```bash
cd cat/frontend

# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.local.example .env.local
# Default: NEXT_PUBLIC_API_URL=http://localhost:8000

# 3. Start dev server
npm run dev
```

App available at **http://localhost:3000** (auto-redirects to `/dashboard`)

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/enrich/batch` | Upload 6-col supplier CSV → returns `job_id` immediately |
| `GET` | `/api/v1/jobs/{job_id}` | Poll async job: `QUEUED` → `PROCESSING` → `COMPLETED` |
| `GET` | `/api/v1/products` | Paginated list — filter by `?status=REQUIRES_REVIEW` |
| `GET` | `/api/v1/products/{id}` | Single product with full confidence breakdown |
| `PUT` | `/api/v1/products/{id}/review` | HITL override — sets status to `APPROVED` |
| `GET` | `/api/v1/evaluate` | 5-metric accuracy report vs ground-truth CSV |
| `POST` | `/api/v1/evaluate/upload-expected` | Load expected delivery CSV for benchmarking |
| `GET` | `/api/v1/export` | Stream full 252-column delivery CSV download |
| `GET` | `/api/v1/stats` | Dashboard KPIs (counts by status, active jobs) |
| `GET` | `/health` | Liveness check |

### Example: Upload CSV

```bash
curl -X POST http://localhost:8000/api/v1/enrich/batch \
  -F "file=@Unihack_Sample_Dataset_Input.csv"
```

Response:
```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "QUEUED",
  "total_records": 150,
  "message": "Enrichment job queued. 0 parse warning(s)."
}
```

### Example: HITL Override

```bash
curl -X PUT http://localhost:8000/api/v1/products/{id}/review \
  -H "Content-Type: application/json" \
  -d '{
    "manufacturer_name": "3M",
    "brand_name": "3M",
    "short_description": "3M 314D P80 Flap Disc 4.5in 10pk",
    "invoice_description": "3M Flap Disc P80",
    "review_notes": "Brand confirmed from E1_Brand field."
  }'
```

### Example: Export 252-Col CSV

```bash
curl http://localhost:8000/api/v1/export \
  -o catalogiq_export.csv
```

---

## Testing

### Smoke Test (End-to-End Pipeline)

Runs ingestion → deterministic extraction → validation → 252-col CSV export with assertions:

```bash
cd backend
python _smoke_test.py
```

Expected output:
```
[INGEST] 3 records parsed, 0 warnings
[RESULTS]
  [ENRICHED         ] DCB518ASTS06G             manuf=FREUD  brand=DIABLO  grit=None  dims=0.5x18.0  qty=6  conf=0.900
  [REQUIRES_REVIEW  ] 3M-314D-P80               manuf=3M     brand=3M      grit=P80   dims=None       qty=10 conf=0.710
  [ENRICHED         ] NOR-66261131655            manuf=NORTON brand=NORTON  grit=P120  dims=1.0x42.0   qty=None conf=0.860
[EXPORT] 3 rows, 252 columns
All smoke-test assertions PASSED
```

### API Smoke Test (requires running server)

```bash
# Health check
curl http://localhost:8000/health

# Upload sample data and get job ID
curl -X POST http://localhost:8000/api/v1/enrich/batch \
  -F "file=@backend/_smoke_test.py"  # replace with real CSV

# Stats
curl http://localhost:8000/api/v1/stats
```

---

## Security

| Control | Implementation |
|---------|---------------|
| CSV Injection | Pydantic validator strips leading `=` `@` `+` `-` from all input fields |
| Prompt Injection | LLM inputs wrapped in `<product_enrichment_task>` XML envelope |
| LLM Hallucination Guard | All LLM JSON outputs validated through `LLMEnrichmentResponse` Pydantic schema |
| CORS | Configurable allowlist via `CORS_ORIGINS` environment variable |
| Rate Limiting | In-memory token bucket — `RATE_LIMIT_RPM` requests/IP/60s |
| No Trace Leakage | Centralized exception handlers return sanitized JSON — no stack traces |
| Secret Management | All keys via `pydantic-settings` + `.env` — never hardcoded |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./catalogiq.db` | Async DB connection string |
| `OPENAI_API_KEY` | _(empty)_ | OpenAI API key (optional) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `GEMINI_API_KEY` | _(empty)_ | Google Gemini API key (optional) |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model name |
| `CONFIDENCE_THRESHOLD` | `0.85` | Minimum score for auto-enrichment |
| `BATCH_CONCURRENCY` | `10` | Max parallel LLM calls per batch |
| `MAX_UPLOAD_BYTES` | `52428800` | Max CSV upload size (50 MB) |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins |
| `RATE_LIMIT_RPM` | `60` | Requests per IP per minute |

---

## Tech Stack

**Backend**
- Python 3.11 · FastAPI 0.111 · Uvicorn
- Pydantic v2 · pydantic-settings
- SQLAlchemy 2.0 Async · aiosqlite (dev) · asyncpg (prod)
- Pandas · RapidFuzz
- OpenAI SDK v2 · Google GenerativeAI SDK

**Frontend**
- Next.js 14 (App Router) · TypeScript
- Tailwind CSS · Recharts

---

## License

MIT © 2024 RohetM — Built for Unilog UniHack

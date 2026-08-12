# CatalogIQ

<div align="center">

[![Live Demo](https://img.shields.io/badge/Live%20Demo-CatalogIQ%20Studio-00C7B7?style=for-the-badge&logo=render&logoColor=white)](https://catalogiq-frontend.onrender.com/demo)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat)](https://docs.pydantic.dev)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat&logo=docker&logoColor=white)](docker-compose.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![UniHack](https://img.shields.io/badge/Unilog-UniHack%202024-6366F1?style=flat)](https://unilog.com)

**Enterprise Deterministic-First AI Product Enrichment, Validation & Governance System**

*Transforms sparse 6-column supplier CSV rows into standardized, guaranteed 252-column B2B commerce records using a high-throughput 3-layer trust architecture.*

### 🚀 **[Try Live Demo Studio](https://catalogiq-frontend.onrender.com/demo)**

[Live Demo (Cloud)](https://catalogiq-frontend.onrender.com/demo) · [HITL Review Queue](https://catalogiq-frontend.onrender.com/review) · [Metrics Dashboard](https://catalogiq-frontend.onrender.com/dashboard) · [Architecture](#3-layer-trust-architecture) · [Docker Quick Start](#quick-start-docker--local)

</div>

---

## Problem Statement

Industrial B2B distributors receive tens of thousands of raw, incomplete product records from suppliers every month:
- **Incomplete & Sparse** — Sparse 6-column CSVs missing dimensions, grit, UOM, and product types.
- **Inconsistent Aliases** — Brand misspellings like `"Freud Inc (2435)"` vs `"FREUD"` vs `"DIABLO"`.
- **Unstructured Text** — All physical parameters crammed into an unstructured `Part_Desc` text blob.

### The Breakdown of Traditional Approaches
* **Manual Data Entry:** Takes 2–4 weeks per catalog, incurs thousands in labor costs, and suffers from human fatigue.
* **Naive LLM Pipelines:** Prone to unconstrained hallucinations, non-deterministic schema drift, 2–5s latency/SKU, and prohibitive token costs.

**CatalogIQ solves this with a mathematically grounded 3-Layer Trust Architecture.**

---

## 3-Layer Trust Architecture

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
│  Layer 1 – Deterministic (<1ms, 0 Token Cost)                   │
│  ├─ Regex: grit (P80/120), dims (WxL), qty (6pc/10pk)           │
│  ├─ RapidFuzz: canonical manufacturer & brand entity resolution │
│  └─ Keyword taxonomy tables & UOM standardizer                  │
│                                                                 │
│  Layer 2 – LLM Fallback (triggered ONLY when conf < 0.85)       │
│  ├─ OpenAI GPT-4o-mini OR Google Gemini 1.5 Flash               │
│  ├─ XML prompt-injection guard + Pydantic v2 JSON schema        │
│  └─ Merges only empty or low-confidence fields                  │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌───────────────────┐
│  Validation Engine│  Length rules · Valid UOM codes · Required fields
└────────┬──────────┘
         │
    conf ≥ 0.85?
    ┌────┴────┐
   YES        NO
    │          │
    ▼          ▼
ENRICHED   REQUIRES_REVIEW ──► Layer 3: HITL Review Queue (1-Click Approve)
    │          │
    └────┬─────┘
         ▼
┌───────────────────┐
│  Export (252-col) │  Guaranteed 252-Column CSV Streaming Export
└───────────────────┘
```

### Confidence Scoring & Routing Strategy

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

* Records scoring `overall >= 0.85` pass directly into production.
* Records scoring `overall < 0.85` escalate to the **Human-in-the-Loop (HITL)** queue for visual side-by-side diff verification.

---

## Quick Start (Docker & Local)

### Option A: Docker Compose (Recommended)

Run both backend and frontend in isolated production containers with one command:

```bash
git clone https://github.com/RohetM/cat.git
cd cat
docker compose up --build
```

Access the services:
* **Interactive Demo Showcase:** [http://localhost:3000/demo](http://localhost:3000/demo)
* **HITL Review Queue:** [http://localhost:3000/review](http://localhost:3000/review)
* **Metrics & Evaluation Dashboard:** [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
* **FastAPI Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option B: Local Development

#### 1. Backend Setup (FastAPI + Python 3.11)

```bash
cd backend
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env

# Run smoke test & seed data
python _smoke_test.py
python populate.py

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend Setup (Next.js 14 + Tailwind)

```bash
cd frontend
npm install
npm run dev
```

The frontend will run on [http://localhost:3000](http://localhost:3000).

---

## Directory Structure

```
RohetM-cat/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py             # FastAPI REST endpoints
│   │   ├── core/
│   │   │   └── config.py             # Settings & confidence thresholds
│   │   ├── db/
│   │   │   ├── repository.py         # SQLAlchemy async CRUD
│   │   │   └── session.py            # SQLite / PostgreSQL engine
│   │   ├── schemas/
│   │   │   └── product.py            # Pydantic v2 252-column schemas
│   │   ├── services/
│   │   │   ├── hybrid_engine.py      # Layer 1 & 2 orchestration
│   │   │   ├── ingestion_service.py  # CSV sanitize & tokenization
│   │   │   ├── llm_service.py        # GPT-4o-mini & Gemini clients
│   │   │   ├── regex_parser.py       # Deterministic regex patterns
│   │   │   └── validator.py          # Ground truth evaluator & exporter
│   │   └── main.py                   # App factory & rate limiter
│   ├── Dockerfile
│   ├── requirements.txt
│   └── _smoke_test.py
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── demo/page.tsx         # Interactive Demo Showcase Studio
│   │       ├── dashboard/page.tsx    # Metrics & Accuracy Dashboard
│   │       ├── review/page.tsx       # Side-by-side HITL Review Queue
│   │       ├── layout.tsx
│   │       └── page.tsx
│   ├── Dockerfile
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml
├── render.yaml                       # Render Blueprint cloud deployment (Free tier)
├── vendor_feed_raw.csv               # Sample raw vendor test feed
└── README.md
```

---

## Live Demo & Cloud Deployment (Render)

> 🚀 **Live Production Demo:** **[https://catalogiq-frontend.onrender.com/demo](https://catalogiq-frontend.onrender.com/demo)**
> - **Interactive Demo Studio:** [https://catalogiq-frontend.onrender.com/demo](https://catalogiq-frontend.onrender.com/demo)
> - **HITL Review Queue:** [https://catalogiq-frontend.onrender.com/review](https://catalogiq-frontend.onrender.com/review)
> - **Metrics & Evaluation Dashboard:** [https://catalogiq-frontend.onrender.com/dashboard](https://catalogiq-frontend.onrender.com/dashboard)

Deploy your own instance of CatalogIQ to Render with zero credit card required:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Go to **[Render Dashboard](https://dashboard.render.com)** → **New +** → **Blueprint**.
2. Select repository `RohetM/cat`.
3. Render automatically provisions `catalogiq-backend` (FastAPI) and `catalogiq-frontend` (Next.js standalone).
4. Optionally supply `OPENAI_API_KEY` / `GEMINI_API_KEY` in the environment settings (or run 100% deterministically with 0 API keys).
5. Click **Apply** to deploy!


---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/enrich/batch` | Upload 6-col supplier CSV → returns async `job_id` |
| `GET` | `/api/v1/jobs/{job_id}` | Poll enrichment job: `QUEUED` → `PROCESSING` → `COMPLETED` |
| `GET` | `/api/v1/products` | Paginated product list with status filter (`?status=REQUIRES_REVIEW`) |
| `GET` | `/api/v1/products/{id}` | Single product with granular confidence scores |
| `PUT` | `/api/v1/products/{id}/review` | HITL human override — transitions status to `APPROVED` |
| `GET` | `/api/v1/evaluate` | 5-metric ground-truth precision & accuracy report |
| `POST` | `/api/v1/evaluate/upload-expected`| Upload expected delivery CSV for real-time benchmark |
| `GET` | `/api/v1/export` | Stream guaranteed 252-column master catalog CSV |
| `GET` | `/api/v1/stats` | Dashboard KPIs (record counts, accuracy, active jobs) |
| `GET` | `/health` | Liveness health check |

---

## Security & Reliability Controls

| Control | Implementation |
|---------|----------------|
| **CSV Injection Guard** | Strips leading `=`, `@`, `+`, `-` from untrusted input cells |
| **Prompt Injection Defense** | LLM inputs wrapped in structured `<product_enrichment_task>` XML envelopes |
| **Zero Hallucination Guarantee**| All LLM JSON responses parsed through strict Pydantic v2 schemas |
| **CORS Protection** | Origin-controlled allowlist via `CORS_ORIGINS` |
| **Rate Limiting** | In-memory token bucket enforcing request limits per IP |
| **No Trace Leakage** | Sanitized exception handlers preventing stack trace leakage |

---

## Tech Stack

* **Backend:** Python 3.11 · FastAPI 0.111 · Pydantic v2 · SQLAlchemy 2.0 Async · RapidFuzz · Pandas · Uvicorn
* **Frontend:** Next.js 14 · React 18 · TypeScript · Tailwind CSS · Recharts
* **AI Fallback:** OpenAI GPT-4o-mini · Google Gemini 1.5 Flash (Strict JSON Schema Enforcement)
* **DevOps:** Docker · Docker Compose · Multi-stage Container Builds

---

## Repository & Submission Details

* **Live Demo:** [https://catalogiq-frontend.onrender.com/demo](https://catalogiq-frontend.onrender.com/demo)
* **Repository:** [https://github.com/RohetM/cat](https://github.com/RohetM/cat)
* **Event:** Unilog UniHack 2024
* **License:** MIT

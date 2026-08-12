"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

type RecordStatus = "RAW" | "ENRICHED" | "REQUIRES_REVIEW" | "APPROVED";

interface Product {
  id: string;
  status: RecordStatus;
  enrichment_source: string;
  mfg_part_num: string | null;
  part_desc: string | null;
  manufacturer_name: string | null;
  brand_name: string | null;
  part_number: string | null;
  class_name: string | null;
  fine_class: string | null;
  short_description: string | null;
  invoice_description: string | null;
  mobile_description: string | null;
  marketing_description: string | null;
  attributes: Record<string, unknown>;
  confidence: Record<string, number>;
  confidence_overall: number;
  validation_errors: string[];
  review_notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

interface ProductListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Product[];
}

interface ReviewForm {
  manufacturer_name: string;
  brand_name: string;
  part_number: string;
  short_description: string;
  invoice_description: string;
  class_name: string;
  fine_class: string;
  review_notes: string;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const STATUS_CONFIG: Record<
  RecordStatus,
  { label: string; bg: string; text: string; dot: string }
> = {
  RAW:             { label: "Raw",            bg: "bg-slate-100",  text: "text-slate-600",  dot: "bg-slate-400"  },
  ENRICHED:        { label: "Enriched",       bg: "bg-blue-50",   text: "text-blue-700",   dot: "bg-blue-500"   },
  REQUIRES_REVIEW: { label: "Needs Review",   bg: "bg-amber-50",  text: "text-amber-700",  dot: "bg-amber-500"  },
  APPROVED:        { label: "Approved",       bg: "bg-green-50",  text: "text-green-700",  dot: "bg-green-500"  },
};

// ─── Utility helpers ──────────────────────────────────────────────────────────

function confColor(score: number): string {
  if (score >= 0.85) return "bg-green-500";
  if (score >= 0.6)  return "bg-amber-400";
  return "bg-red-400";
}

function confLabel(score: number): string {
  if (score >= 0.85) return "High";
  if (score >= 0.6)  return "Medium";
  return "Low";
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "API error");
  }
  return res.json() as Promise<T>;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: RecordStatus }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.RAW;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  return (
    <div className="flex items-center gap-2 min-w-0">
      <div className="flex-1 h-1.5 rounded-full bg-gray-200 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${confColor(score)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 tabular-nums w-8 text-right">
        {pct}%
      </span>
    </div>
  );
}

function FieldDiff({
  label,
  original,
  enriched,
  edited,
  onChange,
  maxLength,
  editable,
}: {
  label: string;
  original?: string | null;
  enriched?: string | null;
  edited: string;
  onChange: (v: string) => void;
  maxLength?: number;
  editable?: boolean;
}) {
  const hasChange = enriched && enriched !== original;
  return (
    <div className="space-y-1">
      <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider">
        {label}
        {maxLength && (
          <span className="ml-1 font-normal normal-case text-gray-400">
            (max {maxLength})
          </span>
        )}
      </label>

      {/* Raw vs Enriched side-by-side */}
      <div className="grid grid-cols-2 gap-2 text-xs mb-1">
        <div className="rounded bg-gray-50 border border-gray-200 px-2 py-1 text-gray-400 truncate">
          <span className="font-medium text-gray-400">Raw: </span>
          {original || <em className="italic">—</em>}
        </div>
        <div
          className={`rounded border px-2 py-1 truncate ${
            hasChange
              ? "bg-blue-50 border-blue-200 text-blue-800"
              : "bg-gray-50 border-gray-200 text-gray-500"
          }`}
        >
          <span className="font-medium">AI: </span>
          {enriched || <em className="italic">—</em>}
        </div>
      </div>

      {/* Human override input */}
      {editable !== false && (
        <input
          type="text"
          value={edited}
          maxLength={maxLength}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Override value…"
        />
      )}
    </div>
  );
}

// ─── Review Panel ─────────────────────────────────────────────────────────────

function ReviewPanel({
  product,
  onClose,
  onApproved,
}: {
  product: Product;
  onClose: () => void;
  onApproved: (updated: Product) => void;
}) {
  const [form, setForm] = useState<ReviewForm>({
    manufacturer_name:   product.manufacturer_name   ?? "",
    brand_name:          product.brand_name          ?? "",
    part_number:         product.part_number         ?? "",
    short_description:   product.short_description   ?? "",
    invoice_description: product.invoice_description ?? "",
    class_name:          product.class_name          ?? "",
    fine_class:          product.fine_class          ?? "",
    review_notes:        product.review_notes        ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setField = (key: keyof ReviewForm) => (val: string) =>
    setForm((prev) => ({ ...prev, [key]: val }));

  const handleApprove = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await apiFetch<Product>(
        `/api/v1/products/${product.id}/review`,
        {
          method: "PUT",
          body: JSON.stringify(form),
        }
      );
      onApproved(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  };

  const confPct = Math.round((product.confidence_overall ?? 0) * 100);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end bg-black/30 backdrop-blur-sm">
      <div className="w-full max-w-2xl h-full bg-white shadow-2xl overflow-y-auto flex flex-col">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-gray-900">
              Human Review
            </h2>
            <p className="text-xs text-gray-500 mt-0.5 font-mono">
              {product.id}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Summary bar */}
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200 grid grid-cols-3 gap-4 text-xs">
          <div>
            <p className="text-gray-400 uppercase tracking-wider font-semibold mb-1">Status</p>
            <StatusBadge status={product.status} />
          </div>
          <div>
            <p className="text-gray-400 uppercase tracking-wider font-semibold mb-1">AI Confidence</p>
            <div className="flex items-center gap-2">
              <span
                className={`font-bold text-sm ${
                  confPct >= 85 ? "text-green-600" : confPct >= 60 ? "text-amber-600" : "text-red-600"
                }`}
              >
                {confPct}%
              </span>
              <span className="text-gray-400">({confLabel(product.confidence_overall ?? 0)})</span>
            </div>
          </div>
          <div>
            <p className="text-gray-400 uppercase tracking-wider font-semibold mb-1">Source</p>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-purple-700">
              {product.enrichment_source}
            </span>
          </div>
        </div>

        {/* Validation errors */}
        {product.validation_errors.length > 0 && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-red-50 border border-red-200">
            <p className="text-xs font-semibold text-red-700 mb-1.5">
              ⚠ Validation Errors ({product.validation_errors.length})
            </p>
            <ul className="space-y-0.5">
              {product.validation_errors.map((e, i) => (
                <li key={i} className="text-xs text-red-600 font-mono">
                  • {e}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Raw description */}
        <div className="mx-6 mt-4 p-3 rounded-lg bg-amber-50 border border-amber-200">
          <p className="text-xs font-semibold text-amber-700 mb-1">Original Part Description</p>
          <p className="text-sm text-amber-900">{product.part_desc || "—"}</p>
        </div>

        {/* Field overrides */}
        <div className="px-6 pt-5 pb-2 space-y-5 flex-1">
          <h3 className="text-sm font-semibold text-gray-700 border-b border-gray-100 pb-2">
            Identity &amp; Classification
          </h3>

          <FieldDiff
            label="Manufacturer Name"
            original={product.part_manuf_raw}
            enriched={product.manufacturer_name}
            edited={form.manufacturer_name}
            onChange={setField("manufacturer_name")}
            maxLength={120}
          />
          <FieldDiff
            label="Brand Name"
            original={null}
            enriched={product.brand_name}
            edited={form.brand_name}
            onChange={setField("brand_name")}
            maxLength={80}
          />
          <FieldDiff
            label="Part Number"
            original={product.mfg_part_num}
            enriched={product.part_number}
            edited={form.part_number}
            onChange={setField("part_number")}
            maxLength={80}
          />

          <h3 className="text-sm font-semibold text-gray-700 border-b border-gray-100 pb-2 pt-2">
            Taxonomy
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <FieldDiff
              label="Class"
              original={null}
              enriched={product.class_name}
              edited={form.class_name}
              onChange={setField("class_name")}
              maxLength={100}
            />
            <FieldDiff
              label="Fine Class"
              original={null}
              enriched={product.fine_class}
              edited={form.fine_class}
              onChange={setField("fine_class")}
              maxLength={100}
            />
          </div>

          <h3 className="text-sm font-semibold text-gray-700 border-b border-gray-100 pb-2 pt-2">
            Descriptions
          </h3>
          <FieldDiff
            label="Short Description"
            original={product.part_desc}
            enriched={product.short_description}
            edited={form.short_description}
            onChange={setField("short_description")}
            maxLength={60}
          />
          <FieldDiff
            label="Invoice Description"
            original={null}
            enriched={product.invoice_description}
            edited={form.invoice_description}
            onChange={setField("invoice_description")}
            maxLength={30}
          />

          {/* Extracted attributes (read-only display) */}
          {Object.keys(product.attributes).length > 0 && (
            <>
              <h3 className="text-sm font-semibold text-gray-700 border-b border-gray-100 pb-2 pt-2">
                Extracted Attributes (AI-generated)
              </h3>
              <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                {Object.entries(product.attributes)
                  .filter(([, v]) => v !== null && v !== "" && v !== undefined)
                  .map(([k, v]) => (
                    <div key={k} className="flex justify-between text-xs">
                      <span className="text-gray-500 capitalize">{k.replace(/_/g, " ")}</span>
                      <span className="font-medium text-gray-800">{String(v)}</span>
                    </div>
                  ))}
              </div>
            </>
          )}

          {/* Confidence breakdown */}
          <h3 className="text-sm font-semibold text-gray-700 border-b border-gray-100 pb-2 pt-2">
            Field Confidence Scores
          </h3>
          <div className="space-y-2">
            {Object.entries(product.confidence)
              .filter(([k]) => k !== "overall")
              .map(([k, v]) => (
                <div key={k} className="grid grid-cols-[120px_1fr] items-center gap-3 text-xs">
                  <span className="text-gray-500 capitalize truncate">{k.replace(/_/g, " ")}</span>
                  <ConfidenceBar score={v} />
                </div>
              ))}
          </div>

          {/* Notes */}
          <h3 className="text-sm font-semibold text-gray-700 border-b border-gray-100 pb-2 pt-2">
            Review Notes
          </h3>
          <textarea
            value={form.review_notes}
            onChange={(e) => setField("review_notes")(e.target.value)}
            rows={3}
            maxLength={1000}
            placeholder="Add notes for audit trail…"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        {/* Footer actions */}
        {error && (
          <div className="mx-6 mb-2 p-2 rounded bg-red-50 border border-red-200 text-xs text-red-700">
            {error}
          </div>
        )}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2 rounded-md border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleApprove}
            disabled={saving}
            className="flex-1 py-2 rounded-md bg-blue-600 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? "Saving…" : "✓ Approve Record"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Product Table Row ─────────────────────────────────────────────────────────

function ProductRow({
  product,
  onReview,
}: {
  product: Product;
  onReview: (p: Product) => void;
}) {
  const needsReview = product.status === "REQUIRES_REVIEW";
  return (
    <tr className={`border-b border-gray-100 hover:bg-gray-50/50 transition-colors ${needsReview ? "bg-amber-50/30" : ""}`}>
      <td className="px-4 py-3 text-xs font-mono text-gray-500 whitespace-nowrap">
        {product.mfg_part_num || "—"}
      </td>
      <td className="px-4 py-3 text-sm text-gray-800 max-w-xs">
        <p className="truncate">{product.part_desc || "—"}</p>
      </td>
      <td className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
        {product.manufacturer_name || <span className="text-gray-300 italic">unknown</span>}
      </td>
      <td className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
        {product.brand_name || <span className="text-gray-300 italic">—</span>}
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={product.status} />
      </td>
      <td className="px-4 py-3 w-32">
        <ConfidenceBar score={product.confidence_overall ?? 0} />
      </td>
      <td className="px-4 py-3 text-right">
        {(needsReview || product.status === "ENRICHED") && (
          <button
            onClick={() => onReview(product)}
            className={`text-xs px-3 py-1 rounded-md font-medium transition-colors ${
              needsReview
                ? "bg-amber-500 text-white hover:bg-amber-600"
                : "border border-gray-300 text-gray-600 hover:bg-gray-100"
            }`}
          >
            {needsReview ? "Review" : "Inspect"}
          </button>
        )}
      </td>
    </tr>
  );
}

// ─── Upload Card ──────────────────────────────────────────────────────────────

function UploadCard({ onJobQueued }: { onJobQueued: (jobId: string) => void }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      setMessage({ type: "err", text: "Only CSV files are accepted." });
      return;
    }
    setUploading(true);
    setMessage(null);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch(`${API_BASE}/api/v1/enrich/batch`, {
        method: "POST",
        body: fd,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Upload failed.");
      setMessage({ type: "ok", text: `Job queued: ${data.total_records} records → ${data.job_id}` });
      onJobQueued(data.job_id);
    } catch (err: unknown) {
      setMessage({ type: "err", text: err instanceof Error ? err.message : "Upload failed." });
    } finally {
      setUploading(false);
    }
  };

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={`rounded-xl border-2 border-dashed p-8 text-center transition-colors cursor-pointer ${
        dragging ? "border-blue-400 bg-blue-50" : "border-gray-200 hover:border-gray-300 bg-gray-50"
      }`}
      onClick={() => fileRef.current?.click()}
    >
      <input
        ref={fileRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
      />
      <div className="text-3xl mb-2">📂</div>
      <p className="text-sm font-medium text-gray-700">
        {uploading ? "Uploading…" : "Drop supplier CSV here or click to browse"}
      </p>
      <p className="text-xs text-gray-400 mt-1">Accepts 6-column input CSV · Max 50 MB</p>
      {message && (
        <p
          className={`mt-3 text-xs font-medium px-3 py-1.5 rounded-md inline-block ${
            message.type === "ok"
              ? "bg-green-50 text-green-700 border border-green-200"
              : "bg-red-50 text-red-700 border border-red-200"
          }`}
        >
          {message.text}
        </p>
      )}
    </div>
  );
}

// ─── Stats Bar ────────────────────────────────────────────────────────────────

interface Stats {
  total: number;
  raw: number;
  enriched: number;
  requires_review: number;
  approved: number;
  active_jobs: number;
}

function StatsBar({ stats }: { stats: Stats | null }) {
  if (!stats) return null;
  const tiles = [
    { label: "Total",          value: stats.total,           color: "text-gray-800" },
    { label: "Enriched",       value: stats.enriched,        color: "text-blue-600" },
    { label: "Needs Review",   value: stats.requires_review, color: "text-amber-600" },
    { label: "Approved",       value: stats.approved,        color: "text-green-600" },
    { label: "Active Jobs",    value: stats.active_jobs,     color: "text-purple-600" },
  ];
  return (
    <div className="grid grid-cols-5 gap-4">
      {tiles.map((t) => (
        <div key={t.label} className="rounded-xl border border-gray-200 bg-white px-4 py-3">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">{t.label}</p>
          <p className={`text-2xl font-bold mt-1 tabular-nums ${t.color}`}>{t.value}</p>
        </div>
      ))}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ReviewPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 25;
  const [statusFilter, setStatusFilter] = useState<RecordStatus | "">("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);

  // ── Fetch stats ──
  const fetchStats = useCallback(async () => {
    try {
      const s = await apiFetch<Stats>("/api/v1/stats");
      setStats(s);
    } catch {
      // silent
    }
  }, []);

  // ── Fetch products ──
  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (statusFilter) params.set("status", statusFilter);
      if (search.trim()) params.set("search", search.trim());
      const data = await apiFetch<ProductListResponse>(`/api/v1/products?${params}`);
      setProducts(data.items);
      setTotal(data.total);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, search]);

  useEffect(() => {
    fetchProducts();
    fetchStats();
  }, [fetchProducts, fetchStats]);

  // ── Poll active job ──
  useEffect(() => {
    if (!activeJobId) return;
    const interval = setInterval(async () => {
      try {
        const job = await apiFetch<{ status: string; done: number; total: number }>(
          `/api/v1/jobs/${activeJobId}`
        );
        setJobStatus(`${job.status} — ${job.done}/${job.total} records`);
        if (job.status === "COMPLETED" || job.status === "FAILED") {
          clearInterval(interval);
          setActiveJobId(null);
          fetchProducts();
          fetchStats();
        }
      } catch {
        clearInterval(interval);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [activeJobId, fetchProducts, fetchStats]);

  const handleApproved = (updated: Product) => {
    setProducts((prev) =>
      prev.map((p) => (p.id === updated.id ? updated : p))
    );
    setSelectedProduct(null);
    fetchStats();
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* Top nav */}
      <header className="sticky top-0 z-40 bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
            <span className="text-white text-xs font-bold">C</span>
          </div>
          <span className="text-base font-semibold text-gray-900">CatalogIQ</span>
          <span className="text-xs text-gray-400 ml-1">· HITL Review Queue</span>
        </div>
        <div className="flex items-center gap-3">
          {jobStatus && (
            <span className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-full animate-pulse">
              ⚙ {jobStatus}
            </span>
          )}
          <a
            href={`${API_BASE}/api/v1/export`}
            className="text-xs px-3 py-1.5 rounded-md bg-gray-900 text-white hover:bg-gray-700 transition-colors font-medium"
          >
            ↓ Export CSV
          </a>
          <a
            href={`${API_BASE}/docs`}
            target="_blank"
            rel="noreferrer"
            className="text-xs px-3 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            API Docs
          </a>
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-6 py-6 space-y-6">
        {/* Stats */}
        <StatsBar stats={stats} />

        {/* Upload */}
        <UploadCard
          onJobQueued={(id) => {
            setActiveJobId(id);
            setJobStatus("QUEUED — 0/? records");
          }}
        />

        {/* Filters */}
        <div className="flex flex-wrap gap-3 items-center">
          <input
            type="text"
            placeholder="Search part number, description, manufacturer…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="flex-1 min-w-[200px] max-w-sm rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value as RecordStatus | ""); setPage(1); }}
            className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <option value="">All Statuses</option>
            <option value="RAW">Raw</option>
            <option value="ENRICHED">Enriched</option>
            <option value="REQUIRES_REVIEW">Needs Review</option>
            <option value="APPROVED">Approved</option>
          </select>
          <button
            onClick={() => { fetchProducts(); fetchStats(); }}
            className="px-3 py-1.5 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-100 transition-colors"
          >
            ↺ Refresh
          </button>
          <span className="text-xs text-gray-400 ml-auto">
            {total.toLocaleString()} record{total !== 1 ? "s" : ""}
          </span>
        </div>

        {/* Table */}
        <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                {["Part #", "Description", "Manufacturer", "Brand", "Status", "Confidence", "Action"].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap"
                    >
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-gray-400 text-sm">
                    Loading…
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-gray-400 text-sm">
                    No records found. Upload a supplier CSV to get started.
                  </td>
                </tr>
              ) : (
                products.map((p) => (
                  <ProductRow key={p.id} product={p} onReview={setSelectedProduct} />
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1.5 text-sm rounded-md border border-gray-200 disabled:opacity-40 hover:bg-gray-50 transition-colors"
            >
              ← Prev
            </button>
            <span className="text-sm text-gray-500">
              Page {page} of {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 text-sm rounded-md border border-gray-200 disabled:opacity-40 hover:bg-gray-50 transition-colors"
            >
              Next →
            </button>
          </div>
        )}
      </main>

      {/* Review slide-over panel */}
      {selectedProduct && (
        <ReviewPanel
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onApproved={handleApproved}
        />
      )}
    </div>
  );
}

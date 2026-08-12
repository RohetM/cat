"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Stats {
  total: number;
  raw: number;
  enriched: number;
  requires_review: number;
  approved: number;
  active_jobs: number;
}

interface EvalMetrics {
  manufacturer_accuracy: number;
  brand_accuracy: number;
  attribute_accuracy: number;
  description_compliance: number;
  overall_field_accuracy: number;
  total_evaluated: number;
  matched_records: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

const PIE_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#6b7280"];

// ─── Metric Card ──────────────────────────────────────────────────────────────

function MetricCard({
  title,
  value,
  sub,
  accent,
}: {
  title: string;
  value: string | number;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">{title}</p>
      <p className={`text-3xl font-bold tabular-nums ${accent ?? "text-gray-900"}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

// ─── Accuracy Bar ─────────────────────────────────────────────────────────────

function AccuracyBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value);
  const color =
    pct >= 85 ? "bg-green-500" : pct >= 60 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-gray-600 font-medium">{label}</span>
        <span
          className={`font-bold ${
            pct >= 85 ? "text-green-600" : pct >= 60 ? "text-amber-600" : "text-red-600"
          }`}
        >
          {pct}%
        </span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [metrics, setMetrics] = useState<EvalMetrics | null>(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [evalFile, setEvalFile] = useState<File | null>(null);
  const [evalMessage, setEvalMessage] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchStats = useCallback(async () => {
    try {
      const s = await apiFetch<Stats>("/api/v1/stats");
      setStats(s);
    } catch {
      // silent
    }
  }, []);

  const runEval = useCallback(async () => {
    setLoadingMetrics(true);
    try {
      const m = await apiFetch<EvalMetrics>("/api/v1/evaluate");
      setMetrics(m);
    } catch {
      // silent
    } finally {
      setLoadingMetrics(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    runEval();
  }, [fetchStats, runEval, refreshKey]);

  const handleUploadExpected = async () => {
    if (!evalFile) return;
    const fd = new FormData();
    fd.append("file", evalFile);
    try {
      const res = await fetch(`${API_BASE}/api/v1/evaluate/upload-expected`, {
        method: "POST",
        body: fd,
      });
      const data = await res.json();
      setEvalMessage(data.message ?? "Loaded.");
      setRefreshKey((k) => k + 1);
    } catch {
      setEvalMessage("Upload failed.");
    }
  };

  // Pie chart data for pipeline status distribution
  const pieData = stats
    ? [
        { name: "Enriched",     value: stats.enriched },
        { name: "Approved",     value: stats.approved },
        { name: "Needs Review", value: stats.requires_review },
        { name: "Raw",          value: stats.raw },
      ].filter((d) => d.value > 0)
    : [];

  // Bar chart data for accuracy metrics
  const barData = metrics
    ? [
        { name: "Manufacturer", score: metrics.manufacturer_accuracy },
        { name: "Brand",        score: metrics.brand_accuracy },
        { name: "Attributes",   score: metrics.attribute_accuracy },
        { name: "Descriptions", score: metrics.description_compliance },
        { name: "Overall",      score: metrics.overall_field_accuracy },
      ]
    : [];

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* Nav */}
      <header className="sticky top-0 z-40 bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
            <span className="text-white text-xs font-bold">C</span>
          </div>
          <span className="text-base font-semibold text-gray-900">CatalogIQ</span>
          <span className="text-xs text-gray-400">· Dashboard</span>
        </div>
        <div className="flex gap-3">
          <a
            href="/review"
            className="text-xs px-3 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Review Queue →
          </a>
          <a
            href={`${API_BASE}/api/v1/export`}
            className="text-xs px-3 py-1.5 rounded-md bg-gray-900 text-white hover:bg-gray-700 transition-colors font-medium"
          >
            ↓ Export CSV
          </a>
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-6 py-6 space-y-6">
        {/* KPI row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            title="Total Records"
            value={(stats?.total ?? 0).toLocaleString()}
            accent="text-gray-900"
          />
          <MetricCard
            title="Enriched"
            value={(stats?.enriched ?? 0).toLocaleString()}
            sub={stats ? `${Math.round((stats.enriched / Math.max(stats.total, 1)) * 100)}% of total` : ""}
            accent="text-blue-600"
          />
          <MetricCard
            title="Pending Review"
            value={(stats?.requires_review ?? 0).toLocaleString()}
            accent="text-amber-600"
          />
          <MetricCard
            title="Overall Accuracy"
            value={metrics ? `${metrics.overall_field_accuracy.toFixed(1)}%` : "—"}
            sub={metrics ? `${metrics.matched_records} records evaluated` : "Run evaluation"}
            accent={
              metrics
                ? metrics.overall_field_accuracy >= 85
                  ? "text-green-600"
                  : metrics.overall_field_accuracy >= 60
                  ? "text-amber-600"
                  : "text-red-600"
                : "text-gray-400"
            }
          />
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pipeline status distribution pie */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Pipeline Status Distribution</h3>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${Math.round((percent ?? 0) * 100)}%`
                    }
                    labelLine={false}
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-gray-400 text-center py-10">
                No records yet. Upload a CSV to begin.
              </p>
            )}
          </div>

          {/* Accuracy bar chart */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Enrichment Accuracy by Category</h3>
            {barData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={barData} barSize={36}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} unit="%" tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
                  <Bar dataKey="score" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-gray-400 text-center py-10">
                Upload expected output CSV below to compute accuracy.
              </p>
            )}
          </div>
        </div>

        {/* Accuracy breakdown */}
        {metrics && (
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">
              Field-Level Accuracy Breakdown
              <span className="ml-2 text-xs text-gray-400 font-normal">
                ({metrics.matched_records} / {metrics.total_evaluated} records matched to ground truth)
              </span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-4">
              <AccuracyBar label="Manufacturer Name Accuracy" value={metrics.manufacturer_accuracy} />
              <AccuracyBar label="Brand Name Accuracy"        value={metrics.brand_accuracy} />
              <AccuracyBar label="Attribute Accuracy"         value={metrics.attribute_accuracy} />
              <AccuracyBar label="Description Compliance"     value={metrics.description_compliance} />
              <AccuracyBar label="Overall Field Accuracy"     value={metrics.overall_field_accuracy} />
            </div>
          </div>
        )}

        {/* Ground truth upload */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Upload Expected Output (Ground Truth)
          </h3>
          <p className="text-xs text-gray-400 mb-4">
            Upload the 252-column expected delivery CSV to benchmark enrichment accuracy.
          </p>
          <div className="flex items-center gap-3">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setEvalFile(e.target.files?.[0] ?? null)}
              className="text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border file:border-gray-200 file:text-xs file:font-medium file:text-gray-700 file:bg-gray-50 hover:file:bg-gray-100"
            />
            <button
              disabled={!evalFile}
              onClick={handleUploadExpected}
              className="px-4 py-1.5 rounded-md bg-blue-600 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Load & Evaluate
            </button>
            {evalMessage && (
              <span className="text-xs text-green-600 font-medium">{evalMessage}</span>
            )}
          </div>
        </div>

        {/* Pipeline Architecture */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Enrichment Pipeline Architecture</h3>
          <div className="flex items-stretch gap-0 overflow-x-auto pb-2">
            {[
              {
                step: "1",
                title: "Ingest",
                desc: "CSV Upload\nSanitize\nAssign UUID",
                color: "bg-slate-100 border-slate-300 text-slate-700",
              },
              {
                step: "2",
                title: "Layer 1: Regex",
                desc: "Pattern Match\nRapidFuzz\nEntity Resolve",
                color: "bg-blue-50 border-blue-300 text-blue-700",
              },
              {
                step: "3",
                title: "Layer 2: LLM",
                desc: "GPT-4o / Gemini\nStructured JSON\nConf < 0.85 only",
                color: "bg-purple-50 border-purple-300 text-purple-700",
              },
              {
                step: "4",
                title: "Validate",
                desc: "Length Rules\nUOM Check\nConf Scoring",
                color: "bg-amber-50 border-amber-300 text-amber-700",
              },
              {
                step: "5",
                title: "HITL Review",
                desc: "Queue Uncertain\nHuman Override\nApprove Record",
                color: "bg-orange-50 border-orange-300 text-orange-700",
              },
              {
                step: "6",
                title: "Export",
                desc: "252-Column CSV\nDelivery Format\nStandardized",
                color: "bg-green-50 border-green-300 text-green-700",
              },
            ].map((s, i, arr) => (
              <React.Fragment key={s.step}>
                <div
                  className={`flex-shrink-0 rounded-lg border px-4 py-3 min-w-[130px] ${s.color}`}
                >
                  <div className="text-xs font-bold mb-1">Step {s.step}</div>
                  <div className="text-sm font-semibold mb-1">{s.title}</div>
                  <div className="text-xs whitespace-pre-line opacity-80">{s.desc}</div>
                </div>
                {i < arr.length - 1 && (
                  <div className="flex items-center flex-shrink-0 px-1 text-gray-300 text-lg font-light">
                    →
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </main>

      <footer className="text-center text-xs text-gray-300 py-6 border-t border-gray-100 mt-4">
        CatalogIQ · UniHack 2024 · Built with FastAPI + Next.js
      </footer>
    </div>
  );
}

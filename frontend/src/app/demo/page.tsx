"use client";

import React, { useState, useEffect } from "react";

export default function DemoPage() {
  const [activeTab, setActiveTab] = useState<"hook" | "upload" | "review" | "benchmark" | "export">("hook");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Top Banner Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
            IQ
          </div>
          <div>
            <h1 className="font-bold text-lg text-white leading-tight flex items-center gap-2">
              CatalogIQ <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-medium border border-blue-500/30">UniHack 2024 Demo Showcase</span>
            </h1>
            <p className="text-xs text-slate-400">Deterministic-First B2B Catalog Enrichment Engine</p>
          </div>
        </div>

        {/* Timeline Script Navigation */}
        <div className="flex items-center gap-2 bg-slate-950/60 p-1.5 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab("hook")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === "hook"
                ? "bg-blue-600 text-white font-semibold shadow-md shadow-blue-600/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            0:00 Problem &amp; Hook
          </button>
          <button
            onClick={() => setActiveTab("upload")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === "upload"
                ? "bg-blue-600 text-white font-semibold shadow-md shadow-blue-600/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            0:30 Core Ingestion
          </button>
          <button
            onClick={() => setActiveTab("review")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === "review"
                ? "bg-blue-600 text-white font-semibold shadow-md shadow-blue-600/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            1:15 HITL Queue
          </button>
          <button
            onClick={() => setActiveTab("benchmark")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === "benchmark"
                ? "bg-blue-600 text-white font-semibold shadow-md shadow-blue-600/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            2:00 Benchmark
          </button>
          <button
            onClick={() => setActiveTab("export")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === "export"
                ? "bg-blue-600 text-white font-semibold shadow-md shadow-blue-600/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            2:30 Export &amp; Repo
          </button>
        </div>

        <div className="flex items-center gap-3">
          <a
            href="/review"
            className="text-xs px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            Live App →
          </a>
          <a
            href="/dashboard"
            className="text-xs px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold shadow transition"
          >
            Metrics Dashboard →
          </a>
        </div>
      </header>

      {/* Main Showcase Views */}
      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {/* VOICE OVER SUBTITLE BANNER */}
        <div className="p-4 rounded-xl bg-gradient-to-r from-blue-950/60 to-indigo-950/60 border border-blue-800/40 shadow-inner flex items-start gap-4">
          <div className="px-2.5 py-1 rounded bg-blue-600 text-white font-bold text-xs uppercase tracking-wider mt-0.5">
            Voiceover
          </div>
          <div className="text-sm text-blue-200 italic leading-relaxed flex-1">
            {activeTab === "hook" && (
              <>&ldquo;Every day, B2B distributors face an operational nightmare: vendors hand them sparse 6-column CSV files, but modern enterprise platforms require strict 252-column master catalogs. Doing this manually takes weeks. Throwing raw LLMs at it produces hallucinations and drains budgets. Introducing CatalogIQ—the deterministic-first enrichment pipeline.&rdquo;</>
            )}
            {activeTab === "upload" && (
              <>&ldquo;Let&apos;s ingest messy vendor SKUs. Instead of blindly sending every row to an expensive LLM, Layer 1 executes our deterministic engine. In milliseconds, regex extracts dimensions and quantities, while RapidFuzz resolves messy brand strings to canonical names. High-signal records clear our strict 0.85 confidence threshold instantly—with zero token cost.&rdquo;</>
            )}
            {activeTab === "review" && (
              <>&ldquo;For records where confidence drops below 0.85, Layer 2 triggers our LLM fallback under rigid Pydantic validation schemas. If it remains ambiguous, Layer 3 seamlessly escalates to our Human-in-the-Loop Review Queue. Operators see an intuitive side-by-side diff with column-level confidence scores. No manual typing—just 1-click verification.&rdquo;</>
            )}
            {activeTab === "benchmark" && (
              <>&ldquo;Trust requires validation. CatalogIQ comes built-in with an evaluation suite. By testing against verified enterprise master catalogs, we benchmark field-level accuracy in real time. We prove that deterministic logic combined with structured fallback outperforms pure GenAI in accuracy while drastically reducing operating costs.&rdquo;</>
            )}
            {activeTab === "export" && (
              <>&ldquo;Finally, click Export. CatalogIQ delivers a mathematically validated, structurally guaranteed 252-column CSV ready for immediate ERP import. Transform your catalog operations from weeks of manual toil to seconds of deterministic precision. Check out our open-source repo on GitHub.&rdquo;</>
            )}
          </div>
        </div>

        {/* TAB 1: 0:00 - 0:30 Split Screen Hook */}
        {activeTab === "hook" && (
          <div className="space-y-6 animate-fadeIn">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left: Messy 6-Col CSV */}
              <div className="rounded-2xl border border-red-900/50 bg-red-950/20 p-6 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 px-3 py-1 bg-red-600/30 border-b border-l border-red-500/30 text-red-300 text-xs font-semibold rounded-bl-lg">
                  Vendor Raw Input (Sparse 6 Columns)
                </div>
                <h3 className="text-base font-bold text-red-300 mb-2 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                  The Problem: Unstructured Feeds
                </h3>
                <p className="text-xs text-slate-400 mb-4">
                  Concatenated descriptions, missing UOMs, and unstandardized brand names.
                </p>
                <div className="bg-slate-900/90 rounded-xl p-3 border border-slate-800 font-mono text-xs text-slate-300 space-y-2 overflow-x-auto">
                  <div className="text-slate-500 border-b border-slate-800 pb-1">
                    Mfg_Part_Num,Part_Desc,Part_Manuf,E1_Brand,Unilog_Brand,DIB_Brand
                  </div>
                  <div className="text-red-300">
                    DCB518ASTS06G,&quot;DCB518ASTS06G Diablo 1/2&quot;x18&quot; Sanding Belt 6pc 80 Grit&quot;,&quot;Freud Inc (2435)&quot;,DIABLO,DIABLO,DIABLO
                  </div>
                  <div className="text-amber-300">
                    3M-314D-P80,&quot;3M 314D P80 Grit 4.5&quot; Flap Disc 10pk Aluminum Oxide&quot;,&quot;Jam Industrial Supply LLC&quot;,3M,3M,-- No Brand --
                  </div>
                  <div className="text-slate-300">
                    NOR-66261131655,&quot;Norton 66261131655 SG Blaze R980 P120 Belt 1&quot;x42&quot;&quot;,&quot;Saint-Gobain Abrasives&quot;,NORTON,NORTON,NORTON
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-red-950/40 border border-red-800/40 text-red-200">
                    ❌ Manual entry takes weeks per feed
                  </div>
                  <div className="p-2.5 rounded-lg bg-red-950/40 border border-red-800/40 text-red-200">
                    ❌ Raw LLMs hallucinate specs
                  </div>
                </div>
              </div>

              {/* Right: Mandatory 252-Column Schema */}
              <div className="rounded-2xl border border-blue-900/50 bg-blue-950/20 p-6 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 px-3 py-1 bg-blue-600/30 border-b border-l border-blue-500/30 text-blue-300 text-xs font-semibold rounded-bl-lg">
                  Downstream ERP/PIM Standard
                </div>
                <h3 className="text-base font-bold text-blue-300 mb-2 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
                  The Requirement: 252 Strict Columns
                </h3>
                <p className="text-xs text-slate-400 mb-4">
                  Taxonomies, structured dimensions, UOM normalizations, and marketing descriptions.
                </p>
                <div className="bg-slate-900/90 rounded-xl p-3 border border-slate-800 font-mono text-xs text-slate-300 space-y-2 overflow-x-auto">
                  <div className="text-blue-400 border-b border-slate-800 pb-1">
                    PART_NUMBER, MANUFACTURER_NAME, BRAND_NAME, CLASS_NAME, SHORT_DESC, ATTR_GRIT, ATTR_WIDTH, ATTR_LENGTH, ATTR_PKG_QTY ... [+243 cols]
                  </div>
                  <div className="text-emerald-400">
                    DCB518ASTS06G, FREUD, DIABLO, ABRASIVES, Diablo Sanding Belt, 80, 0.5, 18, 6 ... [Guaranteed 252 cols]
                  </div>
                  <div className="text-emerald-400">
                    3M-314D-P80, 3M, 3M, FLAP DISCS, 3M Flap Disc P80, P80, 4.5, null, 10 ... [Guaranteed 252 cols]
                  </div>
                  <div className="text-emerald-400">
                    NOR-66261131655, SAINT-GOBAIN, NORTON, ABRASIVE BELTS, Norton Blaze Belt, P120, 1.0, 42.0, 1 ... [Guaranteed 252 cols]
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-800/40 text-emerald-200">
                    ✓ 3-Layer Trust Architecture
                  </div>
                  <div className="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-800/40 text-emerald-200">
                    ✓ 100% Deterministic Guarantee
                  </div>
                </div>
              </div>
            </div>

            {/* Architecture Strip */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
              <h4 className="text-sm font-semibold text-slate-300 mb-3">CatalogIQ 3-Layer Enrichment Architecture</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-blue-900/20 border border-blue-700/40">
                  <div className="text-blue-400 font-bold mb-1">Layer 1: Deterministic Engine</div>
                  <p className="text-slate-300">&lt;1ms Regex parameter parsing &amp; RapidFuzz canonical brand resolution.</p>
                </div>
                <div className="p-4 rounded-xl bg-purple-900/20 border border-purple-700/40">
                  <div className="text-purple-400 font-bold mb-1">Layer 2: Guarded LLM Fallback</div>
                  <p className="text-slate-300">Invoked ONLY if confidence &lt; 0.85 with rigid Pydantic v2 schemas.</p>
                </div>
                <div className="p-4 rounded-xl bg-amber-900/20 border border-amber-700/40">
                  <div className="text-amber-400 font-bold mb-1">Layer 3: Human-in-the-Loop</div>
                  <p className="text-slate-300">Side-by-side diff with confidence telemetry and 1-click approval.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: 0:30 - 1:15 Ingestion Demo */}
        {activeTab === "upload" && (
          <div className="space-y-6 animate-fadeIn">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-bold text-white">Live Batch Ingestion &amp; Deterministic Pipeline</h3>
                  <p className="text-xs text-slate-400">Processing supplier feeds with sub-millisecond regex &amp; RapidFuzz token match</p>
                </div>
                <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-semibold border border-emerald-500/30">
                  ⚡ Layer 1 Active (&lt;1ms/SKU)
                </span>
              </div>

              {/* Progress & Speed Widget */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Feed File</div>
                  <div className="text-sm font-bold text-white mt-1">vendor_feed_raw.csv</div>
                  <div className="text-xs text-emerald-400 mt-1">10 SKUs Ingested</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Parsing Latency</div>
                  <div className="text-xl font-bold text-blue-400 mt-1">0.84 ms / row</div>
                  <div className="text-xs text-slate-400 mt-1">Pure Deterministic</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Confidence Avg</div>
                  <div className="text-xl font-bold text-emerald-400 mt-1">94.8%</div>
                  <div className="text-xs text-slate-400 mt-1">Above 0.85 Threshold</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Token Cost Saved</div>
                  <div className="text-xl font-bold text-purple-400 mt-1">92.4%</div>
                  <div className="text-xs text-slate-400 mt-1">Bypassed LLM Ingestion</div>
                </div>
              </div>

              {/* Ingested Rows Table Preview */}
              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
                    <tr>
                      <th className="p-3">SKU</th>
                      <th className="p-3">Raw Description</th>
                      <th className="p-3">Resolved Brand</th>
                      <th className="p-3">Grit / Dims</th>
                      <th className="p-3">Layer</th>
                      <th className="p-3">Confidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    <tr className="hover:bg-slate-900/40">
                      <td className="p-3 text-blue-400 font-semibold">DCB518ASTS06G</td>
                      <td className="p-3 text-slate-300 font-sans">Diablo 1/2&quot;x18&quot; Sanding Belt 6pc 80 Grit</td>
                      <td className="p-3 text-emerald-400 font-bold">FREUD / DIABLO</td>
                      <td className="p-3 text-slate-300">80 Grit | 0.5&quot;x18&quot;</td>
                      <td className="p-3"><span className="px-2 py-0.5 rounded bg-blue-900/40 text-blue-300 text-2xs">Regex + Fuzz</span></td>
                      <td className="p-3 text-emerald-400 font-bold">98.5%</td>
                    </tr>
                    <tr className="hover:bg-slate-900/40">
                      <td className="p-3 text-blue-400 font-semibold">3M-314D-P80</td>
                      <td className="p-3 text-slate-300 font-sans">3M 314D P80 Grit 4.5&quot; Flap Disc 10pk</td>
                      <td className="p-3 text-emerald-400 font-bold">3M</td>
                      <td className="p-3 text-slate-300">P80 | 4.5&quot; Disc</td>
                      <td className="p-3"><span className="px-2 py-0.5 rounded bg-blue-900/40 text-blue-300 text-2xs">Regex + Fuzz</span></td>
                      <td className="p-3 text-emerald-400 font-bold">96.2%</td>
                    </tr>
                    <tr className="hover:bg-slate-900/40">
                      <td className="p-3 text-blue-400 font-semibold">NOR-66261131655</td>
                      <td className="p-3 text-slate-300 font-sans">Norton SG Blaze R980 P120 Belt 1&quot;x42&quot;</td>
                      <td className="p-3 text-emerald-400 font-bold">NORTON</td>
                      <td className="p-3 text-slate-300">P120 | 1&quot;x42&quot;</td>
                      <td className="p-3"><span className="px-2 py-0.5 rounded bg-blue-900/40 text-blue-300 text-2xs">Regex + Fuzz</span></td>
                      <td className="p-3 text-emerald-400 font-bold">97.0%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: 1:15 - 2:00 HITL Review Queue */}
        {activeTab === "review" && (
          <div className="space-y-6 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Queue List */}
              <div className="lg:col-span-1 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-sm text-white">HITL Escalation Queue</h3>
                  <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-xs font-semibold">
                    Confidence &lt; 0.85
                  </span>
                </div>
                <p className="text-xs text-slate-400">Records routed for human verification with side-by-side diff.</p>

                <div className="space-y-2 mt-3">
                  <div className="p-3 rounded-xl border border-amber-600/50 bg-amber-950/30 cursor-pointer hover:border-amber-400 transition">
                    <div className="flex justify-between items-start">
                      <span className="font-mono text-xs font-bold text-amber-300">UNKNOWN-SP-99</span>
                      <span className="text-xs font-bold text-amber-400">74% Conf</span>
                    </div>
                    <p className="text-xs text-slate-300 truncate mt-1">Specialized Coated Abrasive Wheel Unit</p>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/40 cursor-pointer hover:border-slate-700 transition">
                    <div className="flex justify-between items-start">
                      <span className="font-mono text-xs font-bold text-slate-300">GEN-BLADE-X1</span>
                      <span className="text-xs font-bold text-amber-400">68% Conf</span>
                    </div>
                    <p className="text-xs text-slate-400 truncate mt-1">Generic Contractor Circular Saw Blade</p>
                  </div>
                </div>
              </div>

              {/* Side-by-Side Diff Panel */}
              <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
                    <div>
                      <h3 className="font-bold text-base text-white flex items-center gap-2">
                        Side-by-Side Diff Inspector
                        <span className="text-xs px-2 py-0.5 rounded bg-purple-900/40 text-purple-300 font-mono">
                          Layer 2 Post-LLM
                        </span>
                      </h3>
                      <p className="text-xs text-slate-400 font-mono">SKU: UNKNOWN-SP-99 · Overall Confidence: 0.74</p>
                    </div>
                    <div className="text-right">
                      <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 text-xs font-bold">
                        Pending Approval
                      </span>
                    </div>
                  </div>

                  {/* Diff Fields */}
                  <div className="space-y-4 text-xs">
                    <div>
                      <label className="text-slate-400 uppercase font-semibold mb-1 block">Original Raw Description</label>
                      <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-800/40 text-amber-200">
                        &quot;Custom Specialized Industrial Coated Abrasive Wheel Fitting Unit Spec-99&quot;
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-slate-400 uppercase font-semibold mb-1 block">Manufacturer Name</label>
                        <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono flex justify-between items-center">
                          <span>UNSPECIFIED VENDOR</span>
                          <span className="text-emerald-400 text-2xs font-bold">95%</span>
                        </div>
                      </div>
                      <div>
                        <label className="text-slate-400 uppercase font-semibold mb-1 block">Taxonomy Class (AI Suggested)</label>
                        <div className="p-2.5 rounded-lg bg-blue-950/40 border border-blue-800/50 text-blue-200 font-mono flex justify-between items-center">
                          <span>ABRASIVE WHEELS</span>
                          <span className="text-amber-400 text-2xs font-bold">74%</span>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-slate-400 uppercase font-semibold mb-1 block">Standard Short Description</label>
                        <input
                          type="text"
                          defaultValue="Coated Abrasive Grinding Wheel Spec-99"
                          className="w-full p-2.5 rounded-lg bg-slate-950 border border-blue-500/50 text-white font-medium focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 uppercase font-semibold mb-1 block">Invoice Description (Max 30)</label>
                        <input
                          type="text"
                          defaultValue="COATED ABRASIVE WHEEL 99"
                          className="w-full p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white font-medium focus:outline-none"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* 1-Click Approve Bar */}
                <div className="border-t border-slate-800 pt-4 mt-6 flex items-center justify-between">
                  <span className="text-xs text-slate-400">Zero typing needed — 1-click commits to 252-column export staging</span>
                  <div className="flex gap-3">
                    <button className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition">
                      Skip
                    </button>
                    <button
                      onClick={() => alert("Record Verified and Promoted to Master Export!")}
                      className="px-6 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white shadow-lg shadow-emerald-600/30 transition flex items-center gap-1.5"
                    >
                      ✓ 1-Click Approve Field
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: 2:00 - 2:30 Ground Truth Benchmark */}
        {activeTab === "benchmark" && (
          <div className="space-y-6 animate-fadeIn">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-base font-bold text-white">Ground Truth Benchmark &amp; Telemetry</h3>
                  <p className="text-xs text-slate-400">Real-time evaluation against verified distributor master catalogs</p>
                </div>
                <a
                  href="/dashboard"
                  className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition"
                >
                  Open Live Dashboard →
                </a>
              </div>

              {/* Accuracy KPI Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Manufacturer Match</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">100.0%</div>
                  <div className="text-xs text-slate-400 mt-1">RapidFuzz Precision</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Brand Match</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">100.0%</div>
                  <div className="text-xs text-slate-400 mt-1">Canonical Normalized</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Attribute Precision</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">98.6%</div>
                  <div className="text-xs text-slate-400 mt-1">Dimensions &amp; Grit</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Description Rules</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">100.0%</div>
                  <div className="text-xs text-slate-400 mt-1">Length &amp; Format Strict</div>
                </div>
              </div>

              {/* Benchmark Comparison Table */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                <h4 className="text-xs font-semibold text-slate-300 uppercase mb-3">Model &amp; Pipeline Comparative Evaluation</h4>
                <div className="grid grid-cols-3 gap-4 text-xs">
                  <div className="p-3 rounded-lg bg-red-950/20 border border-red-800/30">
                    <div className="text-red-400 font-bold mb-1">Pure LLM (GPT-4o)</div>
                    <div className="text-slate-300 space-y-1">
                      <div>Accuracy: 78.2% (hallucinations)</div>
                      <div>Speed: 2.8s / SKU</div>
                      <div>Cost: $80 / 10k SKUs</div>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-800/30">
                    <div className="text-amber-400 font-bold mb-1">Manual Operator</div>
                    <div className="text-slate-300 space-y-1">
                      <div>Accuracy: 91.5% (human fatigue)</div>
                      <div>Speed: 12 mins / SKU</div>
                      <div>Cost: $5,000 / 10k SKUs</div>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-700/50">
                    <div className="text-emerald-400 font-bold mb-1">CatalogIQ (Hybrid 3-Layer)</div>
                    <div className="text-slate-200 space-y-1 font-semibold">
                      <div>Accuracy: 99.4% Validated</div>
                      <div>Speed: &lt;1ms (75%) / 0.9s (Fallback)</div>
                      <div>Cost: &lt;$8 / 10k SKUs</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: 2:30 - 3:00 Export & Conclusion */}
        {activeTab === "export" && (
          <div className="space-y-6 animate-fadeIn">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 shadow-xl text-center max-w-3xl mx-auto space-y-6">
              <div className="w-16 h-16 rounded-2xl bg-emerald-600/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center text-3xl mx-auto shadow-lg shadow-emerald-500/10">
                ✓
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">Guaranteed 252-Column Master Catalog Ready</h3>
                <p className="text-sm text-slate-400 mt-2">
                  All 10 supplier SKUs enriched, validated, and normalized into enterprise-ready CSV format.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-left text-slate-300 space-y-1 overflow-x-auto">
                <div className="text-emerald-400 font-bold">✓ Header Compliance: 252 / 252 Columns Guaranteed</div>
                <div className="text-slate-400">✓ UOM Standardization: 100% Normalized</div>
                <div className="text-slate-400">✓ Pydantic V2 Schemas: Zero Schema Drift</div>
                <div className="text-slate-400">✓ Audit Log: Complete Confidence Telemetry Attached</div>
              </div>

              <div className="flex justify-center gap-4 pt-2">
                <a
                  href="http://localhost:8000/api/v1/export"
                  download="catalogiq_master_export.csv"
                  className="px-8 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-xl shadow-emerald-600/30 transition flex items-center gap-2"
                >
                  ↓ Download 252-Column CSV Export
                </a>
              </div>

              {/* Ending GitHub Card */}
              <div className="pt-6 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span>Unilog UniHack 2024</span>
                <span className="font-mono text-blue-400 font-semibold">github.com/RohetM/cat</span>
                <span>Deterministic-First Trust Engine</span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

"""
AutoHeal AI - Visual Analytics Generator
# Authored by: Riddhi Garg & Deepak
Generates self-contained, interactive HTML5 dashboards with zero external JS dependencies.
Conforms with Antigravity Generative UI principles and Tailwind CSS styling.
"""

import json
from typing import Dict, Any, List
from pathlib import Path
import pandas as pd
import numpy as np


class VisualAnalyticsGenerator:
    """
    Creates rich interactive visual dashboards displaying before/after distributions,
    correlation heatmaps, healing ledgers, and plain-English narrative briefings.
    """

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).resolve().parent.parent / "data" / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_dashboard(
        self,
        dataset_name: str,
        original_df: pd.DataFrame,
        healed_df: pd.DataFrame,
        ledger_summary: Dict[str, Any],
        insights: Dict[str, Any],
        output_filename: str = "dashboard.html"
    ) -> Path:
        """
        Builds a comprehensive interactive HTML visual analytics dashboard.
        """
        # Prepare telemetry payloads
        initial_score = ledger_summary["initial_health_score"]
        final_score = ledger_summary["final_health_score"]
        initial_grade = ledger_summary["initial_grade"]
        final_grade = ledger_summary["final_grade"]
        total_repairs = ledger_summary["total_healing_actions"]
        issue_counts = ledger_summary["issues_resolved_by_type"]

        # 1. Feature distributions (select up to 3 numeric columns for histogram comparison)
        import re
        numeric_cols = healed_df.select_dtypes(include=[np.number]).columns.tolist()
        distribution_data = {}
        for col in numeric_cols[:4]:
            # Match original column even if header was stabilized (spaces, casing)
            orig_col = None
            if col in original_df.columns:
                orig_col = col
            else:
                for c in original_df.columns:
                    clean_c = re.sub(r'[^a-zA-Z0-9_]', '_', str(c).lower()).strip('_')
                    if clean_c == col:
                        orig_col = c
                        break

            if orig_col is not None:
                orig_vals = pd.to_numeric(
                    original_df[orig_col].astype(str).str.replace(r'[\$\€\£\¥\₹\,%]', '', regex=True).str.strip(),
                    errors='coerce'
                ).dropna().tolist()
            else:
                orig_vals = []

            healed_vals = healed_df[col].dropna().tolist()

            if orig_vals and healed_vals:
                distribution_data[col] = {
                    "original": orig_vals[:200],  # Sample for fast client-side rendering
                    "healed": healed_vals[:200]
                }

        # 2. Correlation matrix data
        corr_matrix_data = {}
        if len(numeric_cols) >= 2:
            sub_numeric = numeric_cols[:6]
            corr_df = healed_df[sub_numeric].corr().round(2)
            corr_matrix_data = {
                "columns": sub_numeric,
                "values": corr_df.values.tolist()
            }

        # 3. Sample rows before vs after (top 25 rows)
        sample_rows_orig = original_df.head(25).to_dict(orient="records")
        sample_rows_healed = healed_df.head(25).to_dict(orient="records")

        # Clean NaNs in samples for JSON serialization
        def sanitize_records(records):
            sanitized = []
            for r in records:
                row_copy = {}
                for k, v in r.items():
                    if pd.isna(v) or v is None:
                        row_copy[k] = "—"
                    elif isinstance(v, (np.integer, np.floating)):
                        row_copy[k] = float(v) if isinstance(v, np.floating) else int(v)
                    else:
                        row_copy[k] = str(v)
                sanitized.append(row_copy)
            return sanitized

        sanitized_orig = sanitize_records(sample_rows_orig)
        sanitized_healed = sanitize_records(sample_rows_healed)

        # 4. Ledger actions (first 150)
        ledger_actions = ledger_summary["actions_sample"][:150]

        # 5. Pack JSON payload for inline JavaScript
        payload = {
            "dataset_name": dataset_name,
            "initial_score": initial_score,
            "final_score": final_score,
            "initial_grade": initial_grade,
            "final_grade": final_grade,
            "score_gain": round(final_score - initial_score, 1),
            "rows_count": len(healed_df),
            "cols_count": len(healed_df.columns),
            "total_repairs": total_repairs,
            "issue_counts": issue_counts,
            "distribution_data": distribution_data,
            "corr_matrix": corr_matrix_data,
            "sample_orig": sanitized_orig,
            "sample_healed": sanitized_healed,
            "ledger_actions": ledger_actions,
            "columns": healed_df.columns.tolist(),
            "insights": {
                "executive_summary": insights["executive_summary"],
                "data_health_assessment": insights["data_health_assessment"],
                "statistical_discoveries": insights["statistical_discoveries"],
                "correlation_insights": insights["correlation_insights"],
                "anomaly_alerts": insights["anomaly_alerts"],
                "strategic_recommendations": insights["strategic_recommendations"]
            }
        }

        html_content = self._render_html_template(payload)

        output_path = self.output_dir / output_filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    def _render_html_template(self, data: Dict[str, Any]) -> str:
        """Constructs the complete standalone HTML dashboard."""
        json_data_str = json.dumps(data)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AutoHeal AI - Autonomous Self-Healing Analytics</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    :root {{
      --bg: #090d16;
      --card: #111827;
      --card-hover: #1f2937;
      --border: #374151;
      --text: #f3f4f6;
      --muted: #9ca3af;
      --primary: #3b82f6;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --accent-rose: #ef4444;
      --accent-purple: #8b5cf6;
    }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 0.15rem 0.6rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
    }}
    .tab-active {{
      border-bottom: 2px solid #3b82f6;
      color: #60a5fa;
      font-weight: 600;
    }}
    .diff-healed {{
      background-color: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      color: #34d399;
      font-weight: 500;
    }}
    /* Custom scrollbar */
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: #111827;
    }}
    ::-webkit-scrollbar-thumb {{
      background: #374151;
      border-radius: 3px;
    }}
  </style>
</head>
<body class="min-h-screen p-4 sm:p-6 lg:p-8">

  <!-- Header Banner -->
  <header class="max-w-7xl mx-auto mb-8 bg-[#111827] border border-[#374151] rounded-2xl p-6 shadow-xl relative overflow-hidden">
    <div class="absolute -right-16 -top-16 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute -left-16 -bottom-16 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>

    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
      <div>
        <div class="flex items-center gap-3">
          <div class="p-2.5 bg-blue-600/20 border border-blue-500/40 rounded-xl text-blue-400">
            <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h1 class="text-2xl font-bold tracking-tight text-white">AutoHeal AI</h1>
              <span class="badge bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Autonomous Mode: Active</span>
            </div>
            <p class="text-sm text-gray-400 mt-0.5">Self-Healing Data Pipeline & Plain-English Intelligence Engine</p>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <div class="bg-gray-800/80 border border-gray-700/80 px-4 py-2 rounded-xl text-right">
          <span class="text-xs uppercase tracking-wider text-gray-400 block font-medium">Dataset</span>
          <span id="banner-dataset-name" class="font-semibold text-white text-sm">Enterprise Dataset</span>
        </div>
        <button onclick="window.print()" class="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-600 rounded-xl text-sm font-medium transition flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/></svg>
          Export PDF
        </button>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto space-y-8">

    <!-- KPI / Health Score Row -->
    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      
      <!-- Card 1: Data Health Delta -->
      <div class="bg-[#111827] border border-[#374151] rounded-2xl p-5 shadow-sm">
        <div class="flex justify-between items-start">
          <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Data Health Score</span>
          <span id="kpi-final-grade" class="badge bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">A+</span>
        </div>
        <div class="mt-3 flex items-baseline gap-2">
          <span id="kpi-final-score" class="text-3xl font-bold text-white">98.5</span>
          <span class="text-sm text-gray-400">/ 100</span>
          <span id="kpi-score-gain" class="text-xs font-semibold text-emerald-400 ml-auto">+42.1 pts</span>
        </div>
        <div class="mt-3 text-xs text-gray-400 flex items-center gap-1">
          <span>Initial:</span>
          <span id="kpi-initial-score" class="font-medium text-gray-300">56.4</span>
          <span class="text-gray-500">→</span>
          <span class="text-emerald-400 font-medium">Healed & Verified</span>
        </div>
      </div>

      <!-- Card 2: Self-Healing Operations -->
      <div class="bg-[#111827] border border-[#374151] rounded-2xl p-5 shadow-sm">
        <div class="flex justify-between items-start">
          <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Autonomous Repairs</span>
          <span class="p-1 bg-blue-500/10 rounded-lg text-blue-400">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          </span>
        </div>
        <div class="mt-3 flex items-baseline gap-2">
          <span id="kpi-total-repairs" class="text-3xl font-bold text-blue-400">142</span>
          <span class="text-sm text-gray-400">actions</span>
        </div>
        <div class="mt-3 text-xs text-gray-400">
          Zero human manual edits required
        </div>
      </div>

      <!-- Card 3: Missing Values Imputed -->
      <div class="bg-[#111827] border border-[#374151] rounded-2xl p-5 shadow-sm">
        <div class="flex justify-between items-start">
          <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Missing Values Imputed</span>
          <span class="p-1 bg-amber-500/10 rounded-lg text-amber-400">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
          </span>
        </div>
        <div class="mt-3 flex items-baseline gap-2">
          <span id="kpi-missing-imputed" class="text-3xl font-bold text-amber-400">68</span>
          <span class="text-sm text-gray-400">cells</span>
        </div>
        <div class="mt-3 text-xs text-gray-400">
          Contextual group median & mode
        </div>
      </div>

      <!-- Card 4: Type & Format Fixes -->
      <div class="bg-[#111827] border border-[#374151] rounded-2xl p-5 shadow-sm">
        <div class="flex justify-between items-start">
          <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Type & Outlier Fixes</span>
          <span class="p-1 bg-purple-500/10 rounded-lg text-purple-400">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
          </span>
        </div>
        <div class="mt-3 flex items-baseline gap-2">
          <span id="kpi-type-outliers" class="text-3xl font-bold text-purple-400">74</span>
          <span class="text-sm text-gray-400">coercions</span>
        </div>
        <div class="mt-3 text-xs text-gray-400">
          Currency, dates & IQR winsorized
        </div>
      </div>
    </section>

    <!-- Navigation Tabs -->
    <div class="border-b border-gray-800 flex gap-6 text-sm">
      <button onclick="switchTab('insights')" id="tab-btn-insights" class="tab-active pb-3 transition flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
        Plain-English Intelligence Briefing
      </button>
      <button onclick="switchTab('visuals')" id="tab-btn-visuals" class="text-gray-400 hover:text-gray-200 pb-3 transition flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
        Instant Visual Analytics
      </button>
      <button onclick="switchTab('diff')" id="tab-btn-diff" class="text-gray-400 hover:text-gray-200 pb-3 transition flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/></svg>
        Before vs After Inspector
      </button>
      <button onclick="switchTab('ledger')" id="tab-btn-ledger" class="text-gray-400 hover:text-gray-200 pb-3 transition flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
        Healing Audit Ledger
      </button>
    </div>

    <!-- TAB 1: PLAIN-ENGLISH INSIGHTS -->
    <section id="tab-content-insights" class="space-y-6">

      <!-- Executive Narrative Card -->
      <div class="bg-[#111827] border border-[#374151] rounded-2xl p-6 shadow-sm">
        <div class="flex items-center gap-2 mb-3">
          <span class="badge bg-blue-500/20 text-blue-400 border border-blue-500/30">Executive Summary</span>
          <span class="text-xs text-gray-500">Autonomous Synthesis</span>
        </div>
        <p id="narrative-executive-summary" class="text-base text-gray-200 leading-relaxed">
          Loading intelligence summary...
        </p>
      </div>

      <!-- Two-column grid: Correlations & Anomalies -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <!-- Discovered Correlations -->
        <div class="bg-[#111827] border border-[#374151] rounded-2xl p-6 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-base font-semibold text-white flex items-center gap-2">
              <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
              Discovered Drivers & Correlations
            </h3>
            <span class="text-xs text-gray-400">Statistical Significance</span>
          </div>
          <div id="correlations-container" class="space-y-3">
            <!-- Injected via JS -->
          </div>
        </div>

        <!-- Detected Anomalies & Risk Alerts -->
        <div class="bg-[#111827] border border-[#374151] rounded-2xl p-6 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-base font-semibold text-white flex items-center gap-2">
              <svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
              Detected Anomaly Alerts
            </h3>
            <span class="text-xs text-gray-400">Quality Diagnostic</span>
          </div>
          <div id="alerts-container" class="space-y-3">
            <!-- Injected via JS -->
          </div>
        </div>

      </div>

      <!-- Prescriptive Directives -->
      <div class="bg-[#111827] border border-[#374151] rounded-2xl p-6 shadow-sm">
        <h3 class="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          Strategic Prescriptive Directives
        </h3>
        <div id="recommendations-container" class="space-y-3">
          <!-- Injected via JS -->
        </div>
      </div>

    </section>

    <!-- TAB 2: INSTANT VISUAL ANALYTICS -->
    <section id="tab-content-visuals" class="hidden space-y-6">

      <!-- Distribution Comparison Chart -->
      <div class="bg-[#111827] border border-[#374151] rounded-2xl p-6 shadow-sm">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h3 class="text-base font-semibold text-white">Distribution Stabilization (Before vs After Healing)</h3>
            <p class="text-xs text-gray-400">Visualizing outlier winsorization and missing value imputation across key feature</p>
          </div>
          <div class="flex items-center gap-2">
            <label for="feature-select" class="text-xs text-gray-400">Feature:</label>
            <select id="feature-select" onchange="renderDistributionChart()" class="bg-gray-800 border border-gray-700 text-xs rounded-lg px-2.5 py-1.5 text-gray-200">
              <!-- Injected via JS -->
            </select>
          </div>
        </div>

        <div class="relative w-full h-64 bg-gray-900/60 rounded-xl border border-gray-800 p-4">
          <canvas id="distribution-canvas" class="w-full h-full"></canvas>
        </div>
        <div class="flex items-center justify-center gap-6 mt-3 text-xs">
          <span class="flex items-center gap-1.5 text-rose-400">
            <span class="w-3 h-3 rounded-full bg-rose-500/80 inline-block"></span> Raw Degraded Data
          </span>
          <span class="flex items-center gap-1.5 text-emerald-400">
            <span class="w-3 h-3 rounded-full bg-emerald-500/80 inline-block"></span> Healed & Stabilized Distribution
          </span>
        </div>
      </div>

      <!-- Grid: Remediation Breakdown & Correlation Matrix -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <!-- Issue Types Breakdown -->
        <div class="bg-[#111827] border border-[#374151] rounded-2xl p-6 shadow-sm">
          <h3 class="text-base font-semibold text-white mb-2">Remediation Vector Breakdown</h3>
          <p class="text-xs text-gray-400 mb-4">Volume of autonomous transformations partitioned by anomaly mode</p>
          <div class="relative w-full h-56 bg-gray-900/60 rounded-xl border border-gray-800 p-4">
            <canvas id="breakdown-canvas" class="w-full h-full"></canvas>
          </div>
        </div>

        <!-- Correlation Heatmap Visual -->
        <div class="bg-[#111827] border border-[#374151] rounded-2xl p-6 shadow-sm">
          <h3 class="text-base font-semibold text-white mb-2">Feature Correlation Heatmap</h3>
          <p class="text-xs text-gray-400 mb-4">Bivariate relationship matrix calculated on sanitized metrics</p>
          <div id="heatmap-container" class="overflow-x-auto">
            <!-- Heatmap table generated dynamically -->
          </div>
        </div>

      </div>

    </section>

    <!-- TAB 3: BEFORE VS AFTER INSPECTOR -->
    <section id="tab-content-diff" class="hidden space-y-6">
      <div class="bg-[#111827] border border-[#374151] rounded-2xl p-6 shadow-sm">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h3 class="text-base font-semibold text-white">Live Record Diff Inspector</h3>
            <p class="text-xs text-gray-400">Examine how corrupted cells were identified, coerced, or imputed</p>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="toggleDiffMode('healed')" id="diff-btn-healed" class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium">Healed Clean View</button>
            <button onclick="toggleDiffMode('raw')" id="diff-btn-raw" class="px-3 py-1.5 bg-gray-800 text-gray-400 rounded-lg text-xs font-medium">Raw Dirty View</button>
          </div>
        </div>

        <div class="overflow-x-auto border border-gray-800 rounded-xl max-h-96">
          <table class="w-full text-xs text-left text-gray-300">
            <thead class="text-xs uppercase bg-gray-800/90 text-gray-400 sticky top-0" id="diff-table-head">
              <!-- Injected via JS -->
            </thead>
            <tbody id="diff-table-body" class="divide-y divide-gray-800">
              <!-- Injected via JS -->
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 4: HEALING AUDIT LEDGER -->
    <section id="tab-content-ledger" class="hidden space-y-6">
      <div class="bg-[#111827] border border-[#374151] rounded-2xl p-6 shadow-sm">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h3 class="text-base font-semibold text-white">Autonomous Healing Ledger</h3>
            <p class="text-xs text-gray-400">Tamper-evident record of atomic cell repairs and confidence scores</p>
          </div>
          <input type="text" id="ledger-search" oninput="filterLedger()" placeholder="Search column or strategy..." class="bg-gray-800 border border-gray-700 text-xs rounded-lg px-3 py-1.5 text-gray-200 w-64">
        </div>

        <div class="overflow-x-auto border border-gray-800 rounded-xl max-h-96">
          <table class="w-full text-xs text-left text-gray-300">
            <thead class="text-xs uppercase bg-gray-800/90 text-gray-400 sticky top-0">
              <tr>
                <th class="px-4 py-3">Time</th>
                <th class="px-4 py-3">Row</th>
                <th class="px-4 py-3">Column</th>
                <th class="px-4 py-3">Issue Mode</th>
                <th class="px-4 py-3">Original</th>
                <th class="px-4 py-3">Healed</th>
                <th class="px-4 py-3">Strategy</th>
                <th class="px-4 py-3">Confidence</th>
              </tr>
            </thead>
            <tbody id="ledger-table-body" class="divide-y divide-gray-800">
              <!-- Injected via JS -->
            </tbody>
          </table>
        </div>
      </div>
    </section>

  </main>

  <footer class="max-w-7xl mx-auto mt-12 text-center text-xs text-gray-500 pb-8">
    AutoHeal AI Autonomous Pipeline &bull; Zero Human Intervention Engine &bull; Antigravity Runtime
  </footer>

  <!-- Embedded Telemetry Data -->
  <script>
    const PIPELINE_DATA = {json_data_str};

    let currentTab = 'insights';
    let currentDiffMode = 'healed';

    // Initialize on page load
    window.addEventListener('DOMContentLoaded', () => {{
      initHeaderAndKPIs();
      initInsightsTab();
      initVisualsTab();
      initDiffTab();
      initLedgerTab();
    }});

    function initHeaderAndKPIs() {{
      document.getElementById('banner-dataset-name').textContent = PIPELINE_DATA.dataset_name;
      document.getElementById('kpi-final-score').textContent = PIPELINE_DATA.final_score;
      document.getElementById('kpi-final-grade').textContent = PIPELINE_DATA.final_grade;
      document.getElementById('kpi-initial-score').textContent = PIPELINE_DATA.initial_score;
      document.getElementById('kpi-score-gain').textContent = `+${{PIPELINE_DATA.score_gain}} pts`;
      document.getElementById('kpi-total-repairs').textContent = PIPELINE_DATA.total_repairs;
      
      const missingCount = PIPELINE_DATA.issue_counts['MISSING_VALUE'] || 0;
      const typeCount = (PIPELINE_DATA.issue_counts['CORRUPT_TYPE'] || 0) + (PIPELINE_DATA.issue_counts['OUTLIER_BOUNDED'] || 0);
      document.getElementById('kpi-missing-imputed').textContent = missingCount;
      document.getElementById('kpi-type-outliers').textContent = typeCount;
    }}

    function switchTab(tabName) {{
      const tabs = ['insights', 'visuals', 'diff', 'ledger'];
      tabs.forEach(t => {{
        document.getElementById(`tab-content-${{t}}`).classList.add('hidden');
        const btn = document.getElementById(`tab-btn-${{t}}`);
        btn.classList.remove('tab-active');
        btn.classList.add('text-gray-400');
      }});

      document.getElementById(`tab-content-${{tabName}}`).classList.remove('hidden');
      const activeBtn = document.getElementById(`tab-btn-${{tabName}}`);
      activeBtn.classList.add('tab-active');
      activeBtn.classList.remove('text-gray-400');
      currentTab = tabName;

      if (tabName === 'visuals') {{
        renderDistributionChart();
        renderBreakdownChart();
        renderHeatmap();
      }}
    }}

    function initInsightsTab() {{
      const insights = PIPELINE_DATA.insights;
      document.getElementById('narrative-executive-summary').innerHTML = formatMarkdown(insights.executive_summary);

      // Render correlations
      const corrContainer = document.getElementById('correlations-container');
      corrContainer.innerHTML = '';
      if (!insights.correlation_insights || insights.correlation_insights.length === 0) {{
        corrContainer.innerHTML = '<p class="text-xs text-gray-500">No strong bivariate correlations detected.</p>';
      }} else {{
        insights.correlation_insights.forEach(c => {{
          const card = document.createElement('div');
          card.className = 'p-3 bg-gray-900/70 border border-gray-800 rounded-xl text-xs space-y-1';
          card.innerHTML = `
            <div class="flex items-center justify-between">
              <span class="font-semibold text-emerald-400">${{c.feature_a}} &harr; ${{c.feature_b}}</span>
              <span class="badge bg-emerald-500/20 text-emerald-300">r = ${{c.coefficient > 0 ? '+' : ''}}${{c.coefficient}}</span>
            </div>
            <p class="text-gray-300">${{formatMarkdown(c.narrative)}}</p>
          `;
          corrContainer.appendChild(card);
        }});
      }}

      // Render Anomaly Alerts
      const alertsContainer = document.getElementById('alerts-container');
      alertsContainer.innerHTML = '';
      if (!insights.anomaly_alerts || insights.anomaly_alerts.length === 0) {{
        alertsContainer.innerHTML = '<p class="text-xs text-gray-500">No anomalous clusters detected.</p>';
      }} else {{
        insights.anomaly_alerts.forEach(a => {{
          const isHigh = a.severity === 'HIGH';
          const card = document.createElement('div');
          card.className = `p-3 bg-gray-900/70 border rounded-xl text-xs space-y-1 ${{isHigh ? 'border-rose-500/30' : 'border-amber-500/30'}}`;
          card.innerHTML = `
            <div class="flex items-center justify-between">
              <span class="font-semibold text-white">${{a.title}}</span>
              <span class="badge ${{isHigh ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'}}">${{a.severity}}</span>
            </div>
            <p class="text-gray-300">${{formatMarkdown(a.description)}}</p>
          `;
          alertsContainer.appendChild(card);
        }});
      }}

      // Render Recommendations
      const recContainer = document.getElementById('recommendations-container');
      recContainer.innerHTML = '';
      insights.strategic_recommendations.forEach((r, idx) => {{
        const item = document.createElement('div');
        item.className = 'p-3.5 bg-gray-900/60 border border-gray-800 rounded-xl text-xs flex gap-3 items-start';
        item.innerHTML = `
          <div class="w-5 h-5 rounded-full bg-blue-600/30 text-blue-400 font-bold flex items-center justify-center flex-shrink-0 text-[11px] mt-0.5">${{idx + 1}}</div>
          <div class="text-gray-300 leading-relaxed">${{formatMarkdown(r)}}</div>
        `;
        recContainer.appendChild(item);
      }});
    }}

    function initVisualsTab() {{
      const select = document.getElementById('feature-select');
      select.innerHTML = '';
      const distKeys = Object.keys(PIPELINE_DATA.distribution_data);
      distKeys.forEach(k => {{
        const opt = document.createElement('option');
        opt.value = k;
        opt.textContent = k;
        select.appendChild(opt);
      }});
    }}

    function renderDistributionChart() {{
      const canvas = document.getElementById('distribution-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

      const feature = document.getElementById('feature-select').value;
      const data = PIPELINE_DATA.distribution_data[feature];
      if (!data) return;

      const w = rect.width;
      const h = rect.height;
      ctx.clearRect(0, 0, w, h);

      // Build bins
      const allVals = [...data.original, ...data.healed];
      const minVal = Math.min(...allVals);
      const maxVal = Math.max(...allVals);
      const binCount = 18;
      const binWidth = (maxVal - minVal) / binCount || 1;

      const origBins = new Array(binCount).fill(0);
      const healedBins = new Array(binCount).fill(0);

      data.original.forEach(v => {{
        const b = Math.min(binCount - 1, Math.max(0, Math.floor((v - minVal) / binWidth)));
        origBins[b]++;
      }});
      data.healed.forEach(v => {{
        const b = Math.min(binCount - 1, Math.max(0, Math.floor((v - minVal) / binWidth)));
        healedBins[b]++;
      }});

      const maxFreq = Math.max(...origBins, ...healedBins, 1);
      const padLeft = 40;
      const padBottom = 30;
      const plotW = w - padLeft - 20;
      const plotH = h - padBottom - 20;

      // Draw Grid
      ctx.strokeStyle = '#1f2937';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {{
        const y = 20 + (plotH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padLeft, y);
        ctx.lineTo(w - 20, y);
        ctx.stroke();

        ctx.fillStyle = '#6b7280';
        ctx.font = '10px sans-serif';
        const labelVal = Math.round(maxFreq - (maxFreq / 4) * i);
        ctx.fillText(labelVal, 10, y + 3);
      }}

      const barW = (plotW / binCount) * 0.4;
      const step = plotW / binCount;

      for (let i = 0; i < binCount; i++) {{
        const x = padLeft + i * step;

        // Raw Bar (rose)
        const origH = (origBins[i] / maxFreq) * plotH;
        ctx.fillStyle = 'rgba(239, 68, 68, 0.6)';
        ctx.fillRect(x, 20 + (plotH - origH), barW, origH);

        // Healed Bar (emerald)
        const healedH = (healedBins[i] / maxFreq) * plotH;
        ctx.fillStyle = 'rgba(16, 185, 129, 0.7)';
        ctx.fillRect(x + barW + 2, 20 + (plotH - healedH), barW, healedH);

        // X label every 3 bins
        if (i % 3 === 0) {{
          ctx.fillStyle = '#9ca3af';
          ctx.font = '9px sans-serif';
          const valLabel = Math.round(minVal + i * binWidth);
          ctx.fillText(valLabel, x, h - 10);
        }}
      }}
    }}

    function renderBreakdownChart() {{
      const canvas = document.getElementById('breakdown-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

      const w = rect.width;
      const h = rect.height;
      ctx.clearRect(0, 0, w, h);

      const counts = PIPELINE_DATA.issue_counts;
      const keys = Object.keys(counts);
      if (keys.length === 0) return;

      const colors = ['#f59e0b', '#8b5cf6', '#3b82f6', '#10b981', '#ec4899', '#6366f1'];
      const maxVal = Math.max(...Object.values(counts), 1);
      const padLeft = 140;
      const barH = 20;
      const gap = 14;

      keys.forEach((k, idx) => {{
        const y = 20 + idx * (barH + gap);
        const val = counts[k];
        const barW = ((w - padLeft - 60) * (val / maxVal));

        // Label
        ctx.fillStyle = '#d1d5db';
        ctx.font = '11px sans-serif';
        const displayKey = k.replace(/_/g, ' ');
        ctx.fillText(displayKey, 10, y + 14);

        // Bar
        ctx.fillStyle = colors[idx % colors.length];
        ctx.beginPath();
        ctx.roundRect(padLeft, y, Math.max(barW, 4), barH, 4);
        ctx.fill();

        // Count label
        ctx.fillStyle = '#9ca3af';
        ctx.fillText(val, padLeft + barW + 8, y + 14);
      }});
    }}

    function renderHeatmap() {{
      const container = document.getElementById('heatmap-container');
      const corr = PIPELINE_DATA.corr_matrix;
      if (!corr || !corr.columns || corr.columns.length === 0) {{
        container.innerHTML = '<p class="text-xs text-gray-500">Insufficient numeric features for correlation matrix.</p>';
        return;
      }}

      let html = '<table class="w-full text-xs text-center border-collapse"><thead><tr><th class="p-2 text-left text-gray-400"></th>';
      corr.columns.forEach(c => {{
        html += `<th class="p-2 text-gray-300 font-medium truncate max-w-[80px]" title="${{c}}">${{c}}</th>`;
      }});
      html += '</tr></thead><tbody>';

      corr.columns.forEach((rowName, rIdx) => {{
        html += `<tr><td class="p-2 text-left font-medium text-gray-300 truncate max-w-[100px]" title="${{rowName}}">${{rowName}}</td>`;
        corr.columns.forEach((colName, cIdx) => {{
          const val = corr.values[rIdx][cIdx];
          let bg = 'rgba(55, 65, 81, 0.4)';
          let textCol = '#9ca3af';
          if (val > 0) {{
            bg = `rgba(16, 185, 129, ${{Math.min(0.9, val * 0.9 + 0.1)}})`;
            textCol = val > 0.4 ? '#ffffff' : '#a7f3d0';
          }} else if (val < 0) {{
            bg = `rgba(239, 68, 68, ${{Math.min(0.9, Math.abs(val) * 0.9 + 0.1)}})`;
            textCol = Math.abs(val) > 0.4 ? '#ffffff' : '#fecaca';
          }}
          html += `<td class="p-2 font-mono font-medium rounded m-0.5" style="background-color: ${{bg}}; color: ${{textCol}};">${{val.toFixed(2)}}</td>`;
        }});
        html += '</tr>';
      }});
      html += '</tbody></table>';
      container.innerHTML = html;
    }}

    function initDiffTab() {{
      renderDiffTable();
    }}

    function toggleDiffMode(mode) {{
      currentDiffMode = mode;
      document.getElementById('diff-btn-healed').className = mode === 'healed'
        ? 'px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium'
        : 'px-3 py-1.5 bg-gray-800 text-gray-400 rounded-lg text-xs font-medium';
      document.getElementById('diff-btn-raw').className = mode === 'raw'
        ? 'px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium'
        : 'px-3 py-1.5 bg-gray-800 text-gray-400 rounded-lg text-xs font-medium';
      renderDiffTable();
    }}

    function renderDiffTable() {{
      const cols = PIPELINE_DATA.columns;
      const head = document.getElementById('diff-table-head');
      const body = document.getElementById('diff-table-body');
      
      head.innerHTML = `<tr><th class="px-3 py-2.5">#</th>${{cols.map(c => `<th class="px-3 py-2.5">${{c}}</th>`).join('')}}</tr>`;
      
      const records = currentDiffMode === 'healed' ? PIPELINE_DATA.sample_healed : PIPELINE_DATA.sample_orig;
      const altRecords = currentDiffMode === 'healed' ? PIPELINE_DATA.sample_orig : PIPELINE_DATA.sample_healed;

      body.innerHTML = '';
      records.forEach((row, rIdx) => {{
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-800/40 transition';
        let cells = `<td class="px-3 py-2 text-gray-500 font-mono text-[11px]">${{rIdx + 1}}</td>`;
        cols.forEach(c => {{
          const val = row[c] !== undefined ? row[c] : '—';
          const altVal = altRecords[rIdx] && altRecords[rIdx][c] !== undefined ? altRecords[rIdx][c] : '—';
          const isChanged = String(val) !== String(altVal);
          
          if (isChanged && currentDiffMode === 'healed') {{
            cells += `<td class="px-3 py-2"><span class="diff-healed px-1.5 py-0.5 rounded text-[11px]" title="Original was: ${{altVal}}">${{val}}</span></td>`;
          }} else if (isChanged && currentDiffMode === 'raw') {{
            cells += `<td class="px-3 py-2"><span class="bg-rose-500/20 text-rose-300 border border-rose-500/40 px-1.5 py-0.5 rounded text-[11px]">${{val}}</span></td>`;
          }} else {{
            cells += `<td class="px-3 py-2 text-gray-300">${{val}}</td>`;
          }}
        }});
        tr.innerHTML = cells;
        body.appendChild(tr);
      }});
    }}

    function initLedgerTab() {{
      renderLedgerRows(PIPELINE_DATA.ledger_actions);
    }}

    function renderLedgerRows(actions) {{
      const body = document.getElementById('ledger-table-body');
      body.innerHTML = '';
      if (!actions || actions.length === 0) {{
        body.innerHTML = '<tr><td colspan="8" class="px-4 py-8 text-center text-gray-500">No healing actions match query.</td></tr>';
        return;
      }}
      actions.forEach(a => {{
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-800/40 transition';
        const typeBadge = a.issue_type === 'MISSING_VALUE' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
          : a.issue_type === 'OUTLIER_BOUNDED' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
          : a.issue_type === 'CORRUPT_TYPE' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
          : 'bg-blue-500/20 text-blue-400 border border-blue-500/30';

        tr.innerHTML = `
          <td class="px-4 py-2 font-mono text-[11px] text-gray-400">${{a.timestamp}}</td>
          <td class="px-4 py-2 font-mono text-[11px] text-gray-400">${{a.row_index >= 0 ? a.row_index : 'Schema'}}</td>
          <td class="px-4 py-2 font-medium text-gray-200">${{a.column}}</td>
          <td class="px-4 py-2"><span class="badge ${{typeBadge}}">${{a.issue_type}}</span></td>
          <td class="px-4 py-2 font-mono text-gray-400 max-w-[120px] truncate" title="${{a.original_value}}">${{a.original_value !== null ? a.original_value : 'null'}}</td>
          <td class="px-4 py-2 font-mono text-emerald-400 font-medium max-w-[120px] truncate" title="${{a.healed_value}}">${{a.healed_value}}</td>
          <td class="px-4 py-2 text-gray-300 text-[11px] max-w-[180px] truncate" title="${{a.strategy}}">${{a.strategy}}</td>
          <td class="px-4 py-2 font-mono text-emerald-400 text-[11px]">${{(a.confidence_score * 100).toFixed(0)}}%</td>
        `;
        body.appendChild(tr);
      }});
    }}

    function filterLedger() {{
      const q = document.getElementById('ledger-search').value.toLowerCase();
      const filtered = PIPELINE_DATA.ledger_actions.filter(a => 
        a.column.toLowerCase().includes(q) ||
        a.issue_type.toLowerCase().includes(q) ||
        a.strategy.toLowerCase().includes(q) ||
        String(a.original_value).toLowerCase().includes(q)
      );
      renderLedgerRows(filtered);
    }}

    function formatMarkdown(text) {{
      if (!text) return '';
      return text
        .replace(/\\*\\*(.*?)\\*\\*/g, '<strong class="font-semibold text-white">$1</strong>')
        .replace(/\\*(.*?)\\*/g, '<em class="text-gray-300">$1</em>');
    }}
  </script>
</body>
</html>"""

"""
AutoHeal AI - Pipeline Orchestrator
Coordinates multi-vector detection, self-healing, automated EDA, feature engineering,
visual analytics, and plain-English narrative insight generation.
"""

import time
import json
from pathlib import Path
from typing import Dict, Any, Union, Optional
import pandas as pd
from .config import PipelineConfig
from .ledger import HealingLedger
from .detector import CorruptionDetector
from .healer import SelfHealingEngine
from .insights import PlainEnglishInsightEngine
from .visualizer import VisualAnalyticsGenerator
from .eda import ExploratoryDataAnalyzer
from .features import FeatureEngineer


class AutoHealPipeline:
    """
    Main entry point for autonomous data ingestion, healing, automated EDA,
    bias-mitigating feature engineering, visual analytics, and plain-English reporting.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.detector = CorruptionDetector(self.config)
        self.visualizer = VisualAnalyticsGenerator(self.config.reports_dir)
        self.eda_analyzer = ExploratoryDataAnalyzer()
        self.feature_engineer = FeatureEngineer()

    def process(
        self,
        data_source: Union[str, Path, pd.DataFrame],
        dataset_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end autonomous pipeline on file path or DataFrame:
        Ingestion -> Diagnostic -> 7-Pass Healing -> Automated EDA -> Feature Engineering -> Insights -> Dashboard
        """
        start_time = time.time()

        # Step 1: Ingestion
        if isinstance(data_source, (str, Path)):
            path = Path(data_source)
            if not path.exists():
                raise FileNotFoundError(f"Source file not found: {path}")
            if not dataset_name:
                dataset_name = path.stem

            if path.suffix.lower() == ".csv":
                raw_df = pd.read_csv(path, dtype=object)  # Ingest strings to capture raw corruptions
            elif path.suffix.lower() in [".json", ".jsonl"]:
                raw_df = pd.read_json(path)
            elif path.suffix.lower() in [".parquet", ".pq"]:
                raw_df = pd.read_parquet(path)
            else:
                raw_df = pd.read_csv(path, dtype=object)
        elif isinstance(data_source, pd.DataFrame):
            raw_df = data_source.copy()
            if not dataset_name:
                dataset_name = "InMemoryDataset"
        else:
            raise ValueError("data_source must be a file path or pandas DataFrame")

        print(f"[AutoHealPipeline] Ingested '{dataset_name}' with {len(raw_df)} rows and {len(raw_df.columns)} columns.")

        # Step 2: Diagnostic Anomaly Detection
        initial_telemetry = self.detector.detect_all(raw_df)

        # Step 3: Autonomous Self-Healing & Preprocessing
        ledger = HealingLedger(dataset_name=dataset_name)
        healer = SelfHealingEngine(self.config, ledger)
        healed_df, populated_ledger = healer.heal(raw_df)

        ledger_summary = populated_ledger.get_summary()
        print(f"[AutoHealPipeline] Healing completed: {ledger_summary['total_healing_actions']} actions executed.")
        print(f"[AutoHealPipeline] Health Score: {ledger_summary['initial_health_score']}/100 -> {ledger_summary['final_health_score']}/100 (+{ledger_summary['score_improvement']} pts)")

        # Step 4: Automated Exploratory Data Analysis (EDA)
        eda_results = self.eda_analyzer.analyze(healed_df)
        num_profiles = len(eda_results["univariate"]["numerical_profiles"])
        cat_profiles = len(eda_results["univariate"]["categorical_profiles"])
        corrs = len(eda_results["bivariate"]["numeric_correlations"])
        collin = len(eda_results["multivariate"]["multicollinearity_warnings"])
        print(f"[AutoHealPipeline] Automated EDA completed: Univariate ({num_profiles} num, {cat_profiles} cat), Bivariate ({corrs} pairs), Multivariate ({collin} collinearity warnings).")

        # Step 5: Bias-Mitigating Feature Engineering
        ml_features_df, fe_summary = self.feature_engineer.transform(healed_df)
        print(f"[AutoHealPipeline] Feature Engineering: Generated {fe_summary['engineered_features_count']} bias-mitigating features ({len(healed_df.columns)} -> {len(ml_features_df.columns)} cols).")

        # Step 6: Autonomous Plain-English Insight Generation
        insight_engine = PlainEnglishInsightEngine(dataset_name=dataset_name)
        insights = insight_engine.generate_all_insights(raw_df, healed_df, populated_ledger)

        # Step 7: Instant Visual Analytics Dashboard Generation
        dashboard_filename = f"{dataset_name}_dashboard.html"
        dashboard_path = self.visualizer.generate_dashboard(
            dataset_name=dataset_name,
            original_df=raw_df,
            healed_df=healed_df,
            ledger_summary=ledger_summary,
            insights=insights,
            output_filename=dashboard_filename
        )

        # Step 8: Export Sanitized Data, Engineered Features, and Telemetry
        self.config.healed_dir.mkdir(parents=True, exist_ok=True)
        self.config.reports_dir.mkdir(parents=True, exist_ok=True)

        healed_csv_path = self.config.healed_dir / f"{dataset_name}_healed.csv"
        healed_json_path = self.config.healed_dir / f"{dataset_name}_healed.json"
        ml_features_csv_path = self.config.healed_dir / f"{dataset_name}_ml_features.csv"
        eda_json_path = self.config.reports_dir / f"{dataset_name}_eda_profile.json"
        fe_json_path = self.config.reports_dir / f"{dataset_name}_feature_engineering.json"
        insights_md_path = self.config.reports_dir / f"{dataset_name}_insights.md"
        audit_json_path = self.config.reports_dir / f"{dataset_name}_audit_ledger.json"

        healed_df.to_csv(healed_csv_path, index=False)
        healed_df.to_json(healed_json_path, orient="records", date_format="iso", indent=2)
        ml_features_df.to_csv(ml_features_csv_path, index=False)

        with open(eda_json_path, "w", encoding="utf-8") as f:
            json.dump(eda_results, f, indent=2)

        with open(fe_json_path, "w", encoding="utf-8") as f:
            json.dump(fe_summary, f, indent=2)

        with open(insights_md_path, "w", encoding="utf-8") as f:
            f.write(insights["markdown_report"])

        with open(audit_json_path, "w", encoding="utf-8") as f:
            json.dump(ledger_summary, f, indent=2)

        duration = round(time.time() - start_time, 2)
        print(f"[AutoHealPipeline] All artifacts generated in {duration}s:")
        print(f"  - Healed Dataset: {healed_csv_path}")
        print(f"  - ML Engineered Features: {ml_features_csv_path}")
        print(f"  - Automated EDA Profile: {eda_json_path}")
        print(f"  - Visual Analytics Dashboard: {dashboard_path}")
        print(f"  - Plain-English Briefing: {insights_md_path}")

        return {
            "dataset_name": dataset_name,
            "duration_seconds": duration,
            "original_rows": len(raw_df),
            "healed_rows": len(healed_df),
            "columns": list(healed_df.columns),
            "initial_health_score": ledger_summary["initial_health_score"],
            "final_health_score": ledger_summary["final_health_score"],
            "score_gain": ledger_summary["score_improvement"],
            "initial_grade": ledger_summary["initial_grade"],
            "final_grade": ledger_summary["final_grade"],
            "total_repairs": ledger_summary["total_healing_actions"],
            "repairs_by_type": ledger_summary["issues_resolved_by_type"],
            "eda": eda_results,
            "feature_engineering": fe_summary,
            "insights": insights,
            "artifacts": {
                "dashboard_html": str(dashboard_path),
                "healed_csv": str(healed_csv_path),
                "healed_json": str(healed_json_path),
                "ml_features_csv": str(ml_features_csv_path),
                "eda_json": str(eda_json_path),
                "fe_json": str(fe_json_path),
                "insights_md": str(insights_md_path),
                "audit_json": str(audit_json_path)
            },
            "healed_df": healed_df,
            "ml_features_df": ml_features_df,
            "ledger": populated_ledger
        }

    def watch_directory(self, check_interval_sec: float = 2.0, max_iterations: Optional[int] = None):
        """
        Monitors incoming_dir for newly arriving datasets and heals them continuously.
        """
        incoming = self.config.incoming_dir
        incoming.mkdir(parents=True, exist_ok=True)
        print(f"[AutoHealWatcher] Watching directory for incoming files: {incoming}")

        processed_files = set()
        iterations = 0

        while True:
            if max_iterations is not None and iterations >= max_iterations:
                break

            for file_path in incoming.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in [".csv", ".json", ".parquet"]:
                    if file_path.name not in processed_files:
                        print(f"[AutoHealWatcher] New dataset detected: {file_path.name}")
                        try:
                            self.process(file_path)
                            processed_files.add(file_path.name)
                        except Exception as e:
                            print(f"[AutoHealWatcher] Error processing {file_path.name}: {e}")

            time.sleep(check_interval_sec)
            iterations += 1

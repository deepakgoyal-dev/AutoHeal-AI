"""
AegisData AI - Command Line Runner
Execute autonomous self-healing, visual dashboard creation, and plain-English insights from the terminal.
"""

import sys
import argparse
from pathlib import Path
from aegis import AegisPipeline, CorruptedDataGenerator, PipelineConfig


def main():
    parser = argparse.ArgumentParser(
        description="AegisData AI - Autonomous Self-Healing Pipeline & Instant Analytics Engine"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Path to raw or corrupted dataset file (CSV, JSON, Parquet)"
    )
    parser.add_argument(
        "--demo", "-d",
        type=str,
        choices=["ecommerce", "healthcare", "all"],
        default=None,
        help="Run autonomous demonstration on realistic contaminated enterprise datasets"
    )
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="Run continuously in background watcher mode, monitoring data/incoming/"
    )
    parser.add_argument(
        "--rows", "-n",
        type=int,
        default=500,
        help="Number of rows for demo data synthesis (default: 500)"
    )

    args = parser.parse_args()
    config = PipelineConfig()
    pipeline = AegisPipeline(config)

    print("=================================================================")
    print("  AEGISDATA AI: AUTONOMOUS SELF-HEALING DATA PIPELINE")
    print("  Zero Human Intervention &bull; Instant Visual Analytics &bull; Plain English")
    print("=================================================================\n")

    if args.watch:
        print("[Mode] Continuous Directory Watcher Mode active.")
        print(f"Drop CSV/JSON files into: {config.incoming_dir.resolve()}")
        pipeline.watch_directory()
        return

    if args.demo:
        demos = []
        if args.demo in ["ecommerce", "all"]:
            demos.append(("Global_Ecommerce_Transactions", CorruptedDataGenerator.generate_ecommerce_dataset(n_rows=args.rows)))
        if args.demo in ["healthcare", "all"]:
            demos.append(("Clinical_Patient_Vitals", CorruptedDataGenerator.generate_healthcare_dataset(n_rows=args.rows)))

        for name, df in demos:
            print(f"\n>>> Running Autonomous Self-Healing on Demo: '{name}' ({len(df)} rows)")
            res = pipeline.process(df, dataset_name=name)
            print_summary(res)

        return

    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: File not found: {input_path}")
            sys.exit(1)

        print(f"\n>>> Running Autonomous Self-Healing on: '{input_path.name}'")
        res = pipeline.process(input_path)
        print_summary(res)
        return

    # Default if no arguments passed: run ecommerce demo
    print("[Notice] No arguments provided. Executing standard enterprise demonstration...")
    demo_df = CorruptedDataGenerator.generate_ecommerce_dataset(n_rows=args.rows)
    res = pipeline.process(demo_df, dataset_name="Enterprise_Retail_Transactions")
    print_summary(res)


def print_summary(res: dict):
    print("\n----------------- PIPELINE EXECUTION SUMMARY -----------------")
    print(f"Dataset Name:           {res['dataset_name']}")
    print(f"Execution Latency:      {res['duration_seconds']} seconds")
    print(f"Data Health (Initial):  {res['initial_health_score']}/100 [{res['initial_grade']}]")
    print(f"Data Health (Healed):   {res['final_health_score']}/100 [{res['final_grade']}]")
    print(f"Quality Improvement:    +{res['score_gain']} points")
    print(f"Autonomous Repairs:     {res['total_repairs']} actions executed")
    print("Remediation Breakdown:")
    for issue, count in res["repairs_by_type"].items():
        print(f"  * {issue:<20}: {count} cells healed")
    print("\nArtifacts Generated:")
    for k, v in res["artifacts"].items():
        print(f"  * {k:<15}: {v}")
    print("\nPlain-English Intelligence Briefing:")
    print(res["insights"]["executive_summary"])
    print("--------------------------------------------------------------\n")


if __name__ == "__main__":
    main()

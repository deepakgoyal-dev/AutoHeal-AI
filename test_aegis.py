"""
AutoHeal AI - Unit & Integration Test Suite
# Test suite engineered by Riddhi Garg & Deepak
Validates detection accuracy, autonomous self-healing, health scoring, and insight generation.
"""

import unittest
import numpy as np
import pandas as pd
from pathlib import Path

from aegis import (
    AutoHealPipeline,
    PipelineConfig,
    CorruptionDetector,
    SelfHealingEngine,
    HealingLedger,
    PlainEnglishInsightEngine,
    CorruptedDataGenerator
)


class TestAutoHealPipeline(unittest.TestCase):

    def setUp(self):
        self.config = PipelineConfig()
        self.pipeline = AutoHealPipeline(self.config)

    def test_detection_and_healing_synthetic(self):
        """Test detection and healing on controlled synthetic corrupted data."""
        dirty_data = {
            " Product Name ": ["Laptop", "laptop", "Laptp", "Mouse", "Mouse"],
            "Price": ["$1,200.50", "€950.00", "N/A", "-999", "50.00"],
            "Discount": ["10%", " 15% ", "null", "25%", "?? "],
            "Order_Date": ["2023-01-15", "16/01/2023", "Jan 17, 2023", "2023/01/18", "1674086400"],
            "Quantity": [1, 2, 9999, 1, 2]  # 9999 is an outlier
        }
        df = pd.DataFrame(dirty_data)

        # 1. Test Detection
        detector = CorruptionDetector(self.config)
        report = detector.detect_all(df)

        self.assertIn("Price", report["type_corruptions"])
        self.assertGreater(report["missingness"]["Price"]["total_missing"], 0)
        self.assertGreater(len(report["header_issues"]), 0)

        # 2. Test Healing
        ledger = HealingLedger()
        healer = SelfHealingEngine(self.config, ledger)
        healed_df, ledger = healer.heal(df)

        # Verify header stabilization
        self.assertIn("product_name", healed_df.columns)
        self.assertIn("price", healed_df.columns)

        # Verify currency converted to float
        self.assertTrue(pd.api.types.is_numeric_dtype(healed_df["price"]))
        self.assertEqual(healed_df["price"].isna().sum(), 0)  # All missing/sentinels imputed!

        # Verify discount converted to numeric
        self.assertTrue(pd.api.types.is_numeric_dtype(healed_df["discount"]))

        # Verify outlier bounded
        self.assertLess(healed_df["quantity"].max(), 9999)

        # Verify health score improved
        summary = ledger.get_summary()
        self.assertGreater(summary["final_health_score"], summary["initial_health_score"])

    def test_plain_english_insights(self):
        """Test narrative synthesis and correlation discovery."""
        df = CorruptedDataGenerator.generate_ecommerce_dataset(n_rows=150)
        result = self.pipeline.process(df, dataset_name="Test_Ecommerce")

        insights = result["insights"]
        self.assertIn("executive_summary", insights)
        self.assertIn("data_health_assessment", insights)
        self.assertIn("strategic_recommendations", insights)
        self.assertGreater(len(insights["strategic_recommendations"]), 0)
        self.assertTrue(Path(result["artifacts"]["dashboard_html"]).exists())
        self.assertTrue(Path(result["artifacts"]["healed_csv"]).exists())
        self.assertTrue(Path(result["artifacts"]["insights_md"]).exists())

    def test_duplicate_purging(self):
        """Test exact duplicate row detection and purging."""
        data = {
            "id": [1, 2, 2, 3],
            "val": [10.0, 20.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        ledger = HealingLedger()
        healer = SelfHealingEngine(self.config, ledger)
        healed_df, ledger = healer.heal(df)

        self.assertEqual(len(healed_df), 3)
        summary = ledger.get_summary()
        self.assertEqual(summary["issues_resolved_by_type"].get("DUPLICATE_PURGED", 0), 1)


if __name__ == "__main__":
    unittest.main()

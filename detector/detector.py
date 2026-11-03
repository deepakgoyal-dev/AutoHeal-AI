"""
AutoHeal AI - Anomaly & Corruption Detection Engine
# Authored by: Rudra & Deepak
Automatically scans datasets for structural, type, statistical, and missingness anomalies.
"""

import re
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from .config import PipelineConfig


class CorruptionDetector:
    """
    Introspects datasets to identify and classify data quality anomalies across 6 vectors.
    """

    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()

    def detect_all(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs comprehensive diagnostic on DataFrame and returns structured anomaly telemetry.
        """
        report: Dict[str, Any] = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "total_cells": len(df) * len(df.columns),
            "header_issues": self.detect_header_issues(df),
            "duplicate_rows": int(df.duplicated().sum()),
            "missingness": {},
            "type_corruptions": {},
            "statistical_outliers": {},
            "categorical_drifts": {},
            "column_types": {}
        }

        for col in df.columns:
            series = df[col]
            missing_info = self.detect_missingness_in_column(series)
            if missing_info["total_missing"] > 0:
                report["missingness"][col] = missing_info

            type_info = self.detect_type_corruption(series)
            if type_info["is_corrupted"]:
                report["type_corruptions"][col] = type_info

            inferred_type = type_info.get("inferred_type", "string")
            report["column_types"][col] = inferred_type

            if inferred_type in ["numeric", "currency", "percentage"]:
                outlier_info = self.detect_outliers(series)
                if outlier_info["outlier_count"] > 0:
                    report["statistical_outliers"][col] = outlier_info

            elif inferred_type == "categorical":
                drift_info = self.detect_categorical_drift(series)
                if drift_info["potential_typos"]:
                    report["categorical_drifts"][col] = drift_info

        return report

    def detect_header_issues(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Detect trailing spaces, mixed casings, and special characters in column names."""
        issues = []
        for col in df.columns:
            col_str = str(col)
            cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', col_str.strip().lower())
            cleaned = re.sub(r'_+', '_', cleaned).strip('_')
            if col_str != cleaned:
                issues.append({
                    "original": col_str,
                    "recommended": cleaned,
                    "reason": "Header contains non-standard whitespace, special symbols, or erratic casing"
                })
        return issues

    def detect_missingness_in_column(self, series: pd.Series) -> Dict[str, Any]:
        """Identifies standard nulls and hidden sentinel string representations."""
        standard_nulls = int(series.isna().sum())
        sentinel_matches = 0
        sentinel_samples = []

        for val in series.dropna():
            val_clean = str(val).strip().lower()
            if val_clean in self.config.sentinel_nulls:
                sentinel_matches += 1
                if str(val) not in sentinel_samples and len(sentinel_samples) < 5:
                    sentinel_samples.append(str(val))

        total_missing = standard_nulls + sentinel_matches
        pct = round((total_missing / len(series)) * 100.0, 2) if len(series) > 0 else 0.0

        return {
            "standard_nulls": standard_nulls,
            "hidden_sentinels": sentinel_matches,
            "total_missing": total_missing,
            "percentage": pct,
            "sentinel_samples": sentinel_samples
        }

    def detect_type_corruption(self, series: pd.Series) -> Dict[str, Any]:
        """
        Detects numbers stored as dirty strings, currency strings, percentages, or mixed dates.
        """
        valid_series = series.dropna()
        if len(valid_series) == 0:
            return {"is_corrupted": False, "inferred_type": "empty"}

        # If already native numeric, return clean
        if pd.api.types.is_numeric_dtype(series):
            return {"is_corrupted": False, "inferred_type": "numeric"}

        # Check for currency or dirty numeric strings
        currency_regex = re.compile(r'^[\$\€\£\¥\₹\s]*\-?\s*\$?\s*[\d,]+(\.\d+)?\s*[\$\€\£\¥\₹USD]*$', re.IGNORECASE)
        percent_regex = re.compile(r'^\s*\-?[\d,]+(\.\d+)?\s*%\s*$')
        dirty_num_regex = re.compile(r'^\s*[\+\-]?\d{1,3}(,\d{3})*(\.\d+)?\s*$')

        currency_matches = 0
        percent_matches = 0
        dirty_num_matches = 0
        date_candidates = 0

        # Sample non-null values for fast detection
        sample = valid_series.sample(min(100, len(valid_series)), random_state=42)
        non_sentinel_samples = [s for s in sample if str(s).strip().lower() not in self.config.sentinel_nulls]
        
        sample_len = len(non_sentinel_samples)
        if sample_len == 0:
            return {"is_corrupted": False, "inferred_type": "string"}

        for val in non_sentinel_samples:
            val_str = str(val).strip()

            if currency_regex.match(val_str) and any(c in val_str for c in self.config.currency_symbols):
                currency_matches += 1
            elif percent_regex.match(val_str):
                percent_matches += 1
            elif dirty_num_regex.match(val_str) and ("," in val_str or val_str.startswith(" ") or val_str.endswith(" ")):
                dirty_num_matches += 1
            else:
                # Check if potential date
                if self._is_potential_date(val_str):
                    date_candidates += 1

        if (currency_matches / sample_len) >= 0.35:
            return {
                "is_corrupted": True,
                "inferred_type": "currency",
                "corruption_mode": "Currency formatted strings masking numeric values",
                "match_rate": currency_matches / sample_len
            }

        if (percent_matches / sample_len) >= 0.35:
            return {
                "is_corrupted": True,
                "inferred_type": "percentage",
                "corruption_mode": "Percentage formatted strings masking numeric decimals",
                "match_rate": percent_matches / sample_len
            }

        if (dirty_num_matches / sample_len) >= 0.35:
            return {
                "is_corrupted": True,
                "inferred_type": "numeric",
                "corruption_mode": "Unparsed numeric strings with commas or irregular whitespace",
                "match_rate": dirty_num_matches / sample_len
            }

        if (date_candidates / sample_len) >= 0.35:
            return {
                "is_corrupted": True,
                "inferred_type": "datetime",
                "corruption_mode": "Unparsed or heterogeneous timestamp strings",
                "match_rate": date_candidates / sample_len
            }

        # Check unique cardinality for categorical inference
        nunique = series.nunique()
        if nunique < min(50, len(series) * 0.20):
            return {"is_corrupted": False, "inferred_type": "categorical"}

        return {"is_corrupted": False, "inferred_type": "string"}

    def _is_potential_date(self, val_str: str) -> bool:
        """Heuristic check for date-like string."""
        if len(val_str) < 6 or len(val_str) > 35:
            return False
        # Matches patterns like YYYY-MM-DD, DD/MM/YYYY, Mon DD YYYY
        if re.search(r'\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b', val_str):
            return True
        if re.search(r'\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b', val_str):
            return True
        if re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', val_str, re.IGNORECASE):
            return True
        return False

    def detect_outliers(self, series: pd.Series) -> Dict[str, Any]:
        """Detects distribution outliers via robust IQR."""
        # Convert to numeric if possible
        clean_nums = pd.to_numeric(
            series.astype(str).str.replace(r'[\$\€\£\¥\₹\,%]', '', regex=True).str.strip(),
            errors='coerce'
        ).dropna()

        if len(clean_nums) < 10:
            return {"outlier_count": 0, "outlier_percentage": 0.0}

        q1 = clean_nums.quantile(0.25)
        q3 = clean_nums.quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            return {"outlier_count": 0, "outlier_percentage": 0.0}

        lower_bound = q1 - (self.config.iqr_multiplier * iqr)
        upper_bound = q3 + (self.config.iqr_multiplier * iqr)
        extreme_lower = q1 - (self.config.iqr_extreme_multiplier * iqr)
        extreme_upper = q3 + (self.config.iqr_extreme_multiplier * iqr)

        outliers = clean_nums[(clean_nums < lower_bound) | (clean_nums > upper_bound)]
        extreme_outliers = clean_nums[(clean_nums < extreme_lower) | (clean_nums > extreme_upper)]

        return {
            "q1": round(float(q1), 2),
            "median": round(float(clean_nums.median()), 2),
            "q3": round(float(q3), 2),
            "iqr": round(float(iqr), 2),
            "lower_bound": round(float(lower_bound), 2),
            "upper_bound": round(float(upper_bound), 2),
            "outlier_count": int(len(outliers)),
            "extreme_outlier_count": int(len(extreme_outliers)),
            "outlier_percentage": round((len(outliers) / len(clean_nums)) * 100.0, 2),
            "sample_outliers": [float(x) for x in outliers.iloc[:5]]
        }

    def detect_categorical_drift(self, series: pd.Series) -> Dict[str, Any]:
        """
        Detects low-frequency typos and drift matching high-frequency canonical terms.
        """
        counts = series.dropna().astype(str).str.strip().value_counts()
        if len(counts) < 2:
            return {"potential_typos": []}

        # Look at terms with frequency differences
        high_freq = counts[counts >= max(3, int(len(series) * 0.05))].index.tolist()
        low_freq = counts[counts < max(3, int(len(series) * 0.05))].index.tolist()

        potential_typos = []
        for low in low_freq:
            low_clean = low.lower()
            if low_clean in self.config.sentinel_nulls:
                continue
            for high in high_freq:
                high_clean = high.lower()
                # Calculate Levenshtein-like similarity
                ratio = SequenceMatcher(None, low_clean, high_clean).ratio()
                if ratio >= self.config.fuzzy_match_threshold and low != high:
                    potential_typos.append({
                        "errant_value": low,
                        "canonical_target": high,
                        "similarity_score": round(ratio, 3),
                        "frequency": int(counts[low])
                    })
                    break

        return {
            "potential_typos": potential_typos
        }

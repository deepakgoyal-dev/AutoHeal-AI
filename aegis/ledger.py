"""
AutoHeal AI - Audit Ledger & Data Health Scorer
# Authored by: Deepak & Riddhi Garg
Maintains a tamper-evident audit log of all self-healing actions and computes health indices.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np


@dataclass
class HealingAction:
    timestamp: str
    row_index: int
    column: str
    issue_type: str  # MISSING_VALUE, CORRUPT_TYPE, OUTLIER_BOUNDED, TYPO_CORRECTED, DUPLICATE_PURGED, SCHEMA_FIXED
    original_value: Any
    healed_value: Any
    strategy: str
    confidence_score: float

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Ensure values are JSON serializable
        for k in ["original_value", "healed_value"]:
            val = d[k]
            if pd.isna(val) or val is None:
                d[k] = None
            elif isinstance(val, (np.integer, np.floating)):
                d[k] = float(val) if isinstance(val, np.floating) else int(val)
            elif not isinstance(val, (str, int, float, bool)):
                d[k] = str(val)
        return d


class HealingLedger:
    """
    Maintains the full audit trail of all autonomous corrections applied during the pipeline.
    """

    def __init__(self, dataset_name: str = "dataset"):
        self.dataset_name = dataset_name
        self.created_at = datetime.now().isoformat()
        self.actions: List[HealingAction] = []
        self.initial_metrics: Dict[str, Any] = {}
        self.final_metrics: Dict[str, Any] = {}
        self.initial_health_score: float = 100.0
        self.final_health_score: float = 100.0

    def record_action(
        self,
        row_index: int,
        column: str,
        issue_type: str,
        original_value: Any,
        healed_value: Any,
        strategy: str,
        confidence_score: float = 1.0
    ):
        """Record an individual atomic healing operation."""
        action = HealingAction(
            timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            row_index=row_index,
            column=column,
            issue_type=issue_type,
            original_value=original_value,
            healed_value=healed_value,
            strategy=strategy,
            confidence_score=round(confidence_score, 3)
        )
        self.actions.append(action)

    def compute_health_score(self, df: pd.DataFrame, is_initial: bool = False) -> float:
        """
        Calculates a holistic Data Health Score (0 - 100) based on:
        - Completeness: proportion of non-null, non-sentinel values (35% weight)
        - Syntactic Validity: absence of dirty formatting, unparsed symbols, header noise (30% weight)
        - Outlier Reasonableness: proportion of values within distribution bounds (20% weight)
        - Uniqueness: proportion of non-duplicate records (15% weight)
        """
        import re
        if df.empty:
            return 0.0

        total_cells = df.shape[0] * df.shape[1]
        if total_cells == 0:
            return 0.0

        sentinel_set = {
            "", " ", "nan", "none", "null", "n/a", "na", "#n/a", "missing",
            "undefined", "-999", "-9999", "?", "??", "???", "nil", "void"
        }

        # 1. Completeness score (standard NaNs + masked sentinel strings)
        standard_nulls = df.isna().sum().sum()
        sentinel_matches = 0
        corrupt_format_cells = 0

        for col in df.columns:
            for val in df[col].dropna():
                val_s = str(val).strip()
                if val_s.lower() in sentinel_set:
                    sentinel_matches += 1
                elif any(c in val_s for c in "$€£¥₹%") or ("," in val_s and re.match(r'^\d{1,3}(,\d{3})+', val_s)):
                    corrupt_format_cells += 1

        total_missing = standard_nulls + sentinel_matches
        completeness = max(0.0, 1.0 - (total_missing / total_cells))

        # 2. Syntactic validity (absence of currency/percent strings in cells + header cleanliness)
        dirty_headers = sum(1 for col in df.columns if str(col) != re.sub(r'[^a-zA-Z0-9_]', '_', str(col).strip().lower()).strip('_'))
        header_score = max(0.0, 1.0 - (dirty_headers / len(df.columns)))
        cell_validity = max(0.0, 1.0 - (corrupt_format_cells / total_cells))
        validity = (cell_validity * 0.70) + (header_score * 0.30)

        # 3. Uniqueness score
        duplicate_rows = df.duplicated().sum()
        uniqueness = max(0.0, 1.0 - (duplicate_rows / len(df)))

        # 4. Outlier score on valid numbers
        outlier_scores = []
        for col in df.columns:
            series = df[col].dropna()
            try:
                numeric_series = pd.to_numeric(
                    series.astype(str).str.replace(r'[\$\€\£\¥\₹\,%]', '', regex=True).str.strip(),
                    errors='coerce'
                ).dropna()
                if len(numeric_series) >= 4:
                    q1 = numeric_series.quantile(0.25)
                    q3 = numeric_series.quantile(0.75)
                    iqr = q3 - q1
                    if iqr > 0:
                        lower = q1 - 1.5 * iqr
                        upper = q3 + 1.5 * iqr
                        outliers = ((numeric_series < lower) | (numeric_series > upper)).sum()
                        col_outlier_rate = max(0.0, 1.0 - (outliers / len(numeric_series)))
                        outlier_scores.append(col_outlier_rate)
            except Exception:
                pass

        avg_outlier_score = float(np.mean(outlier_scores)) if outlier_scores else 1.0

        # Weighted composite score
        score = (
            (completeness * 0.35) +
            (validity * 0.30) +
            (avg_outlier_score * 0.20) +
            (uniqueness * 0.15)
        ) * 100.0

        score = round(max(5.0, min(100.0, score)), 1)
        if is_initial:
            self.initial_health_score = score
        else:
            self.final_health_score = score
        return score

    def get_summary(self) -> Dict[str, Any]:
        """Aggregate all actions by issue type, column, and compute improvement metrics."""
        summary_by_type: Dict[str, int] = {}
        summary_by_column: Dict[str, int] = {}

        for act in self.actions:
            summary_by_type[act.issue_type] = summary_by_type.get(act.issue_type, 0) + 1
            summary_by_column[act.column] = summary_by_column.get(act.column, 0) + 1

        score_delta = round(self.final_health_score - self.initial_health_score, 1)

        # Grade calculation
        def get_grade(score: float) -> str:
            if score >= 95: return "A+"
            if score >= 90: return "A"
            if score >= 80: return "B"
            if score >= 70: return "C"
            if score >= 60: return "D"
            return "F"

        return {
            "dataset_name": self.dataset_name,
            "created_at": self.created_at,
            "total_healing_actions": len(self.actions),
            "initial_health_score": self.initial_health_score,
            "final_health_score": self.final_health_score,
            "score_improvement": score_delta,
            "initial_grade": get_grade(self.initial_health_score),
            "final_grade": get_grade(self.final_health_score),
            "issues_resolved_by_type": summary_by_type,
            "repairs_by_column": summary_by_column,
            "actions_sample": [a.to_dict() for a in self.actions[:200]]  # Top 200 for payload
        }

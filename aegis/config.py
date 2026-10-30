"""
AegisData AI - Pipeline Configuration
Autonomous Self-Healing Data Pipeline & Plain-English Analytics Engine
"""

from dataclasses import dataclass, field
from typing import Set, Dict, Any
from pathlib import Path


@dataclass
class PipelineConfig:
    # Anomaly & Corruption thresholds
    outlier_method: str = "iqr"  # "iqr" or "zscore"
    iqr_multiplier: float = 1.5
    iqr_extreme_multiplier: float = 3.0
    zscore_threshold: float = 3.0
    fuzzy_match_threshold: float = 0.80  # Minimum similarity ratio for typo healing
    max_missing_drop_threshold: float = 0.90  # Only drop columns with >90% missingness

    # Hidden sentinel representations of missing / null data
    sentinel_nulls: Set[str] = field(default_factory=lambda: {
        "", " ", "nan", "none", "null", "n/a", "na", "#n/a", "missing",
        "undefined", "-999", "-9999", "-999.0", "?", "??", "???", "nil",
        "void", "unknown", "n.a.", "not available", "#ref!", "#value!",
        "blank", "empty"
    })

    # Strategy configurations
    numeric_imputation: str = "auto"  # "auto" (skew-aware), "median", "mean", "knn_grouped"
    categorical_imputation: str = "mode"  # "mode", "frequent", "sentinel"
    temporal_imputation: str = "interpolate"  # "interpolate", "ffill", "bfill"
    outlier_resolution: str = "winsorize"  # "winsorize", "clip", "flag_only"
    
    # Currency symbols & numeric stripping pattern
    currency_symbols: str = "$€£¥₹₽₩"
    
    # Path configuration
    base_dir: Path = Path(__file__).resolve().parent.parent
    incoming_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "incoming")
    healed_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "healed")
    reports_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "reports")
    samples_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "samples")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outlier_method": self.outlier_method,
            "iqr_multiplier": self.iqr_multiplier,
            "iqr_extreme_multiplier": self.iqr_extreme_multiplier,
            "fuzzy_match_threshold": self.fuzzy_match_threshold,
            "numeric_imputation": self.numeric_imputation,
            "outlier_resolution": self.outlier_resolution
        }

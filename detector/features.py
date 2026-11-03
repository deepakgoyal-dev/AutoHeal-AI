"""
AutoHeal AI - Bias-Mitigating Feature Engineering Engine
Engineers variance-stabilizing, cyclical temporal, representation-balanced,
and interaction features to prevent downstream machine learning bias.
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd


class FeatureEngineer:
    """
    Transforms clean datasets into ML-ready feature matrices with built-in
    bias mitigation (variance stabilization, rare-class binning, cyclical time).
    """

    def __init__(
        self,
        skew_threshold: float = 1.0,
        rare_category_pct: float = 0.025,
        create_interactions: bool = True
    ):
        self.skew_threshold = skew_threshold
        self.rare_category_pct = rare_category_pct
        self.create_interactions = create_interactions
        self.engineering_log: List[Dict[str, Any]] = []

    def transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes bias-mitigating feature engineering pipeline:
        1. Cyclical temporal decomposition
        2. Rare-category representation balancing
        3. Skewness variance-stabilization (log1p)
        4. Domain interaction features
        5. Non-parametric robust scaling parameter extraction
        """
        transformed_df = df.copy()
        self.engineering_log.clear()

        # 1. Temporal cyclical decomposition
        transformed_df = self._engineer_temporal_features(transformed_df)

        # 2. Representation bias mitigation (rare-class binning)
        transformed_df = self._mitigate_representation_bias(transformed_df)

        # 3. Variance stabilization for heavy-tailed features
        transformed_df = self._stabilize_skewness_variance(transformed_df)

        # 4. Domain interaction features
        if self.create_interactions:
            transformed_df = self._engineer_interaction_features(transformed_df)

        # 5. Extract RobustScaler parameters for ML consumption
        scaling_params = self._extract_robust_scaling_metadata(transformed_df)

        summary = {
            "initial_columns": len(df.columns),
            "final_columns": len(transformed_df.columns),
            "engineered_features_count": len(self.engineering_log),
            "engineering_log": self.engineering_log,
            "robust_scaling_metadata": scaling_params
        }

        return transformed_df, summary

    def _engineer_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Decomposes datetime columns into cyclical sine/cosine components."""
        datetime_cols = []
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                datetime_cols.append(col)
            elif "date" in str(col).lower() or "time" in str(col).lower() or "timestamp" in str(col).lower():
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    datetime_cols.append(col)
                except Exception:
                    pass

        for col in datetime_cols:
            series = df[col]
            if series.isna().all():
                continue

            year = series.dt.year
            month = series.dt.month
            day = series.dt.day
            dow = series.dt.dayofweek

            # Calendar features
            df[f"{col}_year"] = year
            df[f"{col}_month"] = month
            df[f"{col}_day"] = day
            df[f"{col}_dayofweek"] = dow
            df[f"{col}_is_weekend"] = dow.isin([5, 6]).astype(int)

            # Cyclical sine/cosine transforms to eliminate edge-discontinuity bias
            # Month cycle (1 - 12)
            df[f"{col}_month_sin"] = np.round(np.sin(2 * np.pi * (month - 1) / 12), 4)
            df[f"{col}_month_cos"] = np.round(np.cos(2 * np.pi * (month - 1) / 12), 4)

            # Day of week cycle (0 - 6)
            df[f"{col}_dow_sin"] = np.round(np.sin(2 * np.pi * dow / 7), 4)
            df[f"{col}_dow_cos"] = np.round(np.cos(2 * np.pi * dow / 7), 4)

            self.engineering_log.append({
                "source_feature": col,
                "engineered_features": [
                    f"{col}_year", f"{col}_month", f"{col}_day", f"{col}_dayofweek",
                    f"{col}_is_weekend", f"{col}_month_sin", f"{col}_month_cos",
                    f"{col}_dow_sin", f"{col}_dow_cos"
                ],
                "type": "TEMPORAL_CYCLICAL",
                "bias_mitigation": "Eliminates calendar boundary discontinuity (e.g. Sunday to Monday, Dec to Jan)"
            })

        return df

    def _mitigate_representation_bias(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Consolidates ultra-rare categories (< 2.5% frequency) into 'Other'
        to prevent high-cardinality overfitting and representation bias.
        """
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_datetime64_any_dtype(df[col]):
                series = df[col].astype(str)
                nunique = series.nunique()
                if nunique < 4 or nunique > 100:
                    continue

                counts = series.value_counts()
                threshold_count = max(2, int(len(df) * self.rare_category_pct))
                rare_classes = counts[counts < threshold_count].index.tolist()

                if rare_classes and len(rare_classes) < nunique - 1:
                    binned_col_name = f"{col}_balanced"
                    df[binned_col_name] = series.apply(lambda x: "Other" if x in rare_classes else x)
                    self.engineering_log.append({
                        "source_feature": col,
                        "engineered_features": [binned_col_name],
                        "type": "REPRESENTATION_BALANCED",
                        "bias_mitigation": f"Consolidated {len(rare_classes)} rare categories (<{self.rare_category_pct*100:.1f}%) into 'Other' to prevent class frequency bias"
                    })

        return df

    def _stabilize_skewness_variance(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates log1p variance-stabilized features for heavy-tailed positive distributions
        to prevent high-magnitude instances from dominating model loss gradients.
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if any(col.endswith(sfx) for sfx in ["_sin", "_cos", "_year", "_day", "_month", "_dayofweek", "_is_weekend"]):
                continue

            series = df[col].dropna()
            if len(series) < 5 or (series < 0).any():
                continue

            skewness = float(series.skew())
            if skewness >= self.skew_threshold:
                log_col_name = f"{col}_log1p"
                df[log_col_name] = np.round(np.log1p(df[col]), 4)
                self.engineering_log.append({
                    "source_feature": col,
                    "engineered_features": [log_col_name],
                    "type": "VARIANCE_STABILIZATION",
                    "bias_mitigation": f"Applied log1p transform (skewness={skewness:.2f}) to stabilize gradient variance in downstream estimators"
                })

        return df

    def _engineer_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Discovers domain price & volume pairs to generate non-linear interaction features.
        """
        price_cols = [c for c in df.columns if any(p in c.lower() for p in ["price", "cost", "fee"]) and pd.api.types.is_numeric_dtype(df[c])]
        qty_cols = [c for c in df.columns if any(q in c.lower() for q in ["quantity", "units", "qty", "items", "count"]) and not any(p in c.lower() for p in ["price", "cost", "fee"]) and pd.api.types.is_numeric_dtype(df[c])]

        for p_col in price_cols[:2]:
            for q_col in qty_cols[:2]:
                if p_col == q_col:
                    continue
                inter_col = f"interaction_{p_col}_x_{q_col}"
                df[inter_col] = np.round(df[p_col] * df[q_col], 2)
                self.engineering_log.append({
                    "source_feature": f"{p_col} * {q_col}",
                    "engineered_features": [inter_col],
                    "type": "DOMAIN_INTERACTION",
                    "bias_mitigation": "Explicit interaction product prevents linear models from underestimating compounding volume-price effects"
                })

        return df

    def _extract_robust_scaling_metadata(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Calculates non-parametric median and IQR for every numerical feature
        to enable bias-free RobustScaler normalization for downstream modeling.
        """
        scaling_meta = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 3:
                continue
            q1 = float(series.quantile(0.25))
            q2 = float(series.median())
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1 if (q3 - q1) > 0 else 1.0

            scaling_meta[col] = {
                "median": round(q2, 3),
                "iqr": round(iqr, 3),
                "q1": round(q1, 3),
                "q3": round(q3, 3)
            }
        return scaling_meta

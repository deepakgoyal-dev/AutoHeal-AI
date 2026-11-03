"""
AutoHeal AI - Automated Exploratory Data Analysis (EDA) Engine
Performs intelligent univariate, bivariate, and multivariate analysis
with automated analysis planning and statistical distribution classification.
"""

from typing import Dict, List, Any, Tuple, Optional
import math
import numpy as np
import pandas as pd


class ExploratoryDataAnalyzer:
    """
    Introspects datasets to automatically plan, dispatch, and execute
    univariate, bivariate, and multivariate statistical analyses.
    """

    def __init__(self, sample_limit: int = 5000):
        self.sample_limit = sample_limit

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes end-to-end automated EDA across univariate, bivariate,
        and multivariate statistical dimensions.
        """
        analysis_df = df.copy()
        if len(analysis_df) > self.sample_limit:
            analysis_df = analysis_df.sample(self.sample_limit, random_state=42)

        # Step 1: Automated Analysis Dispatcher (Type & Role Classification)
        column_meta = self._classify_columns(analysis_df)

        # Step 2: Univariate Analysis
        univariate = self._perform_univariate_analysis(analysis_df, column_meta)

        # Step 3: Bivariate Analysis
        bivariate = self._perform_bivariate_analysis(analysis_df, column_meta)

        # Step 4: Multivariate Analysis
        multivariate = self._perform_multivariate_analysis(analysis_df, column_meta)

        return {
            "summary": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "numeric_features": len(column_meta["numeric"]),
                "categorical_features": len(column_meta["categorical"]),
                "temporal_features": len(column_meta["temporal"]),
                "high_cardinality_features": len(column_meta["identifiers"])
            },
            "dispatch_plan": column_meta,
            "univariate": univariate,
            "bivariate": bivariate,
            "multivariate": multivariate
        }

    def _classify_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Intelligently inspects columns and dispatches them to appropriate statistical regimes.
        """
        classification = {
            "numeric": [],
            "categorical": [],
            "temporal": [],
            "binary": [],
            "identifiers": []
        }

        for col in df.columns:
            series = df[col].dropna()
            if len(series) == 0:
                continue

            nunique = int(series.nunique())
            ratio = nunique / len(series)

            if pd.api.types.is_numeric_dtype(series):
                if nunique == 2:
                    classification["binary"].append(col)
                elif nunique < 10 and ratio < 0.05:
                    classification["categorical"].append(col)
                else:
                    classification["numeric"].append(col)
            elif pd.api.types.is_datetime64_any_dtype(series) or "date" in str(col).lower() or "time" in str(col).lower():
                classification["temporal"].append(col)
            else:
                if nunique == 2:
                    classification["binary"].append(col)
                elif ratio > 0.85 and nunique > 50:
                    classification["identifiers"].append(col)
                else:
                    classification["categorical"].append(col)

        return classification

    def _perform_univariate_analysis(self, df: pd.DataFrame, meta: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Computes detailed univariate statistical moments, entropy, and distribution types.
        """
        numeric_results = {}
        for col in meta["numeric"]:
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(series) < 3:
                continue

            mean_val = float(series.mean())
            median_val = float(series.median())
            std_val = float(series.std()) if len(series) > 1 else 0.0
            var_val = float(series.var()) if len(series) > 1 else 0.0
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            skewness = float(series.skew()) if len(series) > 2 else 0.0
            kurtosis = float(series.kurtosis()) if len(series) > 3 else 0.0
            cv = (std_val / mean_val) if abs(mean_val) > 1e-6 else 0.0

            # Empirical Distribution Classification
            if abs(skewness) < 0.5 and abs(kurtosis) < 1.0:
                dist_type = "Gaussian / Approximately Symmetric"
            elif skewness >= 0.5:
                dist_type = "Right-Skewed (Long Upper Tail)"
            elif skewness <= -0.5:
                dist_type = "Left-Skewed (Long Lower Tail)"
            elif kurtosis >= 1.5:
                dist_type = "Leptokurtic (Heavy-Tailed / Spiky)"
            elif kurtosis <= -1.0:
                dist_type = "Platykurtic (Uniform / Flat)"
            else:
                dist_type = "Moderate Variance"

            numeric_results[col] = {
                "mean": round(mean_val, 3),
                "median": round(median_val, 3),
                "std": round(std_val, 3),
                "variance": round(var_val, 3),
                "iqr": round(iqr, 3),
                "min": round(float(series.min()), 3),
                "max": round(float(series.max()), 3),
                "skewness": round(skewness, 3),
                "excess_kurtosis": round(kurtosis, 3),
                "coeff_variation": round(cv, 3),
                "distribution_classification": dist_type
            }

        categorical_results = {}
        for col in meta["categorical"] + meta["binary"]:
            series = df[col].dropna().astype(str)
            if len(series) == 0:
                continue

            counts = series.value_counts()
            probs = counts / len(series)
            # Shannon Entropy: H(X) = -sum(p * log2(p))
            entropy = -sum(p * math.log2(p) for p in probs if p > 0)
            max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
            norm_entropy = (entropy / max_entropy) if max_entropy > 0 else 0.0

            # Class Imbalance Ratio
            imbalance_ratio = float(counts.iloc[0] / counts.iloc[-1]) if len(counts) > 1 and counts.iloc[-1] > 0 else 1.0

            categorical_results[col] = {
                "cardinality": int(len(counts)),
                "mode": str(counts.index[0]),
                "mode_frequency_pct": round(float(probs.iloc[0] * 100.0), 2),
                "shannon_entropy": round(float(entropy), 3),
                "normalized_entropy": round(float(norm_entropy), 3),
                "class_imbalance_ratio": round(imbalance_ratio, 2),
                "top_categories": {k: int(v) for k, v in counts.head(5).items()}
            }

        return {
            "numerical_profiles": numeric_results,
            "categorical_profiles": categorical_results
        }

    def _perform_bivariate_analysis(self, df: pd.DataFrame, meta: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Analyzes numerical linear/rank associations, ANOVA variance ratios, and categorical Cramér's V.
        """
        # 1. Numeric vs Numeric (Pearson r and Spearman rho)
        num_cols = meta["numeric"]
        num_pairs = []
        if len(num_cols) >= 2:
            clean_num_df = df[num_cols].apply(pd.to_numeric, errors='coerce').dropna()
            if len(clean_num_df) >= 5:
                pearson_corr = clean_num_df.corr(method='pearson')
                spearman_corr = clean_num_df.corr(method='spearman')

                for i, col_a in enumerate(num_cols):
                    for j, col_b in enumerate(num_cols):
                        if i >= j:
                            continue
                        r = pearson_corr.loc[col_a, col_b]
                        rho = spearman_corr.loc[col_a, col_b]
                        if pd.isna(r) or pd.isna(rho):
                            continue

                        is_linear = abs(r) >= 0.35 and abs(r - rho) < 0.15
                        is_non_linear_monotonic = abs(rho) >= 0.40 and abs(rho - r) >= 0.15

                        relationship = "Weak / Independent"
                        if abs(r) >= 0.70:
                            relationship = "Very Strong Linear"
                        elif abs(r) >= 0.50:
                            relationship = "Moderate Linear"
                        elif is_non_linear_monotonic:
                            relationship = "Non-Linear Monotonic Relationship"

                        num_pairs.append({
                            "feature_x": col_a,
                            "feature_y": col_b,
                            "pearson_r": round(float(r), 3),
                            "spearman_rho": round(float(rho), 3),
                            "relationship_type": relationship
                        })

        num_pairs.sort(key=lambda x: max(abs(x["pearson_r"]), abs(x["spearman_rho"])), reverse=True)

        # 2. Numeric vs Categorical (One-way ANOVA Eta-squared approximation)
        num_cat_pairs = []
        for num_col in num_cols[:4]:
            for cat_col in meta["categorical"][:4]:
                subset = df[[num_col, cat_col]].dropna()
                if len(subset) < 10:
                    continue
                subset[num_col] = pd.to_numeric(subset[num_col], errors='coerce')
                subset = subset.dropna()
                groups = [group[num_col].values for _, group in subset.groupby(cat_col) if len(group) >= 3]
                if len(groups) < 2:
                    continue

                # Compute Eta-squared: SS_between / SS_total
                grand_mean = np.mean(subset[num_col].values)
                ss_total = np.sum((subset[num_col].values - grand_mean) ** 2)
                ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)

                eta_sq = float(ss_between / ss_total) if ss_total > 1e-9 else 0.0
                if eta_sq >= 0.10:
                    num_cat_pairs.append({
                        "numeric_feature": num_col,
                        "categorical_feature": cat_col,
                        "eta_squared": round(eta_sq, 3),
                        "effect_size": "Large" if eta_sq >= 0.25 else "Moderate"
                    })

        num_cat_pairs.sort(key=lambda x: x["eta_squared"], reverse=True)

        # 3. Categorical vs Categorical (Cramér's V)
        cat_pairs = []
        cat_cols = meta["categorical"][:4]
        for i, col_a in enumerate(cat_cols):
            for j, col_b in enumerate(cat_cols):
                if i >= j:
                    continue
                contingency = pd.crosstab(df[col_a], df[col_b])
                if contingency.size < 4:
                    continue
                cramer_v = self._compute_cramers_v(contingency)
                if cramer_v >= 0.20:
                    cat_pairs.append({
                        "feature_a": col_a,
                        "feature_b": col_b,
                        "cramers_v": round(float(cramer_v), 3),
                        "association_strength": "Strong" if cramer_v >= 0.40 else "Moderate"
                    })

        cat_pairs.sort(key=lambda x: x["cramers_v"], reverse=True)

        return {
            "numeric_correlations": num_pairs[:8],
            "numeric_categorical_effects": num_cat_pairs[:6],
            "categorical_associations": cat_pairs[:5]
        }

    def _perform_multivariate_analysis(self, df: pd.DataFrame, meta: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Multivariate screening: Multicollinearity (VIF proxy), collinear clusters, and dimensionality redundancy.
        """
        num_cols = meta["numeric"]
        if len(num_cols) < 2:
            return {"multicollinearity_warnings": [], "dimensionality_redundancy": "Single numeric dimension"}

        clean_num_df = df[num_cols].apply(pd.to_numeric, errors='coerce').dropna()
        if len(clean_num_df) < 10:
            return {"multicollinearity_warnings": [], "dimensionality_redundancy": "Insufficient records for matrix decomposition"}

        corr = clean_num_df.corr().values
        vif_warnings = []

        # Approximate VIF from correlation matrix inversion: VIF_i = (R^-1)_{ii}
        try:
            inv_corr = np.linalg.pinv(corr)
            for idx, col in enumerate(num_cols):
                vif = float(inv_corr[idx, idx])
                if vif >= 4.0:
                    vif_warnings.append({
                        "column": col,
                        "vif_estimate": round(vif, 2),
                        "risk": "Severe Multicollinearity (Distorts model coefficients)" if vif >= 10.0 else "Moderate Multicollinearity"
                    })
        except Exception:
            pass

        # Dimensionality Redundancy via Eigenvalue Variance Ratio
        try:
            eigenvalues = np.linalg.eigvalsh(corr)
            eigenvalues = np.sort(eigenvalues)[::-1]
            var_explained = eigenvalues / np.sum(eigenvalues)
            cum_var = np.cumsum(var_explained)
            components_for_90pct = int(np.argmax(cum_var >= 0.90) + 1)
        except Exception:
            components_for_90pct = len(num_cols)

        return {
            "multicollinearity_warnings": vif_warnings,
            "total_dimensions": len(num_cols),
            "effective_dimensions_for_90pct_variance": components_for_90pct,
            "redundancy_ratio": round(1.0 - (components_for_90pct / len(num_cols)), 2)
        }

    @staticmethod
    def _compute_cramers_v(contingency_table: pd.DataFrame) -> float:
        """Calculates Cramér's V statistic for categorical association."""
        obs = contingency_table.values
        n = obs.sum()
        if n == 0:
            return 0.0
        row_sums = obs.sum(axis=1, keepdims=True)
        col_sums = obs.sum(axis=0, keepdims=True)
        expected = (row_sums @ col_sums) / n

        with np.errstate(divide='ignore', invalid='ignore'):
            chi2 = np.nansum(((obs - expected) ** 2) / expected)

        r, k = obs.shape
        min_dim = min(r - 1, k - 1)
        if min_dim == 0:
            return 0.0

        v = math.sqrt(chi2 / (n * min_dim))
        return min(1.0, max(0.0, v))

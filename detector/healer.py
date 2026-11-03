"""
AutoHeal AI - Multi-Pass Self-Healing Engine
# Authored by: Deepak (Lead) & Nikhil
Performs multi-pass data repair, missing value imputation, type coercion, and outlier resolution without human intervention.
"""

import re
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from datetime import datetime
from .config import PipelineConfig
from .ledger import HealingLedger
from .detector import CorruptionDetector


class SelfHealingEngine:
    """
    Executes autonomous self-healing routines across raw and corrupted DataFrames.
    """

    def __init__(self, config: PipelineConfig = None, ledger: HealingLedger = None):
        self.config = config or PipelineConfig()
        self.ledger = ledger or HealingLedger()
        self.detector = CorruptionDetector(self.config)

    def heal(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, HealingLedger]:
        """
        Runs the full 7-pass self-healing pipeline on the input DataFrame.
        Returns the healed DataFrame and the populated audit ledger.
        """
        # Calculate initial baseline health
        self.ledger.compute_health_score(df, is_initial=True)

        working_df = df.copy()

        # Pass 1: Schema & Header Stabilization
        working_df = self._heal_headers(working_df)

        # Pass 2: Sentinel Null Clearing
        working_df = self._heal_sentinel_nulls(working_df)

        # Pass 3: Type Coercion & Formatting Repair
        working_df = self._heal_types_and_formats(working_df)

        # Pass 4: Categorical Typo & Drift Consensus
        working_df = self._heal_categorical_typos(working_df)

        # Pass 5: Context-Aware Missing Value Imputation
        working_df = self._heal_missing_values(working_df)

        # Pass 6: Outlier Resolution (Adaptive Winsorization)
        working_df = self._heal_outliers(working_df)

        # Pass 7: Deduplication
        working_df = self._heal_duplicates(working_df)

        # Compute post-healing health score
        self.ledger.compute_health_score(working_df, is_initial=False)

        return working_df, self.ledger

    def _heal_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Stabilizes column headers: removes whitespace, unifies snake_case."""
        renamed = {}
        for idx, col in enumerate(df.columns):
            col_str = str(col).strip()
            clean = re.sub(r'[^a-zA-Z0-9_]', '_', col_str.lower())
            clean = re.sub(r'_+', '_', clean).strip('_')
            if not clean:
                clean = f"column_{idx}"
            if col_str != clean:
                renamed[col] = clean
                self.ledger.record_action(
                    row_index=-1,
                    column=str(col),
                    issue_type="SCHEMA_FIXED",
                    original_value=str(col),
                    healed_value=clean,
                    strategy="Header whitespace & syntax normalization",
                    confidence_score=1.0
                )

        if renamed:
            df = df.rename(columns=renamed)
        return df

    def _heal_sentinel_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        """Replaces hidden sentinel string nulls ('-999', 'N/A', '#REF!', etc.) with true np.nan."""
        for col in df.columns:
            col_vals = df[col].tolist()
            changed = False
            for idx, val in enumerate(col_vals):
                if pd.isna(val):
                    continue
                val_str = str(val).strip().lower()
                if val_str in self.config.sentinel_nulls:
                    self.ledger.record_action(
                        row_index=int(df.index[idx]),
                        column=col,
                        issue_type="MISSING_VALUE",
                        original_value=val,
                        healed_value=np.nan,
                        strategy="Converted masked sentinel string to standard NaN",
                        confidence_score=0.99
                    )
                    col_vals[idx] = np.nan
                    changed = True
            if changed:
                df[col] = pd.Series(col_vals, index=df.index, dtype=object)
        return df

    def _heal_types_and_formats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parses currency strings, dirty numbers, percentages, and heterogeneous timestamps."""
        currency_chars = r'[\$\€\£\¥\₹USDusd\s]'

        for col in df.columns:
            series = df[col].dropna()
            if len(series) == 0:
                continue

            num_like_count = 0
            date_like_count = 0
            sample_size = min(len(series), 50)
            sample = series.iloc[:sample_size]

            for val in sample:
                val_s = str(val).strip()
                cleaned = re.sub(currency_chars, '', val_s).replace(',', '')
                if cleaned.endswith('%'):
                    cleaned = cleaned[:-1]
                try:
                    float(cleaned)
                    num_like_count += 1
                except ValueError:
                    if self.detector._is_potential_date(val_s):
                        date_like_count += 1

            # Case A: Column is numeric / currency / percentage
            if (num_like_count / sample_size) >= 0.50:
                col_vals = df[col].tolist()
                for idx, val in enumerate(col_vals):
                    if pd.isna(val):
                        continue
                    val_s = str(val).strip()
                    is_percent = '%' in val_s
                    cleaned = re.sub(currency_chars, '', val_s).replace(',', '')
                    if is_percent:
                        cleaned = cleaned.replace('%', '').strip()
                    try:
                        num_val = float(cleaned)
                        if is_percent and num_val > 1.0:
                            num_val = round(num_val, 4)
                        if str(val) != str(num_val):
                            self.ledger.record_action(
                                row_index=int(df.index[idx]),
                                column=col,
                                issue_type="CORRUPT_TYPE",
                                original_value=val,
                                healed_value=num_val,
                                strategy="Parsed currency/percent/dirty string to float",
                                confidence_score=0.98
                            )
                        col_vals[idx] = num_val
                    except ValueError:
                        self.ledger.record_action(
                            row_index=int(df.index[idx]),
                            column=col,
                            issue_type="CORRUPT_TYPE",
                            original_value=val,
                            healed_value=np.nan,
                            strategy="Unparseable string in numeric column coerced to NaN",
                            confidence_score=0.90
                        )
                        col_vals[idx] = np.nan

                # Cast column to numeric
                df[col] = pd.to_numeric(pd.Series(col_vals, index=df.index), errors='coerce')

            # Case B: Column is heterogeneous datetime
            elif (date_like_count / sample_size) >= 0.50:
                col_vals = df[col].tolist()
                for idx, val in enumerate(col_vals):
                    if pd.isna(val):
                        continue
                    parsed_dt = self._parse_flexible_date(val)
                    if parsed_dt:
                        formatted = parsed_dt.strftime("%Y-%m-%d %H:%M:%S")
                        if str(val) != formatted:
                            self.ledger.record_action(
                                row_index=int(df.index[idx]),
                                column=col,
                                issue_type="CORRUPT_TYPE",
                                original_value=val,
                                healed_value=formatted,
                                strategy="Standardized mixed timestamp to ISO format",
                                confidence_score=0.95
                            )
                        col_vals[idx] = formatted
                    else:
                        col_vals[idx] = np.nan
                df[col] = pd.Series(col_vals, index=df.index, dtype=object)

        return df

    def _parse_flexible_date(self, val: Any) -> Optional[datetime]:
        """Tries parsing multiple common date formats and unix timestamps."""
        val_s = str(val).strip()
        if re.match(r'^\d{10}(\.\d+)?$', val_s):
            try:
                return datetime.fromtimestamp(float(val_s))
            except Exception:
                pass

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %b %Y",
            "%Y/%m/%d",
            "%Y.%m.%d"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(val_s, fmt)
            except ValueError:
                continue

        try:
            return pd.to_datetime(val_s).to_pydatetime()
        except Exception:
            return None

    def _heal_categorical_typos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Autonomously heals low-frequency category typos using string distance consensus."""
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                continue

            series = df[col].dropna().astype(str).str.strip()
            counts = series.value_counts()
            if len(counts) < 2:
                continue

            threshold_count = max(3, int(len(series) * 0.04))
            high_freq = counts[counts >= threshold_count].index.tolist()
            low_freq = counts[counts < threshold_count].index.tolist()

            mapping = {}
            for low in low_freq:
                if low.lower() in self.config.sentinel_nulls:
                    continue
                best_match = None
                best_score = 0.0
                for high in high_freq:
                    score = SequenceMatcher(None, low.lower(), high.lower()).ratio()
                    if score > best_score and score >= self.config.fuzzy_match_threshold:
                        best_score = score
                        best_match = high

                if best_match and best_match != low:
                    mapping[low] = (best_match, best_score)

            if mapping:
                col_vals = df[col].tolist()
                changed = False
                for idx, val in enumerate(col_vals):
                    val_s = str(val).strip() if pd.notna(val) else None
                    if val_s in mapping:
                        target, score = mapping[val_s]
                        self.ledger.record_action(
                            row_index=int(df.index[idx]),
                            column=col,
                            issue_type="TYPO_CORRECTED",
                            original_value=val,
                            healed_value=target,
                            strategy=f"Fuzzy consensus mapping (similarity {score:.2f})",
                            confidence_score=score
                        )
                        col_vals[idx] = target
                        changed = True
                if changed:
                    df[col] = pd.Series(col_vals, index=df.index, dtype=object)
        return df

    def _heal_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes adaptive, context-aware missing value imputation:
        - If skewed numeric: Median imputation.
        - If symmetrical numeric: Mean imputation.
        - If group-correlated: Group-conditioned median.
        - If categorical: High-frequency Mode.
        """
        group_col = None
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                nunique = df[col].nunique()
                if 2 <= nunique <= 15:
                    group_col = col
                    break

        for col in df.columns:
            is_num = pd.api.types.is_numeric_dtype(df[col])
            col_vals = df[col].tolist()
            null_positions = [i for i, v in enumerate(col_vals) if pd.isna(v)]

            if not null_positions:
                continue

            if is_num:
                valid_nums = [float(v) for v in col_vals if pd.notna(v)]
                if not valid_nums:
                    continue

                valid_series = pd.Series(valid_nums)
                skewness = float(valid_series.skew()) if len(valid_series) > 2 else 0.0

                if abs(skewness) < 0.5:
                    impute_val = round(float(valid_series.mean()), 2)
                    strategy_name = "Gaussian Mean (low skewness)"
                else:
                    impute_val = round(float(valid_series.median()), 2)
                    strategy_name = f"Robust Median (skewness={skewness:.2f})"

                if group_col and df[group_col].nunique() > 1:
                    group_medians = df.groupby(group_col)[col].median().to_dict()
                    for pos in null_positions:
                        row_idx = int(df.index[pos])
                        grp = df.at[row_idx, group_col]
                        chosen_val = group_medians.get(grp, impute_val)
                        if pd.isna(chosen_val):
                            chosen_val = impute_val
                        chosen_val = round(float(chosen_val), 2)
                        self.ledger.record_action(
                            row_index=row_idx,
                            column=col,
                            issue_type="MISSING_VALUE",
                            original_value=None,
                            healed_value=chosen_val,
                            strategy=f"Group-Conditioned Median by '{group_col}={grp}'",
                            confidence_score=0.94
                        )
                        col_vals[pos] = chosen_val
                else:
                    for pos in null_positions:
                        row_idx = int(df.index[pos])
                        self.ledger.record_action(
                            row_index=row_idx,
                            column=col,
                            issue_type="MISSING_VALUE",
                            original_value=None,
                            healed_value=impute_val,
                            strategy=strategy_name,
                            confidence_score=0.91
                        )
                        col_vals[pos] = impute_val

                df[col] = pd.to_numeric(pd.Series(col_vals, index=df.index), errors='coerce')

            else:
                valid_strs = [str(v).strip() for v in col_vals if pd.notna(v)]
                if not valid_strs:
                    continue
                mode_val = pd.Series(valid_strs).mode()[0] if valid_strs else "Unknown"

                for pos in null_positions:
                    row_idx = int(df.index[pos])
                    self.ledger.record_action(
                        row_index=row_idx,
                        column=col,
                        issue_type="MISSING_VALUE",
                        original_value=None,
                        healed_value=mode_val,
                        strategy=f"Dominant Mode Imputation ('{mode_val}')",
                        confidence_score=0.88
                    )
                    col_vals[pos] = mode_val

                df[col] = pd.Series(col_vals, index=df.index, dtype=object)

        return df

    def _heal_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Winsorizes catastrophic outliers to 1.5*IQR boundary limits,
        curbing extreme distribution leverage while retaining record validity.
        """
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue

            series = df[col].dropna()
            if len(series) < 5:
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            if iqr <= 0:
                continue

            lower_bound = round(float(q1 - (self.config.iqr_multiplier * iqr)), 2)
            upper_bound = round(float(q3 + (self.config.iqr_multiplier * iqr)), 2)

            if (series >= 0).all() and lower_bound < 0:
                lower_bound = 0.0

            col_vals = df[col].tolist()
            changed = False
            for pos, val in enumerate(col_vals):
                if pd.isna(val):
                    continue
                orig_num = float(val)
                row_idx = int(df.index[pos])
                if orig_num > upper_bound:
                    self.ledger.record_action(
                        row_index=row_idx,
                        column=col,
                        issue_type="OUTLIER_BOUNDED",
                        original_value=orig_num,
                        healed_value=upper_bound,
                        strategy=f"Winsorized upper outlier to 1.5*IQR threshold ({upper_bound})",
                        confidence_score=0.96
                    )
                    col_vals[pos] = upper_bound
                    changed = True
                elif orig_num < lower_bound:
                    self.ledger.record_action(
                        row_index=row_idx,
                        column=col,
                        issue_type="OUTLIER_BOUNDED",
                        original_value=orig_num,
                        healed_value=lower_bound,
                        strategy=f"Winsorized lower outlier to 1.5*IQR threshold ({lower_bound})",
                        confidence_score=0.96
                    )
                    col_vals[pos] = lower_bound
                    changed = True

            if changed:
                df[col] = pd.to_numeric(pd.Series(col_vals, index=df.index), errors='coerce')

        return df

    def _heal_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Purges exact duplicate records while maintaining primary record index."""
        dupes = df.duplicated(keep='first')
        dupe_count = dupes.sum()

        if dupe_count > 0:
            dupe_indices = df[dupes].index.tolist()
            for idx in dupe_indices:
                self.ledger.record_action(
                    row_index=int(idx),
                    column="*all_columns*",
                    issue_type="DUPLICATE_PURGED",
                    original_value="Duplicate Row Record",
                    healed_value="Removed",
                    strategy="Purged redundant record matching preceding instance",
                    confidence_score=1.0
                )
            df = df.drop(index=dupe_indices).reset_index(drop=True)

        return df

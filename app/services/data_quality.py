"""
Weighted data quality scoring service: computes overall score (0-100)
and detailed breakdown scores across key data health dimensions.
"""

import numpy as np
import pandas as pd


def find_constant_columns(df: pd.DataFrame) -> list:
    """Columns with only one distinct non-null value (zero information)."""
    constant_cols = []
    for col in df.columns:
        non_null = df[col].dropna()
        if non_null.nunique() <= 1 and not non_null.empty:
            constant_cols.append(col)
        elif non_null.empty:
            constant_cols.append(col)
    return constant_cols


def find_high_cardinality_columns(categorical_analysis_result: dict) -> list:
    """Extract high cardinality column names from categorical analysis."""
    return [
        col
        for col, info in categorical_analysis_result.items()
        if info.get("is_high_cardinality")
    ]


def check_invalid_values(df: pd.DataFrame) -> dict:
    """Check for Infinite (inf, -inf) values and non-numeric invalid entries."""
    inf_counts = {}
    total_inf = 0
    numeric_df = df.select_dtypes(include=[np.number])

    for col in numeric_df.columns:
        inf_cnt = int(np.isinf(numeric_df[col]).sum())
        if inf_cnt > 0:
            inf_counts[col] = inf_cnt
            total_inf += inf_cnt

    return {
        "infinite_count": total_inf,
        "infinite_per_column": inf_counts,
    }


def build_quality_report(
    df: pd.DataFrame,
    missing_summary: dict,
    duplicate_summary: dict,
    categorical_result: dict,
    outlier_summary: dict = None,
) -> dict:
    n_rows, n_cols = df.shape

    # 1. Missing Values Score (Sub-score 0-100)
    missing_pct = missing_summary.get("overall_missing_percentage", 0.0)
    missing_score = max(0.0, 100.0 - (missing_pct * 2.0))

    # 2. Duplicates Score (Sub-score 0-100)
    dup_pct = duplicate_summary.get("duplicate_percentage", 0.0)
    dup_score = max(0.0, 100.0 - (dup_pct * 1.5))

    # 3. Outliers Score (Sub-score 0-100)
    outlier_score = 100.0
    if outlier_summary:
        total_outliers = sum(info.get("outlier_count", 0) for info in outlier_summary.values())
        total_numeric_cells = sum(
            info.get("iqr", 0) != 0 for info in outlier_summary.values()
        ) * n_rows
        if total_numeric_cells > 0:
            outlier_pct = (total_outliers / total_numeric_cells) * 100
            outlier_score = max(0.0, 100.0 - (outlier_pct * 3.0))

    # 4. Constant Columns Score (Sub-score 0-100)
    constant_cols = find_constant_columns(df)
    const_pct = (len(constant_cols) / n_cols * 100) if n_cols else 0.0
    constant_score = max(0.0, 100.0 - (const_pct * 2.0))

    # 5. High Cardinality Score (Sub-score 0-100)
    high_card_cols = find_high_cardinality_columns(categorical_result)
    cat_cols_count = len(categorical_result)
    high_card_pct = (len(high_card_cols) / cat_cols_count * 100) if cat_cols_count else 0.0
    high_card_score = max(0.0, 100.0 - (high_card_pct * 1.5))

    # 6. Invalid / Infinite Values Score (Sub-score 0-100)
    invalid_info = check_invalid_values(df)
    total_cells = n_rows * n_cols
    inf_pct = (invalid_info["infinite_count"] / total_cells * 100) if total_cells else 0.0
    invalid_score = max(0.0, 100.0 - (inf_pct * 5.0))

    breakdown = {
        "missing_values": round(missing_score, 1),
        "duplicates": round(dup_score, 1),
        "outliers": round(outlier_score, 1),
        "constant_columns": round(constant_score, 1),
        "high_cardinality": round(high_card_score, 1),
        "invalid_values": round(invalid_score, 1),
    }

    # Weighted Overall Quality Score
    # Weights: Missing (30%), Duplicates (25%), Outliers (15%), Constant (15%), High Card (10%), Invalid (5%)
    overall_score = (
        (missing_score * 0.30)
        + (dup_score * 0.25)
        + (outlier_score * 0.15)
        + (constant_score * 0.15)
        + (high_card_score * 0.10)
        + (invalid_score * 0.05)
    )

    return {
        "quality_score": round(overall_score, 1),
        "breakdown": breakdown,
        "constant_columns": constant_cols,
        "high_cardinality_columns": high_card_cols,
        "invalid_values": invalid_info,
    }

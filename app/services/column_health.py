"""
Column-wise Health Report Service (STEP 7).
Generates an individual health evaluation (Excellent, Good, Needs Attention) and observation
for EVERY column in the dataset.
"""

import pandas as pd


def generate_column_health_report(
    df: pd.DataFrame,
    missing: dict,
    duplicates: dict,
    numeric: dict,
    categorical: dict,
    outliers: dict,
    semantics: dict,
) -> dict:
    health_report = {}
    n_rows = len(df)

    for col in df.columns:
        col_str = str(col)
        dtype_str = str(df[col].dtype)
        col_missing = missing.get("per_column", {}).get(col_str, {})
        missing_cnt = col_missing.get("missing_count", 0)
        missing_pct = col_missing.get("missing_percentage", 0.0)

        n_unique = int(df[col].dropna().nunique())
        unique_ratio = round(n_unique / n_rows, 4) if n_rows else 0.0

        is_num = col_str in numeric and "note" not in numeric[col_str]
        col_outliers = outliers.get(col_str, {}) if is_num else {}
        outlier_cnt = col_outliers.get("outlier_count", 0)
        outlier_pct = col_outliers.get("outlier_percentage", 0.0)

        dist_label = numeric.get(col_str, {}).get("distribution_classification", "Categorical / Discrete") if is_num else "Categorical"
        sem_info = semantics.get(col_str, {})
        is_id = sem_info.get("ignored_for_analysis", False)

        # Health Rating Logic
        if is_id:
            rating = "Good"
            obs = f"'{col_str}' is an identifier column. Excluded from statistical correlation."
        elif missing_pct > 15.0 or outlier_pct > 5.0 or n_unique <= 1:
            rating = "Needs Attention"
            reasons = []
            if missing_pct > 15.0: reasons.append(f"{missing_pct}% missing values")
            if outlier_pct > 5.0: reasons.append(f"{outlier_pct}% outliers")
            if n_unique <= 1: reasons.append("zero variance (constant)")
            obs = f"'{col_str}' requires cleaning due to {', '.join(reasons)}."
        elif missing_pct > 0 or outlier_cnt > 0 or unique_ratio > 0.5:
            rating = "Good"
            obs = f"'{col_str}' is in good condition with minor observations ({missing_cnt} nulls, {outlier_cnt} outliers)."
        else:
            rating = "Excellent"
            obs = f"'{col_str}' is completely clean with 0 missing values and solid data integrity."

        dup_cnt = duplicates.get("duplicate_row_count", 0)
        dup_impact = "High" if dup_cnt > 0 and not is_id else "Low"

        health_report[col_str] = {
            "column_name": col_str,
            "data_type": dtype_str,
            "missing_values": {
                "count": missing_cnt,
                "percentage": missing_pct,
            },
            "duplicate_impact": dup_impact,
            "outliers": {
                "count": outlier_cnt,
                "percentage": outlier_pct,
            },
            "distribution": dist_label,
            "unique_values": {
                "count": n_unique,
                "ratio": unique_ratio,
            },
            "column_health": rating,
            "observation": obs,
        }

    return health_report

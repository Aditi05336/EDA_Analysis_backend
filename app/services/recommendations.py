"""
Structured Data Cleaning & Hygiene Recommendations Engine.
Generates prioritized data preparation steps based on EDA observations.
"""

import pandas as pd


def generate_recommendations(
    overview: dict,
    missing: dict,
    duplicates: dict,
    numeric: dict,
    categorical: dict,
    correlation: dict,
    outliers: dict,
    quality: dict,
    semantics: dict = None,
) -> list:
    recs = []

    # 1. Duplicates
    dup_cnt = duplicates.get("duplicate_row_count", 0)
    dup_pct = duplicates.get("duplicate_percentage", 0.0)
    if dup_cnt > 0:
        recs.append(
            {
                "priority": "High" if dup_pct > 5 else "Medium",
                "category": "Duplicates",
                "title": "Remove Duplicate Rows",
                "reason": f"Detected {dup_cnt} duplicate rows ({dup_pct}% of total records).",
                "expected_benefit": "Eliminates redundant records and restores true population variance.",
            }
        )

    # 2. Missing Values
    if missing.get("columns_fully_missing"):
        cols_str = ", ".join(missing["columns_fully_missing"])
        recs.append(
            {
                "priority": "High",
                "category": "Missing Values",
                "title": "Drop Completely Empty Columns",
                "reason": f"Column(s) {cols_str} contain 100% missing values.",
                "expected_benefit": "Cleans non-informative zero-data attributes.",
            }
        )

    num_missing = [c for c, info in missing.get("per_column", {}).items() if 0 < info["missing_percentage"] < 100 and c in numeric]
    if num_missing:
        recs.append(
            {
                "priority": "Medium",
                "category": "Missing Values",
                "title": "Impute Missing Numeric Values",
                "reason": f"Missing values present in numerical feature(s): {', '.join(num_missing)}.",
                "expected_benefit": "Restores missing inputs using median value imputation robust to skewness.",
            }
        )

    # 3. Constant Columns
    const_cols = quality.get("constant_columns", [])
    if const_cols:
        recs.append(
            {
                "priority": "High",
                "category": "Feature Selection",
                "title": "Drop Zero-Variance Constant Columns",
                "reason": f"Column(s) {', '.join(const_cols)} contain only 1 distinct value.",
                "expected_benefit": "Reduces dataset width by removing zero-variance attributes.",
            }
        )

    # 4. Encoding
    low_card = [c for c, info in categorical.items() if not info.get("is_high_cardinality")]
    if low_card:
        recs.append(
            {
                "priority": "Medium",
                "category": "Encoding",
                "title": "One-Hot Encode Categorical Features",
                "reason": f"Low-cardinality categorical feature(s): {', '.join(low_card)}.",
                "expected_benefit": "Converts string category labels into numerical indicator variables.",
            }
        )

    high_card = [c for c, info in categorical.items() if info.get("is_high_cardinality")]
    if high_card:
        recs.append(
            {
                "priority": "High",
                "category": "Encoding",
                "title": "Apply Target or Frequency Encoding",
                "reason": f"High-cardinality feature(s): {', '.join(high_card)}.",
                "expected_benefit": "Encodes categories without inflating dataset width.",
            }
        )

    # 5. Skewness / Transformation
    skewed = [c for c, s in numeric.items() if "note" not in s and abs(s.get("skewness", 0)) > 1.0]
    if skewed:
        recs.append(
            {
                "priority": "Medium",
                "category": "Feature Transformation",
                "title": "Apply Log Transformation",
                "reason": f"Column(s) {', '.join(skewed)} exhibit heavy right/left skewness.",
                "expected_benefit": "Normalizes variance and compresses long-tail distributions.",
            }
        )

    # 6. Scaling
    if numeric:
        recs.append(
            {
                "priority": "Medium",
                "category": "Scaling",
                "title": "Standardize Numerical Features",
                "reason": "Numerical columns operate across different units and scales.",
                "expected_benefit": "Brings all numerical attributes into a comparable mean-zero scale.",
            }
        )

    # 7. Outliers
    outlier_cols = [c for c, o in outliers.items() if o.get("outlier_count", 0) > 0 and o.get("outlier_percentage", 0) >= 1.0]
    if outlier_cols:
        recs.append(
            {
                "priority": "Medium",
                "category": "Outliers",
                "title": "Cap or Truncate Extreme Outliers",
                "reason": f"Statistical outliers detected in feature(s): {', '.join(outlier_cols)}.",
                "expected_benefit": "Prevents extreme values from distorting sample means.",
            }
        )

    return recs

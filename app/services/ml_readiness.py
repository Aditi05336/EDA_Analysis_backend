"""
ML Readiness Scoring Service.
Evaluates dataset readiness for machine learning workflows based on missingness, duplicates,
outliers, high cardinality, skewness, multicollinearity, constant attributes, and IDs.
"""

import pandas as pd


def compute_ml_readiness(
    df: pd.DataFrame,
    missing: dict,
    duplicates: dict,
    numeric: dict,
    categorical: dict,
    correlation: dict,
    outliers: dict,
    quality: dict,
    semantics: dict,
) -> dict:
    score = 100.0
    deductions = []

    # 1. Missing Values Penalty
    missing_pct = missing.get("overall_missing_percentage", 0.0)
    if missing_pct > 0:
        penalty = min(35.0, missing_pct * 1.5)
        score -= penalty
        deductions.append(
            {
                "factor": "Missing Values",
                "deduction": round(penalty, 1),
                "reason": f"{missing_pct}% missing values present across cells.",
            }
        )

    # 2. Duplicate Rows Penalty
    dup_pct = duplicates.get("duplicate_percentage", 0.0)
    if dup_pct > 0:
        penalty = min(25.0, dup_pct * 1.0)
        score -= penalty
        deductions.append(
            {
                "factor": "Duplicate Rows",
                "deduction": round(penalty, 1),
                "reason": f"{duplicates.get('duplicate_row_count', 0)} duplicate rows detected ({dup_pct}%).",
            }
        )

    # 3. Multicollinearity Penalty
    strong_pairs_cnt = len(correlation.get("strong_pairs", []))
    if strong_pairs_cnt > 0:
        penalty = min(15.0, strong_pairs_cnt * 2.5)
        score -= penalty
        deductions.append(
            {
                "factor": "Multicollinearity",
                "deduction": round(penalty, 1),
                "reason": f"{strong_pairs_cnt} strongly correlated feature pairs (r ≥ 0.70) found.",
            }
        )

    # 4. Outliers Penalty
    outlier_cols = [
        col for col, o in outliers.items() if o.get("outlier_count", 0) > 0 and o.get("outlier_percentage", 0) >= 1.0
    ]
    if outlier_cols:
        penalty = min(15.0, len(outlier_cols) * 3.0)
        score -= penalty
        deductions.append(
            {
                "factor": "Outliers",
                "deduction": round(penalty, 1),
                "reason": f"Outliers present in {len(outlier_cols)} numerical attribute(s).",
            }
        )

    # 5. Skewed Distributions Penalty
    skewed_cols = [
        col for col, stats in numeric.items() if "note" not in stats and abs(stats.get("skewness", 0)) > 1.0
    ]
    if skewed_cols:
        penalty = min(10.0, len(skewed_cols) * 2.0)
        score -= penalty
        deductions.append(
            {
                "factor": "Highly Skewed Features",
                "deduction": round(penalty, 1),
                "reason": f"{len(skewed_cols)} feature(s) present severe skewness (|skew| > 1.0).",
            }
        )

    # 6. Constant Columns Penalty
    const_cols = quality.get("constant_columns", [])
    if const_cols:
        penalty = min(15.0, len(const_cols) * 5.0)
        score -= penalty
        deductions.append(
            {
                "factor": "Zero Variance / Constant Columns",
                "deduction": round(penalty, 1),
                "reason": f"{len(const_cols)} constant column(s) carry no variance.",
            }
        )

    # 7. High Cardinality Penalty
    high_card_cols = quality.get("high_cardinality_columns", [])
    if high_card_cols:
        penalty = min(10.0, len(high_card_cols) * 2.5)
        score -= penalty
        deductions.append(
            {
                "factor": "High Cardinality Features",
                "deduction": round(penalty, 1),
                "reason": f"{len(high_card_cols)} categorical feature(s) present high cardinality.",
            }
        )

    final_score = round(max(0.0, score), 1)

    if final_score >= 85:
        status = "Excellent"
        summary = "Dataset is highly suitable for ML modeling with minimal preprocessing required."
    elif final_score >= 70:
        status = "Good"
        summary = "Dataset is suitable for ML after standard preprocessing (imputation/deduplication/scaling)."
    elif final_score >= 50:
        status = "Moderate"
        summary = "Dataset requires moderate data cleaning and feature engineering before modeling."
    else:
        status = "Poor"
        summary = "Dataset contains severe quality defects (high missingness/duplicates) requiring heavy remediation."

    return {
        "ml_readiness_score": final_score,
        "status": status,
        "summary": summary,
        "deductions": deductions,
    }

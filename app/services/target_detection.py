"""
Target Column Auto-Detection & Target-Based Analysis Service.
Identifies potential classification/regression target columns and runs target-conditioned EDA.
"""

import pandas as pd
from app.config import Config


def detect_target_column(df: pd.DataFrame, semantics: dict = None) -> dict:
    n_rows = len(df)
    if n_rows == 0:
        return {"target_detected": False}

    valid_cols = [c for c in df.columns if not (semantics and semantics.get(c, {}).get("ignored_for_analysis"))]

    candidate_col = None
    reason = None
    task_type = "classification"

    # Strategy 1: Check column names against Config.TARGET_KEYWORDS
    for col in valid_cols:
        clean_name = str(col).strip().lower()
        if clean_name in Config.TARGET_KEYWORDS or any(kw in clean_name for kw in Config.TARGET_KEYWORDS):
            candidate_col = col
            reason = f"Column name '{col}' matches common target keyword."
            break

    # Strategy 2: Check for binary column if keyword match not found
    if not candidate_col:
        for col in valid_cols:
            non_null = df[col].dropna()
            if non_null.nunique() == 2:
                candidate_col = col
                reason = f"Column '{col}' is a binary attribute (2 unique values)."
                break

    # Strategy 3: Check for low-cardinality categorical column at the end of dataset
    if not candidate_col and valid_cols:
        last_col = valid_cols[-1]
        if df[last_col].nunique() <= 10 and df[last_col].nunique() > 1:
            candidate_col = last_col
            reason = f"Column '{last_col}' is a low-cardinality trailing attribute."

    if not candidate_col:
        return {"target_detected": False}

    # Determine task type
    target_series = df[candidate_col].dropna()
    if pd.api.types.is_numeric_dtype(target_series) and target_series.nunique() > 10:
        task_type = "regression"
    else:
        task_type = "classification"

    target_analysis = {
        "target_detected": True,
        "target_column": candidate_col,
        "task_type": task_type,
        "detection_reason": reason,
        "target_class_distribution": {},
        "feature_correlations_with_target": {},
    }

    if task_type == "classification":
        class_counts = target_series.value_counts()
        target_analysis["target_class_distribution"] = [
            {
                "class": str(cls),
                "count": int(cnt),
                "percentage": round((cnt / len(target_series)) * 100, 2),
            }
            for cls, cnt in class_counts.items()
        ]
    else:
        # Regression target stats
        target_analysis["regression_stats"] = {
            "mean": round(float(target_series.mean()), 4),
            "std": round(float(target_series.std()), 4),
            "min": round(float(target_series.min()), 4),
            "max": round(float(target_series.max()), 4),
        }

    # Correlation of numeric features with target
    numeric_df = df.select_dtypes(include=["number"])
    if candidate_col in numeric_df.columns:
        corrs = numeric_df.corrwith(numeric_df[candidate_col]).drop(candidate_col, errors="ignore")
        target_analysis["feature_correlations_with_target"] = {
            col: round(float(val), 4) for col, val in corrs.items() if pd.notna(val)
        }

    return target_analysis

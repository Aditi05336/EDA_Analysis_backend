"""
Pearson correlation matrix for numeric columns, categorized into strong positive,
strong negative, moderate, and weak correlations with plain-English interpretations.
"""

import pandas as pd
from app.config import Config
from app.services.numeric_analysis import get_numeric_columns


def get_interpretation(col_a: str, col_b: str, r: float) -> str:
    """Generates plain-English interpretation for a correlation pair."""
    abs_r = abs(r)
    direction = "positive" if r > 0 else "negative"
    
    if abs_r >= 0.85:
        strength = "very strong"
    elif abs_r >= 0.7:
        strength = "strong"
    elif abs_r >= 0.4:
        strength = "moderate"
    else:
        strength = "weak"

    if r > 0:
        movement = f"as {col_a} increases, {col_b} tends to increase as well."
    else:
        movement = f"as {col_a} increases, {col_b} tends to decrease."

    return (
        f"{col_a} and {col_b} have a {strength} {direction} correlation ({r:.2f}). "
        f"This suggests {movement}"
    )


def analyze_correlation(df: pd.DataFrame, semantics: dict = None) -> dict:
    numeric_cols = get_numeric_columns(df)

    if semantics:
        numeric_cols = [c for c in numeric_cols if not semantics.get(c, {}).get("ignored_for_analysis")]

    if len(numeric_cols) < 2:
        return {
            "matrix": {},
            "strong_pairs": [],
            "strong_positive": [],
            "strong_negative": [],
            "moderate": [],
            "weak": [],
            "note": "Fewer than 2 valid numeric columns — correlation not applicable.",
        }

    corr_df = df[numeric_cols].corr(method="pearson")
    matrix = {
        row: {col: (round(float(val), 4) if pd.notna(val) else None) for col, val in corr_df[row].items()}
        for row in corr_df.index
    }

    strong_positive = []
    strong_negative = []
    moderate = []
    weak = []
    seen = set()

    for col_a in corr_df.columns:
        for col_b in corr_df.columns:
            if col_a == col_b:
                continue
            pair_key = frozenset([col_a, col_b])
            if pair_key in seen:
                continue
            seen.add(pair_key)

            val = corr_df.loc[col_a, col_b]
            if pd.isna(val):
                continue

            r = round(float(val), 4)
            abs_r = abs(r)
            interp = get_interpretation(col_a, col_b, r)

            pair_item = {
                "column_a": col_a,
                "column_b": col_b,
                "correlation": r,
                "direction": "positive" if r > 0 else "negative",
                "interpretation": interp,
            }

            if r >= Config.STRONG_CORR_THRESHOLD:
                strong_positive.append(pair_item)
            elif r <= -Config.STRONG_CORR_THRESHOLD:
                strong_negative.append(pair_item)
            elif Config.MODERATE_CORR_THRESHOLD <= abs_r < Config.STRONG_CORR_THRESHOLD:
                moderate.append(pair_item)
            elif Config.WEAK_CORR_THRESHOLD <= abs_r < Config.MODERATE_CORR_THRESHOLD:
                weak.append(pair_item)

    strong_positive.sort(key=lambda p: p["correlation"], reverse=True)
    strong_negative.sort(key=lambda p: p["correlation"])
    moderate.sort(key=lambda p: abs(p["correlation"]), reverse=True)
    weak.sort(key=lambda p: abs(p["correlation"]), reverse=True)

    all_strong = strong_positive + strong_negative
    all_strong.sort(key=lambda p: abs(p["correlation"]), reverse=True)

    return {
        "matrix": matrix,
        "strong_pairs": all_strong,
        "strong_positive": strong_positive,
        "strong_negative": strong_negative,
        "moderate": moderate,
        "weak": weak,
    }

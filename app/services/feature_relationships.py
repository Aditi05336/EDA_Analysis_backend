"""
Feature Relationship Analysis Service.
Analyzes pairwise analytical relationships across all columns using cross-type association measures
(Pearson r, Cramér's V, and Grouped Variance Eta), excluding Identifier columns.
"""

import math
import numpy as np
import pandas as pd
from app.services.semantic_detection import detect_column_semantics


def compute_cramers_v(series_a: pd.Series, series_b: pd.Series) -> float:
    """Computes Cramér's V association metric for two categorical series."""
    contingency = pd.crosstab(series_a, series_b)
    if contingency.empty or contingency.size <= 1:
        return 0.0

    n = contingency.sum().sum()
    if n == 0:
        return 0.0

    # Chi-square calculation
    row_sums = contingency.sum(axis=1)
    col_sums = contingency.sum(axis=0)
    expected = np.outer(row_sums, col_sums) / n

    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum((contingency.values - expected) ** 2 / expected)

    if np.isnan(chi2) or chi2 <= 0:
        return 0.0

    r, c = contingency.shape
    min_dim = min(r - 1, c - 1)
    if min_dim <= 0:
        return 0.0

    v = math.sqrt(chi2 / (n * min_dim))
    return min(1.0, max(0.0, v))


def compute_eta_squared(cat_series: pd.Series, num_series: pd.Series) -> float:
    """Computes Eta association metric (Correlation Ratio) between categorical and numerical series."""
    valid_mask = cat_series.notna() & num_series.notna()
    c_series = cat_series[valid_mask]
    n_series = num_series[valid_mask]

    if len(n_series) == 0 or n_series.nunique() <= 1 or c_series.nunique() <= 1:
        return 0.0

    overall_mean = n_series.mean()
    total_ss = np.sum((n_series - overall_mean) ** 2)
    if total_ss == 0:
        return 0.0

    group_means = n_series.groupby(c_series).mean()
    group_counts = c_series.groupby(c_series).count()
    between_ss = np.sum(group_counts * (group_means - overall_mean) ** 2)

    eta = math.sqrt(between_ss / total_ss) if total_ss > 0 else 0.0
    return min(1.0, max(0.0, eta))


def get_strength_label(score: float, is_pearson: bool = False) -> str:
    abs_s = abs(score)
    if is_pearson:
        if abs_s >= 0.85: return "Very Strong"
        elif abs_s >= 0.70: return "Strong"
        elif abs_s >= 0.40: return "Moderate"
        elif abs_s >= 0.20: return "Weak"
        else: return "Very Weak"
    else:
        if abs_s >= 0.50: return "Very Strong"
        elif abs_s >= 0.35: return "Strong"
        elif abs_s >= 0.20: return "Moderate"
        elif abs_s >= 0.10: return "Weak"
        else: return "Very Weak"


def analyze_feature_relationships(df: pd.DataFrame, semantics: dict = None) -> dict:
    if semantics is None:
        semantics = detect_column_semantics(df)

    relationships = {}
    all_cols = list(df.columns)

    for col in all_cols:
        col_sem = semantics.get(col, {})
        is_id = col_sem.get("ignored_for_analysis", False) or col_sem.get("semantic_type") == "Identifier"

        if is_id:
            relationships[col] = {
                "column_name": str(col),
                "is_identifier": True,
                "status": "Identifier column detected. No analytical relationship computed.",
                "related_features": [],
                "summary": f"'{col}' is an identifier column. Identifier columns are automatically excluded because they do not contain analytical information.",
            }
            continue

        related_list = []
        is_col_num = pd.api.types.is_numeric_dtype(df[col])

        for other in all_cols:
            if col == other:
                continue

            other_sem = semantics.get(other, {})
            if other_sem.get("ignored_for_analysis", False) or other_sem.get("semantic_type") == "Identifier":
                related_list.append(
                    {
                        "feature": str(other),
                        "relationship_strength": "Identifier (Ignored)",
                        "metric_name": "N/A",
                        "score": None,
                        "description": "Identifier column excluded from analysis.",
                    }
                )
                continue

            is_other_num = pd.api.types.is_numeric_dtype(df[other])

            if is_col_num and is_other_num:
                # Pearson r
                valid_df = df[[col, other]].dropna()
                if len(valid_df) > 2 and valid_df[col].nunique() > 1 and valid_df[other].nunique() > 1:
                    r = float(valid_df[col].corr(valid_df[other]))
                    if pd.notna(r):
                        strength = get_strength_label(r, is_pearson=True)
                        related_list.append(
                            {
                                "feature": str(other),
                                "relationship_strength": strength,
                                "metric_name": "Pearson r",
                                "score": round(r, 4),
                                "description": f"{strength} correlation (r = {r:.2f})",
                            }
                        )
            elif not is_col_num and not is_other_num:
                # Cramér's V
                v = compute_cramers_v(df[col], df[other])
                strength = get_strength_label(v, is_pearson=False)
                related_list.append(
                    {
                        "feature": str(other),
                        "relationship_strength": strength,
                        "metric_name": "Cramér's V",
                        "score": round(v, 4),
                        "description": f"{strength} categorical association (V = {v:.2f})",
                    }
                )
            else:
                # Eta (Categorical vs Numeric)
                cat_col = col if not is_col_num else other
                num_col = col if is_col_num else other
                eta = compute_eta_squared(df[cat_col], df[num_col])
                strength = get_strength_label(eta, is_pearson=False)
                related_list.append(
                    {
                        "feature": str(other),
                        "relationship_strength": strength,
                        "metric_name": "Correlation Ratio (Eta)",
                        "score": round(eta, 4),
                        "description": f"{strength} cross-type association (Eta = {eta:.2f})",
                    }
                )

        # Sort valid related features by score magnitude descending
        valid_related = [r for r in related_list if r["score"] is not None]
        valid_related.sort(key=lambda r: abs(r["score"]), reverse=True)
        id_related = [r for r in related_list if r["score"] is None]
        final_related = valid_related + id_related

        # Generate summary
        top_strong = [r for r in valid_related if r["relationship_strength"] in ("Very Strong", "Strong", "Moderate")][:2]
        if top_strong:
            top_str = " and ".join([f"'{r['feature']}' ({r['relationship_strength']}, score = {r['score']})" for r in top_strong])
            summary = f"'{col}' is primarily associated with {top_str}. Identifier columns are excluded because they do not contain analytical information."
        else:
            summary = f"'{col}' presents weak analytical association with other features. Identifier columns are excluded because they do not contain analytical information."

        relationships[col] = {
            "column_name": str(col),
            "is_identifier": False,
            "status": "Analyzed",
            "related_features": final_related,
            "summary": summary,
        }

    return relationships

"""
Feature Engineering Suggestions Service.
Recommends domain-specific and statistical feature transformations to boost model performance.
"""

import pandas as pd


def generate_feature_engineering_suggestions(
    df: pd.DataFrame,
    numeric: dict,
    categorical: dict,
    datetime_info: dict,
    correlation: dict,
    semantics: dict,
) -> list:
    suggestions = []

    # 1. Age Binning Suggestion
    for col in df.columns:
        c_lower = str(col).lower()
        if "age" in c_lower and col in numeric:
            suggestions.append(
                {
                    "source_column": col,
                    "target_feature": f"{col}_Group",
                    "transformation": "Binned Age Bracket (Child/Young Adult/Adult/Senior)",
                    "reasoning": f"Converting continuous '{col}' into ordinal brackets captures non-linear risk/behavior boundaries.",
                }
            )

    # 2. Income / Salary Log Transform
    for col, stats in numeric.items():
        if "note" in stats:
            continue
        c_lower = str(col).lower()
        skew = stats.get("skewness", 0.0)
        if ("salary" in c_lower or "income" in c_lower or "price" in c_lower or "amount" in c_lower or skew > 1.0):
            suggestions.append(
                {
                    "source_column": col,
                    "target_feature": f"Log_{col}",
                    "transformation": "Natural Logarithm (np.log1p)",
                    "reasoning": f"Compresses high magnitude long-tail values in '{col}' (skew={skew:.2f}) for additive linear modeling.",
                }
            )

    # 3. Datetime Feature Decomposition
    if datetime_info and datetime_info.get("datetime_columns"):
        for dt_col in datetime_info["datetime_columns"]:
            suggestions.append(
                {
                    "source_column": dt_col,
                    "target_feature": f"{dt_col}_Year, {dt_col}_Month, {dt_col}_DayOfWeek, {dt_col}_IsWeekend",
                    "transformation": "Date Decomposition",
                    "reasoning": f"Extracting calendar components from '{dt_col}' isolates seasonal, weekly, and temporal trends.",
                }
            )

    # 4. Interaction Ratios for Strong Correlated Numerical Pairs
    strong_pairs = correlation.get("strong_positive", []) + correlation.get("strong_negative", [])
    for pair in strong_pairs[:3]:
        col_a, col_b = pair["column_a"], pair["column_b"]
        if semantics.get(col_a, {}).get("ignored_for_analysis") or semantics.get(col_b, {}).get("ignored_for_analysis"):
            continue
        suggestions.append(
            {
                "source_column": f"{col_a}, {col_b}",
                "target_feature": f"{col_a}_{col_b}_Ratio",
                "transformation": f"Feature Ratio ({col_a} / {col_b})",
                "reasoning": f"High correlation (r={pair['correlation']:.2f}) indicates an underlying physical/proportional interaction.",
            }
        )

    # 5. Outlier Capping / Trimming
    for col, stats in numeric.items():
        if "note" in stats:
            continue
        c_lower = str(col).lower()
        if "bmi" in c_lower:
            suggestions.append(
                {
                    "source_column": col,
                    "target_feature": f"{col}_Category",
                    "transformation": "Clinical BMI Bins (Underweight, Normal, Overweight, Obese)",
                    "reasoning": f"Categorizing '{col}' aligns with standard medical risk stratification.",
                }
            )

    return suggestions

"""
Analyst Observations Service (STEP 15).
Generates pure observational notes exactly like a human data analyst taking notes in a Jupyter notebook.
"""

import pandas as pd


def generate_analyst_observations(
    overview: dict,
    missing: dict,
    duplicates: dict,
    numeric: dict,
    categorical: dict,
    correlation: dict,
    outliers: dict,
    semantics: dict,
) -> list:
    obs = []

    # 1. Dataset Scale Observation
    n_rows = overview.get("n_rows", 0)
    n_cols = overview.get("n_columns", 0)
    obs.append(f"Dataset contains {n_rows:,} total rows and {n_cols} attributes.")

    # 2. Missing Value Observation
    tot_missing = missing.get("total_missing_cells", 0)
    if tot_missing == 0:
        obs.append("No missing values were detected in the dataset; all attributes are 100% complete.")
    else:
        obs.append(
            f"{missing.get('overall_missing_percentage', 0.0)}% of dataset cells ({tot_missing:,} values) are missing."
        )

    # 3. Duplicate Observation
    dup_cnt = duplicates.get("duplicate_row_count", 0)
    if dup_cnt == 0:
        obs.append("No duplicate rows were identified in the dataset.")
    else:
        obs.append(f"{dup_cnt:,} duplicate rows were identified ({duplicates.get('duplicate_percentage', 0.0)}% of total rows).")

    # 4. Column Semantic / Identifier Observation
    for col, s in semantics.items():
        if s.get("ignored_for_analysis") or s.get("semantic_type") == "Identifier":
            obs.append(f"'{col}' is an identifier column and should be excluded from analytical correlation.")

    # 5. Feature Distribution Observations
    for col, stats in numeric.items():
        if "note" in stats: continue
        dist = stats.get("distribution_classification", "Normal")
        skew = stats.get("skewness", 0.0)
        if dist == "Normal":
            obs.append(f"'{col}' follows an approximately symmetric normal distribution centered around mean {stats['mean']:.2f}.")
        elif "Right Skewed" in dist:
            obs.append(f"'{col}' is right-skewed (skewness = {skew:.2f}) with a cluster of lower values and a long upper tail.")
        elif "Left Skewed" in dist:
            obs.append(f"'{col}' is left-skewed (skewness = {skew:.2f}) with a long lower tail.")

    # 6. Outlier Observations
    for col, o in outliers.items():
        cnt = o.get("outlier_count", 0)
        pct = o.get("outlier_percentage", 0.0)
        if cnt > 0:
            obs.append(f"'{col}' contains {cnt} high-value/low-value statistical outliers ({pct}% of observations).")

    # 7. Correlation Observations
    strong_pos = correlation.get("strong_positive", [])
    strong_neg = correlation.get("strong_negative", [])
    if strong_pos:
        top_p = strong_pos[0]
        obs.append(f"'{top_p['column_a']}' has a strong positive relationship with '{top_p['column_b']}' (r = {top_p['correlation']:.2f}).")
    if strong_neg:
        top_n = strong_neg[0]
        obs.append(f"'{top_n['column_a']}' has a strong negative relationship with '{top_n['column_b']}' (r = {top_n['correlation']:.2f}).")

    # 8. Categorical Observations
    for col, info in categorical.items():
        top_cats = info.get("top_categories", [])
        if top_cats:
            top_val = top_cats[0]
            obs.append(f"For '{col}', the most frequent category is '{top_val['value']}' representing {top_val['percentage']}% of records.")

    return obs

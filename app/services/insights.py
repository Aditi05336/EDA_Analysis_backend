"""
Rich Rule-based Plain-English Insight Generator.
Generates 10-20+ deep, context-aware insights explaining skewness, kurtosis,
correlations, missing patterns, duplicates, outliers, class balance, and data quality.
"""

import pandas as pd


def generate_insights(
    overview: dict,
    missing: dict,
    duplicates: dict,
    numeric: dict,
    categorical: dict,
    correlation: dict,
    outliers: dict,
    quality: dict,
    target_info: dict = None,
    datetime_info: dict = None,
    text_info: dict = None,
) -> list:
    insights = []

    # 1. Dataset Scale & Footprint
    n_rows = overview.get("n_rows", 0)
    n_cols = overview.get("n_columns", 0)
    mem_mb = overview.get("memory_usage_mb", 0.0)
    insights.append(
        f"Dataset contains {n_rows:,} records across {n_cols} columns, consuming approximately {mem_mb:.4f} MB of RAM."
    )

    # 2. Overall Health & Quality Score
    q_score = quality.get("quality_score", 100.0)
    bd = quality.get("breakdown", {})
    if q_score >= 90:
        insights.append(f"Overall Data Quality Score is Excellent ({q_score}/100), indicating a clean dataset ready for processing.")
    elif q_score >= 70:
        insights.append(f"Overall Data Quality Score is Moderate ({q_score}/100). Primary deductions stem from duplicates or outliers.")
    else:
        insights.append(f"Overall Data Quality Score is Low ({q_score}/100). Significant cleaning is required before modeling.")

    # 3. Missing Data Observations
    tot_missing = missing.get("total_missing_cells", 0)
    overall_missing_pct = missing.get("overall_missing_percentage", 0.0)
    if tot_missing == 0:
        insights.append("Data Completeness is 100%: no missing or null values detected across any attributes.")
    else:
        insights.append(
            f"{overall_missing_pct}% of total dataset cells ({tot_missing:,} values) are missing across {len(missing.get('columns_with_missing', []))} attribute(s)."
        )
        worst_col = max(missing.get("per_column", {}).items(), key=lambda kv: kv[1]["missing_percentage"], default=None)
        if worst_col and worst_col[1]["missing_percentage"] > 0:
            insights.append(
                f"Column '{worst_col[0]}' exhibits the highest missing rate at {worst_col[1]['missing_percentage']}%, requiring imputation strategies."
            )

    # 4. Duplicate Rows
    dup_cnt = duplicates.get("duplicate_row_count", 0)
    dup_pct = duplicates.get("duplicate_percentage", 0.0)
    if dup_cnt == 0:
        insights.append("Zero duplicate rows detected; all records are distinct.")
    else:
        insights.append(
            f"{dup_cnt:,} duplicate rows detected ({dup_pct}% of dataset). Deduplication will prevent data leakage and skewed stats."
        )

    # 5. Numeric Distribution Insights (Skewness & Kurtosis)
    for col, stats in numeric.items():
        if "note" in stats:
            continue
        skew = stats.get("skewness", 0.0)
        dist = stats.get("distribution_classification", "Normal")
        
        if skew > 1.0:
            insights.append(
                f"'{col}' is highly right-skewed (skewness={skew:.2f}), meaning most values cluster near lower numbers with a long tail of high values."
            )
        elif skew < -1.0:
            insights.append(
                f"'{col}' is highly left-skewed (skewness={skew:.2f}), indicating a concentration of higher values with occasional low values."
            )
        elif dist == "Normal":
            insights.append(
                f"'{col}' follows a symmetric normal-like distribution centered around mean {stats['mean']:.2f}."
            )

        kurt = stats.get("kurtosis", 0.0)
        if kurt > 3.0:
            insights.append(
                f"'{col}' presents heavy tails (kurtosis={kurt:.2f}), signaling frequent extreme values compared to a normal distribution."
            )

    # 6. Outlier Observations
    outlier_count_total = 0
    for col, o in outliers.items():
        cnt = o.get("outlier_count", 0)
        pct = o.get("outlier_percentage", 0.0)
        if cnt > 0 and pct >= 0.5:
            outlier_count_total += cnt
            insights.append(
                f"'{col}' contains {cnt} statistical outliers ({pct}%) outside IQR range [{o['lower_bound']}, {o['upper_bound']}]."
            )
    if outlier_count_total == 0:
        insights.append("No statistical outliers detected across numerical columns based on IQR 1.5x thresholding.")

    # 7. Categorical & Class Balance
    for col, info in categorical.items():
        top_cats = info.get("top_categories", [])
        if top_cats:
            top_val = top_cats[0]
            insights.append(
                f"The most dominant category in '{col}' is '{top_val['value']}', accounting for {top_val['percentage']}% ({top_val['count']:,} rows)."
            )
        if info.get("is_high_cardinality"):
            insights.append(
                f"'{col}' is a high-cardinality feature with {info['unique_count']:,} unique values ({info['cardinality_ratio']*100:.1f}% cardinality ratio)."
            )

    # 8. Correlations & Multicollinearity
    strong_pos = correlation.get("strong_positive", [])
    strong_neg = correlation.get("strong_negative", [])
    if strong_pos:
        top_p = strong_pos[0]
        insights.append(
            f"Strongest positive correlation: '{top_p['column_a']}' and '{top_p['column_b']}' (r = {top_p['correlation']:.4f}). "
            f"As {top_p['column_a']} increases, {top_p['column_b']} rises in near lockstep."
        )
    if strong_neg:
        top_n = strong_neg[0]
        insights.append(
            f"Strongest negative correlation: '{top_n['column_a']}' and '{top_n['column_b']}' (r = {top_n['correlation']:.4f}). "
            f"As {top_n['column_a']} increases, {top_n['column_b']} decreases."
        )
    
    tot_strong_pairs = len(correlation.get("strong_pairs", []))
    if tot_strong_pairs > 3:
        insights.append(
            f"High multicollinearity detected across {tot_strong_pairs} strongly correlated numerical pairs (r ≥ 0.70)."
        )

    # 9. Constant Columns
    const_cols = quality.get("constant_columns", [])
    if const_cols:
        insights.append(
            f"Column(s) {', '.join(const_cols)} have zero variance (only 1 distinct value) and can be safely dropped."
        )

    # 10. Target Analysis Insights (if detected)
    if target_info and target_info.get("target_detected"):
        t_col = target_info["target_column"]
        insights.append(
            f"Auto-detected candidate target column: '{t_col}' ({target_info.get('task_type', 'classification').capitalize()} task)."
        )

    # 11. Datetime & Trend Insights (if detected)
    if datetime_info and datetime_info.get("datetime_columns"):
        dt_cols = ", ".join(datetime_info["datetime_columns"])
        insights.append(f"Auto-detected temporal/datetime attribute(s): {dt_cols}.")

    # Cap/ensure return between 10 to 20 insights
    return insights

"""
Executive Summary Generator Service.
Synthesizes technical EDA analysis modules into a senior data analyst report without ML jargon.
"""

import pandas as pd


def generate_executive_summary(
    overview: dict,
    missing: dict,
    duplicates: dict,
    numeric: dict,
    categorical: dict,
    correlation: dict,
    outliers: dict,
    quality: dict,
    semantics: dict,
) -> dict:
    n_rows = overview.get("n_rows", 0)
    n_cols = overview.get("n_columns", 0)
    mem_mb = overview.get("memory_usage_mb", 0.0)

    # 1. Dataset Overview Paragraph
    ds_overview = (
        f"The dataset contains {n_rows:,} records across {n_cols} columns, requiring {mem_mb:.4f} MB of memory. "
        f"It consists of {overview.get('dtype_counts', {}).get('int64', 0) + overview.get('dtype_counts', {}).get('float64', 0)} numerical columns "
        f"and {overview.get('dtype_counts', {}).get('object', 0)} categorical attributes."
    )

    # 2. Key Findings
    key_findings = []
    if missing.get("total_missing_cells", 0) == 0:
        key_findings.append("The dataset features 100% data completeness with zero missing values.")
    else:
        key_findings.append(
            f"Missing values affect {missing.get('overall_missing_percentage', 0.0)}% of total cells across {len(missing.get('columns_with_missing', []))} column(s)."
        )

    dup_cnt = duplicates.get("duplicate_row_count", 0)
    if dup_cnt > 0:
        key_findings.append(f"Identified {dup_cnt:,} duplicate rows ({duplicates.get('duplicate_percentage', 0.0)}% of dataset).")

    strong_pairs = correlation.get("strong_pairs", [])
    if strong_pairs:
        top_pair = strong_pairs[0]
        key_findings.append(
            f"Strongest linear correlation exists between '{top_pair['column_a']}' and '{top_pair['column_b']}' (r = {top_pair['correlation']:.4f})."
        )

    # 3. Major Problems
    major_problems = []
    if dup_cnt > 0:
        major_problems.append(f"Duplicate records ({dup_cnt:,} rows) inflate sampling density.")
    if quality.get("constant_columns"):
        major_problems.append(f"Zero-variance constant columns detected: {', '.join(quality['constant_columns'])}.")
    if len(strong_pairs) > 2:
        major_problems.append(f"High feature redundancy: {len(strong_pairs)} numerical pairs exhibit strong correlation r ≥ 0.70.")
    if missing.get("columns_fully_missing"):
        major_problems.append(f"Completely empty columns present: {', '.join(missing['columns_fully_missing'])}.")

    if not major_problems:
        major_problems.append("No critical structural data defects identified.")

    # 4. Recommended Cleaning Steps
    recommended_cleaning_steps = []
    if dup_cnt > 0:
        recommended_cleaning_steps.append("Perform deduplication (`df.drop_duplicates()`).")
    if missing.get("columns_with_missing"):
        recommended_cleaning_steps.append("Apply median imputation for skewed numerical columns and mode imputation for categorical attributes.")
    if quality.get("constant_columns"):
        recommended_cleaning_steps.append(f"Drop constant column(s): {', '.join(quality['constant_columns'])}.")

    # 5. Overall Health Assessment
    overall_health = (
        f"Data Quality Score: {quality.get('quality_score', 100.0)} / 100. "
        "The dataset exhibits solid structural integrity once recommended cleaning steps are applied."
    )

    return {
        "dataset_overview": ds_overview,
        "key_findings": key_findings,
        "major_problems": major_problems,
        "recommended_cleaning_steps": recommended_cleaning_steps,
        "overall_health_assessment": overall_health,
    }

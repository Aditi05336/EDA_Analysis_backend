"""
Automated Preprocessing Pipeline Generator.
Constructs a sequential, ordered ML data engineering pipeline tailored to the dataset.
"""

import pandas as pd


def generate_preprocessing_pipeline(
    df: pd.DataFrame,
    missing: dict,
    duplicates: dict,
    numeric: dict,
    categorical: dict,
    quality: dict,
    semantics: dict,
) -> list:
    pipeline = []
    step_num = 1

    # Step 1: Exclude Identifier Columns
    id_cols = [col for col, s in semantics.items() if s.get("ignored_for_analysis")]
    if id_cols:
        pipeline.append(
            {
                "step": step_num,
                "operation": "Drop Identifier Columns",
                "reason": "Excludes non-predictive 1:1 IDs to prevent overfitting",
                "columns": id_cols,
            }
        )
        step_num += 1

    # Step 2: Remove Constant Columns
    const_cols = quality.get("constant_columns", [])
    if const_cols:
        pipeline.append(
            {
                "step": step_num,
                "operation": "Drop Constant Columns",
                "reason": "Removes zero-variance features",
                "columns": const_cols,
            }
        )
        step_num += 1

    # Step 3: Remove Duplicate Rows
    dup_cnt = duplicates.get("duplicate_row_count", 0)
    if dup_cnt > 0:
        pipeline.append(
            {
                "step": step_num,
                "operation": "Remove Duplicate Rows",
                "reason": f"{dup_cnt} duplicate rows detected",
                "columns": [],
            }
        )
        step_num += 1

    # Step 4: Missing Value Imputation
    num_missing = [
        col for col, info in missing.get("per_column", {}).items() if info["missing_count"] > 0 and col in numeric
    ]
    if num_missing:
        pipeline.append(
            {
                "step": step_num,
                "operation": "Median Numeric Imputation",
                "reason": "Imputes nulls in numeric features robust to skewness",
                "columns": num_missing,
            }
        )
        step_num += 1

    cat_missing = [
        col for col, info in missing.get("per_column", {}).items() if info["missing_count"] > 0 and col in categorical
    ]
    if cat_missing:
        pipeline.append(
            {
                "step": step_num,
                "operation": "Mode Categorical Imputation",
                "reason": "Imputes nulls in categorical features using most frequent label",
                "columns": cat_missing,
            }
        )
        step_num += 1

    # Step 5: Categorical Encoding
    low_card_cols = [
        col for col, info in categorical.items() if not info.get("is_high_cardinality") and col not in id_cols
    ]
    if low_card_cols:
        pipeline.append(
            {
                "step": step_num,
                "operation": "One Hot Encoding",
                "reason": "Converts low-cardinality discrete categories to binary indicators",
                "columns": low_card_cols,
            }
        )
        step_num += 1

    high_card_cols = [
        col for col, info in categorical.items() if info.get("is_high_cardinality") and col not in id_cols
    ]
    if high_card_cols:
        pipeline.append(
            {
                "step": step_num,
                "operation": "Target / Frequency Encoding",
                "reason": "Encodes high-cardinality categories without creating high sparse dimensions",
                "columns": high_card_cols,
            }
        )
        step_num += 1

    # Step 6: Log Transformation for Skewed Features
    skewed_num = [
        col for col, stats in numeric.items() if "note" not in stats and abs(stats.get("skewness", 0)) > 1.0 and col not in id_cols
    ]
    if skewed_num:
        pipeline.append(
            {
                "step": step_num,
                "operation": "Log Transformation (log1p)",
                "reason": "Normalizes heavily skewed continuous features",
                "columns": skewed_num,
            }
        )
        step_num += 1

    # Step 7: Feature Scaling
    valid_numeric = [col for col in numeric.keys() if col not in id_cols]
    if valid_numeric:
        pipeline.append(
            {
                "step": step_num,
                "operation": "Standard Scaling (StandardScaler)",
                "reason": "Standardizes zero mean and unit variance across numerical features",
                "columns": valid_numeric,
            }
        )
        step_num += 1

    return pipeline

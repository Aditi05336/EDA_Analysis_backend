"""
Duplicate Row Analysis Service (STEP 5).
Detects duplicate rows, percentages, sample duplicate rows, and contextual observations on accidental vs meaningful duplicates.
"""

import pandas as pd


def analyze_duplicates(df: pd.DataFrame, max_samples: int = 20) -> dict:
    dup_mask = df.duplicated(keep="first")
    dup_count = int(dup_mask.sum())
    dup_indices = [int(i) for i in df.index[dup_mask].tolist()]

    n_rows = df.shape[0]
    pct = round((dup_count / n_rows) * 100, 2) if n_rows else 0.0

    # Extract sample duplicate rows as clean dict records
    sample_dups_df = df[dup_mask].head(max_samples)
    sample_duplicate_rows = (
        sample_dups_df.astype(object).where(pd.notna(sample_dups_df), None).to_dict(orient="records")
        if not sample_dups_df.empty
        else []
    )

    # Observation on meaningful vs accidental duplicates
    if dup_count == 0:
        obs = "No duplicate rows identified; all dataset records are unique."
    elif pct > 30.0:
        obs = f"Detected {dup_count:,} duplicate rows ({pct}%). High duplicate volume often indicates redundant data ingestion or identical transactional logging."
    else:
        obs = f"Detected {dup_count:,} duplicate rows ({pct}%). In operational datasets, duplicate rows can be meaningful (e.g. repeated customer visits) or accidental (e.g. re-sent webhooks). Evaluate domain context before deduplication."

    return {
        "duplicate_row_count": dup_count,
        "duplicate_percentage": pct,
        "duplicate_row_indices": dup_indices[:50],
        "sample_duplicate_indices": dup_indices[:50],
        "sample_duplicate_rows": sample_duplicate_rows,
        "observation": obs,
        "truncated": dup_count > 50,
    }

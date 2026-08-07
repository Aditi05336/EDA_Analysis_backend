"""Dataset preview service: first 5, last 5, random 5 rows."""

import pandas as pd


def get_preview(df: pd.DataFrame, n: int = 5) -> dict:
    """
    Returns head (first n), tail (last n), and sample (random n) rows
    safely converted to JSON-serializable dictionary records.
    """
    if df.empty:
        return {"first_5": [], "last_5": [], "random_5": []}

    n_rows = len(df)
    head_df = df.head(n)
    tail_df = df.tail(n)

    sample_n = min(n, n_rows)
    # Using fixed random_state if needed, or non-deterministic sample
    sample_df = df.sample(n=sample_n, random_state=42) if n_rows > 0 else pd.DataFrame()

    def clean_records(records_df):
        # Convert NaN / NaT / Inf to None for clean JSON serialization
        records = records_df.astype(object).where(pd.notna(records_df), None).to_dict(orient="records")
        return records

    return {
        "first_5": clean_records(head_df),
        "last_5": clean_records(tail_df),
        "random_5": clean_records(sample_df),
    }

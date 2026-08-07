"""
Unique Value Analysis Service (STEP 6).
Profiles unique count, unique ratio, identity detection, cardinality status,
most frequent value, and frequency count per column.
"""

import pandas as pd
from app.services.semantic_detection import detect_column_semantics


def analyze_unique_values(df: pd.DataFrame, semantics: dict = None) -> dict:
    if semantics is None:
        semantics = detect_column_semantics(df)

    n_rows = len(df)
    unique_summary = {}

    for col in df.columns:
        series = df[col].dropna()
        n_unique = int(series.nunique())
        ratio = round(n_unique / n_rows, 4) if n_rows else 0.0
        is_unique = (n_unique == n_rows) and (n_rows > 0)

        sem_info = semantics.get(col, {})
        sem_type = sem_info.get("semantic_type", "Categorical")

        # Most Frequent Value & Frequency
        if not series.empty:
            top_val_series = series.mode()
            most_freq_val = str(top_val_series.iloc[0]) if not top_val_series.empty else str(series.iloc[0])
            most_freq_cnt = int((series == top_val_series.iloc[0]).sum()) if not top_val_series.empty else 1
            most_freq_pct = round((most_freq_cnt / n_rows) * 100, 2) if n_rows else 0.0
        else:
            most_freq_val = None
            most_freq_cnt = 0
            most_freq_pct = 0.0

        if is_unique or sem_type == "Identifier":
            card_status = "Unique Identifier"
        elif ratio > 0.5:
            card_status = "High Cardinality"
        elif n_unique <= 1:
            card_status = "Zero Variance / Constant"
        elif n_unique <= 10:
            card_status = "Low Cardinality"
        else:
            card_status = "Moderate Cardinality"

        unique_summary[col] = {
            "column_name": str(col),
            "unique_count": n_unique,
            "unique_ratio": ratio,
            "is_unique": is_unique,
            "semantic_type": sem_type,
            "cardinality_status": card_status,
            "most_frequent_value": most_freq_val,
            "most_frequent_count": most_freq_cnt,
            "most_frequent_percentage": most_freq_pct,
            "is_identifier": sem_info.get("ignored_for_analysis", False),
        }

    return unique_summary

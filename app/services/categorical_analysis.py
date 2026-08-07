"""Categorical / object column analysis: frequency table, top categories, cardinality ratio."""

import pandas as pd
from app.config import Config


def get_categorical_columns(df: pd.DataFrame) -> list:
    return df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()


def analyze_categorical(df: pd.DataFrame) -> dict:
    cat_cols = get_categorical_columns(df)
    result = {}
    n_rows = df.shape[0]

    for col in cat_cols:
        series = df[col].dropna()
        n_unique = int(series.nunique())
        cardinality_ratio = round(n_unique / n_rows, 4) if n_rows else 0.0

        all_value_counts = series.value_counts()
        
        # Frequency table (top N + summary)
        freq_table = {
            str(k): int(v) for k, v in all_value_counts.head(Config.TOP_N_CATEGORIES).items()
        }

        top_categories = [
            {
                "value": str(idx),
                "count": int(cnt),
                "percentage": round((cnt / n_rows) * 100, 2) if n_rows else 0.0,
            }
            for idx, cnt in all_value_counts.head(Config.TOP_N_CATEGORIES).items()
        ]

        result[col] = {
            "unique_count": n_unique,
            "cardinality_ratio": cardinality_ratio,
            "is_high_cardinality": cardinality_ratio > Config.HIGH_CARDINALITY_RATIO,
            "frequency_table": freq_table,
            "top_categories": top_categories,
        }

    return result

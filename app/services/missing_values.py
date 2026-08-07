"""Missing value detection per column, overall summary, and heatmap-ready JSON matrix."""

import pandas as pd


def generate_heatmap_json(df: pd.DataFrame, sample_size: int = 50) -> dict:
    """
    Generates a lightweight matrix of boolean missingness (True = missing, False = present)
    for a sample of rows across all columns, ready for UI heatmap rendering.
    """
    if df.empty:
        return {"columns": [], "matrix": []}

    sample_df = df.head(sample_size) if len(df) > sample_size else df
    missing_matrix = sample_df.isna().to_dict(orient="records")

    return {
        "columns": list(df.columns.astype(str)),
        "sample_rows": len(sample_df),
        "matrix": missing_matrix,
    }


def analyze_missing_values(df: pd.DataFrame) -> dict:
    n_rows, n_cols = df.shape
    total_cells = n_rows * n_cols
    per_column = {}

    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        pct = round((missing_count / n_rows) * 100, 2) if n_rows else 0.0
        per_column[col] = {
            "missing_count": missing_count,
            "missing_percentage": pct,
        }

    total_missing = sum(v["missing_count"] for v in per_column.values())
    columns_with_missing = [c for c, v in per_column.items() if v["missing_count"] > 0]
    columns_fully_missing = [c for c, v in per_column.items() if v["missing_percentage"] == 100.0]

    heatmap_json = generate_heatmap_json(df)

    return {
        "per_column": per_column,
        "total_missing_cells": total_missing,
        "total_cells": total_cells,
        "overall_missing_percentage": (
            round((total_missing / total_cells) * 100, 2) if total_cells else 0.0
        ),
        "columns_with_missing": columns_with_missing,
        "columns_fully_missing": columns_fully_missing,
        "heatmap_ready_json": heatmap_json,
    }

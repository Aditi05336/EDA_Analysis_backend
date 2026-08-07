"""
Basic Information Service (df.info() equivalent).
Extracts column index, column name, data type, non-null count, null count, null percentage,
and per-column memory usage.
"""

import pandas as pd


def get_basic_info(df: pd.DataFrame) -> dict:
    n_rows = len(df)
    columns_info = []
    total_memory_bytes = int(df.memory_usage(deep=True).sum())

    for idx, col in enumerate(df.columns):
        series = df[col]
        null_count = int(series.isna().sum())
        non_null_count = n_rows - null_count
        null_pct = round((null_count / n_rows) * 100, 2) if n_rows else 0.0
        col_memory_bytes = int(series.memory_usage(deep=True))

        columns_info.append(
            {
                "index": idx,
                "column_name": str(col),
                "data_type": str(series.dtype),
                "non_null_count": non_null_count,
                "null_count": null_count,
                "null_percentage": null_pct,
                "memory_bytes": col_memory_bytes,
            }
        )

    return {
        "total_rows": n_rows,
        "total_columns": len(df.columns),
        "total_memory_bytes": total_memory_bytes,
        "total_memory_mb": round(total_memory_bytes / (1024 * 1024), 4),
        "columns_info": columns_info,
    }

"""Dataset-level overview: shape, memory footprint, column dtypes."""


def get_overview(df):
    memory_bytes = int(df.memory_usage(deep=True).sum())

    dtype_map = {col: str(dtype) for col, dtype in df.dtypes.items()}

    dtype_counts = {}
    for dtype_str in dtype_map.values():
        dtype_counts[dtype_str] = dtype_counts.get(dtype_str, 0) + 1

    return {
        "n_rows": int(df.shape[0]),
        "n_columns": int(df.shape[1]),
        "column_names": list(df.columns.astype(str)),
        "memory_usage_bytes": memory_bytes,
        "memory_usage_mb": round(memory_bytes / (1024 * 1024), 4),
        "column_dtypes": dtype_map,
        "dtype_counts": dtype_counts,
    }

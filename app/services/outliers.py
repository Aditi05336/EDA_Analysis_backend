"""Outlier detection using the IQR (1.5x) method for numeric columns, with sample values and indices."""

import pandas as pd
from app.services.numeric_analysis import get_numeric_columns


def analyze_outliers(df: pd.DataFrame, max_samples: int = 10) -> dict:
    numeric_cols = get_numeric_columns(df)
    result = {}

    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty or series.nunique() <= 1:
            result[col] = {
                "iqr": 0.0,
                "lower_bound": None,
                "upper_bound": None,
                "outlier_count": 0,
                "outlier_percentage": 0.0,
                "sample_outlier_values": [],
                "sample_outlier_indices": [],
            }
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (series < lower_bound) | (series > upper_bound)
        outlier_count = int(outlier_mask.sum())
        outlier_series = series[outlier_mask]

        sample_indices = [int(i) for i in outlier_series.index[:max_samples].tolist()]
        sample_values = [round(float(v), 4) for v in outlier_series.iloc[:max_samples].tolist()]

        result[col] = {
            "iqr": round(float(iqr), 4),
            "lower_bound": round(float(lower_bound), 4),
            "upper_bound": round(float(upper_bound), 4),
            "outlier_count": outlier_count,
            "outlier_percentage": round((outlier_count / len(series)) * 100, 2),
            "sample_outlier_values": sample_values,
            "sample_outlier_indices": sample_indices,
        }

    return result

"""Summary statistics, variance, mode, distribution classification, skewness, kurtosis for numeric columns."""

import numpy as np
import pandas as pd


def get_numeric_columns(df: pd.DataFrame) -> list:
    return df.select_dtypes(include=["number"]).columns.tolist()


def classify_distribution(skewness: float, kurtosis: float) -> str:
    """Classifies numerical distribution shape based on skewness."""
    if skewness > 1.0:
        return "Highly Right Skewed"
    elif skewness < -1.0:
        return "Highly Left Skewed"
    elif 0.5 < skewness <= 1.0:
        return "Slightly Right Skewed"
    elif -1.0 <= skewness < -0.5:
        return "Slightly Left Skewed"
    else:
        return "Normal"


def analyze_numeric(df: pd.DataFrame) -> dict:
    numeric_cols = get_numeric_columns(df)
    result = {}

    for col in numeric_cols:
        series = df[col].dropna()

        if series.empty:
            result[col] = {"note": "All values missing — no stats computable."}
            continue

        desc = series.describe()
        mean_val = float(desc["mean"])
        median_val = float(desc["50%"])
        std_val = float(desc["std"]) if pd.notna(desc["std"]) else 0.0
        var_val = float(series.var()) if pd.notna(series.var()) else 0.0
        min_val = float(desc["min"])
        max_val = float(desc["max"])
        q1_val = float(series.quantile(0.25))
        q3_val = float(series.quantile(0.75))
        iqr_val = float(q3_val - q1_val)

        # Mode calculation
        mode_series = series.mode()
        mode_val = float(mode_series.iloc[0]) if not mode_series.empty else None

        skew_val = float(series.skew()) if series.nunique() > 1 and len(series) > 2 else 0.0
        kurt_val = float(series.kurt()) if series.nunique() > 1 and len(series) > 3 else 0.0

        dist_label = classify_distribution(skew_val, kurt_val)

        # Outlier calculation (1.5x IQR)
        lower_bound = q1_val - 1.5 * iqr_val
        upper_bound = q3_val + 1.5 * iqr_val
        outlier_count = int(((series < lower_bound) | (series > upper_bound)).sum())

        result[col] = {
            "count": int(desc["count"]),
            "mean": round(mean_val, 4),
            "median": round(median_val, 4),
            "mode": round(mode_val, 4) if mode_val is not None else None,
            "std": round(std_val, 4),
            "variance": round(var_val, 4),
            "min": round(min_val, 4),
            "max": round(max_val, 4),
            "range": round(max_val - min_val, 4),
            "q1": round(q1_val, 4),
            "q3": round(q3_val, 4),
            "iqr": round(iqr_val, 4),
            "skewness": round(skew_val, 4),
            "kurtosis": round(kurt_val, 4),
            "distribution_classification": dist_label,
            "unique_count": int(series.nunique()),
            "zero_count": int((series == 0).sum()),
            "negative_count": int((series < 0).sum()),
            "outlier_count": outlier_count,
        }

    return result

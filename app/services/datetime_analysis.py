"""
Datetime Analysis Service (STEP 17).
Automatically detects temporal/datetime columns, calculates date ranges, time spans,
missing dates, duplicate timestamps, date distributions, time series trends, seasonality,
and analyst-style observations.
"""

import pandas as pd
import numpy as np


def detect_datetime_columns(df: pd.DataFrame) -> dict:
    """
    Detects columns containing datetime values safely.
    Excludes numeric IDs, constant IDs, or non-date text.
    """
    results = {}
    n_rows = len(df)

    for col in df.columns:
        series = df[col]
        col_str = str(col)

        # 1. Already datetime64 dtype
        if pd.api.types.is_datetime64_any_dtype(series):
            parsed = series.dropna()
            success_pct = round((len(parsed) / n_rows) * 100, 2) if n_rows else 0.0
            results[col_str] = {
                "detected": True,
                "parsed_series": series,
                "format": "pandas datetime64",
                "parse_success": success_pct,
            }
            continue

        # Skip numeric columns that aren't strings or datetimes
        if pd.api.types.is_numeric_dtype(series):
            results[col_str] = {"detected": False, "parse_success": 0.0}
            continue

        # 2. String/object columns — attempt safe parsing
        non_null_series = series.dropna().astype(str)
        if non_null_series.empty or len(non_null_series) < 3:
            results[col_str] = {"detected": False, "parse_success": 0.0}
            continue

        # Sample check to avoid expensive parsing on random long text
        sample = non_null_series.head(50)
        parsed_sample = pd.to_datetime(sample, errors="coerce")
        valid_sample_cnt = parsed_sample.notna().sum()

        if valid_sample_cnt / len(sample) >= 0.75:
            full_parsed = pd.to_datetime(series, errors="coerce")
            valid_cnt = full_parsed.notna().sum()
            success_pct = round((valid_cnt / n_rows) * 100, 2) if n_rows else 0.0

            if success_pct >= 50.0:
                # Detect format heuristic
                first_val = non_null_series.iloc[0]
                fmt = "ISO8601 / Standard"
                if "-" in first_val and len(first_val.split("-")[0]) == 4:
                    fmt = "YYYY-MM-DD"
                elif "/" in first_val:
                    parts = first_val.split("/")
                    if len(parts[0]) == 4:
                        fmt = "YYYY/MM/DD"
                    elif int(parts[0]) > 12:
                        fmt = "DD/MM/YYYY"
                    else:
                        fmt = "MM/DD/YYYY"

                results[col_str] = {
                    "detected": True,
                    "parsed_series": full_parsed,
                    "format": fmt,
                    "parse_success": success_pct,
                }
                continue

        results[col_str] = {"detected": False, "parse_success": 0.0}

    return results


def calculate_time_span(min_date: pd.Timestamp, max_date: pd.Timestamp) -> dict:
    """Calculates years, months, and days duration between two dates."""
    if pd.isna(min_date) or pd.isna(max_date):
        return {"span_str": "N/A", "years": 0, "months": 0, "days": 0}

    delta_days = (max_date - min_date).days
    years = delta_days // 365
    remaining_days = delta_days % 365
    months = remaining_days // 30
    days = remaining_days % 30

    parts = []
    if years > 0:
        parts.append(f"{years} Year{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} Month{'s' if months > 1 else ''}")
    if days > 0 or not parts:
        parts.append(f"{days} Day{'s' if days > 1 else ''}")

    return {
        "span_str": " ".join(parts),
        "years": years,
        "months": months,
        "days": days,
        "total_days": delta_days,
    }


def analyze_datetime(df: pd.DataFrame) -> dict:
    """
    Main Datetime Analysis Service.
    Executes only if valid datetime columns exist; returns clean skipped status otherwise.
    """
    detection = detect_datetime_columns(df)
    detected_cols = [col for col, info in detection.items() if info["detected"]]

    if not detected_cols:
        return {
            "datetime_detected": False,
            "message": "No datetime columns detected. Datetime analysis skipped.",
            "columns": [],
            "summary_table": [],
            "observations": [],
        }

    n_rows = len(df)
    column_reports = {}
    summary_table = []
    observations = []

    for col in detected_cols:
        info = detection[col]
        parsed_s = info["parsed_series"].dropna()

        if parsed_s.empty:
            continue

        min_date = parsed_s.min()
        max_date = parsed_s.max()
        time_span = calculate_time_span(min_date, max_date)

        missing_cnt = int(df[col].isna().sum()) + int((info["parsed_series"].isna() & df[col].notna()).sum())
        missing_pct = round((missing_cnt / n_rows) * 100, 2) if n_rows else 0.0

        dup_cnt = int(info["parsed_series"].duplicated(keep="first").sum())
        dup_pct = round((dup_cnt / n_rows) * 100, 2) if n_rows else 0.0

        # Date distributions
        dt_accessor = parsed_s.dt
        year_counts = dt_accessor.year.value_counts().sort_index().to_dict()
        month_counts = dt_accessor.month_name().value_counts().to_dict()
        quarter_counts = dt_accessor.quarter.value_counts().sort_index().to_dict()
        weekday_counts = dt_accessor.day_name().value_counts().to_dict()

        # Seasonality
        most_active_year = str(max(year_counts, key=year_counts.get)) if year_counts else "N/A"
        most_active_month = str(max(month_counts, key=month_counts.get)) if month_counts else "N/A"
        least_active_month = str(min(month_counts, key=month_counts.get)) if month_counts else "N/A"
        most_active_quarter = f"Q{max(quarter_counts, key=quarter_counts.get)}" if quarter_counts else "N/A"
        most_active_weekday = str(max(weekday_counts, key=weekday_counts.get)) if weekday_counts else "N/A"

        # Time Series Trend
        trend_label = "Stable"
        if len(year_counts) > 1:
            years_list = sorted(list(year_counts.keys()))
            first_half_avg = np.mean([year_counts[y] for y in years_list[: len(years_list) // 2]])
            second_half_avg = np.mean([year_counts[y] for y in years_list[len(years_list) // 2 :]])
            if second_half_avg > first_half_avg * 1.1:
                trend_label = "Increasing Trend"
            elif second_half_avg < first_half_avg * 0.9:
                trend_label = "Decreasing Trend"

        earliest_str = min_date.strftime("%Y-%m-%d") if pd.notna(min_date) else "N/A"
        latest_str = max_date.strftime("%Y-%m-%d") if pd.notna(max_date) else "N/A"

        col_report = {
            "column_name": col,
            "detected_format": info["format"],
            "parse_success_rate": info["parse_success"],
            "earliest_date": earliest_str,
            "latest_date": latest_str,
            "duration": time_span["span_str"],
            "years_span": time_span["years"],
            "missing_dates": missing_cnt,
            "missing_percentage": missing_pct,
            "duplicate_timestamps": dup_cnt,
            "duplicate_percentage": dup_pct,
            "records_per_year": {str(k): int(v) for k, v in year_counts.items()},
            "records_per_month": {str(k): int(v) for k, v in month_counts.items()},
            "records_per_quarter": {f"Q{k}": int(v) for k, v in quarter_counts.items()},
            "records_per_weekday": {str(k): int(v) for k, v in weekday_counts.items()},
            "most_active_year": most_active_year,
            "most_active_month": most_active_month,
            "least_active_month": least_active_month,
            "most_active_quarter": most_active_quarter,
            "most_active_weekday": most_active_weekday,
            "trend": trend_label,
        }

        column_reports[col] = col_report

        summary_table.append(
            {
                "column_name": col,
                "earliest_date": earliest_str,
                "latest_date": latest_str,
                "duration": time_span["span_str"],
                "missing_dates": missing_cnt,
                "duplicate_dates": dup_cnt,
                "most_active_year": most_active_year,
                "most_active_month": most_active_month,
                "most_active_weekday": most_active_weekday,
            }
        )

        # Observations
        if time_span["years"] > 0:
            observations.append(f"The '{col}' timeline spans {time_span['span_str']} from {earliest_str} to {latest_str}.")
        else:
            observations.append(f"The '{col}' timeline spans {time_span['total_days']} days from {earliest_str} to {latest_str}.")

        if missing_cnt == 0:
            observations.append(f"No missing timestamps detected for '{col}'.")
        else:
            observations.append(f"'{col}' contains {missing_cnt:,} missing timestamps ({missing_pct}%).")

        observations.append(f"Most records for '{col}' were collected during {most_active_year} (peak month: {most_active_month}, peak day: {most_active_weekday}).")

    return {
        "datetime_detected": True,
        "message": f"Successfully analyzed {len(detected_cols)} datetime column(s).",
        "columns": detected_cols,
        "per_column": column_reports,
        "summary_table": summary_table,
        "observations": observations,
    }

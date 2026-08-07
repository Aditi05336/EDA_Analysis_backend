"""
Human Notebook EDA Engine: Orchestrates 16 sequential Exploratory Data Analysis steps
matching a human data analyst's workflow in a Jupyter Notebook.
"""

import time
import uuid

from app.services import overview as overview_svc
from app.services import preview as preview_svc
from app.services import basic_info as basic_info_svc
from app.services import semantic_detection as semantic_svc
from app.services import numeric_analysis as numeric_svc
from app.services import missing_values as missing_svc
from app.services import duplicates as duplicates_svc
from app.services import unique_values as unique_svc
from app.services import column_health as health_svc
from app.services import categorical_analysis as categorical_svc
from app.services import correlation as correlation_svc
from app.services import feature_relationships as rel_svc
from app.services import datetime_analysis as datetime_svc
from app.services import outliers as outliers_svc
from app.services import data_quality as quality_svc
from app.services import analyst_observations as observations_svc
from app.services import recommendations as recs_svc
from app.services import executive_summary as exec_svc
from app.services import chart_generator as chart_svc


def run_full_eda(df):
    start_time = time.time()
    file_id = uuid.uuid4().hex[:10]

    # STEP 1 — Dataset Overview & Preview
    overview = overview_svc.get_overview(df)
    preview = preview_svc.get_preview(df)
    dataset_overview = {
        "dataset_name": "Uploaded Dataset",
        "n_rows": overview["n_rows"],
        "n_columns": overview["n_columns"],
        "memory_usage_bytes": overview["memory_usage_bytes"],
        "memory_usage_mb": overview["memory_usage_mb"],
        "first_5_rows": preview["first_5"],
        "explanation": f"Dataset contains {overview['n_rows']:,} rows and {overview['n_columns']} attributes, using {overview['memory_usage_mb']} MB in RAM.",
    }

    # STEP 2 — Dataset Information (df.info())
    basic_info = basic_info_svc.get_basic_info(df)

    # STEP 3 — Descriptive Statistics (df.describe() with 17 stats)
    descriptive_statistics = numeric_svc.analyze_numeric(df)

    # STEP 4 — Missing Value Analysis
    missing_values = missing_svc.analyze_missing_values(df)

    # STEP 5 — Duplicate Analysis
    duplicates = duplicates_svc.analyze_duplicates(df)

    # STEP 6 — Unique Value Analysis & Column Semantics
    semantics = semantic_svc.detect_column_semantics(df)
    unique_values = unique_svc.analyze_unique_values(df, semantics=semantics)

    # STEP 7 — Column-wise Health Report (For EVERY column)
    categorical_analysis = categorical_svc.analyze_categorical(df)
    outlier_analysis = outliers_svc.analyze_outliers(df)
    column_health_report = health_svc.generate_column_health_report(
        df, missing_values, duplicates, descriptive_statistics, categorical_analysis, outlier_analysis, semantics
    )

    # STEP 8 — Numerical Feature Analysis
    numerical_feature_analysis = {
        col: {
            "histogram_url": f"/static/charts/{file_id}/histograms.png",
            "boxplot_url": f"/static/charts/{file_id}/boxplots.png",
            "distribution": stats.get("distribution_classification"),
            "skewness": stats.get("skewness"),
            "kurtosis": stats.get("kurtosis"),
            "outlier_count": stats.get("outlier_count"),
            "observation": f"'{col}' presents a {stats.get('distribution_classification', 'Normal')} distribution shape with skewness {stats.get('skewness')} and {stats.get('outlier_count')} outliers.",
        }
        for col, stats in descriptive_statistics.items()
        if "note" not in stats
    }

    # STEP 9 — Categorical Feature Analysis
    categorical_feature_analysis = categorical_analysis

    # STEP 10 — Outlier Analysis
    outliers = outlier_analysis

    # STEP 11 — Correlation Analysis (Identifier columns excluded)
    correlation_analysis = correlation_svc.analyze_correlation(df, semantics=semantics)

    # STEP 12 — Feature Relationship Analysis
    feature_relationship_analysis = rel_svc.analyze_feature_relationships(df, semantics=semantics)

    # STEP 17 — Datetime Analysis
    datetime_analysis = datetime_svc.analyze_datetime(df)

    # STEP 13 — Distribution Summary
    distribution_summary = {
        col: stats.get("distribution_classification")
        for col, stats in descriptive_statistics.items()
        if "note" not in stats
    }

    # STEP 14 — Data Quality Report
    data_quality_report = quality_svc.build_quality_report(
        df, missing_values, duplicates, categorical_analysis, outlier_analysis
    )

    # STEP 15 — Analyst Observations (Pure notes, no recommendations)
    analyst_observations = observations_svc.generate_analyst_observations(
        overview, missing_values, duplicates, descriptive_statistics, categorical_analysis,
        correlation_analysis, outlier_analysis, semantics
    )

    # STEP 16 — Executive Summary
    executive_summary = exec_svc.generate_executive_summary(
        overview, missing_values, duplicates, descriptive_statistics, categorical_analysis,
        correlation_analysis, outlier_analysis, data_quality_report, semantics
    )
    recommendations = recs_svc.generate_recommendations(
        overview, missing_values, duplicates, descriptive_statistics, categorical_analysis,
        correlation_analysis, outlier_analysis, data_quality_report, semantics
    )

    # Automatic Plotly Spec & Matplotlib Chart Generation
    charts, plotly_specs = chart_svc.generate_charts(
        df, correlation_info=correlation_analysis, datetime_info=datetime_analysis, file_id=file_id
    )

    elapsed = round(time.time() - start_time, 4)

    return {
        "success": True,
        "step1_dataset_overview": dataset_overview,
        "step2_dataset_info": basic_info,
        "step3_descriptive_statistics": descriptive_statistics,
        "step4_missing_value_analysis": missing_values,
        "step5_duplicate_analysis": duplicates,
        "step6_unique_value_analysis": unique_values,
        "step7_column_health_report": column_health_report,
        "step8_numerical_feature_analysis": numerical_feature_analysis,
        "step9_categorical_feature_analysis": categorical_feature_analysis,
        "step10_outlier_analysis": outliers,
        "step11_correlation_analysis": correlation_analysis,
        "step12_feature_relationship_analysis": feature_relationship_analysis,
        "step17_datetime_analysis": datetime_analysis,
        "step13_distribution_summary": distribution_summary,
        "step14_data_quality_report": data_quality_report,
        "step15_analyst_observations": analyst_observations,
        "step16_executive_summary": executive_summary,
        # Preserved backward compatibility aliases
        "overview": overview,
        "preview": preview,
        "basic_info": basic_info,
        "descriptive_statistics": descriptive_statistics,
        "missing_values": missing_values,
        "duplicates": duplicates,
        "unique_values": unique_values,
        "numerical_analysis": descriptive_statistics,
        "categorical_analysis": categorical_analysis,
        "outlier_analysis": outlier_analysis,
        "correlation_analysis": correlation_analysis,
        "feature_relationship_analysis": feature_relationship_analysis,
        "datetime_analysis": datetime_analysis,
        "distribution_analysis": distribution_summary,
        "data_quality_report": data_quality_report,
        "executive_summary": executive_summary,
        "charts": charts,
        "plotly_specs": plotly_specs,
        "recommendations": recommendations,
        "meta": {
            "file_id": file_id,
            "processing_time_seconds": elapsed,
            "numeric_column_count": len(descriptive_statistics),
            "categorical_column_count": len(categorical_analysis),
        },
    }

"""
ML Model Recommendation Service.
Suggests optimal machine learning algorithms (Classification, Regression, or Clustering)
with architectural reasoning based on dataset properties.
"""

import pandas as pd


def recommend_models(
    target_info: dict,
    overview: dict,
    quality: dict,
    numeric: dict,
) -> dict:
    target_detected = target_info.get("target_detected", False)
    task_type = target_info.get("task_type", "classification") if target_detected else "clustering"
    n_rows = overview.get("n_rows", 0)
    n_cols = overview.get("n_columns", 0)

    recommended_models = []

    if target_detected and task_type == "classification":
        recommended_models = [
            {
                "algorithm": "XGBoost Classifier",
                "suitability": "Highest",
                "reasoning": "State-of-the-art gradient boosting; handles tabular non-linearities, missing values, and feature interactions robustly.",
            },
            {
                "algorithm": "Random Forest Classifier",
                "suitability": "High",
                "reasoning": "Ensemble of decision trees resistant to overfitting; provides built-in feature importance rankings.",
            },
            {
                "algorithm": "LightGBM / CatBoost Classifier",
                "suitability": "High",
                "reasoning": "Ultra-fast tree boosting optimized for high-performance categorical feature handling.",
            },
            {
                "algorithm": "Logistic Regression",
                "suitability": "Baseline",
                "reasoning": "Simple, interpretable linear baseline model ideal for assessing linear separability.",
            },
        ]
    elif target_detected and task_type == "regression":
        recommended_models = [
            {
                "algorithm": "XGBoost Regressor",
                "suitability": "Highest",
                "reasoning": "Powerful gradient boosted trees for continuous target prediction with regularized loss optimization.",
            },
            {
                "algorithm": "Random Forest Regressor",
                "suitability": "High",
                "reasoning": "Non-parametric regression ensemble resistant to outliers with low variance.",
            },
            {
                "algorithm": "Ridge / Lasso / Linear Regression",
                "suitability": "Baseline",
                "reasoning": "L1/L2 regularized linear model for transparent coefficient interpretation and baseline comparisons.",
            },
        ]
    else:
        recommended_models = [
            {
                "algorithm": "K-Means Clustering",
                "suitability": "High",
                "reasoning": "Unsupervised centroid clustering to discover latent natural groupings in feature space.",
            },
            {
                "algorithm": "DBSCAN",
                "suitability": "Moderate",
                "reasoning": "Density-based spatial clustering effective for discovering arbitrary shaped clusters and filtering noise.",
            },
        ]

    return {
        "primary_task": task_type.capitalize() if target_detected else "Unsupervised Clustering",
        "target_column": target_info.get("target_column") if target_detected else None,
        "recommended_models": recommended_models,
    }

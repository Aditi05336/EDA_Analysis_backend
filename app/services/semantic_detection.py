"""
Column Semantic Detection Service.
Classifies dataset attributes into high-level semantic types (Identifier, Numerical, Binary,
Categorical, Ordinal, Datetime, Text, Boolean, Target Candidate) and flags IDs to exclude
from downstream statistical correlation/modeling.
"""

import re
import pandas as pd
from app.config import Config


ID_PATTERNS = re.compile(
    r"(^|_)id$|^id(_|$)|uuid|guid|serial|patient_id|emp_id|employee_id|user_id|account_id|row_id",
    re.IGNORECASE,
)


def detect_column_semantics(df: pd.DataFrame) -> dict:
    n_rows = len(df)
    semantics = {}

    for col in df.columns:
        series = df[col].dropna()
        col_str = str(col).strip()
        n_unique = series.nunique()
        dtype_str = str(df[col].dtype)

        sem_type = "Categorical"
        ignored = False
        reason = "Standard feature attribute"

        # 1. Identifier Check
        is_id_name = bool(ID_PATTERNS.search(col_str))
        is_unique_id = (n_rows > 5 and n_unique == n_rows)
        is_sequential = False

        if pd.api.types.is_numeric_dtype(df[col]) and not series.empty and n_unique > 5:
            # Check if strictly increasing step 1
            diffs = series.diff().dropna()
            if (diffs == 1).all():
                is_sequential = True

        if is_id_name or is_sequential or (is_unique_id and (is_id_name or dtype_str in ["object", "int64"])):
            sem_type = "Identifier"
            ignored = True
            if is_sequential:
                reason = "Unique sequential numeric identifier"
            elif is_id_name:
                reason = f"Column name '{col}' matches identifier pattern"
            else:
                reason = "Unique 1:1 row identifier ratio"

        # 2. Boolean Check
        elif dtype_str == "bool" or (n_unique == 2 and set(series.unique()).issubset({True, False, 0, 1, "0", "1", "true", "false", "True", "False"})):
            sem_type = "Boolean"
            reason = "Binary boolean state indicator"

        # 3. Binary Check
        elif n_unique == 2:
            sem_type = "Binary"
            reason = "Two-state categorical feature"

        # 4. Target Candidate Check
        elif col_str.lower() in Config.TARGET_KEYWORDS or any(kw in col_str.lower() for kw in Config.TARGET_KEYWORDS):
            sem_type = "Target Candidate"
            reason = f"Matches target keyword pattern '{col}'"

        # 5. Datetime Check
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            sem_type = "Datetime"
            reason = "Temporal timestamp feature"

        # 6. Numerical Check
        elif pd.api.types.is_numeric_dtype(df[col]):
            if n_unique <= 5 and not pd.api.types.is_float_dtype(df[col]):
                sem_type = "Ordinal"
                reason = "Low-cardinality ordered discrete integer feature"
            else:
                sem_type = "Numerical"
                reason = "Continuous numerical measurement"

        # 7. Text vs Categorical Check
        elif dtype_str == "object":
            avg_len = series.astype(str).str.len().mean() if not series.empty else 0
            if avg_len > 35:
                sem_type = "Text"
                reason = "Free-form text attribute (high string length)"
            else:
                sem_type = "Categorical"
                reason = "Discrete categorical labels"

        semantics[col] = {
            "column_name": col_str,
            "semantic_type": sem_type,
            "ignored_for_analysis": ignored,
            "reason": reason,
        }

    return semantics

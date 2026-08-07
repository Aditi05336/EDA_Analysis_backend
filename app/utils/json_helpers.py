"""
Utilities to make numpy / pandas objects safe for json.dumps / jsonify.

Pandas and numpy return types (np.int64, np.float64, np.bool_, NaN, Inf,
Timestamps) that the standard json module cannot serialize. This module
recursively sanitizes any nested dict/list/value structure before it is
returned to the client.
"""

import math
import numpy as np
import pandas as pd


def sanitize(obj):
    """Recursively convert a value (or nested structure) into JSON-safe
    native Python types.

    - numpy scalars -> native int/float/bool
    - NaN / Inf / -Inf -> None (valid JSON has no concept of these)
    - pandas Timestamp / NaT -> ISO string / None
    - dict / list / tuple -> recursively sanitized
    """
    if obj is None:
        return None

    if isinstance(obj, dict):
        return {str(_sanitize_key(k)): sanitize(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [sanitize(v) for v in obj]

    if isinstance(obj, (np.integer,)):
        return int(obj)

    if isinstance(obj, (np.floating,)):
        val = float(obj)
        return None if (math.isnan(val) or math.isinf(val)) else val

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())

    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()

    if obj is pd.NaT:
        return None

    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj

    return obj


def _sanitize_key(key):
    """Dict keys must be strings in JSON; numpy/pandas keys need casting too."""
    if isinstance(key, (np.integer,)):
        return int(key)
    if isinstance(key, (np.floating,)):
        return float(key)
    return key

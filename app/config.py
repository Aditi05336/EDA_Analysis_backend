import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    """Central configuration for the Flask app."""

    BASE_DIR = BASE_DIR
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    CHARTS_FOLDER = os.path.join(BASE_DIR, "app", "static", "charts")

    # Neon Database URL
    NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

    # Firebase Service Account Path
    FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")

    # Secret key
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Only CSV accepted in this phase.
    ALLOWED_EXTENSIONS = {"csv"}

    # 25 MB max upload size — guards against memory blowups on read_csv.
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024

    # Cap on rows sampled for expensive per-cell operations (e.g. correlation
    # on very wide/long files). None = no cap.
    MAX_ROWS_FOR_CORRELATION = 200_000

    # Threshold above which a column is flagged "high cardinality"
    # (unique values / total rows).
    HIGH_CARDINALITY_RATIO = 0.5

    # Number of top categories to report per categorical column.
    TOP_N_CATEGORIES = 10

    # Correlation strength thresholds.
    STRONG_CORR_THRESHOLD = 0.7
    MODERATE_CORR_THRESHOLD = 0.4
    WEAK_CORR_THRESHOLD = 0.2

    # Target column keywords for auto-detection.
    TARGET_KEYWORDS = {
        "target",
        "label",
        "class",
        "survived",
        "purchased",
        "price",
        "outcome",
        "churn",
        "status",
        "default",
    }

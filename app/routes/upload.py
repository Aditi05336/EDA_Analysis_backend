import pandas as pd
from flask import Blueprint, request, jsonify, g

from app.utils.validators import (
    validate_file_present,
    validate_extension,
    validate_dataframe_not_empty,
    ValidationError,
)
from app.utils.file_handler import save_upload, cleanup_file
from app.utils.json_helpers import sanitize
from app.services.eda_engine import run_full_eda
from app.auth.middleware import require_auth

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@upload_bp.route("/upload", methods=["POST"])
@require_auth
def upload_csv():
    """
    Accepts multipart/form-data with a 'file' field containing a CSV.
    Protected by Firebase Bearer Token authentication (@require_auth).
    Returns a full structured EDA report as JSON.
    """
    file_path = None
    try:
        file = validate_file_present(request.files)
        validate_extension(file.filename)

        file_path = save_upload(file)

        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            raise ValidationError("CSV file is empty.")
        except pd.errors.ParserError as e:
            raise ValidationError(f"Could not parse CSV: {e}")
        except UnicodeDecodeError:
            raise ValidationError(
                "Could not decode file. Ensure it is UTF-8 encoded CSV."
            )

        validate_dataframe_not_empty(df)

        result = run_full_eda(df)

        return jsonify(sanitize(result)), 200

    except ValidationError as ve:
        return jsonify({"error": ve.message}), ve.status_code

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        cleanup_file(file_path)

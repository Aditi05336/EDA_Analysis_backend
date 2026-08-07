"""
Request-level validation for the upload endpoint.

Kept separate from routes so validation rules can be unit-tested and
reused without spinning up Flask's request context logic repeatedly.
"""

from app.config import Config


class ValidationError(Exception):
    """Raised for any client-input problem. Carries an HTTP status code
    so the route layer can translate it directly into a response."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def validate_file_present(request_files):
    if "file" not in request_files:
        raise ValidationError(
            "No file part in request. Expected multipart/form-data with key 'file'."
        )
    file = request_files["file"]
    if file.filename == "":
        raise ValidationError("No file selected.")
    return file


def validate_extension(filename):
    if "." not in filename:
        raise ValidationError("File has no extension.")
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in Config.ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '.{ext}'. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}."
        )
    return ext


def validate_dataframe_not_empty(df):
    if df is None or df.shape[0] == 0:
        raise ValidationError("Uploaded CSV contains no rows.")
    if df.shape[1] == 0:
        raise ValidationError("Uploaded CSV contains no columns.")

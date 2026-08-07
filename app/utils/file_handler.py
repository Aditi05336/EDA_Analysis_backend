import os
import uuid
from werkzeug.utils import secure_filename

from app.config import Config


def save_upload(file_storage):
    """Save an incoming FileStorage to the uploads folder with a unique,
    sanitized filename. Returns the full path on disk.

    A UUID prefix avoids collisions when two users upload files with the
    same name concurrently.
    """
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    safe_name = secure_filename(file_storage.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    full_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)

    file_storage.save(full_path)
    return full_path


def cleanup_file(path):
    """Best-effort delete of a temp file. Never raises — cleanup failures
    shouldn't crash a request that already produced a valid response."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass

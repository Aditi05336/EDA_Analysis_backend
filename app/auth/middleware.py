from functools import wraps
from flask import request, jsonify, g
from app.auth.firebase_admin import verify_id_token
from app.database.models import get_or_create_user
import logging

logger = logging.getLogger(__name__)


def require_auth(f):
    """
    Decorator to protect Flask endpoints.
    Verifies Bearer Firebase ID Token in Authorization header,
    ensures email is verified, syncs user with Neon DB, and sets g.user.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({
                "status": "error",
                "message": "Missing Authorization header. Authentication required."
            }), 401

        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({
                "status": "error",
                "message": "Invalid Authorization header format. Expected 'Bearer <id_token>'."
            }), 401

        token = parts[1]
        try:
            decoded_token = verify_id_token(token)
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")
            name = decoded_token.get("name") or decoded_token.get("display_name")
            email_verified = decoded_token.get("email_verified", False)

            if not email_verified:
                return jsonify({
                    "status": "error",
                    "message": "Email address not verified. Please check your inbox and verify your email."
                }), 403

            # Sync user profile with Neon Database
            db_user = get_or_create_user(firebase_uid=uid, email=email, name=name)

            # Store in Flask global context
            g.user = db_user
            g.firebase_claims = decoded_token

        except ValueError as ve:
            return jsonify({
                "status": "error",
                "message": f"Authentication failed: {str(ve)}"
            }), 401
        except Exception as e:
            logger.error(f"Authentication error in middleware: {e}")
            return jsonify({
                "status": "error",
                "message": "Authentication failed. Invalid or expired token."
            }), 401

        return f(*args, **kwargs)

    return decorated_function

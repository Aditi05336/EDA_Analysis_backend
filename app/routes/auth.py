from flask import Blueprint, jsonify, g, request
from app.auth.middleware import require_auth
from app.database.models import get_or_create_user, get_user_by_firebase_uid
import logging

from app.utils.email_validator import validate_email_domain

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/validate-email", methods=["POST"])
def validate_email_endpoint():
    """
    Validates email format and verifies domain DNS existence.
    Public endpoint used before account creation or authentication.
    """
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip()
        if not email or not validate_email_domain(email):
            return jsonify({
                "status": "error",
                "valid": False,
                "message": "Invalid email address."
            }), 400

        return jsonify({
            "status": "success",
            "valid": True,
            "message": "Email address and domain are valid."
        }), 200
    except Exception as e:
        logger.error(f"Error in validate_email_endpoint: {e}")
        return jsonify({
            "status": "error",
            "valid": False,
            "message": "Invalid email address."
        }), 400


@auth_bp.route("/sync", methods=["POST"])
@require_auth
def sync_user():
    """
    Synchronizes the authenticated Firebase user with the Neon PostgreSQL DB.
    Triggered by the frontend upon successful login/signup.
    """
    try:
        user = g.user
        return jsonify({
            "status": "success",
            "message": "User synchronized successfully with Neon DB.",
            "user": {
                "id": str(user["id"]),
                "firebase_uid": user["firebase_uid"],
                "name": user["name"],
                "email": user["email"],
                "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
            }
        }), 200
    except Exception as e:
        logger.error(f"Error in sync_user endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_current_user():
    """Returns profile information for the currently authenticated user."""
    try:
        user = g.user
        return jsonify({
            "status": "success",
            "user": {
                "id": str(user["id"]),
                "firebase_uid": user["firebase_uid"],
                "name": user["name"],
                "email": user["email"],
                "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
            }
        }), 200
    except Exception as e:
        logger.error(f"Error in get_current_user endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

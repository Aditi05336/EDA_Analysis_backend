from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config
from app.routes.upload import upload_bp
from app.routes.auth import auth_bp
from app.database.models import init_db
from app.auth.firebase_admin import init_firebase_admin
import logging

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for frontend client requests
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize Firebase Admin SDK & Neon Database
    try:
        init_firebase_admin()
        init_db()
    except Exception as e:
        logger.error(f"Error during app initialization: {e}")

    # Register Blueprints
    app.register_blueprint(upload_bp, url_prefix="/api")
    app.register_blueprint(auth_bp)

    @app.route("/")
    def index():
        return jsonify({
            "status": "ok",
            "message": "EDA Engine Backend API & Auth Portal running.",
            "endpoints": {
                "health": "/api/health",
                "upload": "/api/upload [POST]",
                "auth_sync": "/api/auth/sync [POST]",
                "auth_me": "/api/auth/me [GET]",
            }
        }), 200

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "healthy",
            "service": "Automated EDA Backend Engine",
            "version": "1.0.0"
        }), 200

    @app.errorhandler(413)
    def file_too_large(e):
        return {"error": "File too large. Max size is 25MB."}, 413

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Endpoint not found."}, 404

    return app

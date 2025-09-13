from flask import Blueprint, jsonify
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Create Blueprint for basic routes
basic_bp = Blueprint("basic", __name__)


@basic_bp.route("/")
def hello_world():
    logger.info("📍 Root endpoint accessed")
    return jsonify(
        {
            "message": "Hello World from Python Backend!",
            "status": "success",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@basic_bp.route("/api/health")
def health_check():
    logger.info("🏥 Health check endpoint accessed")
    return jsonify(
        {
            "status": "healthy",
            "service": "OpenVibe Backend",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@basic_bp.route("/api/hello")
def api_hello():
    logger.info("👋 Hello API endpoint accessed")
    return jsonify(
        {
            "message": "Hello from the API!",
            "endpoint": "/api/hello",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

from flask import Blueprint, jsonify, request
import logging
from services.integrations_service import integrations_service

logger = logging.getLogger(__name__)

# Create Blueprint for integrations
integrations_bp = Blueprint("integrations", __name__)

# Store API keys in memory (in production, use a secure storage solution)
api_keys = {"anthropic": None, "github": None, "fly": None}


@integrations_bp.route("/api/integrations/<provider>", methods=["POST"])
def set_api_key(provider):
    """Set API key for a provider"""
    logger.info(f"🔑 POST /api/integrations/{provider} - Setting API key")
    logger.debug(f"📥 Request headers: {dict(request.headers)}")
    logger.debug(f"📥 Request remote addr: {request.remote_addr}")
    logger.debug(
        f"📥 Request user agent: {request.headers.get('User-Agent', 'Unknown')}"
    )

    # Get UUID from headers
    user_uuid = request.headers.get("X-User-UUID")
    logger.debug(f"🆔 Raw UUID from header: '{user_uuid}'")

    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        logger.debug(f"📋 Available headers: {list(request.headers.keys())}")
        return jsonify({"error": "X-User-UUID header is required"}), 400

    user_uuid = user_uuid.strip()
    logger.debug(f"🆔 Cleaned UUID: '{user_uuid}' (length: {len(user_uuid)})")

    if not user_uuid:
        logger.warning("❌ Empty UUID provided in header")
        return jsonify({"error": "UUID cannot be empty"}), 400

    data = request.get_json()
    if not data or "api_key" not in data:
        logger.warning("❌ API key is required in request body")
        return jsonify({"error": "API key is required"}), 400

    api_key = data["api_key"].strip()
    if not api_key:
        logger.warning("❌ Empty API key provided")
        return jsonify({"error": "API key cannot be empty"}), 400

    # Use service layer to set API key
    success, result = integrations_service.set_api_key(user_uuid, provider, api_key)

    if success:
        # Also store in memory for backward compatibility
        api_keys[provider] = api_key
        return jsonify(result)
    else:
        status_code = 500 if "Failed to save" in result.get("message", "") else 400
        return jsonify(result), status_code


@integrations_bp.route("/api/integrations/<provider>", methods=["GET"])
def check_api_key(provider):
    """Check if API key is set and valid for a provider"""
    logger.info(f"🔍 GET /api/integrations/{provider} - Checking API key status")

    # Get UUID from headers
    user_uuid = request.headers.get("X-User-UUID")
    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        return jsonify({"error": "X-User-UUID header is required"}), 400

    user_uuid = user_uuid.strip()
    if not user_uuid:
        logger.warning("❌ Empty UUID provided in header")
        return jsonify({"error": "UUID cannot be empty"}), 400

    # Use service layer to check API key
    success, result = integrations_service.check_api_key(user_uuid, provider)

    if success:
        return jsonify(result)
    else:
        return jsonify(result), 400

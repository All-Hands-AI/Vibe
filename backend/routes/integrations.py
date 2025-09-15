from flask import Blueprint, jsonify, request
import logging
from keys import (
    load_user_keys,
    save_user_keys,
    user_has_keys,
    validate_api_key,
    get_supported_providers,
    is_valid_provider,
)

logger = logging.getLogger(__name__)

# Create Blueprint for integrations
integrations_bp = Blueprint("integrations", __name__)

# Store API keys in memory (in production, use a secure storage solution)
api_keys = {"anthropic": None, "github": None, "fly": None}


@integrations_bp.route("/integrations/<provider>", methods=["POST"])
def set_api_key(provider):
    """Set API key for a provider"""
    logger.info(f"🔑 POST /integrations/{provider} - Setting API key")
    logger.debug(f"📥 Request headers: {dict(request.headers)}")
    logger.debug(f"📥 Request remote addr: {request.remote_addr}")
    logger.debug(
        f"📥 Request user agent: {request.headers.get('User-Agent', 'Unknown')}"
    )

    if not is_valid_provider(provider):
        logger.warning(f"❌ Invalid provider requested: {provider}")
        logger.debug(f"📋 Valid providers: {get_supported_providers()}")
        return jsonify({"error": "Invalid provider"}), 400

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

    logger.debug(f"🔍 Validating {provider} API key for user {user_uuid[:8]}...")

    # Validate the API key using the keys module
    is_valid = validate_api_key(provider, api_key)

    if is_valid:
        # Load existing keys for this user
        user_keys = load_user_keys(user_uuid)
        user_keys[provider] = api_key

        # Save to file
        if save_user_keys(user_uuid, user_keys):
            # Also store in memory for backward compatibility
            api_keys[provider] = api_key
            logger.info(
                f"✅ {provider} API key validated and stored for user {user_uuid[:8]}"
            )
            return jsonify(
                {"valid": True, "message": f"{provider.title()} API key is valid"}
            )
        else:
            logger.error(
                f"❌ Failed to save {provider} API key for user {user_uuid[:8]}"
            )
            return jsonify({"valid": False, "message": "Failed to save API key"}), 500
    else:
        logger.warning(
            f"❌ {provider} API key validation failed for user {user_uuid[:8]}"
        )
        return (
            jsonify(
                {"valid": False, "message": f"{provider.title()} API key is invalid"}
            ),
            400,
        )


@integrations_bp.route("/integrations/<provider>", methods=["GET"])
def check_api_key(provider):
    """Check if API key is set and valid for a provider"""
    logger.info(f"🔍 GET /integrations/{provider} - Checking API key status")

    if not is_valid_provider(provider):
        logger.warning(f"❌ Invalid provider requested: {provider}")
        return jsonify({"error": "Invalid provider"}), 400

    # Get UUID from headers
    user_uuid = request.headers.get("X-User-UUID")
    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        return jsonify({"error": "X-User-UUID header is required"}), 400

    user_uuid = user_uuid.strip()
    if not user_uuid:
        logger.warning("❌ Empty UUID provided in header")
        return jsonify({"error": "UUID cannot be empty"}), 400

    logger.debug(f"🔍 Checking {provider} API key status for user {user_uuid[:8]}...")

    # Check if user has keys file
    if not user_has_keys(user_uuid):
        logger.debug(f"⚠️ No keys file found for user {user_uuid[:8]}")
        return jsonify(
            {"valid": False, "message": f"{provider.title()} API key not set"}
        )

    # Load user's keys
    user_keys = load_user_keys(user_uuid)
    api_key = user_keys.get(provider)

    if not api_key:
        logger.debug(f"⚠️ {provider} API key not set for user {user_uuid[:8]}")
        return jsonify(
            {"valid": False, "message": f"{provider.title()} API key not set"}
        )

    logger.debug(
        f"🔍 Re-validating stored {provider} API key for user {user_uuid[:8]}..."
    )

    # Re-validate the stored key using the keys module
    is_valid = validate_api_key(provider, api_key)

    result = {
        "valid": is_valid,
        "message": f'{provider.title()} API key is {"valid" if is_valid else "invalid"}',
    }

    logger.info(
        f"📊 {provider} API key check result for user {user_uuid[:8]}: {result}"
    )
    return jsonify(result)

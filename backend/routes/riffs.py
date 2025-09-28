from flask import Blueprint, jsonify, request
import logging
from services.riffs_service import riffs_service
from utils.logging import log_api_request, log_api_response

logger = logging.getLogger(__name__)

# Create Blueprint for riffs
riffs_bp = Blueprint("riffs", __name__)


def get_user_uuid_from_request():
    """Helper function to extract and validate user UUID from request headers."""
    user_uuid = request.headers.get("X-User-UUID")
    if not user_uuid:
        return None, jsonify({"error": "X-User-UUID header is required"}), 400

    user_uuid = user_uuid.strip()
    if not user_uuid:
        return None, jsonify({"error": "UUID cannot be empty"}), 400

    return user_uuid, None, None


@riffs_bp.route("/api/apps/<slug>/riffs", methods=["GET"])
def get_riffs(slug):
    """Get all riffs for a specific app"""
    logger.info(f"📋 GET /api/apps/{slug}/riffs - Fetching riffs")

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        logger.debug(f"📋 Loading riffs for app {slug} for user {user_uuid[:8]}...")

        # Load riffs using service layer
        riffs = riffs_service.load_user_riffs(user_uuid, slug)

        logger.info(f"✅ Loaded {len(riffs)} riffs for app {slug}")
        return jsonify({"riffs": riffs})

    except Exception as e:
        logger.error(f"💥 Error loading riffs: {str(e)}")
        return jsonify({"error": "Failed to load riffs"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs", methods=["POST"])
def create_riff(slug):
    """Create a new riff for a specific app"""
    logger.info(f"🆕 POST /api/apps/{slug}/riffs - Creating new riff")

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        # Get riff name from request body
        data = request.get_json()
        if not data or "name" not in data:
            logger.warning("❌ Riff name is required in request body")
            return jsonify({"error": "Riff name is required"}), 400

        riff_name = data["name"]
        logger.debug(f"🆕 Creating riff: {riff_name} for app {slug}")

        # Create riff using service layer
        success, result = riffs_service.create_riff(user_uuid, slug, riff_name)

        if success:
            logger.info(f"✅ Riff created successfully: {result['riff']['slug']}")
            return jsonify(result), 201
        else:
            logger.error(
                f"❌ Riff creation failed: {result.get('error', 'Unknown error')}"
            )
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"💥 Error creating riff: {str(e)}")
        return jsonify({"error": "Failed to create riff"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/messages", methods=["GET"])
def get_messages(slug, riff_slug):
    """Get all messages for a specific riff"""
    logger.info(
        f"📋 GET /api/apps/{slug}/riffs/{riff_slug}/messages - Fetching messages"
    )

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        logger.debug(
            f"📋 Loading messages for riff {riff_slug} for user {user_uuid[:8]}..."
        )

        # Load messages using service layer
        messages = riffs_service.load_user_messages(user_uuid, slug, riff_slug)

        logger.info(f"✅ Loaded {len(messages)} messages for riff {riff_slug}")
        return jsonify({"messages": messages})

    except Exception as e:
        logger.error(f"💥 Error loading messages: {str(e)}")
        return jsonify({"error": "Failed to load messages"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/messages", methods=["POST"])
def create_message(slug):
    """Create a new message for a specific riff"""
    logger.info(f"🆕 POST /api/apps/{slug}/riffs/messages - Creating new message")

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        # Get message data from request body
        data = request.get_json()
        if not data:
            logger.warning("❌ Request body is required")
            return jsonify({"error": "Request body is required"}), 400

        if "content" not in data:
            logger.warning("❌ Message content is required")
            return jsonify({"error": "Message content is required"}), 400

        if "riff_slug" not in data:
            logger.warning("❌ Riff slug is required")
            return jsonify({"error": "Riff slug is required"}), 400

        content = data["content"]
        riff_slug = data["riff_slug"]

        logger.debug(f"🆕 Creating message for riff {riff_slug} in app {slug}")

        # Send message using service layer
        success, result = riffs_service.send_message(
            user_uuid, slug, riff_slug, content
        )

        if success:
            logger.info(f"✅ Message sent successfully to riff {riff_slug}")
            return jsonify(result), 201
        else:
            logger.error(
                f"❌ Message sending failed: {result.get('error', 'Unknown error')}"
            )
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"💥 Error creating message: {str(e)}")
        return jsonify({"error": "Failed to create message"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/ready", methods=["GET"])
def check_riff_ready(slug, riff_slug):
    """Check if an agent is ready for a specific riff"""
    log_api_request(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/ready")

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        # Check agent readiness using service layer
        success, result = riffs_service.check_agent_ready(user_uuid, slug, riff_slug)

        if success:
            log_api_response(logger, result)
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"💥 Error checking riff readiness: {str(e)}")
        return jsonify({"error": "Failed to check riff readiness"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/reset", methods=["POST"])
def reset_riff_llm(slug, riff_slug):
    """Reset the agent for a specific riff by creating a brand new one"""
    log_api_request(logger, "POST", f"/api/apps/{slug}/riffs/{riff_slug}/reset")

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        # Reset agent using service layer
        success, result = riffs_service.reset_agent(user_uuid, slug, riff_slug)

        if success:
            log_api_response(logger, result)
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"💥 Error resetting riff agent: {str(e)}")
        return jsonify({"error": "Failed to reset riff agent"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/status", methods=["GET"])
def get_agent_status(slug, riff_slug):
    """Get the current status of the agent for a specific riff"""
    log_api_request(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/status")

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        # Get agent status using service layer
        success, result = riffs_service.get_agent_status(user_uuid, slug, riff_slug)

        if success:
            log_api_response(logger, result)
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"💥 Error getting agent status: {str(e)}")
        return jsonify({"error": "Failed to get agent status"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/play", methods=["POST"])
def play_agent(slug, riff_slug):
    """Resume/play the agent for a specific riff"""
    log_api_request(logger, "POST", f"/api/apps/{slug}/riffs/{riff_slug}/play")

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        # Play agent using service layer
        success, result = riffs_service.play_agent(user_uuid, slug, riff_slug)

        if success:
            log_api_response(logger, result)
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"💥 Error playing agent: {str(e)}")
        return jsonify({"error": "Failed to play agent"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/pause", methods=["POST"])
def pause_agent(slug, riff_slug):
    """Pause the agent for a specific riff"""
    log_api_request(logger, "POST", f"/api/apps/{slug}/riffs/{riff_slug}/pause")

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        # Pause agent using service layer
        success, result = riffs_service.pause_agent(user_uuid, slug, riff_slug)

        if success:
            log_api_response(logger, result)
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"💥 Error pausing agent: {str(e)}")
        return jsonify({"error": "Failed to pause agent"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/pr-status", methods=["GET"])
def get_riff_pr_status(slug, riff_slug):
    """Get GitHub Pull Request status for a specific riff (using riff name as branch)"""
    log_api_request(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/pr-status")

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        # Get PR status using service layer
        success, result = riffs_service.get_pr_status(user_uuid, slug, riff_slug)

        if success:
            log_api_response(logger, result)
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"💥 Error getting PR status: {str(e)}")
        return jsonify({"error": "Failed to get PR status"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>", methods=["DELETE"])
def delete_riff(slug, riff_slug):
    """Delete a riff and its associated resources"""
    logger.info(f"🗑️ DELETE /api/apps/{slug}/riffs/{riff_slug} - Deleting riff")

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        # Delete riff using service layer
        success, result = riffs_service.delete_riff(user_uuid, slug, riff_slug)

        if success:
            logger.info(f"✅ Riff deletion completed: {riff_slug}")
            return jsonify(result)
        else:
            status_code = 404 if "not found" in result.get("error", "").lower() else 500
            return jsonify(result), status_code

    except Exception as e:
        logger.error(f"💥 Error deleting riff: {str(e)}")
        return jsonify({"error": "Failed to delete riff"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/deployment", methods=["GET"])
def get_riff_deployment_status(slug, riff_slug):
    """Get deployment status for a riff (checks riff branch)"""
    logger.info(
        f"🚀 GET /api/apps/{slug}/riffs/{riff_slug}/deployment - Getting riff deployment status"
    )

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        # Get deployment status using service layer
        success, result = riffs_service.get_deployment_status(
            user_uuid, slug, riff_slug
        )

        if success:
            return jsonify(result)
        else:
            status_code = 404 if "not found" in result.get("error", "").lower() else 500
            return jsonify(result), status_code

    except Exception as e:
        logger.error(f"💥 Error getting riff deployment status: {str(e)}")
        return jsonify({"error": "Failed to get deployment status"}), 500


@riffs_bp.route("/api/runtime/status", methods=["GET"])
def get_runtime_api_status():
    """Get the status of the runtime API service"""
    log_api_request(logger, "GET", "/api/runtime/status")

    try:
        # Get global runtime status using service layer
        success, result = riffs_service.get_global_runtime_status()

        if success:
            log_api_response(logger, result)
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"💥 Error getting runtime API status: {str(e)}")
        return jsonify({"error": "Failed to get runtime API status"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/runtime/status", methods=["GET"])
def get_riff_runtime_status(slug, riff_slug):
    """Get the runtime status for a specific riff"""
    log_api_request(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/runtime/status")

    try:
        # Get UUID from headers
        user_uuid, error_response, status_code = get_user_uuid_from_request()
        if error_response:
            return error_response, status_code

        # Get runtime status using service layer
        success, result = riffs_service.get_runtime_status(user_uuid, slug, riff_slug)

        if success:
            log_api_response(logger, result)
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"💥 Error getting riff runtime status: {str(e)}")
        return jsonify({"error": "Failed to get riff runtime status"}), 500


# Legacy functions for backward compatibility - these are now handled by the service layer
def load_user_riffs(user_uuid, app_slug):
    """Load riffs for a specific user and app - DEPRECATED"""
    logger.warning("⚠️ Using deprecated load_user_riffs() function")
    return riffs_service.load_user_riffs(user_uuid, app_slug)


def load_user_riff(user_uuid, app_slug, riff_slug):
    """Load specific riff for a user - DEPRECATED"""
    logger.warning("⚠️ Using deprecated load_user_riff() function")
    return riffs_service.load_user_riff(user_uuid, app_slug, riff_slug)


def save_user_riff(user_uuid, app_slug, riff_slug, riff_data):
    """Save riff for a specific user - DEPRECATED"""
    logger.warning("⚠️ Using deprecated save_user_riff() function")
    return riffs_service.save_user_riff(user_uuid, app_slug, riff_slug, riff_data)


def user_riff_exists(user_uuid, app_slug, riff_slug):
    """Check if riff exists for user - DEPRECATED"""
    logger.warning("⚠️ Using deprecated user_riff_exists() function")
    return riffs_service.user_riff_exists(user_uuid, app_slug, riff_slug)


def delete_user_riff(user_uuid, app_slug, riff_slug):
    """Delete riff for a specific user - DEPRECATED"""
    logger.warning("⚠️ Using deprecated delete_user_riff() function")
    return riffs_service.delete_user_riff(user_uuid, app_slug, riff_slug)


def create_slug(name):
    """Convert riff name to slug format - DEPRECATED"""
    logger.warning("⚠️ Using deprecated create_slug() function")
    return riffs_service.create_slug(name)


def is_valid_slug(slug):
    """Validate that a slug contains only lowercase letters, numbers, and hyphens - DEPRECATED"""
    logger.warning("⚠️ Using deprecated is_valid_slug() function")
    return riffs_service.is_valid_slug(slug)


def load_user_messages(user_uuid, app_slug, riff_slug):
    """Load messages for a specific riff - DEPRECATED"""
    logger.warning("⚠️ Using deprecated load_user_messages() function")
    return riffs_service.load_user_messages(user_uuid, app_slug, riff_slug)


def create_agent_for_user(user_uuid, app_slug, riff_slug):
    """Create a new agent for a user's riff - DEPRECATED"""
    logger.warning("⚠️ Using deprecated create_agent_for_user() function")
    return riffs_service.create_agent_for_user(user_uuid, app_slug, riff_slug)


def reconstruct_agent_from_state(user_uuid, app_slug, riff_slug):
    """Reconstruct an Agent object from existing serialized state - DEPRECATED"""
    logger.warning("⚠️ Using deprecated reconstruct_agent_from_state() function")
    return riffs_service.reconstruct_agent_from_state(user_uuid, app_slug, riff_slug)


def get_llm_instance(api_key, model="claude-sonnet-4-20250514"):
    """Get the appropriate LLM instance - DEPRECATED"""
    logger.warning("⚠️ Using deprecated get_llm_instance() function")
    return riffs_service.get_llm_instance(api_key, model)

from flask import Blueprint, jsonify, request
import logging
import re
from datetime import datetime, timezone
from storage import get_riffs_storage, get_apps_storage, get_messages_storage
from agent_loop import agent_loop_manager
from keys import get_user_key
from openhands.sdk import LLM

logger = logging.getLogger(__name__)

# Create Blueprint for riffs
riffs_bp = Blueprint("riffs", __name__)


def load_user_riffs(user_uuid, app_slug):
    """Load riffs for a specific app and user"""
    storage = get_riffs_storage(user_uuid)
    return storage.list_riffs(app_slug)


def load_user_riff(user_uuid, app_slug, riff_slug):
    """Load specific riff for a user"""
    storage = get_riffs_storage(user_uuid)
    return storage.load_riff(app_slug, riff_slug)


def save_user_riff(user_uuid, app_slug, riff_slug, riff_data):
    """Save riff for a specific user"""
    storage = get_riffs_storage(user_uuid)
    return storage.save_riff(app_slug, riff_slug, riff_data)


def user_riff_exists(user_uuid, app_slug, riff_slug):
    """Check if riff exists for user"""
    storage = get_riffs_storage(user_uuid)
    return storage.riff_exists(app_slug, riff_slug)


def delete_user_riff(user_uuid, app_slug, riff_slug):
    """Delete riff for a specific user"""
    storage = get_riffs_storage(user_uuid)
    return storage.delete_riff(app_slug, riff_slug)


def user_app_exists(user_uuid, app_slug):
    """Check if app exists for user"""
    storage = get_apps_storage(user_uuid)
    return storage.app_exists(app_slug)


# Legacy functions for backward compatibility during migration
def load_apps():
    """Load apps from legacy file - DEPRECATED"""
    logger.warning("⚠️ Using deprecated load_apps() function in riffs.py")
    return []


def load_riffs(app_slug):
    """Load riffs from legacy file - DEPRECATED"""
    logger.warning("⚠️ Using deprecated load_riffs() function")
    return []


def save_riffs(app_slug, riffs):
    """Save riffs to legacy file - DEPRECATED"""
    logger.warning("⚠️ Using deprecated save_riffs() function")
    return False


def create_slug(name):
    """Convert riff name to slug format"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


@riffs_bp.route("/api/apps/<slug>/riffs", methods=["GET"])
def get_riffs(slug):
    """Get all riffs for a specific app"""
    logger.info(f"📋 GET /api/apps/{slug}/riffs - Fetching riffs")

    try:
        # Get UUID from headers
        user_uuid = request.headers.get("X-User-UUID")
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            return jsonify({"error": "X-User-UUID header is required"}), 400

        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({"error": "UUID cannot be empty"}), 400

        # Verify app exists for this user
        if not user_app_exists(user_uuid, slug):
            logger.warning(f"❌ App not found: {slug} for user {user_uuid[:8]}")
            return jsonify({"error": "App not found"}), 404

        riffs = load_user_riffs(user_uuid, slug)
        # Sort riffs by creation date (newest first)
        riffs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        logger.info(
            f"📊 Returning {len(riffs)} riffs for app {slug} for user {user_uuid[:8]}"
        )
        return jsonify({"riffs": riffs, "count": len(riffs), "app_slug": slug})
    except Exception as e:
        logger.error(f"💥 Error fetching riffs: {str(e)}")
        return jsonify({"error": "Failed to fetch riffs"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs", methods=["POST"])
def create_riff(slug):
    """Create a new riff for a specific app"""
    logger.info(f"🆕 POST /api/apps/{slug}/riffs - Creating new riff")

    try:
        # Get UUID from headers
        user_uuid = request.headers.get("X-User-UUID")
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            return jsonify({"error": "X-User-UUID header is required"}), 400

        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({"error": "UUID cannot be empty"}), 400

        # Verify app exists for this user
        if not user_app_exists(user_uuid, slug):
            logger.warning(f"❌ App not found: {slug} for user {user_uuid[:8]}")
            return jsonify({"error": "App not found"}), 404

        # Get request data
        data = request.get_json()
        if not data or "name" not in data:
            logger.warning("❌ Riff name is required")
            return jsonify({"error": "Riff name is required"}), 400

        riff_name = data["name"].strip()
        if not riff_name:
            logger.warning("❌ Riff name cannot be empty")
            return jsonify({"error": "Riff name cannot be empty"}), 400

        # Create slug from name (use provided slug if available, otherwise generate)
        riff_slug = data.get("slug", create_slug(riff_name)).strip()
        if not riff_slug:
            riff_slug = create_slug(riff_name)

        if not riff_slug:
            logger.warning("❌ Invalid riff name - cannot create slug")
            return jsonify({"error": "Invalid riff name"}), 400

        logger.info(
            f"🔄 Creating riff: {riff_name} -> {riff_slug} for user {user_uuid[:8]}"
        )

        # Check if riff with same slug already exists for this user
        if user_riff_exists(user_uuid, slug, riff_slug):
            logger.warning(
                f"❌ Riff with slug '{riff_slug}' already exists for user {user_uuid[:8]}"
            )
            return (
                jsonify({"error": f'Riff with name "{riff_name}" already exists'}),
                409,
            )

        # Create riff record
        riff = {
            "slug": riff_slug,
            "name": riff_name,
            "app_slug": slug,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_uuid,
            "last_message_at": None,
            "message_count": 0,
        }

        # Save riff for this user
        if not save_user_riff(user_uuid, slug, riff_slug, riff):
            logger.error("❌ Failed to save riff to file")
            return jsonify({"error": "Failed to save riff"}), 500

        # Create AgentLoop with user's Anthropic token
        try:
            anthropic_token = get_user_key(user_uuid, "anthropic")
            if not anthropic_token:
                logger.warning(f"⚠️ No Anthropic token found for user {user_uuid[:8]}")
                return jsonify({"error": "Anthropic API key required"}), 400
            
            # Create LLM instance
            try:
                llm = LLM(api_key=anthropic_token, model="claude-3-haiku-20240307")
                
                # Create and store the agent loop
                agent_loop_manager.create_agent_loop(user_uuid, slug, riff_slug, llm)
                logger.info(f"🤖 Created AgentLoop for riff: {riff_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create LLM instance: {e}")
                return jsonify({"error": "Failed to initialize LLM"}), 500
                
        except Exception as e:
            logger.error(f"❌ Failed to create AgentLoop: {e}")
            # Don't fail the riff creation if AgentLoop creation fails
            # The riff is still created, just without the agent loop
            logger.warning("⚠️ Riff created but AgentLoop creation failed")

        logger.info(f"✅ Riff created successfully: {riff_name}")
        return jsonify({"message": "Riff created successfully", "riff": riff}), 201

    except Exception as e:
        logger.error(f"💥 Error creating riff: {str(e)}")
        return jsonify({"error": "Failed to create riff"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/messages", methods=["GET"])
def get_messages(slug, riff_slug):
    """Get all messages for a specific riff"""
    logger.info(f"💬 GET /api/apps/{slug}/riffs/{riff_slug}/messages - Fetching messages")

    try:
        # Get UUID from headers
        user_uuid = request.headers.get("X-User-UUID")
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            return jsonify({"error": "X-User-UUID header is required"}), 400

        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({"error": "UUID cannot be empty"}), 400

        # Verify app exists for this user
        if not user_app_exists(user_uuid, slug):
            logger.warning(f"❌ App not found: {slug} for user {user_uuid[:8]}")
            return jsonify({"error": "App not found"}), 404

        # Verify riff exists for this user
        if not user_riff_exists(user_uuid, slug, riff_slug):
            logger.warning(f"❌ Riff not found: {slug}/{riff_slug} for user {user_uuid[:8]}")
            return jsonify({"error": "Riff not found"}), 404

        # Load messages
        messages_storage = get_messages_storage(user_uuid)
        messages = messages_storage.load_messages(slug, riff_slug)

        logger.info(
            f"📊 Returning {len(messages)} messages for riff {slug}/{riff_slug} for user {user_uuid[:8]}"
        )
        return jsonify({
            "messages": messages,
            "count": len(messages),
            "app_slug": slug,
            "riff_slug": riff_slug
        })

    except Exception as e:
        logger.error(f"💥 Error fetching messages: {str(e)}")
        return jsonify({"error": "Failed to fetch messages"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/messages", methods=["POST"])
def send_message(slug, riff_slug):
    """Send a message to the agent and get a response"""
    logger.info(f"💬 POST /api/apps/{slug}/riffs/{riff_slug}/messages - Sending message")

    try:
        # Get UUID from headers
        user_uuid = request.headers.get("X-User-UUID")
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            return jsonify({"error": "X-User-UUID header is required"}), 400

        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({"error": "UUID cannot be empty"}), 400

        # Verify app exists for this user
        if not user_app_exists(user_uuid, slug):
            logger.warning(f"❌ App not found: {slug} for user {user_uuid[:8]}")
            return jsonify({"error": "App not found"}), 404

        # Verify riff exists for this user
        if not user_riff_exists(user_uuid, slug, riff_slug):
            logger.warning(f"❌ Riff not found: {slug}/{riff_slug} for user {user_uuid[:8]}")
            return jsonify({"error": "Riff not found"}), 404

        # Get request data
        data = request.get_json()
        if not data or "content" not in data:
            logger.warning("❌ Message content is required")
            return jsonify({"error": "Message content is required"}), 400

        message_content = data["content"].strip()
        if not message_content:
            logger.warning("❌ Message content cannot be empty")
            return jsonify({"error": "Message content cannot be empty"}), 400

        # Get the agent loop
        agent_loop = agent_loop_manager.get_agent_loop(user_uuid, slug, riff_slug)
        if not agent_loop:
            logger.error(f"❌ AgentLoop not found for {user_uuid[:8]}/{slug}/{riff_slug}")
            return jsonify({"error": "Agent not available for this conversation"}), 500

        # Get messages storage
        messages_storage = get_messages_storage(user_uuid)

        # Create user message
        user_message = {
            "role": "user",
            "content": message_content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Save user message
        if not messages_storage.add_message(slug, riff_slug, user_message):
            logger.error("❌ Failed to save user message")
            return jsonify({"error": "Failed to save message"}), 500

        # Send message to LLM and get response
        try:
            logger.info(f"🤖 Sending message to LLM for {user_uuid[:8]}/{slug}/{riff_slug}")
            llm_response = agent_loop.send_message(message_content)
            
            # Create assistant message
            assistant_message = {
                "role": "assistant",
                "content": llm_response,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Save assistant message
            if not messages_storage.add_message(slug, riff_slug, assistant_message):
                logger.error("❌ Failed to save assistant message")
                return jsonify({"error": "Failed to save assistant response"}), 500

            # Update riff metadata
            riff_storage = get_riffs_storage(user_uuid)
            riff_data = riff_storage.load_riff(slug, riff_slug)
            if riff_data:
                riff_data["last_message_at"] = datetime.now(timezone.utc).isoformat()
                riff_data["message_count"] = messages_storage.get_message_count(slug, riff_slug)
                riff_storage.save_riff(slug, riff_slug, riff_data)

            logger.info(f"✅ Message exchange completed for {user_uuid[:8]}/{slug}/{riff_slug}")
            return jsonify({
                "message": "Message sent successfully",
                "user_message": user_message,
                "assistant_message": assistant_message
            }), 201

        except Exception as e:
            logger.error(f"❌ Error getting LLM response: {e}")
            return jsonify({"error": "Failed to get response from agent"}), 500

    except Exception as e:
        logger.error(f"💥 Error sending message: {str(e)}")
        return jsonify({"error": "Failed to send message"}), 500

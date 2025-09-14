from flask import Blueprint, jsonify, request
import re
import uuid
import sys
from datetime import datetime, timezone
from storage import get_riffs_storage, get_apps_storage
from agent_loop import agent_loop_manager
from keys import get_user_key, load_user_keys
from utils.repository import setup_riff_workspace
from utils.event_serializer import serialize_agent_event_to_message

import os

# Add the site-packages to the path for openhands imports
sys.path.insert(0, ".venv/lib/python3.12/site-packages")

from openhands.sdk import LLM


# Mock LLM class for testing
class MockLLM:
    def __init__(self, *args, **kwargs):
        pass

    def completion(self, messages):
        # Mock response for testing
        class MockChoice:
            def __init__(self):
                self.message = MockMessage()

        class MockMessage:
            def __init__(self):
                self.content = "Hello! This is a mock response from the LLM."

        class MockResponse:
            def __init__(self):
                self.choices = [MockChoice()]

        return MockResponse()


def get_llm_instance(api_key: str, model: str = "claude-3-haiku-20240307"):
    """Get the appropriate LLM instance based on MOCK_MODE environment variable"""
    if os.environ.get("MOCK_MODE", "false").lower() == "true":
        # In mock mode, create a real LLM instance but with a fake key
        # The actual API calls will be mocked by the mocks.py module
        return LLM(api_key="mock-key", model=model)
    else:
        # Use the real API key
        return LLM(api_key=api_key, model=model)


from utils.logging import get_logger, log_api_request, log_api_response

# Import get_pr_status from apps route for riff-specific PR status
from routes.apps import get_pr_status

logger = get_logger(__name__)

# Create Blueprint for riffs
riffs_bp = Blueprint("riffs", __name__)


def create_agent_for_user(user_uuid, app_slug, riff_slug):
    """
    Create and store an Agent object for a specific user, app, and riff.
    This function creates an AgentLoop with Agent and Conversation from openhands-sdk.

    Args:
        user_uuid: User's UUID
        app_slug: App slug identifier
        riff_slug: Riff slug identifier

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        # Get user's Anthropic token
        anthropic_token = get_user_key(user_uuid, "anthropic")
        if not anthropic_token:
            logger.warning(f"⚠️ No Anthropic token found for user {user_uuid[:8]}")
            return False, "Anthropic API key required"

        # Get app data to retrieve GitHub URL
        apps_storage = get_apps_storage(user_uuid)
        app_data = apps_storage.load_app(app_slug)
        if not app_data:
            logger.error(f"❌ App data not found for {app_slug}")
            return False, "App not found"

        github_url = app_data.get("github_url")
        if not github_url:
            logger.error(f"❌ No GitHub URL found for app {app_slug}")
            return False, "GitHub URL not configured for this app"

        # Setup workspace: create directory and clone repository
        logger.info(f"🏗️ Setting up workspace for riff {riff_slug}")
        workspace_success, workspace_path, workspace_error = setup_riff_workspace(
            user_uuid, app_slug, riff_slug, github_url
        )

        if not workspace_success:
            logger.error(f"❌ Failed to setup workspace: {workspace_error}")
            return False, f"Failed to setup workspace: {workspace_error}"

        logger.info(f"✅ Workspace ready at: {workspace_path}")

        # Create LLM instance
        try:
            llm = get_llm_instance(
                api_key=anthropic_token, model="claude-3-haiku-20240307"
            )

            # Create message callback to store events as messages
            def message_callback(event):
                """Callback to handle events from the agent conversation"""
                try:
                    logger.info(f"📨 Received event from agent: {type(event).__name__}")

                    # Serialize the event to a message format
                    serialized_message = serialize_agent_event_to_message(
                        event, user_uuid, app_slug, riff_slug
                    )

                    if serialized_message:
                        # Save the serialized message
                        if add_user_message(
                            user_uuid, app_slug, riff_slug, serialized_message
                        ):
                            logger.info(
                                f"✅ Agent event ({type(event).__name__}) saved as message for riff: {riff_slug}"
                            )

                            # Update riff message stats
                            messages = load_user_messages(
                                user_uuid, app_slug, riff_slug
                            )
                            update_riff_message_stats(
                                user_uuid,
                                app_slug,
                                riff_slug,
                                len(messages),
                                serialized_message["created_at"],
                            )
                        else:
                            logger.error(
                                f"❌ Failed to save agent event ({type(event).__name__}) for riff: {riff_slug}"
                            )
                    else:
                        logger.debug(
                            f"🔇 Event {type(event).__name__} was not serialized (likely filtered out)"
                        )

                except Exception as e:
                    logger.error(f"❌ Error in message callback: {e}")
                    import traceback

                    logger.error(f"❌ Traceback: {traceback.format_exc()}")

            # Create and store the agent loop
            logger.info(
                f"🔧 Creating AgentLoop with key: {user_uuid[:8]}:{app_slug}:{riff_slug}"
            )
            agent_loop_manager.create_agent_loop(
                user_uuid, app_slug, riff_slug, llm, workspace_path, message_callback
            )
            logger.info(f"🤖 Created AgentLoop for riff: {riff_slug}")

            # Verify it was stored correctly
            test_retrieval = agent_loop_manager.get_agent_loop(
                user_uuid, app_slug, riff_slug
            )
            if test_retrieval:
                logger.info(
                    f"✅ AgentLoop verification successful for {user_uuid[:8]}:{app_slug}:{riff_slug}"
                )
                return True, None
            else:
                logger.error(
                    f"❌ AgentLoop verification failed for {user_uuid[:8]}:{app_slug}:{riff_slug}"
                )
                return False, "Failed to verify Agent creation"

        except Exception as e:
            logger.error(f"❌ Failed to create LLM instance: {e}")
            return False, f"Failed to initialize LLM: {str(e)}"

    except Exception as e:
        logger.error(f"❌ Failed to create AgentLoop: {e}")
        return False, f"Failed to create Agent: {str(e)}"


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
        success, error_message = create_agent_for_user(user_uuid, slug, riff_slug)
        if not success:
            logger.error(f"❌ Failed to create Agent for riff: {error_message}")
            # Return 500 for git/workspace setup failures, 400 for other client errors
            status_code = (
                500
                if "git" in error_message.lower()
                or "workspace" in error_message.lower()
                else 400
            )
            return jsonify({"error": error_message}), status_code

        logger.info(f"✅ Riff created successfully: {riff_name}")
        return jsonify({"message": "Riff created successfully", "riff": riff}), 201

    except Exception as e:
        logger.error(f"💥 Error creating riff: {str(e)}")
        return jsonify({"error": "Failed to create riff"}), 500


# Message utility functions using new storage pattern
def load_user_messages(user_uuid, app_slug, riff_slug):
    """Load messages for a specific riff using storage pattern"""
    storage = get_riffs_storage(user_uuid)
    return storage.load_messages(app_slug, riff_slug)


def save_user_messages(user_uuid, app_slug, riff_slug, messages):
    """Save messages for a specific riff using storage pattern"""
    storage = get_riffs_storage(user_uuid)
    return storage.save_messages(app_slug, riff_slug, messages)


def add_user_message(user_uuid, app_slug, riff_slug, message):
    """Add a single message to a riff using storage pattern"""
    storage = get_riffs_storage(user_uuid)
    return storage.add_message(app_slug, riff_slug, message)


def update_riff_message_stats(
    user_uuid, app_slug, riff_slug, message_count, last_message_at
):
    """Update riff statistics with message count and last message time"""
    try:
        # Load the riff data
        riff_data = load_user_riff(user_uuid, app_slug, riff_slug)
        if riff_data:
            # Update stats
            riff_data["message_count"] = message_count
            riff_data["last_message_at"] = last_message_at

            # Save updated riff data
            success = save_user_riff(user_uuid, app_slug, riff_slug, riff_data)
            if success:
                logger.debug(
                    f"📊 Updated riff stats: {message_count} messages, last at {last_message_at}"
                )
            return success
    except Exception as e:
        logger.error(f"❌ Failed to update riff stats: {e}")
    return False


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/messages", methods=["GET"])
def get_messages(slug, riff_slug):
    """Get all messages for a specific riff"""
    logger.info(
        f"📋 GET /api/apps/{slug}/riffs/{riff_slug}/messages - Fetching messages"
    )

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

        # Verify app exists
        if not user_app_exists(user_uuid, slug):
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({"error": "App not found"}), 404

        # Verify riff exists
        if not user_riff_exists(user_uuid, slug, riff_slug):
            logger.warning(f"❌ Riff not found: {riff_slug}")
            return jsonify({"error": "Riff not found"}), 404

        messages = load_user_messages(user_uuid, slug, riff_slug)
        # Sort messages by creation time (oldest first for chat display)
        messages.sort(key=lambda x: x.get("created_at", ""))

        logger.info(f"📊 Returning {len(messages)} messages for riff {riff_slug}")
        return jsonify(
            {
                "messages": messages,
                "count": len(messages),
                "app_slug": slug,
                "riff_slug": riff_slug,
            }
        )
    except Exception as e:
        logger.error(f"💥 Error fetching messages: {str(e)}")
        return jsonify({"error": "Failed to fetch messages"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/messages", methods=["POST"])
def create_message(slug):
    """Create a new message for a specific riff"""
    logger.info(f"🆕 POST /api/apps/{slug}/riffs/messages - Creating new message")

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

        # Verify app exists
        if not user_app_exists(user_uuid, slug):
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({"error": "App not found"}), 404

        # Get request data
        data = request.get_json()
        if not data:
            logger.warning("❌ Request body is required")
            return jsonify({"error": "Request body is required"}), 400

        riff_slug = data.get("riff_slug", "").strip()
        if not riff_slug:
            logger.warning("❌ Riff slug is required")
            return jsonify({"error": "Riff slug is required"}), 400

        content = data.get("content", "").strip()
        if not content:
            logger.warning("❌ Message content is required")
            return jsonify({"error": "Message content is required"}), 400

        # Verify riff exists
        if not user_riff_exists(user_uuid, slug, riff_slug):
            logger.warning(f"❌ Riff not found: {riff_slug}")
            return jsonify({"error": "Riff not found"}), 404

        logger.info(f"🔄 Creating message for riff: {riff_slug}")

        # Create message record
        message_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        message = {
            "id": message_id,
            "content": content,
            "riff_slug": riff_slug,
            "app_slug": slug,
            "created_at": created_at,
            "created_by": user_uuid,
            "type": data.get("type", "text"),  # text, file, etc.
            "metadata": data.get("metadata", {}),  # Additional data like file info
        }

        # Add message using storage pattern
        if not add_user_message(user_uuid, slug, riff_slug, message):
            logger.error("❌ Failed to save message to file")
            return jsonify({"error": "Failed to save message"}), 500

        # Check if this is a user message that should trigger LLM response
        message_type = data.get("type", "text")
        logger.info(
            f"🔍 Message type: {message_type}, created_by: {message.get('created_by')}, user_uuid: {user_uuid[:8]}"
        )

        if message_type == "user" or (
            message_type == "text" and message.get("created_by") == user_uuid
        ):
            # Try to get agent loop and generate LLM response
            logger.info(
                f"🔍 Looking for AgentLoop with key: {user_uuid[:8]}:{slug}:{riff_slug}"
            )

            # Debug: Show all available agent loops
            stats = agent_loop_manager.get_stats()
            logger.info(f"📊 Current AgentLoop stats: {stats}")

            agent_loop = agent_loop_manager.get_agent_loop(user_uuid, slug, riff_slug)
            if agent_loop:
                logger.info(
                    f"✅ Found AgentLoop for {user_uuid[:8]}:{slug}:{riff_slug}"
                )
            else:
                logger.warning(
                    f"❌ AgentLoop not found for {user_uuid[:8]}:{slug}:{riff_slug}"
                )
                # Debug: Show what keys are actually stored
                with agent_loop_manager._lock:
                    stored_keys = list(agent_loop_manager.agent_loops.keys())
                    logger.info(f"🔑 Available AgentLoop keys: {stored_keys}")

            if agent_loop:
                try:
                    logger.info(
                        f"🤖 Sending message to Agent for {user_uuid[:8]}/{slug}/{riff_slug}"
                    )
                    # Send message to agent - response will come through callback
                    confirmation = agent_loop.send_message(content)
                    logger.info(f"✅ Message sent to agent: {confirmation}")

                    # Update riff message stats for the user message
                    messages = load_user_messages(user_uuid, slug, riff_slug)
                    update_riff_message_stats(
                        user_uuid,
                        slug,
                        riff_slug,
                        len(messages),
                        created_at,
                    )

                    # Return success - agent response will be saved via callback
                    return (
                        jsonify(
                            {
                                "message": "Message sent to agent successfully. Response will be processed asynchronously.",
                                "user_message": message,
                                "agent_status": confirmation,
                            }
                        ),
                        201,
                    )

                except Exception as e:
                    logger.error(f"❌ Error sending message to agent: {e}")
                    # Continue without agent response - user message was still saved

        # Get updated message count for stats (fallback if no LLM response)
        messages = load_user_messages(user_uuid, slug, riff_slug)
        update_riff_message_stats(user_uuid, slug, riff_slug, len(messages), created_at)

        logger.info(f"✅ Message created successfully for riff: {riff_slug}")
        return (
            jsonify({"message": "Message created successfully", "data": message}),
            201,
        )

    except Exception as e:
        logger.error(f"💥 Error creating message: {str(e)}")
        return jsonify({"error": "Failed to create message"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/ready", methods=["GET"])
def check_riff_ready(slug, riff_slug):
    """Check if an LLM object is ready in memory for a specific riff"""
    log_api_request(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/ready")

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

        # Verify app exists
        if not user_app_exists(user_uuid, slug):
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({"error": "App not found"}), 404

        # Verify riff exists
        if not user_riff_exists(user_uuid, slug, riff_slug):
            logger.warning(f"❌ Riff not found: {riff_slug}")
            return jsonify({"error": "Riff not found"}), 404

        # Check if AgentLoop exists for this riff
        agent_loop = agent_loop_manager.get_agent_loop(user_uuid, slug, riff_slug)
        is_ready = agent_loop is not None

        # Additional debugging for flakiness
        if not is_ready:
            stats = agent_loop_manager.get_stats()
            logger.warning(
                f"🔍 LLM not ready for {user_uuid[:8]}:{slug}:{riff_slug}. "
                f"Total loops: {stats.get('total_loops', 0)}"
            )
        else:
            logger.info(f"✅ LLM ready for {user_uuid[:8]}:{slug}:{riff_slug}")

        log_api_response(
            logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/ready", 200, user_uuid
        )
        return jsonify({"ready": is_ready}), 200

    except Exception as e:
        logger.error(f"💥 Error checking riff readiness: {str(e)}")
        log_api_response(
            logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/ready", 500
        )
        return jsonify({"error": "Failed to check riff readiness"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/reset", methods=["POST"])
def reset_riff_llm(slug, riff_slug):
    """Reset the LLM object for a specific riff by creating a brand new one"""
    log_api_request(logger, "POST", f"/api/apps/{slug}/riffs/{riff_slug}/reset")

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

        # Verify app exists
        if not user_app_exists(user_uuid, slug):
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({"error": "App not found"}), 404

        # Verify riff exists
        if not user_riff_exists(user_uuid, slug, riff_slug):
            logger.warning(f"❌ Riff not found: {riff_slug}")
            return jsonify({"error": "Riff not found"}), 404

        # Remove existing AgentLoop if it exists
        existing_removed = agent_loop_manager.remove_agent_loop(
            user_uuid, slug, riff_slug
        )
        if existing_removed:
            logger.info(
                f"🗑️ Removed existing AgentLoop for {user_uuid[:8]}:{slug}:{riff_slug}"
            )
        else:
            logger.info(
                f"ℹ️ No existing AgentLoop found for {user_uuid[:8]}:{slug}:{riff_slug}"
            )

        # Create a brand new Agent object using the reusable function
        success, error_message = create_agent_for_user(user_uuid, slug, riff_slug)
        if not success:
            logger.error(f"❌ Failed to reset Agent for riff: {error_message}")
            return jsonify({"error": error_message}), 500

        # Double-check that the LLM is actually ready before returning success
        logger.info(
            f"🔍 Verifying LLM readiness after reset for {user_uuid[:8]}:{slug}:{riff_slug}"
        )
        agent_loop = agent_loop_manager.get_agent_loop(user_uuid, slug, riff_slug)
        if not agent_loop:
            logger.error(
                f"❌ LLM reset appeared successful but AgentLoop not found for {user_uuid[:8]}:{slug}:{riff_slug}"
            )
            return (
                jsonify({"error": "LLM reset failed - could not verify readiness"}),
                500,
            )

        # Test that the LLM can actually respond to a simple query
        try:
            logger.info(
                f"🧪 Testing LLM functionality for {user_uuid[:8]}:{slug}:{riff_slug}"
            )
            test_response = agent_loop.send_message("Hello")
            if test_response and len(test_response.strip()) > 0:
                logger.info(
                    f"✅ LLM test successful for {user_uuid[:8]}:{slug}:{riff_slug}"
                )
            else:
                logger.error(
                    f"❌ LLM test failed - empty response for {user_uuid[:8]}:{slug}:{riff_slug}"
                )
                return (
                    jsonify(
                        {"error": "LLM reset failed - LLM not responding properly"}
                    ),
                    500,
                )
        except Exception as e:
            logger.error(
                f"❌ LLM test failed with exception for {user_uuid[:8]}:{slug}:{riff_slug}: {e}"
            )
            return (
                jsonify({"error": f"LLM reset failed - LLM test error: {str(e)}"}),
                500,
            )

        logger.info(f"✅ LLM reset and verification successful for riff: {riff_slug}")
        log_api_response(
            logger, "POST", f"/api/apps/{slug}/riffs/{riff_slug}/reset", 200, user_uuid
        )
        return jsonify({"message": "LLM reset successfully", "ready": True}), 200

    except Exception as e:
        logger.error(f"💥 Error resetting riff LLM: {str(e)}")
        log_api_response(
            logger, "POST", f"/api/apps/{slug}/riffs/{riff_slug}/reset", 500
        )
        return jsonify({"error": "Failed to reset riff LLM"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/status", methods=["GET"])
def get_agent_status(slug, riff_slug):
    """Get the current status of the agent for a specific riff"""
    log_api_request(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/status")

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

        # Verify app exists
        if not user_app_exists(user_uuid, slug):
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({"error": "App not found"}), 404

        # Verify riff exists
        if not user_riff_exists(user_uuid, slug, riff_slug):
            logger.warning(f"❌ Riff not found: {riff_slug}")
            return jsonify({"error": "Riff not found"}), 404

        # Get the agent loop
        agent_loop = agent_loop_manager.get_agent_loop(user_uuid, slug, riff_slug)
        if not agent_loop:
            logger.warning(
                f"❌ Agent loop not found for {user_uuid[:8]}:{slug}:{riff_slug}"
            )
            return (
                jsonify(
                    {
                        "status": "not_found",
                        "message": "Agent loop not found. Create a new riff to initialize the agent.",
                    }
                ),
                404,
            )

        # Get agent status
        status = agent_loop.get_agent_status()

        logger.info(f"📊 Agent status retrieved for {user_uuid[:8]}:{slug}:{riff_slug}")
        log_api_response(
            logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/status", 200, user_uuid
        )
        return jsonify(status), 200

    except Exception as e:
        logger.error(f"💥 Error getting agent status: {str(e)}")
        log_api_response(
            logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/status", 500
        )
        return jsonify({"error": "Failed to get agent status"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/play", methods=["POST"])
def play_agent(slug, riff_slug):
    """Resume/play the agent for a specific riff"""
    log_api_request(logger, "POST", f"/api/apps/{slug}/riffs/{riff_slug}/play")

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

        # Verify app exists
        if not user_app_exists(user_uuid, slug):
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({"error": "App not found"}), 404

        # Verify riff exists
        if not user_riff_exists(user_uuid, slug, riff_slug):
            logger.warning(f"❌ Riff not found: {riff_slug}")
            return jsonify({"error": "Riff not found"}), 404

        # Get the agent loop
        agent_loop = agent_loop_manager.get_agent_loop(user_uuid, slug, riff_slug)
        if not agent_loop:
            logger.warning(
                f"❌ Agent loop not found for {user_uuid[:8]}:{slug}:{riff_slug}"
            )
            return (
                jsonify(
                    {
                        "error": "Agent loop not found. Create a new riff to initialize the agent."
                    }
                ),
                404,
            )

        # Resume the agent
        success = agent_loop.resume_agent()
        if success:
            logger.info(f"▶️ Agent resumed for {user_uuid[:8]}:{slug}:{riff_slug}")
            log_api_response(
                logger,
                "POST",
                f"/api/apps/{slug}/riffs/{riff_slug}/play",
                200,
                user_uuid,
            )
            return (
                jsonify({"message": "Agent resumed successfully", "status": "playing"}),
                200,
            )
        else:
            logger.error(
                f"❌ Failed to resume agent for {user_uuid[:8]}:{slug}:{riff_slug}"
            )
            return jsonify({"error": "Failed to resume agent"}), 500

    except Exception as e:
        logger.error(f"💥 Error resuming agent: {str(e)}")
        log_api_response(
            logger, "POST", f"/api/apps/{slug}/riffs/{riff_slug}/play", 500
        )
        return jsonify({"error": "Failed to resume agent"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/pause", methods=["POST"])
def pause_agent(slug, riff_slug):
    """Pause the agent for a specific riff"""
    log_api_request(logger, "POST", f"/api/apps/{slug}/riffs/{riff_slug}/pause")

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

        # Verify app exists
        if not user_app_exists(user_uuid, slug):
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({"error": "App not found"}), 404

        # Verify riff exists
        if not user_riff_exists(user_uuid, slug, riff_slug):
            logger.warning(f"❌ Riff not found: {riff_slug}")
            return jsonify({"error": "Riff not found"}), 404

        # Get the agent loop
        agent_loop = agent_loop_manager.get_agent_loop(user_uuid, slug, riff_slug)
        if not agent_loop:
            logger.warning(
                f"❌ Agent loop not found for {user_uuid[:8]}:{slug}:{riff_slug}"
            )
            return (
                jsonify(
                    {
                        "error": "Agent loop not found. Create a new riff to initialize the agent."
                    }
                ),
                404,
            )

        # Pause the agent
        success = agent_loop.pause_agent()
        if success:
            logger.info(f"⏸️ Agent paused for {user_uuid[:8]}:{slug}:{riff_slug}")
            log_api_response(
                logger,
                "POST",
                f"/api/apps/{slug}/riffs/{riff_slug}/pause",
                200,
                user_uuid,
            )
            return (
                jsonify({"message": "Agent paused successfully", "status": "paused"}),
                200,
            )
        else:
            logger.error(
                f"❌ Failed to pause agent for {user_uuid[:8]}:{slug}:{riff_slug}"
            )
            return jsonify({"error": "Failed to pause agent"}), 500

    except Exception as e:
        logger.error(f"💥 Error pausing agent: {str(e)}")
        log_api_response(
            logger, "POST", f"/api/apps/{slug}/riffs/{riff_slug}/pause", 500
        )
        return jsonify({"error": "Failed to pause agent"}), 500


@riffs_bp.route("/api/apps/<slug>/riffs/<riff_slug>/pr-status", methods=["GET"])
def get_riff_pr_status(slug, riff_slug):
    """Get GitHub Pull Request status for a specific riff (using riff name as branch)"""
    log_api_request(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/pr-status")
    
    try:
        # Get UUID from headers
        user_uuid = request.headers.get("X-User-UUID")
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            log_api_response(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/pr-status", 400)
            return jsonify({"error": "X-User-UUID header is required"}), 400

        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            log_api_response(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/pr-status", 400)
            return jsonify({"error": "UUID cannot be empty"}), 400

        # Load app to get GitHub URL
        apps_storage = get_apps_storage(user_uuid)
        app = apps_storage.load_app(slug)
        if not app:
            logger.warning(f"❌ App not found: {slug} for user {user_uuid[:8]}")
            log_api_response(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/pr-status", 404)
            return jsonify({"error": "App not found"}), 404

        # Check if app has GitHub URL
        github_url = app.get("github_url")
        if not github_url:
            logger.info(f"ℹ️ No GitHub URL configured for app {slug}")
            log_api_response(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/pr-status", 200)
            return jsonify({"pr_status": None, "message": "No GitHub URL configured"})

        # Get user's GitHub token
        try:
            user_keys = load_user_keys(user_uuid)
            github_token = user_keys.get("github")
            
            if not github_token:
                logger.info(f"ℹ️ No GitHub token found for user {user_uuid[:8]}")
                log_api_response(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/pr-status", 200)
                return jsonify({"pr_status": None, "message": "No GitHub token configured"})

            # Use riff name as branch name (this is the key fix!)
            branch_name = riff_slug
            logger.info(f"🔍 Getting PR status for riff branch: {branch_name}")
            
            # First try searching for PRs FROM this branch (head search)
            logger.info(f"🔍 Trying head search: PRs from branch '{branch_name}'")
            pr_status = get_pr_status(github_url, github_token, branch_name, search_by_base=False)
            
            # If no PRs found, try searching for PRs TO this branch (base search)
            # This handles cases where the riff branch is the target branch
            if not pr_status:
                logger.info(f"🔍 No PRs found from branch '{branch_name}', trying base search")
                logger.info(f"🔍 Trying base search: PRs targeting branch '{branch_name}'")
                pr_status = get_pr_status(github_url, github_token, branch_name, search_by_base=True)
            
            if pr_status:
                logger.info(f"✅ Found PR status for riff {riff_slug}: #{pr_status['number']}")
            else:
                logger.info(f"ℹ️ No PR found for riff {riff_slug} (branch: {branch_name})")
            
            log_api_response(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/pr-status", 200)
            return jsonify({"pr_status": pr_status})
            
        except Exception as e:
            logger.warning(f"⚠️ Error getting PR status: {str(e)}")
            log_api_response(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/pr-status", 200)
            return jsonify({"pr_status": None, "error": str(e)})

    except Exception as e:
        logger.error(f"💥 Error getting riff PR status: {str(e)}")
        log_api_response(logger, "GET", f"/api/apps/{slug}/riffs/{riff_slug}/pr-status", 500)
        return jsonify({"error": "Failed to get PR status"}), 500

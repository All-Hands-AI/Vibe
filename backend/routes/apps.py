from flask import Blueprint, jsonify, request
import logging
from services.apps_service import apps_service

logger = logging.getLogger(__name__)

# Create Blueprint for apps
apps_bp = Blueprint("apps", __name__)


@apps_bp.route("/api/apps", methods=["GET"])
def get_apps():
    """Get all apps for a user"""
    logger.info("📋 GET /api/apps - Getting user apps")

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

        logger.debug(f"📋 Loading apps for user {user_uuid[:8]}...")

        # Load apps using service layer
        apps = apps_service.load_user_apps(user_uuid)

        logger.info(f"✅ Loaded {len(apps)} apps for user {user_uuid[:8]}")
        return jsonify({"apps": apps})

    except Exception as e:
        logger.error(f"💥 Error loading apps: {str(e)}")
        return jsonify({"error": "Failed to load apps"}), 500


@apps_bp.route("/api/apps/<slug>", methods=["GET"])
def get_app(slug):
    """Get a specific app for a user"""
    logger.info(f"📋 GET /api/apps/{slug} - Getting app details")

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

        logger.debug(f"📋 Loading app {slug} for user {user_uuid[:8]}...")

        # Load app using service layer
        app = apps_service.load_user_app(user_uuid, slug)

        if not app:
            logger.warning(f"❌ App not found: {slug} for user {user_uuid[:8]}")
            return jsonify({"error": "App not found"}), 404

        logger.info(f"✅ Loaded app {slug} for user {user_uuid[:8]}")
        return jsonify({"app": app})

    except Exception as e:
        logger.error(f"💥 Error loading app: {str(e)}")
        return jsonify({"error": "Failed to load app"}), 500


@apps_bp.route("/api/apps", methods=["POST"])
def create_app():
    """Create a new app"""
    logger.info("🆕 POST /api/apps - Creating new app")

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

        # Get app name from request body
        data = request.get_json()
        if not data or "name" not in data:
            logger.warning("❌ App name is required in request body")
            return jsonify({"error": "App name is required"}), 400

        app_name = data["name"]
        logger.debug(f"🆕 Creating app: {app_name} for user {user_uuid[:8]}")

        # Create app using service layer
        success, result = apps_service.create_app(user_uuid, app_name)

        if success:
            logger.info(f"✅ App created successfully: {result['app']['slug']}")
            return jsonify(result), 201
        else:
            logger.error(
                f"❌ App creation failed: {result.get('error', 'Unknown error')}"
            )
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"💥 Error creating app: {str(e)}")
        return jsonify({"error": "Failed to create app"}), 500


@apps_bp.route("/api/apps/<slug>", methods=["DELETE"])
def delete_app(slug):
    """Delete an app and its associated GitHub repo and Fly.io app"""
    logger.info(f"🗑️ DELETE /api/apps/{slug} - Deleting app")

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

        logger.debug(f"🗑️ Deleting app {slug} for user {user_uuid[:8]}...")

        # Delete app using service layer
        success, result = apps_service.delete_app(user_uuid, slug)

        if success:
            logger.info(f"✅ App deletion completed: {slug}")
            return jsonify(result)
        else:
            status_code = 404 if "not found" in result.get("error", "").lower() else 500
            return jsonify(result), status_code

    except Exception as e:
        logger.error(f"💥 Error deleting app: {str(e)}")
        return jsonify({"error": "Failed to delete app"}), 500


@apps_bp.route("/api/apps/<slug>/deployment", methods=["GET"])
def get_app_deployment_status(slug):
    """Get deployment status for an app (checks main branch)"""
    logger.info(f"🚀 GET /api/apps/{slug}/deployment - Getting app deployment status")

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

        logger.debug(
            f"🚀 Getting deployment status for app {slug} for user {user_uuid[:8]}..."
        )

        # Get deployment status using service layer
        success, result = apps_service.get_app_deployment_status(user_uuid, slug)

        if success:
            return jsonify(result)
        else:
            status_code = 404 if "not found" in result.get("error", "").lower() else 500
            return jsonify(result), status_code

    except Exception as e:
        logger.error(f"💥 Error getting app deployment status: {str(e)}")
        return jsonify({"error": "Failed to get deployment status"}), 500


# Legacy functions for backward compatibility - these are now handled by the service layer
def load_user_apps(user_uuid):
    """Load apps for a specific user - DEPRECATED, use apps_service instead"""
    logger.warning("⚠️ Using deprecated load_user_apps() function")
    return apps_service.load_user_apps(user_uuid)


def load_user_app(user_uuid, app_slug):
    """Load specific app for a user - DEPRECATED, use apps_service instead"""
    logger.warning("⚠️ Using deprecated load_user_app() function")
    return apps_service.load_user_app(user_uuid, app_slug)


def save_user_app(user_uuid, app_slug, app_data):
    """Save app for a specific user - DEPRECATED, use apps_service instead"""
    logger.warning("⚠️ Using deprecated save_user_app() function")
    return apps_service.save_user_app(user_uuid, app_slug, app_data)


def user_app_exists(user_uuid, app_slug):
    """Check if app exists for user - DEPRECATED, use apps_service instead"""
    logger.warning("⚠️ Using deprecated user_app_exists() function")
    return apps_service.user_app_exists(user_uuid, app_slug)


def delete_user_app(user_uuid, app_slug):
    """Delete app for a specific user - DEPRECATED, use apps_service instead"""
    logger.warning("⚠️ Using deprecated delete_user_app() function")
    return apps_service.delete_user_app(user_uuid, app_slug)


def is_valid_slug(slug):
    """Validate that a slug contains only lowercase letters, numbers, and hyphens - DEPRECATED"""
    logger.warning("⚠️ Using deprecated is_valid_slug() function")
    return apps_service.is_valid_slug(slug)


def create_slug(name):
    """Convert app name to slug format - DEPRECATED"""
    logger.warning("⚠️ Using deprecated create_slug() function")
    return apps_service.create_slug(name)


def get_pr_status(repo_url, github_token, branch="main", search_by_base=False):
    """Get GitHub Pull Request status for a specific branch - DEPRECATED"""
    logger.warning("⚠️ Using deprecated get_pr_status() function")
    return apps_service.get_pr_status(repo_url, github_token, branch, search_by_base)


def close_github_pr(repo_url, github_token, branch_name):
    """Close GitHub Pull Request for a specific branch - DEPRECATED"""
    logger.warning("⚠️ Using deprecated close_github_pr() function")
    return apps_service.close_github_pr(repo_url, github_token, branch_name)


def delete_github_branch(repo_url, github_token, branch_name):
    """Delete a GitHub branch - DEPRECATED"""
    logger.warning("⚠️ Using deprecated delete_github_branch() function")
    return apps_service.delete_github_branch(repo_url, github_token, branch_name)


def delete_fly_app(app_name, fly_token):
    """Delete a Fly.io app - DEPRECATED"""
    logger.warning("⚠️ Using deprecated delete_fly_app() function")
    return apps_service.delete_fly_app(app_name, fly_token)


def create_github_repo(repo_name, github_token, fly_token):
    """Create a GitHub repository from template and set FLY_API_TOKEN secret - DEPRECATED"""
    logger.warning("⚠️ Using deprecated create_github_repo() function")
    return apps_service.create_github_repo(repo_name, github_token, fly_token)


def create_fly_app(app_name, fly_token):
    """Create a new Fly.io app - DEPRECATED"""
    logger.warning("⚠️ Using deprecated create_fly_app() function")
    return apps_service.create_fly_app(app_name, fly_token)


def get_github_status(repo_url, github_token):
    """Get GitHub repository status including CI/CD tests - DEPRECATED"""
    logger.warning("⚠️ Using deprecated get_github_status() function")
    return apps_service.get_github_status(repo_url, github_token)


def get_fly_status(project_slug, fly_token):
    """Get Fly.io deployment status - DEPRECATED"""
    logger.warning("⚠️ Using deprecated get_fly_status() function")
    return apps_service.get_fly_status(project_slug, fly_token)


def create_initial_riff_and_message(
    user_uuid, app_slug, app_slug_for_message, github_url
):
    """Create initial riff and message for a new app - DEPRECATED"""
    logger.warning("⚠️ Using deprecated create_initial_riff_and_message() function")
    return apps_service.create_initial_riff_and_message(
        user_uuid, app_slug, app_slug_for_message, github_url
    )

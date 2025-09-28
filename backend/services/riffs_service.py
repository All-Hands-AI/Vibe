"""
Riffs Service - Business logic for riff management and agent operations.

This service handles:
- Riff CRUD operations
- Agent creation and management
- Message handling
- Runtime management
- Deployment status checking
"""

import re
import uuid
import sys
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

from storage import get_riffs_storage, get_apps_storage
from storage.base_storage import DATA_DIR
from agents import agent_loop_manager
from keys import get_user_key, load_user_keys
from utils.repository import setup_riff_workspace
from utils.event_serializer import serialize_agent_event_to_message
from utils.deployment_status import get_deployment_status
from services.runtime_service import runtime_service

# Add the site-packages to the path for openhands imports
sys.path.insert(0, ".venv/lib/python3.12/site-packages")

from openhands.sdk import LLM


logger = logging.getLogger(__name__)


class RiffsService:
    """Service for managing riffs and agent operations."""

    def __init__(self):
        pass

    # LLM management
    def get_llm_instance(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> LLM:
        """Get the appropriate LLM instance based on MOCK_MODE environment variable."""
        if os.environ.get("MOCK_MODE", "false").lower() == "true":
            # In mock mode, create a real LLM instance but with a fake key
            # The actual API calls will be mocked by the mocks.py module
            return LLM(api_key="mock-key", model=model, service_id="mock-service")
        else:
            # Use the real API key
            return LLM(api_key=api_key, model=model, service_id="openvibe-llm")

    # Riff CRUD operations
    def load_user_riffs(self, user_uuid: str, app_slug: str) -> List[Dict[str, Any]]:
        """Load riffs for a specific user and app."""
        storage = get_riffs_storage(user_uuid)
        return storage.list_riffs(app_slug)

    def load_user_riff(self, user_uuid: str, app_slug: str, riff_slug: str) -> Optional[Dict[str, Any]]:
        """Load specific riff for a user."""
        storage = get_riffs_storage(user_uuid)
        return storage.load_riff(app_slug, riff_slug)

    def save_user_riff(self, user_uuid: str, app_slug: str, riff_slug: str, riff_data: Dict[str, Any]) -> bool:
        """Save riff for a specific user."""
        storage = get_riffs_storage(user_uuid)
        return storage.save_riff(app_slug, riff_slug, riff_data)

    def user_riff_exists(self, user_uuid: str, app_slug: str, riff_slug: str) -> bool:
        """Check if riff exists for user."""
        storage = get_riffs_storage(user_uuid)
        return storage.riff_exists(app_slug, riff_slug)

    def delete_user_riff(self, user_uuid: str, app_slug: str, riff_slug: str) -> bool:
        """Delete riff for a specific user."""
        storage = get_riffs_storage(user_uuid)
        return storage.delete_riff(app_slug, riff_slug)

    # Slug validation and creation
    def create_slug(self, name: str) -> str:
        """Convert riff name to slug format."""
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
        slug = re.sub(r"\s+", "-", slug.strip())
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")

    def is_valid_slug(self, slug: str) -> bool:
        """Validate that a slug contains only lowercase letters, numbers, and hyphens."""
        if not slug:
            return False
        # Check if slug matches the pattern: lowercase letters, numbers, and hyphens only
        # Must not start or end with hyphen, and no consecutive hyphens
        pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
        return bool(re.match(pattern, slug))

    # Message operations
    def load_user_messages(self, user_uuid: str, app_slug: str, riff_slug: str) -> List[Dict[str, Any]]:
        """Load messages for a specific riff."""
        storage = get_riffs_storage(user_uuid)
        return storage.list_messages(app_slug, riff_slug)

    def add_user_message(self, user_uuid: str, app_slug: str, riff_slug: str, message: Dict[str, Any]) -> bool:
        """Add a message to a riff for a specific user."""
        storage = get_riffs_storage(user_uuid)
        return storage.add_message(app_slug, riff_slug, message)

    # Agent operations
    def reconstruct_agent_from_state(self, user_uuid: str, app_slug: str, riff_slug: str) -> Tuple[bool, Optional[str]]:
        """
        Reconstruct an Agent object from existing serialized state for a specific user, app, and riff.
        This function creates an AgentLoop from existing state without re-cloning the repository.
        """
        try:
            # Get user's Anthropic token
            anthropic_token = get_user_key(user_uuid, "anthropic")
            if not anthropic_token:
                logger.warning(f"⚠️ No Anthropic token found for user {user_uuid[:8]}")
                return False, "Anthropic API key required"

            # Get workspace path (should already exist from previous setup)
            workspace_path = str(
                DATA_DIR / user_uuid / "apps" / app_slug / "riffs" / riff_slug / "workspace"
            )

            if not os.path.exists(workspace_path):
                logger.warning(f"⚠️ Workspace path does not exist: {workspace_path}")
                return False, f"Workspace not found at {workspace_path}"

            logger.info(f"🔄 Reconstructing agent from state for {user_uuid[:8]}:{app_slug}:{riff_slug}")
            logger.debug(f"📁 Using workspace: {workspace_path}")

            # Get LLM instance
            llm = self.get_llm_instance(anthropic_token)

            # Define message callback for handling agent events
            def message_callback(event):
                try:
                    logger.debug(f"📨 Agent event received: {event.event_type}")
                    
                    # Serialize the event to a message format
                    message = serialize_agent_event_to_message(event, user_uuid, app_slug, riff_slug)
                    
                    if message:
                        # Add the message to storage
                        success = self.add_user_message(user_uuid, app_slug, riff_slug, message)
                        if success:
                            logger.debug(f"✅ Agent event saved as message: {message['id']}")
                        else:
                            logger.warning(f"⚠️ Failed to save agent event as message")
                    else:
                        logger.debug(f"🔄 Event {event.event_type} not serialized to message")
                        
                except Exception as e:
                    logger.error(f"💥 Error in message callback: {str(e)}")

            # Create AgentLoop from existing state
            agent_loop = agent_loop_manager.create_agent_loop_from_state(
                user_uuid=user_uuid,
                app_slug=app_slug,
                riff_slug=riff_slug,
                workspace_path=workspace_path,
                llm=llm,
                message_callback=message_callback
            )

            if agent_loop:
                logger.info(f"✅ Agent reconstructed successfully for {user_uuid[:8]}:{app_slug}:{riff_slug}")
                return True, None
            else:
                logger.error(f"❌ Failed to reconstruct agent for {user_uuid[:8]}:{app_slug}:{riff_slug}")
                return False, "Failed to create agent loop from state"

        except Exception as e:
            logger.error(f"💥 Error reconstructing agent: {str(e)}")
            return False, f"Error reconstructing agent: {str(e)}"

    def create_agent_for_user(self, user_uuid: str, app_slug: str, riff_slug: str) -> Tuple[bool, Optional[str]]:
        """Create a new agent for a user's riff."""
        try:
            # Get user's Anthropic token
            anthropic_token = get_user_key(user_uuid, "anthropic")
            if not anthropic_token:
                logger.warning(f"⚠️ No Anthropic token found for user {user_uuid[:8]}")
                return False, "Anthropic API key required"

            # Get user's GitHub token for repository operations
            github_token = get_user_key(user_uuid, "github")
            if not github_token:
                logger.warning(f"⚠️ No GitHub token found for user {user_uuid[:8]}")
                return False, "GitHub API key required"

            # Load the app to get GitHub URL
            apps_storage = get_apps_storage(user_uuid)
            app = apps_storage.load_app(app_slug)
            if not app:
                logger.error(f"❌ App not found: {app_slug} for user {user_uuid[:8]}")
                return False, f"App '{app_slug}' not found"

            github_url = app.get("github_url")
            if not github_url:
                logger.error(f"❌ No GitHub URL found for app: {app_slug}")
                return False, f"No GitHub URL configured for app '{app_slug}'"

            logger.info(f"🤖 Creating agent for {user_uuid[:8]}:{app_slug}:{riff_slug}")
            logger.debug(f"🐙 GitHub URL: {github_url}")

            # Setup workspace for the riff
            workspace_path = setup_riff_workspace(
                user_uuid, app_slug, riff_slug, github_url, github_token, riff_slug
            )

            if not workspace_path:
                logger.error(f"❌ Failed to setup workspace for {user_uuid[:8]}:{app_slug}:{riff_slug}")
                return False, "Failed to setup workspace"

            logger.info(f"📁 Workspace setup complete: {workspace_path}")

            # Get LLM instance
            llm = self.get_llm_instance(anthropic_token)

            # Define message callback for handling agent events
            def message_callback(event):
                try:
                    logger.debug(f"📨 Agent event received: {event.event_type}")
                    
                    # Serialize the event to a message format
                    message = serialize_agent_event_to_message(event, user_uuid, app_slug, riff_slug)
                    
                    if message:
                        # Add the message to storage
                        success = self.add_user_message(user_uuid, app_slug, riff_slug, message)
                        if success:
                            logger.debug(f"✅ Agent event saved as message: {message['id']}")
                        else:
                            logger.warning(f"⚠️ Failed to save agent event as message")
                    else:
                        logger.debug(f"🔄 Event {event.event_type} not serialized to message")
                        
                except Exception as e:
                    logger.error(f"💥 Error in message callback: {str(e)}")

            # Create new AgentLoop
            agent_loop = agent_loop_manager.create_agent_loop(
                user_uuid=user_uuid,
                app_slug=app_slug,
                riff_slug=riff_slug,
                workspace_path=workspace_path,
                llm=llm,
                message_callback=message_callback
            )

            if agent_loop:
                logger.info(f"✅ Agent created successfully for {user_uuid[:8]}:{app_slug}:{riff_slug}")
                return True, None
            else:
                logger.error(f"❌ Failed to create agent for {user_uuid[:8]}:{app_slug}:{riff_slug}")
                return False, "Failed to create agent loop"

        except Exception as e:
            logger.error(f"💥 Error creating agent: {str(e)}")
            return False, f"Error creating agent: {str(e)}"

    # Riff operations
    def create_riff(self, user_uuid: str, app_slug: str, riff_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Create a new riff for an app."""
        try:
            # Validate inputs
            if not riff_name or not riff_name.strip():
                return False, {"error": "Riff name is required"}

            riff_slug = self.create_slug(riff_name.strip())

            if not self.is_valid_slug(riff_slug):
                return False, {"error": f"Invalid riff name. Generated slug '{riff_slug}' is not valid."}

            # Check if app exists
            apps_storage = get_apps_storage(user_uuid)
            if not apps_storage.app_exists(app_slug):
                return False, {"error": f"App '{app_slug}' not found"}

            # Check if riff already exists
            if self.user_riff_exists(user_uuid, app_slug, riff_slug):
                return False, {"error": f"Riff '{riff_slug}' already exists for this app"}

            # Create riff record
            riff = {
                "slug": riff_slug,
                "app_slug": app_slug,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user_uuid,
                "last_message_at": None,
                "message_count": 0,
            }

            # Save riff
            if not self.save_user_riff(user_uuid, app_slug, riff_slug, riff):
                logger.error("❌ Failed to save riff")
                return False, {"error": "Failed to save riff"}

            # Create agent for the riff
            logger.info(f"🤖 Creating agent for new riff: {riff_slug}")
            agent_success, agent_error = self.create_agent_for_user(user_uuid, app_slug, riff_slug)

            if not agent_success:
                logger.warning(f"⚠️ Failed to create agent for riff: {agent_error}")
                # Don't fail the entire riff creation if agent creation fails
                return True, {
                    "message": "Riff created successfully",
                    "riff": riff,
                    "warning": f"Agent creation failed: {agent_error}",
                }

            logger.info(f"✅ Riff created successfully: {riff_slug}")
            return True, {
                "message": "Riff created successfully",
                "riff": riff,
            }

        except Exception as e:
            logger.error(f"💥 Error creating riff: {str(e)}")
            return False, {"error": "Failed to create riff"}

    def send_message(self, user_uuid: str, app_slug: str, riff_slug: str, content: str) -> Tuple[bool, Dict[str, Any]]:
        """Send a message to a riff's agent."""
        try:
            # Validate inputs
            if not content or not content.strip():
                return False, {"error": "Message content is required"}

            content = content.strip()

            # Check if riff exists
            if not self.user_riff_exists(user_uuid, app_slug, riff_slug):
                return False, {"error": f"Riff '{riff_slug}' not found"}

            # Create message record
            message_id = str(uuid.uuid4())
            created_at = datetime.now(timezone.utc).isoformat()

            message = {
                "id": message_id,
                "content": content,
                "riff_slug": riff_slug,
                "app_slug": app_slug,
                "created_at": created_at,
                "created_by": user_uuid,
                "type": "user",
            }

            # Add message to storage
            if not self.add_user_message(user_uuid, app_slug, riff_slug, message):
                logger.error("❌ Failed to save message")
                return False, {"error": "Failed to save message"}

            # Get agent loop
            agent_loop = agent_loop_manager.get_agent_loop(user_uuid, app_slug, riff_slug)

            if not agent_loop:
                logger.warning(f"⚠️ No agent loop found for {user_uuid[:8]}:{app_slug}:{riff_slug}")
                # Try to reconstruct agent from state
                logger.info(f"🔄 Attempting to reconstruct agent from state...")
                reconstruct_success, reconstruct_error = self.reconstruct_agent_from_state(
                    user_uuid, app_slug, riff_slug
                )

                if not reconstruct_success:
                    logger.error(f"❌ Failed to reconstruct agent: {reconstruct_error}")
                    return False, {"error": f"Agent not available: {reconstruct_error}"}

                # Try to get agent loop again
                agent_loop = agent_loop_manager.get_agent_loop(user_uuid, app_slug, riff_slug)

                if not agent_loop:
                    logger.error(f"❌ Still no agent loop after reconstruction")
                    return False, {"error": "Agent not available after reconstruction"}

            # Send message to agent
            try:
                logger.info(f"📤 Sending message to agent for {user_uuid[:8]}:{app_slug}:{riff_slug}")
                confirmation = agent_loop.send_message(content)
                logger.info(f"✅ Message sent to agent: {confirmation}")

                return True, {
                    "message": "Message sent successfully",
                    "user_message": message,
                    "agent_confirmation": confirmation,
                }

            except Exception as e:
                logger.error(f"💥 Error sending message to agent: {str(e)}")
                return False, {"error": f"Failed to send message to agent: {str(e)}"}

        except Exception as e:
            logger.error(f"💥 Error processing message: {str(e)}")
            return False, {"error": "Failed to process message"}

    def delete_riff(self, user_uuid: str, app_slug: str, riff_slug: str) -> Tuple[bool, Dict[str, Any]]:
        """Delete a riff and clean up associated resources."""
        try:
            # Check if riff exists
            riff = self.load_user_riff(user_uuid, app_slug, riff_slug)
            if not riff:
                return False, {"error": "Riff not found"}

            logger.info(f"🗑️ Deleting riff: {riff_slug} for user {user_uuid[:8]}")

            # Stop and clean up agent loop if it exists
            agent_loop = agent_loop_manager.get_agent_loop(user_uuid, app_slug, riff_slug)
            if agent_loop:
                logger.info(f"🛑 Stopping agent loop for {user_uuid[:8]}:{app_slug}:{riff_slug}")
                try:
                    agent_loop_manager.stop_agent_loop(user_uuid, app_slug, riff_slug)
                    logger.info(f"✅ Agent loop stopped successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Error stopping agent loop: {str(e)}")

            # Delete riff and all associated data
            if self.delete_user_riff(user_uuid, app_slug, riff_slug):
                logger.info(f"✅ Riff {riff_slug} deleted successfully for user {user_uuid[:8]}")
                return True, {
                    "message": f"Riff '{riff_slug}' deleted successfully",
                    "riff_slug": riff_slug,
                }
            else:
                logger.error("❌ Failed to delete riff data")
                return False, {"error": "Failed to delete riff data"}

        except Exception as e:
            logger.error(f"💥 Error deleting riff: {str(e)}")
            return False, {"error": "Failed to delete riff"}

    # Agent control operations
    def get_agent_status(self, user_uuid: str, app_slug: str, riff_slug: str) -> Tuple[bool, Dict[str, Any]]:
        """Get the status of an agent."""
        try:
            agent_loop = agent_loop_manager.get_agent_loop(user_uuid, app_slug, riff_slug)

            if not agent_loop:
                return True, {
                    "status": "not_found",
                    "message": "Agent not found or not running",
                }

            # Get agent status
            status = agent_loop.get_status()
            
            return True, {
                "status": status.get("state", "unknown"),
                "details": status,
            }

        except Exception as e:
            logger.error(f"💥 Error getting agent status: {str(e)}")
            return False, {"error": "Failed to get agent status"}

    def play_agent(self, user_uuid: str, app_slug: str, riff_slug: str) -> Tuple[bool, Dict[str, Any]]:
        """Start/resume an agent."""
        try:
            agent_loop = agent_loop_manager.get_agent_loop(user_uuid, app_slug, riff_slug)

            if not agent_loop:
                # Try to reconstruct agent from state
                logger.info(f"🔄 Agent not found, attempting to reconstruct from state...")
                reconstruct_success, reconstruct_error = self.reconstruct_agent_from_state(
                    user_uuid, app_slug, riff_slug
                )

                if not reconstruct_success:
                    return False, {"error": f"Agent not available: {reconstruct_error}"}

                agent_loop = agent_loop_manager.get_agent_loop(user_uuid, app_slug, riff_slug)

                if not agent_loop:
                    return False, {"error": "Agent not available after reconstruction"}

            # Start/resume the agent
            try:
                result = agent_loop.start()
                logger.info(f"▶️ Agent started/resumed for {user_uuid[:8]}:{app_slug}:{riff_slug}")
                
                return True, {
                    "message": "Agent started successfully",
                    "result": result,
                }

            except Exception as e:
                logger.error(f"💥 Error starting agent: {str(e)}")
                return False, {"error": f"Failed to start agent: {str(e)}"}

        except Exception as e:
            logger.error(f"💥 Error playing agent: {str(e)}")
            return False, {"error": "Failed to play agent"}

    def pause_agent(self, user_uuid: str, app_slug: str, riff_slug: str) -> Tuple[bool, Dict[str, Any]]:
        """Pause an agent."""
        try:
            agent_loop = agent_loop_manager.get_agent_loop(user_uuid, app_slug, riff_slug)

            if not agent_loop:
                return False, {"error": "Agent not found or not running"}

            # Pause the agent
            try:
                result = agent_loop.pause()
                logger.info(f"⏸️ Agent paused for {user_uuid[:8]}:{app_slug}:{riff_slug}")
                
                return True, {
                    "message": "Agent paused successfully",
                    "result": result,
                }

            except Exception as e:
                logger.error(f"💥 Error pausing agent: {str(e)}")
                return False, {"error": f"Failed to pause agent: {str(e)}"}

        except Exception as e:
            logger.error(f"💥 Error pausing agent: {str(e)}")
            return False, {"error": "Failed to pause agent"}

    def reset_agent(self, user_uuid: str, app_slug: str, riff_slug: str) -> Tuple[bool, Dict[str, Any]]:
        """Reset an agent to its initial state."""
        try:
            # Stop existing agent loop if it exists
            agent_loop = agent_loop_manager.get_agent_loop(user_uuid, app_slug, riff_slug)
            if agent_loop:
                logger.info(f"🛑 Stopping existing agent loop for reset...")
                try:
                    agent_loop_manager.stop_agent_loop(user_uuid, app_slug, riff_slug)
                except Exception as e:
                    logger.warning(f"⚠️ Error stopping agent loop: {str(e)}")

            # Create new agent
            logger.info(f"🔄 Creating new agent for reset...")
            agent_success, agent_error = self.create_agent_for_user(user_uuid, app_slug, riff_slug)

            if not agent_success:
                logger.error(f"❌ Failed to create new agent: {agent_error}")
                return False, {"error": f"Failed to reset agent: {agent_error}"}

            logger.info(f"✅ Agent reset successfully for {user_uuid[:8]}:{app_slug}:{riff_slug}")
            return True, {
                "message": "Agent reset successfully",
            }

        except Exception as e:
            logger.error(f"💥 Error resetting agent: {str(e)}")
            return False, {"error": "Failed to reset agent"}

    def check_agent_ready(self, user_uuid: str, app_slug: str, riff_slug: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if an agent is ready to receive messages."""
        try:
            agent_loop = agent_loop_manager.get_agent_loop(user_uuid, app_slug, riff_slug)

            if not agent_loop:
                return True, {
                    "ready": False,
                    "message": "Agent not found or not running",
                }

            # Check if agent is ready
            try:
                status = agent_loop.get_status()
                is_ready = status.get("state") in ["idle", "waiting"]
                
                return True, {
                    "ready": is_ready,
                    "status": status.get("state", "unknown"),
                    "details": status,
                }

            except Exception as e:
                logger.error(f"💥 Error checking agent readiness: {str(e)}")
                return True, {
                    "ready": False,
                    "error": f"Failed to check agent status: {str(e)}",
                }

        except Exception as e:
            logger.error(f"💥 Error checking agent ready: {str(e)}")
            return False, {"error": "Failed to check agent readiness"}

    # Deployment and PR operations
    def get_pr_status(self, user_uuid: str, app_slug: str, riff_slug: str) -> Tuple[bool, Dict[str, Any]]:
        """Get PR status for a riff."""
        try:
            # Load app to get GitHub URL
            apps_storage = get_apps_storage(user_uuid)
            app = apps_storage.load_app(app_slug)
            if not app:
                return False, {"error": "App not found"}

            github_url = app.get("github_url")
            if not github_url:
                return True, {
                    "status": "error",
                    "message": "No GitHub URL configured for this app",
                    "details": {"error": "no_github_url"},
                }

            # Get user's GitHub token
            user_keys = load_user_keys(user_uuid)
            github_token = user_keys.get("github")

            if not github_token:
                return True, {
                    "status": "error",
                    "message": "No GitHub token configured",
                    "details": {"error": "no_github_token"},
                }

            # Import PR status function from apps service
            from services.apps_service import apps_service
            
            # Get PR status for the riff branch
            pr_status = apps_service.get_pr_status(github_url, github_token, riff_slug, search_by_base=False)

            if pr_status:
                logger.info(f"✅ PR status retrieved for riff {riff_slug}")
                return True, pr_status
            else:
                logger.debug(f"ℹ️ No PR found for riff {riff_slug}")
                return True, {
                    "status": "no_pr",
                    "message": f"No pull request found for branch '{riff_slug}'",
                }

        except Exception as e:
            logger.error(f"💥 Error getting PR status: {str(e)}")
            return False, {"error": "Failed to get PR status"}

    def get_deployment_status(self, user_uuid: str, app_slug: str, riff_slug: str) -> Tuple[bool, Dict[str, Any]]:
        """Get deployment status for a riff."""
        try:
            # Load app to get GitHub URL
            apps_storage = get_apps_storage(user_uuid)
            app = apps_storage.load_app(app_slug)
            if not app:
                return False, {"error": "App not found"}

            github_url = app.get("github_url")
            if not github_url:
                return True, {
                    "status": "error",
                    "message": "No GitHub URL configured for this app",
                    "details": {"error": "no_github_url"},
                }

            # Get user's GitHub token
            user_keys = load_user_keys(user_uuid)
            github_token = user_keys.get("github")

            if not github_token:
                return True, {
                    "status": "error",
                    "message": "No GitHub token configured",
                    "details": {"error": "no_github_token"},
                }

            # Check deployment status for the riff branch
            logger.info(f"🔍 Checking deployment status for riff '{riff_slug}' on branch '{riff_slug}'")

            deployment_status = get_deployment_status(github_url, github_token, riff_slug)

            logger.info(f"✅ Deployment status retrieved for riff {riff_slug}: {deployment_status['status']}")
            return True, deployment_status

        except Exception as e:
            logger.error(f"💥 Error getting deployment status: {str(e)}")
            return False, {"error": "Failed to get deployment status"}

    # Runtime operations
    def get_runtime_status(self, user_uuid: str, app_slug: str, riff_slug: str) -> Tuple[bool, Dict[str, Any]]:
        """Get runtime status for a riff."""
        try:
            logger.info(f"📊 Getting runtime status for {user_uuid[:8]}:{app_slug}:{riff_slug}")

            # Get runtime status from runtime service
            success, response = runtime_service.get_runtime_status(user_uuid, app_slug, riff_slug)

            if success:
                logger.info(f"✅ Runtime status retrieved: {response.get('status', 'unknown')}")
                return True, response
            else:
                logger.warning(f"⚠️ Failed to get runtime status: {response.get('error', 'unknown')}")
                return False, response

        except Exception as e:
            logger.error(f"💥 Error getting runtime status: {str(e)}")
            return False, {"error": "Failed to get runtime status"}

    def get_global_runtime_status(self) -> Tuple[bool, Dict[str, Any]]:
        """Get global runtime API status."""
        try:
            logger.info("🏥 Checking global runtime API status")

            # Check runtime API health
            success, response = runtime_service.get_api_health()

            if success:
                logger.info("✅ Runtime API is healthy")
                return True, {
                    "status": "healthy",
                    "message": "Runtime API is operational",
                    "details": response,
                }
            else:
                logger.warning(f"⚠️ Runtime API health check failed: {response.get('error', 'unknown')}")
                return True, {
                    "status": "unhealthy",
                    "message": "Runtime API is not operational",
                    "details": response,
                }

        except Exception as e:
            logger.error(f"💥 Error checking global runtime status: {str(e)}")
            return False, {"error": "Failed to check runtime status"}


# Create a singleton instance
riffs_service = RiffsService()
"""
Refactored AgentLoopManager for managing multiple agent conversations.
Provides a singleton interface for creating, managing, and cleaning up AgentLoop instances.

This refactored version works with the new modular AgentLoop architecture.
"""

from typing import Dict, Optional, Callable, Any
from threading import Lock
from utils.logging import get_logger
from .agent_loop import AgentLoop

# Add the site-packages to the path for openhands imports
import sys

sys.path.insert(0, ".venv/lib/python3.12/site-packages")

from openhands.sdk import LLM

logger = get_logger(__name__)


class AgentLoopManager:
    """
    Singleton manager for AgentLoop instances.
    Handles creation, retrieval, and cleanup of agent conversations.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the manager if not already initialized."""
        if not hasattr(self, "_initialized"):
            self._agent_loops: Dict[str, AgentLoop] = {}
            self._loops_lock = Lock()
            self._initialized = True
            logger.info("🏗️ Initialized AgentLoopManager singleton")

    def _get_key(self, user_uuid: str, app_slug: str, riff_slug: str) -> str:
        """Generate a unique key for an agent loop."""
        return f"{user_uuid}:{app_slug}:{riff_slug}"

    def create_agent_loop(
        self,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        llm: LLM,
        workspace_path: str,
        message_callback: Optional[Callable] = None,
        runtime_url: Optional[str] = None,
        session_api_key: Optional[str] = None,
    ) -> AgentLoop:
        """
        Create a new AgentLoop instance.

        Args:
            user_uuid: UUID identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation
            llm: LLM instance from openhands-sdk
            workspace_path: Required path to the workspace directory (cloned repository)
            message_callback: Optional callback function to handle events/messages
            runtime_url: Optional URL for remote runtime server
            session_api_key: Optional API key for remote runtime session

        Returns:
            The created AgentLoop instance
        """
        key = self._get_key(user_uuid, app_slug, riff_slug)

        with self._loops_lock:
            # Check if agent loop already exists
            if key in self._agent_loops:
                logger.warning(
                    f"⚠️ AgentLoop already exists for {key}, returning existing instance"
                )
                return self._agent_loops[key]

            try:
                # Create new agent loop
                logger.info(f"🏗️ Creating new AgentLoop for {key}")
                agent_loop = AgentLoop(
                    user_uuid=user_uuid,
                    app_slug=app_slug,
                    riff_slug=riff_slug,
                    llm=llm,
                    workspace_path=workspace_path,
                    message_callback=message_callback,
                    runtime_url=runtime_url,
                    session_api_key=session_api_key,
                )

                # Store the agent loop
                self._agent_loops[key] = agent_loop
                logger.info(f"✅ Created and stored AgentLoop for {key}")

                return agent_loop

            except Exception as e:
                logger.error(f"❌ Failed to create AgentLoop for {key}: {e}")
                raise

    def create_agent_loop_from_state(
        self,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        llm: LLM,
        workspace_path: str,
        message_callback: Optional[Callable] = None,
        runtime_url: Optional[str] = None,
        session_api_key: Optional[str] = None,
    ) -> AgentLoop:
        """
        Create an AgentLoop from existing state.

        Args:
            user_uuid: UUID identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation
            llm: LLM instance from openhands-sdk
            workspace_path: Required path to the workspace directory (cloned repository)
            message_callback: Optional callback function to handle events/messages
            runtime_url: Optional URL for remote runtime server
            session_api_key: Optional API key for remote runtime session

        Returns:
            The created AgentLoop instance
        """
        key = self._get_key(user_uuid, app_slug, riff_slug)

        with self._loops_lock:
            # Check if agent loop already exists
            if key in self._agent_loops:
                logger.warning(
                    f"⚠️ AgentLoop already exists for {key}, returning existing instance"
                )
                return self._agent_loops[key]

            try:
                # Create agent loop from existing state
                logger.info(f"🔄 Creating AgentLoop from existing state for {key}")
                agent_loop = AgentLoop.from_existing_state(
                    user_uuid=user_uuid,
                    app_slug=app_slug,
                    riff_slug=riff_slug,
                    llm=llm,
                    workspace_path=workspace_path,
                    message_callback=message_callback,
                    runtime_url=runtime_url,
                    session_api_key=session_api_key,
                )

                # Store the agent loop
                self._agent_loops[key] = agent_loop
                logger.info(f"✅ Created and stored AgentLoop from state for {key}")

                return agent_loop

            except Exception as e:
                logger.error(f"❌ Failed to create AgentLoop from state for {key}: {e}")
                raise

    def get_agent_loop(
        self, user_uuid: str, app_slug: str, riff_slug: str
    ) -> Optional[AgentLoop]:
        """
        Get an existing AgentLoop instance.

        Args:
            user_uuid: UUID identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation

        Returns:
            The AgentLoop instance if it exists, None otherwise
        """
        key = self._get_key(user_uuid, app_slug, riff_slug)

        with self._loops_lock:
            agent_loop = self._agent_loops.get(key)
            if agent_loop:
                logger.debug(f"📋 Retrieved existing AgentLoop for {key}")
            else:
                logger.debug(f"❓ No AgentLoop found for {key}")
            return agent_loop

    def remove_agent_loop(self, user_uuid: str, app_slug: str, riff_slug: str) -> bool:
        """
        Remove and cleanup an AgentLoop instance.

        Args:
            user_uuid: UUID identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation

        Returns:
            True if the agent loop was found and removed, False otherwise
        """
        key = self._get_key(user_uuid, app_slug, riff_slug)

        with self._loops_lock:
            agent_loop = self._agent_loops.get(key)
            if agent_loop:
                logger.info(f"🗑️ Removing and cleaning up AgentLoop for {key}")

                # Cleanup the agent loop
                try:
                    agent_loop.cleanup()
                except Exception as e:
                    logger.error(f"❌ Error during cleanup of AgentLoop {key}: {e}")

                # Remove from storage
                del self._agent_loops[key]
                logger.info(f"✅ Removed AgentLoop for {key}")
                return True
            else:
                logger.warning(f"⚠️ No AgentLoop found to remove for {key}")
                return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about managed agent loops.

        Returns:
            Dictionary containing statistics and status information
        """
        with self._loops_lock:
            total_loops = len(self._agent_loops)

            # Count loops by status
            running_loops = 0
            remote_loops = 0
            local_loops = 0

            loop_details = []

            for key, agent_loop in self._agent_loops.items():
                try:
                    status = agent_loop.get_agent_status()
                    loop_details.append(status)

                    if status.get("is_running", False):
                        running_loops += 1

                    if status.get("runtime_type") == "remote":
                        remote_loops += 1
                    else:
                        local_loops += 1

                except Exception as e:
                    logger.error(f"❌ Error getting status for {key}: {e}")
                    loop_details.append(
                        {
                            "key": key,
                            "error": str(e),
                            "is_running": False,
                        }
                    )

            return {
                "total_loops": total_loops,
                "running_loops": running_loops,
                "remote_loops": remote_loops,
                "local_loops": local_loops,
                "loop_details": loop_details,
            }

    def cleanup_all(self):
        """Clean up all managed agent loops."""
        logger.info("🧹 Starting cleanup of all AgentLoops")

        with self._loops_lock:
            keys_to_remove = list(self._agent_loops.keys())

            for key in keys_to_remove:
                agent_loop = self._agent_loops.get(key)
                if agent_loop:
                    try:
                        logger.info(f"🧹 Cleaning up AgentLoop for {key}")
                        agent_loop.cleanup()
                    except Exception as e:
                        logger.error(f"❌ Error during cleanup of AgentLoop {key}: {e}")

                    # Remove from storage
                    del self._agent_loops[key]

            logger.info(f"✅ Cleaned up {len(keys_to_remove)} AgentLoops")


# Create singleton instance
agent_loop_manager = AgentLoopManager()

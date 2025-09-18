"""
Improved AgentLoop and AgentLoopManager classes for OpenVibe backend.
Manages agent conversations using openhands-sdk Agent and Conversation with proper
threading, error handling, and resource management.

Key improvements:
- Simplified threading model using ThreadPoolExecutor
- Proper error handling and recovery mechanisms
- SDK-aligned state management
- Robust tool configuration with path validation
- Resource cleanup and lifecycle management
"""

import sys
import os
import uuid
import traceback
from typing import Dict, Optional, Callable, Any
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, Future
from utils.logging import get_logger

# Add the site-packages to the path for openhands imports
sys.path.insert(0, ".venv/lib/python3.12/site-packages")

from openhands.sdk import (
    Agent,
    Conversation,
    LLM,
    Message,
    TextContent,
    AgentContext,
    LocalFileStore,
    Event,
)
from openhands.sdk.context import render_template
from openhands.sdk.conversation.state import AgentExecutionStatus
from openhands.tools import FileEditorTool, TaskTrackerTool, BashTool
from storage import get_keys_storage

logger = get_logger(__name__)


def ensure_directory_exists(path: str) -> bool:
    """Ensure a directory exists, creating it if necessary."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create directory {path}: {e}")
        return False


def create_env_provider(user_uuid: str) -> Callable[[str], Dict[str, str]]:
    """Create an environment provider that includes user secrets as environment variables."""

    def env_provider(command: str) -> Dict[str, str]:
        """Provide environment variables including user secrets."""
        env = {}

        try:
            # Get user storage and retrieve secrets
            keys_storage = get_keys_storage(user_uuid)
            user_keys = keys_storage.load_keys()

            # Map user keys to environment variables
            if user_keys.get("github"):
                env["GITHUB_TOKEN"] = user_keys["github"]
                logger.debug(
                    f"✅ Added GITHUB_TOKEN to environment for user {user_uuid}"
                )

            if user_keys.get("fly"):
                env["FLY_TOKEN"] = user_keys["fly"]
                logger.debug(f"✅ Added FLY_TOKEN to environment for user {user_uuid}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to retrieve user secrets for {user_uuid}: {e}")

        return env

    return env_provider


def create_env_masker(user_uuid: str) -> Callable[[str], str]:
    """Create an environment masker that hides sensitive credentials in logs and outputs."""

    def env_masker(text: str) -> str:
        """Mask sensitive environment variables in text output."""
        if not text:
            return text

        masked_text = text

        try:
            # Get user storage and retrieve secrets to know what to mask
            keys_storage = get_keys_storage(user_uuid)
            user_keys = keys_storage.load_keys()

            # Mask GitHub token if it exists
            if user_keys.get("github"):
                github_token = user_keys["github"]
                if github_token and len(github_token) > 8:
                    # Show first 4 and last 4 characters, mask the middle
                    masked_token = f"{github_token[:4]}{'*' * (len(github_token) - 8)}{github_token[-4:]}"
                    masked_text = masked_text.replace(github_token, masked_token)

            # Mask Fly token if it exists
            if user_keys.get("fly"):
                fly_token = user_keys["fly"]
                if fly_token and len(fly_token) > 8:
                    # Show first 4 and last 4 characters, mask the middle
                    masked_token = (
                        f"{fly_token[:4]}{'*' * (len(fly_token) - 8)}{fly_token[-4:]}"
                    )
                    masked_text = masked_text.replace(fly_token, masked_token)

        except Exception as e:
            logger.debug(f"⚠️ Failed to mask credentials for user {user_uuid}: {e}")

        return masked_text

    return env_masker


def create_tools_with_validation(workspace_path: str, user_uuid: str) -> list:
    """Create tools with proper path validation and setup, including user secrets."""
    tools = []

    # Ensure workspace exists
    if not ensure_directory_exists(workspace_path):
        raise ValueError(f"Cannot create workspace directory: {workspace_path}")

    # Create project directory if it doesn't exist
    project_dir = os.path.join(workspace_path, "project")
    if not ensure_directory_exists(project_dir):
        logger.warning(f"⚠️ Could not create project directory: {project_dir}")
        # Fall back to workspace root for bash operations
        project_dir = workspace_path

    # Create tasks directory for TaskTracker
    tasks_dir = os.path.join(workspace_path, "tasks")
    if not ensure_directory_exists(tasks_dir):
        logger.warning(f"⚠️ Could not create tasks directory: {tasks_dir}")
        # Fall back to workspace root
        tasks_dir = workspace_path

    try:
        # FileEditorTool - no specific directory needed
        tools.append(FileEditorTool.create())
        logger.info(f"✅ Created FileEditorTool")

        # TaskTrackerTool - save to tasks directory
        tools.append(TaskTrackerTool.create(save_dir=tasks_dir))
        logger.info(f"✅ Created TaskTrackerTool with save_dir: {tasks_dir}")

        # BashTool - work in project directory with user secrets as environment variables
        env_provider = create_env_provider(user_uuid)
        env_masker = create_env_masker(user_uuid)
        tools.append(
            BashTool.create(
                working_dir=project_dir,
                env_provider=env_provider,
                env_masker=env_masker,
            )
        )
        logger.info(
            f"✅ Created BashTool with working_dir: {project_dir}, secrets environment, and credential masking"
        )

    except Exception as e:
        logger.error(f"❌ Failed to create tools: {e}")
        raise

    return tools


class CustomAgentContext(AgentContext):
    """Custom AgentContext that can store workspace_path."""

    workspace_path: str = "/tmp"  # default value


class CustomAgent(Agent):
    """Custom Agent that uses our local system prompt template."""

    @property
    def prompt_dir(self) -> str:
        """Override to use our backend/prompts directory."""
        return os.path.join(os.path.dirname(__file__), "prompts")

    @property
    def system_message(self) -> str:
        """Compute system message with workspace_path template variable."""
        # Get the workspace_path from agent_context if available
        workspace_path = "/tmp"  # default
        if self.agent_context and isinstance(self.agent_context, CustomAgentContext):
            workspace_path = self.agent_context.workspace_path

        # Prepare template kwargs, including cli_mode if available (like base class)
        template_kwargs = dict(self.system_prompt_kwargs)
        if hasattr(self, "cli_mode"):
            template_kwargs["cli_mode"] = getattr(self, "cli_mode")

        # Add workspace_path to template kwargs
        template_kwargs["workspace_path"] = workspace_path

        system_message = render_template(
            prompt_dir=self.prompt_dir,
            template_name=self.system_prompt_filename,
            **template_kwargs,
        )

        # Note: We don't append system_message_suffix since we've integrated
        # everything into the main template
        return system_message


def create_agent(llm, tools, workspace_path):
    """Create an agent with development tools and workspace configuration"""
    # Create a custom agent context to store workspace_path for template rendering
    agent_context = CustomAgentContext(workspace_path=workspace_path)

    return CustomAgent(llm=llm, tools=tools, agent_context=agent_context)


class AgentLoop:
    """
    Represents an agent conversation loop for a specific user, app, and riff.
    Contains an Agent and Conversation instance from openhands-sdk, running in a thread.
    """

    def __init__(
        self,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        llm: LLM,
        workspace_path: str,
        message_callback: Optional[Callable] = None,
    ):
        """Initialize an AgentLoop instance with improved error handling."""
        self.user_uuid = user_uuid
        self.app_slug = app_slug
        self.riff_slug = riff_slug
        self.llm = llm
        self.message_callback = message_callback

        # Validate workspace_path
        if not workspace_path:
            raise ValueError("workspace_path is required and cannot be None or empty")

        if not os.path.isabs(workspace_path):
            raise ValueError("workspace_path must be an absolute path")

        self.workspace_path = workspace_path

        # Create state directory as sibling of workspace
        workspace_parent = os.path.dirname(workspace_path)
        self.state_path = os.path.join(workspace_parent, "state")

        if not ensure_directory_exists(self.state_path):
            raise ValueError(f"Cannot create state directory: {self.state_path}")

        # Create tools with validation
        try:
            tools = create_tools_with_validation(self.workspace_path, self.user_uuid)
        except Exception as e:
            logger.error(f"❌ Failed to create tools for {self.get_key()}: {e}")
            raise

        # Create agent
        try:
            self.agent = create_agent(llm, tools, self.workspace_path)
        except Exception as e:
            logger.error(f"❌ Failed to create agent for {self.get_key()}: {e}")
            raise

        # Create LocalFileStore for persistence
        try:
            self.file_store = LocalFileStore(self.state_path)
        except Exception as e:
            logger.error(f"❌ Failed to create file store for {self.get_key()}: {e}")
            raise

        # Generate conversation ID as a proper UUID object
        # Use uuid5 to create a deterministic UUID from the user/app/riff combination
        conversation_key = f"{user_uuid}:{app_slug}:{riff_slug}"
        conversation_id = uuid.uuid5(uuid.NAMESPACE_DNS, conversation_key)

        # Create conversation with callbacks
        callbacks = []
        if message_callback:
            callbacks.append(self._safe_event_callback)

        try:
            self.conversation = Conversation(
                agent=self.agent,
                callbacks=callbacks,
                persist_filestore=self.file_store,
                conversation_id=conversation_id,
                visualize=False,
            )
        except Exception as e:
            logger.error(f"❌ Failed to create conversation for {self.get_key()}: {e}")
            raise

        # Thread management - simplified approach
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix=f"Agent-{self.get_key()}"
        )
        self._current_task: Optional[Future] = None
        self._lock = Lock()
        self._is_running = False

        logger.info(f"🤖 Created improved AgentLoop for {self.get_key()}")

    @classmethod
    def from_existing_state(
        cls,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        llm: LLM,
        workspace_path: str,
        message_callback: Optional[Callable] = None,
    ):
        """Create an AgentLoop from existing persisted state with improved error handling."""
        # Check if state exists
        workspace_parent = os.path.dirname(workspace_path)
        state_path = os.path.join(workspace_parent, "state")

        if not os.path.exists(state_path):
            logger.warning(
                f"⚠️ No existing state found at {state_path}, creating new AgentLoop"
            )
            return cls(
                user_uuid, app_slug, riff_slug, llm, workspace_path, message_callback
            )

        try:
            # Create new instance - the Conversation constructor will automatically load existing state
            instance = cls(
                user_uuid, app_slug, riff_slug, llm, workspace_path, message_callback
            )
            logger.info(
                f"🔄 Reconstructed AgentLoop from existing state for {instance.get_key()}"
            )
            return instance
        except Exception as e:
            logger.error(f"❌ Failed to reconstruct AgentLoop from state: {e}")
            # Fall back to creating a new instance
            logger.info("🔄 Falling back to creating new AgentLoop")
            return cls(
                user_uuid, app_slug, riff_slug, llm, workspace_path, message_callback
            )

    def _safe_event_callback(self, event: Event):
        """Safe wrapper for event callbacks with proper error handling."""
        try:
            if self.message_callback:
                self.message_callback(event)
        except Exception as e:
            logger.error(f"❌ Error in event callback for {self.get_key()}: {e}")
            # Don't re-raise - we don't want callback errors to break the agent

    def get_key(self) -> str:
        """Get the unique key for this agent loop"""
        return f"{self.user_uuid}:{self.app_slug}:{self.riff_slug}"

    def _run_conversation_safely(self):
        """Run the conversation with proper error handling and cleanup."""
        try:
            logger.info(f"🔄 Starting conversation execution for {self.get_key()}")
            self.conversation.run()
            logger.info(f"✅ Conversation execution completed for {self.get_key()}")
        except Exception as e:
            logger.error(
                f"❌ Error in conversation execution for {self.get_key()}: {e}"
            )
            # Log the full traceback for debugging
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
        finally:
            with self._lock:
                self._is_running = False
            logger.info(f"🏁 Conversation task finished for {self.get_key()}")

    def send_message(self, message: str) -> str:
        """
        Send a message to the agent with improved error handling and threading.

        Args:
            message: The user message to send

        Returns:
            A confirmation message
        """
        logger.info(f"💬 Sending message to agent for {self.get_key()}")

        try:
            # Create a Message object
            user_message = Message(role="user", content=[TextContent(text=message)])

            # Send message to conversation
            self.conversation.send_message(user_message)

            # Start conversation processing in background thread
            with self._lock:
                # Cancel any existing task
                if self._current_task and not self._current_task.done():
                    logger.info(
                        f"🔄 Cancelling existing conversation task for {self.get_key()}"
                    )
                    self._current_task.cancel()

                # Submit new conversation task
                self._current_task = self._executor.submit(
                    self._run_conversation_safely
                )
                self._is_running = True

            logger.info(
                f"✅ Message sent and conversation started for {self.get_key()}"
            )
            return "Message sent to agent. Response will be processed asynchronously."

        except Exception as e:
            logger.error(f"❌ Error sending message to agent for {self.get_key()}: {e}")
            with self._lock:
                self._is_running = False
            raise

    def get_all_events(self):
        """
        Retrieve all events from the agent conversation.

        Returns:
            list: List of all events from the conversation
        """
        try:
            if (
                self.conversation
                and hasattr(self.conversation, "state")
                and hasattr(self.conversation.state, "events")
            ):
                return self.conversation.state.events
            else:
                logger.warning(f"⚠️ No events available for {self.get_key()}")
                return []
        except Exception as e:
            logger.error(f"❌ Error retrieving events for {self.get_key()}: {e}")
            return []

    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status information as transparent passthrough from SDK."""
        try:
            if not self.conversation or not hasattr(self.conversation, "state"):
                return {
                    "status": "not_initialized",
                    "error": "Conversation not initialized",
                    "is_running": False,
                    "has_active_task": False,
                    "event_count": 0,
                }

            state = self.conversation.state
            agent_status = getattr(state, "agent_status", None)

            with self._lock:
                has_active_task = (
                    self._current_task is not None and not self._current_task.done()
                )
                is_running = self._is_running

            # Get event count for activity indication
            events = getattr(state, "events", [])

            # Return SDK agent_status as the primary status field (transparent passthrough)
            sdk_status = agent_status.value if agent_status else "idle"

            # Convert UUID to string for JSON serialization
            conversation_id = getattr(state, "id", None)
            conversation_id_str = str(conversation_id) if conversation_id else None

            return {
                "status": sdk_status,  # Primary status field - direct from SDK
                "is_running": is_running,
                "has_active_task": has_active_task,
                "conversation_id": conversation_id_str,
                "event_count": len(events),
                "workspace_path": self.workspace_path,
                "state_path": self.state_path,
                # Keep agent_status for backward compatibility
                "agent_status": sdk_status,
            }

        except Exception as e:
            logger.error(f"❌ Error getting agent status for {self.get_key()}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "is_running": False,
                "has_active_task": False,
                "event_count": 0,
                "agent_status": "error",
            }

    def pause_agent(self) -> bool:
        """Pause the agent execution using SDK methods."""
        try:
            if not self.conversation:
                logger.warning(
                    f"⚠️ Cannot pause agent for {self.get_key()}: conversation not available"
                )
                return False

            self.conversation.pause()
            logger.info(f"⏸️ Agent paused for {self.get_key()}")
            return True

        except Exception as e:
            logger.error(f"❌ Error pausing agent for {self.get_key()}: {e}")
            return False

    def resume_agent(self) -> bool:
        """Resume the agent execution."""
        try:
            if not self.conversation:
                logger.warning(
                    f"⚠️ Cannot resume agent for {self.get_key()}: conversation not available"
                )
                return False

            # Check if agent is in a resumable state
            status = self.get_agent_status()
            agent_status = status.get("agent_status")

            if agent_status == AgentExecutionStatus.FINISHED.value:
                logger.info(f"ℹ️ Agent for {self.get_key()} is finished, cannot resume")
                return False

            if agent_status == AgentExecutionStatus.PAUSED.value:
                # Resume by running the conversation
                with self._lock:
                    if self._current_task and not self._current_task.done():
                        logger.info(
                            f"ℹ️ Agent for {self.get_key()} already has active task"
                        )
                        return True

                    self._current_task = self._executor.submit(
                        self._run_conversation_safely
                    )
                    self._is_running = True

                logger.info(f"▶️ Agent resumed for {self.get_key()}")
                return True
            else:
                logger.info(
                    f"ℹ️ Agent for {self.get_key()} is not paused (status: {agent_status})"
                )
                return True

        except Exception as e:
            logger.error(f"❌ Error resuming agent for {self.get_key()}: {e}")
            return False

    def cleanup(self):
        """Clean up resources properly."""
        logger.info(f"🧹 Cleaning up resources for {self.get_key()}")

        try:
            with self._lock:
                # Cancel any running task
                if self._current_task and not self._current_task.done():
                    logger.info(f"🔄 Cancelling active task for {self.get_key()}")
                    self._current_task.cancel()

                self._is_running = False

            # Shutdown the executor
            if self._executor:
                logger.info(f"🔄 Shutting down executor for {self.get_key()}")
                self._executor.shutdown(wait=True, timeout=10)

        except Exception as e:
            logger.error(f"❌ Error during cleanup for {self.get_key()}: {e}")

        logger.info(f"✅ Cleanup completed for {self.get_key()}")


class AgentLoopManager:
    """
    Improved singleton manager for AgentLoop instances with better resource management.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Ensure singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AgentLoopManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the manager (only once due to singleton pattern)"""
        if not self._initialized:
            self.agent_loops: Dict[str, AgentLoop] = {}
            self._initialized = True
            logger.info("🏗️ Improved AgentLoopManager initialized")

    def _get_key(self, user_uuid: str, app_slug: str, riff_slug: str) -> str:
        """Generate a unique key for the agent loop"""
        key = f"{user_uuid}:{app_slug}:{riff_slug}"
        logger.debug(f"🔑 Generated key: {key}")
        return key

    def create_agent_loop(
        self,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        llm: LLM,
        workspace_path: str,
        message_callback: Optional[Callable] = None,
    ) -> AgentLoop:
        """
        Create a new AgentLoop and store it in the dictionary.

        Args:
            user_uuid: Unique identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation
            llm: LLM instance from openhands-sdk
            workspace_path: Required path to the workspace directory (cloned repository)
            message_callback: Optional callback function to handle events/messages

        Returns:
            The created AgentLoop instance
        """
        key = self._get_key(user_uuid, app_slug, riff_slug)

        with self._lock:
            # Clean up existing agent loop if it exists
            if key in self.agent_loops:
                logger.warning(
                    f"⚠️ AgentLoop already exists for {key}, cleaning up old instance"
                )
                old_loop = self.agent_loops[key]
                try:
                    old_loop.cleanup()
                except Exception as e:
                    logger.error(f"❌ Error cleaning up old agent loop: {e}")

            try:
                agent_loop = AgentLoop(
                    user_uuid,
                    app_slug,
                    riff_slug,
                    llm,
                    workspace_path,
                    message_callback,
                )
                self.agent_loops[key] = agent_loop

                logger.info(f"✅ Created and stored improved AgentLoop for {key}")
                logger.info(f"📊 Total agent loops: {len(self.agent_loops)}")

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
    ) -> AgentLoop:
        """
        Create an AgentLoop from existing persisted state and store it in the dictionary.
        This method reconstructs the agent from its serialization instead of creating a new one.

        Args:
            user_uuid: Unique identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation
            llm: LLM instance from openhands-sdk
            workspace_path: Required path to the workspace directory (cloned repository)
            message_callback: Optional callback function to handle events/messages

        Returns:
            The reconstructed AgentLoop instance
        """
        key = self._get_key(user_uuid, app_slug, riff_slug)

        with self._lock:
            # Clean up existing agent loop if it exists
            if key in self.agent_loops:
                logger.warning(
                    f"⚠️ AgentLoop already exists for {key}, cleaning up old instance"
                )
                old_loop = self.agent_loops[key]
                try:
                    old_loop.cleanup()
                except Exception as e:
                    logger.error(f"❌ Error cleaning up old agent loop: {e}")

            try:
                agent_loop = AgentLoop.from_existing_state(
                    user_uuid,
                    app_slug,
                    riff_slug,
                    llm,
                    workspace_path,
                    message_callback,
                )
                self.agent_loops[key] = agent_loop

                logger.info(f"✅ Reconstructed and stored improved AgentLoop for {key}")
                logger.info(f"📊 Total agent loops: {len(self.agent_loops)}")

                return agent_loop

            except Exception as e:
                logger.error(f"❌ Failed to reconstruct AgentLoop for {key}: {e}")
                raise

    def get_agent_loop(
        self, user_uuid: str, app_slug: str, riff_slug: str
    ) -> Optional[AgentLoop]:
        """
        Retrieve an existing AgentLoop from the dictionary.

        Args:
            user_uuid: Unique identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation

        Returns:
            The AgentLoop instance if found, None otherwise
        """
        key = self._get_key(user_uuid, app_slug, riff_slug)

        with self._lock:
            agent_loop = self.agent_loops.get(key)

            if agent_loop:
                logger.info(f"✅ Retrieved AgentLoop for {key}")
            else:
                logger.warning(f"❌ AgentLoop not found for {key}")
                logger.debug(f"🔑 Available keys: {list(self.agent_loops.keys())}")
                logger.info(f"🔍 Searching for key: '{key}'")
                # Check for partial matches to help debug
                for stored_key in self.agent_loops.keys():
                    if user_uuid in stored_key:
                        logger.info(
                            f"🔍 Found partial match with user_uuid: '{stored_key}'"
                        )

            return agent_loop

    def remove_agent_loop(self, user_uuid: str, app_slug: str, riff_slug: str) -> bool:
        """
        Remove an AgentLoop from the dictionary.

        Args:
            user_uuid: Unique identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation

        Returns:
            True if removed, False if not found
        """
        key = self._get_key(user_uuid, app_slug, riff_slug)

        with self._lock:
            if key in self.agent_loops:
                agent_loop = self.agent_loops[key]

                try:
                    # Clean up resources
                    agent_loop.cleanup()
                except Exception as e:
                    logger.error(f"❌ Error during agent loop cleanup: {e}")

                del self.agent_loops[key]
                logger.info(f"🗑️ Removed AgentLoop for {key}")
                logger.debug(f"📊 Total agent loops: {len(self.agent_loops)}")
                return True
            else:
                logger.warning(f"❌ AgentLoop not found for removal: {key}")
                return False

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the agent loops."""
        with self._lock:
            stats = {
                "total_loops": len(self.agent_loops),
                "active_users": len(
                    set(loop.user_uuid for loop in self.agent_loops.values())
                ),
                "active_apps": len(
                    set(loop.app_slug for loop in self.agent_loops.values())
                ),
                "loop_details": {},
            }

            # Add detailed status for each loop
            for key, loop in self.agent_loops.items():
                try:
                    status = loop.get_agent_status()
                    loop_details = stats["loop_details"]
                    if isinstance(loop_details, dict):
                        loop_details[key] = {
                            "status": status.get("status"),
                            "agent_status": status.get("agent_status"),
                            "is_running": status.get("is_running", False),
                            "has_active_task": status.get("has_active_task", False),
                            "event_count": status.get("event_count", 0),
                        }
                except Exception as e:
                    loop_details = stats["loop_details"]
                    if isinstance(loop_details, dict):
                        loop_details[key] = {"error": str(e)}

            return stats

    def cleanup_all(self):
        """Clean up all agent loops - useful for shutdown."""
        logger.info("🧹 Cleaning up all agent loops")

        with self._lock:
            for key, agent_loop in list(self.agent_loops.items()):
                try:
                    agent_loop.cleanup()
                except Exception as e:
                    logger.error(f"❌ Error cleaning up agent loop {key}: {e}")

            self.agent_loops.clear()

        logger.info("✅ All agent loops cleaned up")


# Global instance
agent_loop_manager = AgentLoopManager()

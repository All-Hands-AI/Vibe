"""
Improved AgentLoop and AgentLoopManager classes for OpenVibe backend.
Manages agent conversations using both local and remote OpenHands runtimes with proper
threading, error handling, and resource management.

Key improvements:
- Support for both local and remote runtimes
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
from typing import Dict, Optional, Callable, Any, Union
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, Future
from utils.logging import get_logger
from remote_runtime_client import RemoteRuntimeClient, RemoteConversationInfo

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

logger = get_logger(__name__)


def ensure_directory_exists(path: str) -> bool:
    """Ensure a directory exists, creating it if necessary."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create directory {path}: {e}")
        return False


def create_tools_with_validation(workspace_path: str) -> list:
    """Create tools with proper path validation and setup."""
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

        # BashTool - work in project directory
        tools.append(BashTool.create(working_dir=project_dir))
        logger.info(f"✅ Created BashTool with working_dir: {project_dir}")

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
    Supports both local and remote runtime execution modes.
    """

    def __init__(
        self,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        llm: LLM,
        workspace_path: str,
        message_callback: Optional[Callable] = None,
        use_remote_runtime: bool = False,
        remote_runtime_client: Optional[RemoteRuntimeClient] = None,
    ):
        """Initialize an AgentLoop instance with support for local and remote runtimes."""
        self.user_uuid = user_uuid
        self.app_slug = app_slug
        self.riff_slug = riff_slug
        self.llm = llm
        self.message_callback = message_callback
        self.use_remote_runtime = use_remote_runtime
        self.remote_runtime_client = remote_runtime_client

        # Validate workspace_path
        if not workspace_path:
            raise ValueError("workspace_path is required and cannot be None or empty")

        if not os.path.isabs(workspace_path):
            raise ValueError("workspace_path must be an absolute path")

        self.workspace_path = workspace_path

        # Initialize runtime-specific components
        if self.use_remote_runtime:
            self._init_remote_runtime()
        else:
            self._init_local_runtime()

        # Thread management - simplified approach
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix=f"Agent-{self.get_key()}"
        )
        self._current_task: Optional[Future] = None
        self._lock = Lock()
        self._is_running = False

        logger.info(f"🤖 Created AgentLoop ({'remote' if use_remote_runtime else 'local'}) for {self.get_key()}")

    def _init_local_runtime(self):
        """Initialize local runtime components."""
        # Create state directory as sibling of workspace
        workspace_parent = os.path.dirname(self.workspace_path)
        self.state_path = os.path.join(workspace_parent, "state")

        if not ensure_directory_exists(self.state_path):
            raise ValueError(f"Cannot create state directory: {self.state_path}")

        # Create tools with validation
        try:
            tools = create_tools_with_validation(self.workspace_path)
        except Exception as e:
            logger.error(f"❌ Failed to create tools for {self.get_key()}: {e}")
            raise

        # Create agent
        try:
            self.agent = create_agent(self.llm, tools, self.workspace_path)
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
        conversation_key = f"{self.user_uuid}:{self.app_slug}:{self.riff_slug}"
        conversation_id = uuid.uuid5(uuid.NAMESPACE_DNS, conversation_key)

        # Create conversation with callbacks
        callbacks = []
        if self.message_callback:
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

        # Set runtime-specific attributes
        self.remote_conversation_info = None

    def _init_remote_runtime(self):
        """Initialize remote runtime components."""
        if not self.remote_runtime_client:
            raise ValueError("remote_runtime_client is required when use_remote_runtime=True")

        # Set local attributes to None for remote runtime
        self.agent = None
        self.conversation = None
        self.file_store = None
        self.state_path = None

        # Start remote runtime
        try:
            runtime_info = self.remote_runtime_client.start_remote_runtime(
                working_dir=self.workspace_path,
                environment={"DEBUG": "true"},
            )
            logger.info(f"✅ Started remote runtime: {runtime_info.runtime_id}")
        except Exception as e:
            logger.error(f"❌ Failed to start remote runtime for {self.get_key()}: {e}")
            raise

        # Prepare LLM configuration for remote agent
        llm_config = {
            "model": self.llm.model,
            "api_key": self.llm.api_key.get_secret_value() if self.llm.api_key else None,
            "base_url": self.llm.base_url,
        }

        # Create remote conversation
        try:
            self.remote_conversation_info = self.remote_runtime_client.create_conversation(
                runtime_info=runtime_info,
                llm_config=llm_config,
                workspace_path=self.workspace_path,
            )
            logger.info(f"✅ Created remote conversation: {self.remote_conversation_info.conversation_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create remote conversation for {self.get_key()}: {e}")
            raise

    @classmethod
    def from_existing_state(
        cls,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        llm: LLM,
        workspace_path: str,
        message_callback: Optional[Callable] = None,
        use_remote_runtime: bool = False,
        remote_runtime_client: Optional[RemoteRuntimeClient] = None,
    ):
        """Create an AgentLoop from existing persisted state with improved error handling."""
        # For remote runtimes, we don't have local state to restore from
        if use_remote_runtime:
            logger.info("🔄 Remote runtime mode - creating new AgentLoop (no local state)")
            return cls(
                user_uuid, app_slug, riff_slug, llm, workspace_path, message_callback,
                use_remote_runtime, remote_runtime_client
            )

        # Check if local state exists
        workspace_parent = os.path.dirname(workspace_path)
        state_path = os.path.join(workspace_parent, "state")

        if not os.path.exists(state_path):
            logger.warning(
                f"⚠️ No existing state found at {state_path}, creating new AgentLoop"
            )
            return cls(
                user_uuid, app_slug, riff_slug, llm, workspace_path, message_callback,
                use_remote_runtime, remote_runtime_client
            )

        try:
            # Create new instance - the Conversation constructor will automatically load existing state
            instance = cls(
                user_uuid, app_slug, riff_slug, llm, workspace_path, message_callback,
                use_remote_runtime, remote_runtime_client
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
                user_uuid, app_slug, riff_slug, llm, workspace_path, message_callback,
                use_remote_runtime, remote_runtime_client
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
            if self.use_remote_runtime:
                # Send message to remote runtime
                success = self.remote_runtime_client.send_message(
                    self.remote_conversation_info, message, run=True
                )
                if success:
                    logger.info(f"✅ Message sent to remote agent for {self.get_key()}")
                    return "Message sent to remote agent. Response will be processed asynchronously."
                else:
                    raise Exception("Failed to send message to remote agent")
            else:
                # Local runtime - existing logic
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
            if self.use_remote_runtime:
                # Get events from remote runtime
                events = self.remote_runtime_client.get_conversation_events(
                    self.remote_conversation_info, limit=1000
                )
                return events
            else:
                # Local runtime - existing logic
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
            if self.use_remote_runtime:
                # Get status from remote runtime
                try:
                    remote_status = self.remote_runtime_client.get_conversation_status(
                        self.remote_conversation_info
                    )
                    
                    return {
                        "status": remote_status.get("status", "idle"),
                        "is_running": False,  # Remote runtime manages its own execution
                        "has_active_task": False,  # Remote runtime manages its own tasks
                        "conversation_id": self.remote_conversation_info.conversation_id,
                        "event_count": 0,  # Would need separate call to get event count
                        "workspace_path": self.workspace_path,
                        "state_path": None,  # No local state path for remote runtime
                        "agent_status": remote_status.get("status", "idle"),
                        "runtime_type": "remote",
                        "runtime_id": self.remote_conversation_info.runtime_info.runtime_id,
                    }
                except Exception as e:
                    logger.error(f"❌ Error getting remote status for {self.get_key()}: {e}")
                    return {
                        "status": "error",
                        "error": f"Remote status error: {str(e)}",
                        "is_running": False,
                        "has_active_task": False,
                        "event_count": 0,
                        "agent_status": "error",
                        "runtime_type": "remote",
                    }
            else:
                # Local runtime - existing logic
                if not self.conversation or not hasattr(self.conversation, "state"):
                    return {
                        "status": "not_initialized",
                        "error": "Conversation not initialized",
                        "is_running": False,
                        "has_active_task": False,
                        "event_count": 0,
                        "runtime_type": "local",
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
                    "runtime_type": "local",
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
                "runtime_type": "local" if not self.use_remote_runtime else "remote",
            }

    def pause_agent(self) -> bool:
        """Pause the agent execution using SDK methods."""
        try:
            if self.use_remote_runtime:
                # Pause remote conversation
                success = self.remote_runtime_client.pause_conversation(
                    self.remote_conversation_info
                )
                if success:
                    logger.info(f"⏸️ Remote agent paused for {self.get_key()}")
                return success
            else:
                # Local runtime - existing logic
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
            if self.use_remote_runtime:
                # Resume remote conversation
                success = self.remote_runtime_client.resume_conversation(
                    self.remote_conversation_info
                )
                if success:
                    logger.info(f"▶️ Remote agent resumed for {self.get_key()}")
                return success
            else:
                # Local runtime - existing logic
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
            if self.use_remote_runtime:
                # Clean up remote runtime resources
                if self.remote_conversation_info and self.remote_runtime_client:
                    self.remote_runtime_client.cleanup_conversation(
                        self.remote_conversation_info.conversation_id
                    )
                    # Also cleanup the runtime if needed
                    self.remote_runtime_client.cleanup_runtime(
                        self.remote_conversation_info.runtime_info.runtime_id
                    )
            else:
                # Local runtime cleanup
                with self._lock:
                    # Cancel any running task
                    if self._current_task and not self._current_task.done():
                        logger.info(f"🔄 Cancelling active task for {self.get_key()}")
                        self._current_task.cancel()

                    self._is_running = False

            # Shutdown the executor (common for both local and remote)
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
        use_remote_runtime: bool = False,
        remote_runtime_client: Optional[RemoteRuntimeClient] = None,
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
            use_remote_runtime: Whether to use remote runtime instead of local
            remote_runtime_client: Client for remote runtime communication

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
                    use_remote_runtime,
                    remote_runtime_client,
                )
                self.agent_loops[key] = agent_loop

                runtime_type = "remote" if use_remote_runtime else "local"
                logger.info(f"✅ Created and stored {runtime_type} AgentLoop for {key}")
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
        use_remote_runtime: bool = False,
        remote_runtime_client: Optional[RemoteRuntimeClient] = None,
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
            use_remote_runtime: Whether to use remote runtime instead of local
            remote_runtime_client: Client for remote runtime communication

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
                    use_remote_runtime,
                    remote_runtime_client,
                )
                self.agent_loops[key] = agent_loop

                runtime_type = "remote" if use_remote_runtime else "local"
                logger.info(f"✅ Reconstructed and stored {runtime_type} AgentLoop for {key}")
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

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
    EventBase,
    ToolSpec,
)

from openhands.sdk.conversation.state import AgentExecutionStatus

# Import tools to register them automatically
from openhands.tools.str_replace_editor import FileEditorTool  # noqa: F401
from openhands.tools.task_tracker import TaskTrackerTool  # noqa: F401
from openhands.tools.execute_bash import BashTool  # noqa: F401

logger = get_logger(__name__)

# Import runtime service for checking runtime alive status
from services.runtime_service import runtime_service


def ensure_directory_exists(path: str) -> bool:
    """Ensure a directory exists, creating it if necessary."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create directory {path}: {e}")
        return False


def create_tools_with_validation(
    workspace_path: str, use_remote_runtime: bool = False
) -> list:
    """Create tools with proper path validation and setup."""
    # Register default tools first
    from openhands.sdk.preset.default import register_default_tools

    register_default_tools(enable_browser=False)
    logger.info("✅ Registered default tools")

    tools = []

    if use_remote_runtime:
        # For remote runtimes, use fixed paths that match the remote environment
        project_dir = "/workspace/project"
        tasks_dir = "/workspace/tasks"
        logger.info(
            f"🌐 Using remote runtime paths - project_dir: {project_dir}, tasks_dir: {tasks_dir}"
        )
    else:
        # For local runtimes, use workspace_path-based directories
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
        # BashTool - work in project directory
        tools.append(ToolSpec(name="BashTool", params={"working_dir": project_dir}))
        logger.info(f"✅ Created BashTool with working_dir: {project_dir}")

        # FileEditorTool - workspace root directory
        tools.append(
            ToolSpec(name="FileEditorTool", params={"workspace_root": project_dir})
        )
        logger.info(f"✅ Created FileEditorTool with workspace_root: {project_dir}")

        # TaskTrackerTool - save to tasks directory
        tools.append(ToolSpec(name="TaskTrackerTool", params={"save_dir": tasks_dir}))
        logger.info(f"✅ Created TaskTrackerTool with save_dir: {tasks_dir}")

    except Exception as e:
        logger.error(f"❌ Failed to create tools: {e}")
        raise

    return tools


def create_agent(llm, tools, workspace_path, use_remote_runtime: bool = False):
    """Create an agent with development tools and workspace configuration"""
    # For remote runtimes, tell the agent about the remote workspace path
    if use_remote_runtime:
        agent_workspace_path = "/workspace"
    else:
        agent_workspace_path = workspace_path

    # Create workspace-specific system message suffix
    workspace_suffix = f"""
<TASK_MANAGEMENT>
* You have access to the `task_tracker` tool to help you organize and monitor development work. Use this tool REGULARLY to maintain task visibility and provide users with clear progress updates. This tool is ESSENTIAL for systematic planning and decomposing complex development work into manageable components. Failing to use this tool for planning may result in overlooked requirements - which is unacceptable.
* It is crucial that you update task status to "done" immediately upon completion of each work item. Do not accumulate multiple finished tasks before updating their status.
* For complex, multi-phase development work, use `task_tracker` to establish a comprehensive plan with well-defined steps:
  1. Begin by decomposing the overall objective into primary phases using `task_tracker`
  2. Include detailed work items as necessary to break complex activities into actionable units
  3. Update tasks to "in_progress" status when commencing work on them
  4. Update tasks to "done" status immediately after completing each item
  5. For each primary phase, incorporate additional work items as you identify new requirements
  6. If you determine the plan requires substantial modifications, suggest revisions and obtain user confirmation before proceeding
* Example workflow for debugging and resolution:
  ```
  User: "Execute the test suite and resolve any validation failures"
  Assistant: I'm going to use the task_tracker tool to organize the following work items:
  - Execute the test suite
  - Resolve any validation failures
  I'm now going to run the test suite using the terminal.
  [After running tests and discovering 8 validation failures]
  I found 8 validation failures that need attention. I'm going to use the task_tracker tool to add 8 specific items to the task list.
  [Updating first task to in_progress]
  Let me begin addressing the first validation issue...
  [After resolving first failure]
  The first validation issue has been resolved, let me mark that task as done and proceed to the second item...
  ```
* Example workflow for component development:
  ```
  User: "Build a dashboard component that displays analytics data with interactive charts and filtering options"
  Assistant: I'll help you create an analytics dashboard with interactive charts and filtering. Let me first use the task_tracker tool to organize this development work.
  Adding the following tasks to the tracker:
  1. Analyze existing analytics data structure and requirements
  2. Design dashboard layout and component architecture
  3. Implement data visualization charts with interactivity
  4. Create filtering and search functionality
  5. Integrate components and perform testing
  Let me start by examining the current analytics data structure to understand what we're working with...
  [Assistant proceeds with implementation step by step, updating tasks to in_progress and done as work progresses]
  ```
</TASK_MANAGEMENT>

<TASK_TRACKING_PERSISTENCE>
* IMPORTANT: If you were using the task_tracker tool before a condensation event, continue using it after condensation
* Check condensation summaries for TASK_TRACKING sections to maintain continuity
* If you see a condensation event with TASK_TRACKING, immediately use task_tracker to view and continue managing them
</TASK_TRACKING_PERSISTENCE>

WORKSPACE INFORMATION:
You are working in a workspace located at: {agent_workspace_path}/project/

<IMPORTANT>
Do all your work in the directory {agent_workspace_path}/project/
</IMPORTANT>

This workspace has a git repository in it.

When using the FileEditor tool, always use absolute paths.

<WORKFLOW>
Only work on the current branch. Push to its analog on the remote branch.

<IMPORTANT>
COMMIT AND PUSH your work whenever you've made an improvement. DO NOT wait for the user to tell you to push.
</IMPORTANT>

Whenever you push, ALWAYS update the PR title and description, unless you're sure they don't need updating.
PR title should ALWAYS begin with [Riff $riffname] where $riffname is the name of the current riff.
For subsequent pushes, update the PR title and description as necessary, especially if they're currently blank.

For PR descriptions: keep it short!
</WORKFLOW>
"""

    # Create agent context with workspace-specific system message suffix
    agent_context = AgentContext(system_message_suffix=workspace_suffix)

    # Use built-in Agent with built-in system prompt template
    return Agent(
        llm=llm,
        tools=tools,
        agent_context=agent_context,
    )


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
        runtime_url: Optional[str] = None,
        session_api_key: Optional[str] = None,
    ):
        """Initialize an AgentLoop instance with improved error handling."""
        self.user_uuid = user_uuid
        self.app_slug = app_slug
        self.riff_slug = riff_slug
        self.llm = llm
        self.message_callback = message_callback
        self.runtime_url = runtime_url
        self.session_api_key = session_api_key

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

        # Determine if we're using remote runtime
        use_remote_runtime = bool(self.runtime_url and self.session_api_key)

        # Create tools with validation
        try:
            tools = create_tools_with_validation(
                self.workspace_path, use_remote_runtime
            )
        except Exception as e:
            logger.error(f"❌ Failed to create tools for {self.get_key()}: {e}")
            raise

        # Create agent
        try:
            self.agent = create_agent(
                llm, tools, self.workspace_path, use_remote_runtime
            )
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
            if self.runtime_url and self.session_api_key:
                logger.info(
                    f"🌐 Creating RemoteConversation for {self.get_key()} using runtime: {self.runtime_url}"
                )

                # Wait for the runtime to be ready and alive before creating the conversation
                logger.info(
                    f"⏳ Waiting for runtime to be ready and alive before creating conversation: {self.runtime_url}"
                )
                ready_success, ready_response = (
                    runtime_service.wait_for_runtime_ready_and_alive(
                        self.user_uuid,
                        self.app_slug,
                        self.riff_slug,
                        self.runtime_url,
                        timeout=300,
                        check_interval=5,
                    )
                )

                if not ready_success:
                    error_msg = f"Runtime is not ready and alive: {ready_response.get('error', 'Unknown error')}"
                    logger.error(f"❌ {error_msg}")
                    raise RuntimeError(error_msg)

                logger.info(
                    f"✅ Runtime is ready and alive, creating conversation: {self.runtime_url}"
                )
                self.conversation = Conversation(
                    agent=self.agent,
                    host=self.runtime_url,
                    api_key=self.session_api_key,
                    callbacks=callbacks,
                    visualize=False,
                )
            else:
                logger.info(f"🏠 Creating local Conversation for {self.get_key()}")
                self.conversation = Conversation(
                    agent=self.agent,
                    callbacks=callbacks,
                    persist_filestore=self.file_store,
                    conversation_id=conversation_id,
                    visualize=False,
                )
        except ValueError as e:
            error_msg = str(e)
            # Handle tool name migration - clear persisted state if tool names have changed
            if (
                ("Tool" in error_msg and "is not registered" in error_msg)
                or (
                    "Agent provided is different" in error_msg and "tools:" in error_msg
                )
                or ("Conversation ID mismatch" in error_msg)
            ):
                logger.warning(
                    f"⚠️ Detected tool migration issue for {self.get_key()}: {error_msg}"
                )
                logger.info(
                    f"🔄 Clearing persisted state to handle tool name changes..."
                )

                # Clear the persisted state directory
                import shutil

                if os.path.exists(self.state_path):
                    shutil.rmtree(self.state_path)
                    ensure_directory_exists(self.state_path)

                # Recreate the file store
                self.file_store = LocalFileStore(self.state_path)

                # Retry conversation creation
                if self.runtime_url and self.session_api_key:
                    logger.info(
                        f"🌐 Retrying RemoteConversation creation for {self.get_key()}"
                    )

                    # Wait for the runtime to be ready and alive before retrying conversation creation
                    logger.info(
                        f"⏳ Waiting for runtime to be ready and alive before retrying conversation: {self.runtime_url}"
                    )
                    ready_success, ready_response = (
                        runtime_service.wait_for_runtime_ready_and_alive(
                            self.user_uuid,
                            self.app_slug,
                            self.riff_slug,
                            self.runtime_url,
                            timeout=300,
                            check_interval=5,
                        )
                    )

                    if not ready_success:
                        error_msg = f"Runtime is not ready and alive during retry: {ready_response.get('error', 'Unknown error')}"
                        logger.error(f"❌ {error_msg}")
                        raise RuntimeError(error_msg)

                    logger.info(
                        f"✅ Runtime is ready and alive, retrying conversation creation: {self.runtime_url}"
                    )
                    self.conversation = Conversation(
                        agent=self.agent,
                        host=self.runtime_url,
                        api_key=self.session_api_key,
                        callbacks=callbacks,
                        visualize=False,
                    )
                else:
                    logger.info(
                        f"🏠 Retrying local Conversation creation for {self.get_key()}"
                    )
                    self.conversation = Conversation(
                        agent=self.agent,
                        callbacks=callbacks,
                        persist_filestore=self.file_store,
                        conversation_id=conversation_id,
                        visualize=False,
                    )
                logger.info(
                    f"✅ Successfully recreated conversation after state migration"
                )
            else:
                raise
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
        runtime_url: Optional[str] = None,
        session_api_key: Optional[str] = None,
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
                user_uuid,
                app_slug,
                riff_slug,
                llm,
                workspace_path,
                message_callback,
                runtime_url,
                session_api_key,
            )

        try:
            # Create new instance - the Conversation constructor will automatically load existing state
            instance = cls(
                user_uuid,
                app_slug,
                riff_slug,
                llm,
                workspace_path,
                message_callback,
                runtime_url,
                session_api_key,
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
                user_uuid,
                app_slug,
                riff_slug,
                llm,
                workspace_path,
                message_callback,
                runtime_url,
                session_api_key,
            )

    def _safe_event_callback(self, event: EventBase):
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
        runtime_url: Optional[str] = None,
        session_api_key: Optional[str] = None,
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
            runtime_url: Optional URL for remote runtime server
            session_api_key: Optional API key for remote runtime session

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
                    runtime_url,
                    session_api_key,
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
        runtime_url: Optional[str] = None,
        session_api_key: Optional[str] = None,
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
                    runtime_url,
                    session_api_key,
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

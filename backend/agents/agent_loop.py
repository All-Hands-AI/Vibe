"""
Refactored AgentLoop class for OpenVibe backend.
Manages agent conversations using openhands-sdk Agent and Conversation with proper
threading, error handling, and resource management.

This refactored version uses factory patterns and handlers to separate concerns
and eliminate the remote vs local logic duplication.
"""

import sys
import traceback
from typing import Dict, Optional, Callable, Any
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, Future
from utils.logging import get_logger
from .runtime_handler import RuntimeHandler
from .agent_factory import create_agent
from .conversation_factory import ConversationFactory

# Add the site-packages to the path for openhands imports
sys.path.insert(0, ".venv/lib/python3.12/site-packages")

from openhands.sdk import (
    LLM,
    Message,
    TextContent,
    EventBase,
)

logger = get_logger(__name__)


class AgentLoop:
    """
    Represents an agent conversation loop for a specific user, app, and riff.
    Contains an Agent and Conversation instance from openhands-sdk, running in a thread.

    This refactored version uses composition with specialized handlers and factories
    to manage the complexity of remote vs local runtime configurations.
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

        # Create runtime handler to manage remote vs local configuration
        self.runtime_handler = RuntimeHandler(
            workspace_path=workspace_path,
            runtime_url=runtime_url,
            session_api_key=session_api_key,
        )

        # Create agent using factory
        try:
            self.agent = create_agent(llm, self.runtime_handler)
        except Exception as e:
            logger.error(f"❌ Failed to create agent for {self.get_key()}: {e}")
            raise

        # Create conversation using factory
        conversation_factory = ConversationFactory(self.runtime_handler)

        # Create conversation with callbacks
        callbacks = []
        if message_callback:
            callbacks.append(self._safe_event_callback)

        try:
            self.conversation = conversation_factory.create_conversation_with_retry(
                agent=self.agent,
                user_uuid=user_uuid,
                app_slug=app_slug,
                riff_slug=riff_slug,
                callbacks=callbacks,
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

        logger.info(f"🤖 Created refactored AgentLoop for {self.get_key()}")

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
        """
        Create an AgentLoop from existing state.
        This is a factory method that creates a new instance - the SDK handles state restoration.
        """
        logger.info(
            f"🔄 Creating AgentLoop from existing state for {user_uuid}:{app_slug}:{riff_slug}"
        )

        return cls(
            user_uuid=user_uuid,
            app_slug=app_slug,
            riff_slug=riff_slug,
            llm=llm,
            workspace_path=workspace_path,
            message_callback=message_callback,
            runtime_url=runtime_url,
            session_api_key=session_api_key,
        )

    def _safe_event_callback(self, event: EventBase):
        """Safely call the message callback with error handling."""
        if self.message_callback:
            try:
                self.message_callback(event)
            except Exception as e:
                logger.error(f"❌ Error in message callback for {self.get_key()}: {e}")

    def get_key(self) -> str:
        """Get a unique key for this agent loop."""
        return f"{self.user_uuid}:{self.app_slug}:{self.riff_slug}"

    def _run_conversation_safely(self):
        """Run the conversation with proper error handling."""
        try:
            with self._lock:
                self._is_running = True

            logger.info(f"🚀 Starting conversation for {self.get_key()}")
            self.conversation.run()
            logger.info(f"✅ Conversation completed for {self.get_key()}")

        except Exception as e:
            logger.error(f"❌ Error in conversation for {self.get_key()}: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
        finally:
            with self._lock:
                self._is_running = False

    def send_message(self, message: str) -> str:
        """
        Send a message to the agent and start/continue the conversation.

        Args:
            message: The message to send to the agent

        Returns:
            A status message indicating the result
        """
        try:
            # Create message object with user role
            msg = Message(role="user", content=[TextContent(text=message)])

            # Send message to conversation
            self.conversation.send_message(msg)
            logger.info(
                f"📤 Sent message to conversation for {self.get_key()}: {message[:100]}..."
            )

            # Start conversation in thread if not already running
            with self._lock:
                if not self._is_running and (
                    self._current_task is None or self._current_task.done()
                ):
                    logger.info(
                        f"🎯 Starting new conversation task for {self.get_key()}"
                    )
                    self._current_task = self._executor.submit(
                        self._run_conversation_safely
                    )
                    return (
                        f"✅ Message sent and conversation started for {self.get_key()}"
                    )
                else:
                    return (
                        f"✅ Message sent to running conversation for {self.get_key()}"
                    )

        except Exception as e:
            error_msg = f"❌ Failed to send message for {self.get_key()}: {e}"
            logger.error(error_msg)
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return error_msg

    def get_all_events(self):
        """
        Get all events from the conversation.

        Returns:
            List of events from the conversation
        """
        try:
            return list(self.conversation.state.events)
        except Exception as e:
            logger.error(f"❌ Failed to get events for {self.get_key()}: {e}")
            return []

    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent and conversation.

        Returns:
            Dictionary containing status information
        """
        try:
            # Get conversation state
            state = self.conversation.state

            # Get runtime info
            runtime_info = self.runtime_handler.get_runtime_info()

            with self._lock:
                is_running = self._is_running
                has_active_task = (
                    self._current_task is not None and not self._current_task.done()
                )

            # Return SDK state transparently with minimal wrapper
            # Convert the state to a dict to make it JSON serializable
            state_dict = state.model_dump()

            # Add minimal metadata that the frontend needs
            status = {
                # Core SDK state - transparent passthrough
                **state_dict,
                # Minimal metadata for the frontend
                "_metadata": {
                    "key": self.get_key(),
                    "user_uuid": self.user_uuid,
                    "app_slug": self.app_slug,
                    "riff_slug": self.riff_slug,
                    "is_running": is_running,
                    "has_active_task": has_active_task,
                    "runtime_type": runtime_info["type"],
                    "workspace_path": runtime_info["workspace_path"],
                    "state_path": runtime_info["state_path"],
                },
            }

            # Add runtime-specific info to metadata
            if runtime_info["type"] == "remote":
                status["_metadata"]["runtime_url"] = runtime_info.get("runtime_url")
                status["_metadata"]["has_session_key"] = runtime_info.get(
                    "has_session_key", False
                )

            return status

        except Exception as e:
            logger.error(f"❌ Failed to get agent status for {self.get_key()}: {e}")
            return {
                "key": self.get_key(),
                "error": str(e),
                "is_running": False,
                "has_active_task": False,
            }

    def pause_agent(self) -> bool:
        """
        Pause the agent conversation.

        Returns:
            True if successfully paused, False otherwise
        """
        try:
            # Check if conversation supports pausing
            if hasattr(self.conversation, "pause"):
                self.conversation.pause()
                logger.info(f"⏸️ Paused conversation for {self.get_key()}")
                return True
            else:
                logger.warning(
                    f"⚠️ Conversation does not support pausing for {self.get_key()}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Failed to pause agent for {self.get_key()}: {e}")
            return False

    def resume_agent(self) -> bool:
        """
        Resume the agent conversation.

        Returns:
            True if successfully resumed, False otherwise
        """
        try:
            # Check if conversation supports resuming
            if hasattr(self.conversation, "resume"):
                self.conversation.resume()
                logger.info(f"▶️ Resumed conversation for {self.get_key()}")
                return True
            else:
                logger.warning(
                    f"⚠️ Conversation does not support resuming for {self.get_key()}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Failed to resume agent for {self.get_key()}: {e}")
            return False

    def cleanup(self):
        """Clean up resources used by this agent loop."""
        try:
            logger.info(f"🧹 Cleaning up AgentLoop for {self.get_key()}")

            # Cancel any running tasks
            with self._lock:
                if self._current_task and not self._current_task.done():
                    logger.info(f"🛑 Cancelling running task for {self.get_key()}")
                    self._current_task.cancel()

            # Shutdown the executor
            if self._executor:
                logger.info(f"🔌 Shutting down executor for {self.get_key()}")
                self._executor.shutdown(wait=True, timeout=10)

            logger.info(f"✅ Cleanup completed for {self.get_key()}")

        except Exception as e:
            logger.error(f"❌ Error during cleanup for {self.get_key()}: {e}")

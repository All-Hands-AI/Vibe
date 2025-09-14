"""
AgentLoop and AgentLoopManager classes for OpenVibe backend.
Manages agent conversations using openhands-sdk Agent and Conversation.
"""

import sys
import os
import threading
from typing import Dict, Optional, Callable
from threading import Lock
from utils.logging import get_logger

# Add the site-packages to the path for openhands imports
sys.path.insert(0, ".venv/lib/python3.12/site-packages")

from openhands.sdk import Agent, Conversation, LLM, Message, TextContent, AgentContext
from openhands.tools import FileEditorTool, TaskTrackerTool

logger = get_logger(__name__)


def create_test_agent(llm, tools, workspace_path):
    """Create an agent with FileEditor and TaskTracker tools that prefixes all responses with 'howdy!' for testing"""
    # Create agent context with custom system message suffix that includes workspace info
    system_message_suffix = f"""IMPORTANT: Always prefix your response with 'howdy!' followed by a space, then respond normally to the user's request.

WORKSPACE INFORMATION:
You are working in a cloned GitHub repository located at: {workspace_path}

This directory contains the complete source code of the project you'll be working on. You can:
- View, edit, and create files using the FileEditor tool
- Navigate the repository structure
- Make changes to the codebase
- The repository is already checked out to the appropriate branch for this riff

Your file operations will be performed within this workspace directory."""

    agent_context = AgentContext(system_message_suffix=system_message_suffix)

    return Agent(llm=llm, tools=tools, agent_context=agent_context)


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
        """
        Initialize an AgentLoop instance.

        Args:
            user_uuid: Unique identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation
            llm: LLM instance from openhands-sdk
            workspace_path: Required path to the workspace directory (cloned repository)
            message_callback: Optional callback function to handle events/messages
        """
        self.user_uuid = user_uuid
        self.app_slug = app_slug
        self.riff_slug = riff_slug
        self.llm = llm
        self.message_callback = message_callback

        # Require workspace_path to be explicitly provided
        if not workspace_path:
            raise ValueError("workspace_path is required and cannot be None or empty")
        self.workspace_path = workspace_path

        # Create Agent with development tools
        # Use workspace path for file operations, /data for task tracking
        tools: list = [
            FileEditorTool.create(working_dir=self.workspace_path),
            TaskTrackerTool.create(
                save_dir="/data"
            ),  # Save task tracking data to /data directory
        ]  # Include FileEditor and TaskTracker tools for development capabilities

        # Use custom agent for testing - it will always reply with "howdy!"
        self.agent = create_test_agent(llm, tools, self.workspace_path)

        # Create conversation callbacks
        callbacks = []
        if message_callback:
            callbacks.append(self._event_callback)

        # Create Conversation
        self.conversation = Conversation(
            agent=self.agent,
            callbacks=callbacks,
            visualize=False,  # Disable default visualization since we handle events ourselves
        )

        # Thread management
        self.thread = None
        self.running = False
        self._thread_lock = threading.Lock()

        logger.info(f"🤖 Created AgentLoop for {user_uuid[:8]}/{app_slug}/{riff_slug}")

    def _event_callback(self, event):
        """Internal callback to handle events from the conversation"""
        try:
            if self.message_callback:
                self.message_callback(event)
        except Exception as e:
            logger.error(f"❌ Error in event callback for {self.get_key()}: {e}")

    def get_key(self) -> str:
        """Get the unique key for this agent loop"""
        return f"{self.user_uuid}:{self.app_slug}:{self.riff_slug}"

    def start_agent_thread(self):
        """Start the agent running in a background thread"""
        with self._thread_lock:
            if self.thread is not None and self.thread.is_alive():
                logger.warning(f"⚠️ Agent thread already running for {self.get_key()}")
                return

            self.running = True
            self.thread = threading.Thread(
                target=self._run_agent, name=f"AgentLoop-{self.get_key()}", daemon=True
            )
            self.thread.start()
            logger.info(f"🚀 Started agent thread for {self.get_key()}")

    def _run_agent(self):
        """Internal method to run the agent in the thread"""
        try:
            logger.info(f"🔄 Agent thread running for {self.get_key()}")
            # The conversation will handle the agent loop automatically
            # We just need to keep the thread alive
            while self.running:
                threading.Event().wait(1)  # Sleep for 1 second
        except Exception as e:
            logger.error(f"❌ Error in agent thread for {self.get_key()}: {e}")
        finally:
            logger.info(f"🛑 Agent thread stopped for {self.get_key()}")

    def stop_agent_thread(self):
        """Stop the agent thread"""
        with self._thread_lock:
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
                logger.info(f"🛑 Stopped agent thread for {self.get_key()}")

    def send_message(self, message: str) -> str:
        """
        Send a message to the agent and trigger conversation processing.

        Args:
            message: The user message to send

        Returns:
            A confirmation message (actual response will come through callbacks)
        """
        logger.info(f"💬 Sending message to agent for {self.get_key()}")
        try:
            # Create a Message object for the conversation
            user_message = Message(role="user", content=[TextContent(text=message)])

            # Send message to conversation
            self.conversation.send_message(user_message)

            # Start the conversation processing (this will trigger the agent)
            # We run this in the background so it doesn't block
            if not self.thread or not self.thread.is_alive():
                self.start_agent_thread()

            # Trigger conversation run in a separate thread
            threading.Thread(target=self._run_conversation, daemon=True).start()

            logger.info(f"✅ Message sent to agent for {self.get_key()}")
            return "Message sent to agent. Response will be processed asynchronously."

        except Exception as e:
            logger.error(f"❌ Error sending message to agent for {self.get_key()}: {e}")
            raise

    def _run_conversation(self):
        """Run the conversation processing"""
        try:
            self.conversation.run()
        except Exception as e:
            logger.error(f"❌ Error running conversation for {self.get_key()}: {e}")


class AgentLoopManager:
    """
    Singleton class that manages AgentLoop instances.
    Keeps a dictionary of AgentLoops keyed by user_uuid:app_slug:riff_slug.
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
            logger.info("🏗️ AgentLoopManager initialized")

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
            if key in self.agent_loops:
                logger.warning(f"⚠️ AgentLoop already exists for {key}, replacing it")
                # Stop the existing agent thread before replacing
                old_loop = self.agent_loops[key]
                old_loop.stop_agent_thread()

            agent_loop = AgentLoop(
                user_uuid, app_slug, riff_slug, llm, workspace_path, message_callback
            )
            self.agent_loops[key] = agent_loop

            logger.info(f"✅ Created and stored AgentLoop for {key}")
            logger.info(f"📊 Total agent loops: {len(self.agent_loops)}")
            logger.info(f"🔑 All stored keys: {list(self.agent_loops.keys())}")

            return agent_loop

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
                logger.info(f"🔑 Available keys: {list(self.agent_loops.keys())}")
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
                # Stop the agent thread before removing
                agent_loop = self.agent_loops[key]
                agent_loop.stop_agent_thread()

                del self.agent_loops[key]
                logger.info(f"🗑️ Removed AgentLoop for {key}")
                logger.info(f"📊 Total agent loops: {len(self.agent_loops)}")
                return True
            else:
                logger.warning(f"❌ AgentLoop not found for removal: {key}")
                return False

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the agent loops"""
        with self._lock:
            return {
                "total_loops": len(self.agent_loops),
                "active_users": len(
                    set(loop.user_uuid for loop in self.agent_loops.values())
                ),
                "active_apps": len(
                    set(loop.app_slug for loop in self.agent_loops.values())
                ),
            }


# Global instance
agent_loop_manager = AgentLoopManager()

"""
AgentLoop and AgentLoopManager classes for OpenVibe backend.
Manages agent conversations using openhands-sdk Agent and Conversation.
"""

import sys
import threading
from typing import Dict, Optional, Callable
from threading import Lock
from utils.logging import get_logger

# Add the site-packages to the path for openhands imports
sys.path.insert(0, ".venv/lib/python3.12/site-packages")

from openhands.sdk import Agent, Conversation, LLM, Message, TextContent, AgentContext

logger = get_logger(__name__)


def create_test_agent(llm, tools):
    """Create an agent that prefixes all responses with 'howdy!' for testing"""
    # Create agent context with custom system message suffix
    agent_context = AgentContext(
        system_message_suffix="IMPORTANT: Always prefix your response with 'howdy!' followed by a space, then respond normally to the user's request."
    )

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
        message_callback: Optional[Callable] = None,
    ):
        """
        Initialize an AgentLoop instance.

        Args:
            user_uuid: Unique identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation
            llm: LLM instance from openhands-sdk
            message_callback: Optional callback function to handle events/messages
        """
        self.user_uuid = user_uuid
        self.app_slug = app_slug
        self.riff_slug = riff_slug
        self.llm = llm
        self.message_callback = message_callback

        # Create Agent with only built-in tools (no bash or file tools)
        tools: list = (
            []
        )  # Empty tools list - agent will only have built-in tools like 'finish' and 'think'

        # Use custom agent for testing - it will always reply with "howdy!"
        self.agent = create_test_agent(llm, tools)

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

    def get_agent_status(self):
        """
        Get the current status of the agent.

        Returns:
            dict: Dictionary containing agent status information
        """
        try:
            if not self.conversation or not hasattr(self.conversation, "state"):
                return {
                    "status": "not_initialized",
                    "agent_finished": False,
                    "agent_paused": False,
                    "agent_waiting_for_confirmation": False,
                    "thread_alive": False,
                    "running": False,
                }

            state = self.conversation.state

            # Determine if the agent is actually running based on conversation state
            agent_finished = getattr(state, "agent_finished", False)
            agent_paused = getattr(state, "agent_paused", False)
            agent_waiting = getattr(state, "agent_waiting_for_confirmation", False)

            # Agent is considered "running" if it's not finished, not paused, and not waiting
            is_running = not agent_finished and not agent_paused and not agent_waiting

            # Check if there are recent events indicating activity
            events = getattr(state, "events", [])
            has_recent_activity = len(events) > 0

            return {
                "status": "initialized",
                "agent_finished": agent_finished,
                "agent_paused": agent_paused,
                "agent_waiting_for_confirmation": agent_waiting,
                "thread_alive": self.thread is not None and self.thread.is_alive(),
                "running": is_running,
                "conversation_id": getattr(state, "id", None),
                "event_count": len(events),
                "has_recent_activity": has_recent_activity,
            }
        except Exception as e:
            logger.error(f"❌ Error getting agent status for {self.get_key()}: {e}")
            return {"status": "error", "error": str(e), "running": False}

    def pause_agent(self):
        """
        Pause the agent execution.

        Returns:
            bool: True if pause was successful, False otherwise
        """
        try:
            if self.conversation and hasattr(self.conversation, "pause"):
                self.conversation.pause()
                logger.info(f"🔄 Agent paused for {self.get_key()}")
                return True
            else:
                logger.warning(
                    f"⚠️ Cannot pause agent for {self.get_key()}: conversation not available"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Error pausing agent for {self.get_key()}: {e}")
            return False

    def resume_agent(self):
        """
        Resume the agent execution by starting a new conversation run.

        Returns:
            bool: True if resume was successful, False otherwise
        """
        try:
            if not self.conversation:
                logger.warning(
                    f"⚠️ Cannot resume agent for {self.get_key()}: conversation not available"
                )
                return False

            state = self.conversation.state

            # Check current agent state
            agent_finished = getattr(state, "agent_finished", False)
            agent_paused = getattr(state, "agent_paused", False)

            if agent_finished:
                logger.info(f"ℹ️ Agent for {self.get_key()} is finished, cannot resume")
                return False

            if not agent_paused:
                # Agent is already running or idle, check if we need to start it
                events = getattr(state, "events", [])
                if len(events) <= 1:  # Only initial event, agent hasn't started
                    logger.info(
                        f"🔄 Agent for {self.get_key()} is idle, will start on next message"
                    )
                else:
                    logger.info(f"ℹ️ Agent for {self.get_key()} is already running")
                return True

            # Agent is paused, resume it by running the conversation
            # The OpenHands SDK will handle the resume automatically when run() is called
            threading.Thread(target=self._run_conversation, daemon=True).start()

            logger.info(f"🔄 Agent resumed for {self.get_key()}")
            return True
        except Exception as e:
            logger.error(f"❌ Error resuming agent for {self.get_key()}: {e}")
            return False


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
        message_callback: Optional[Callable] = None,
    ) -> AgentLoop:
        """
        Create a new AgentLoop and store it in the dictionary.

        Args:
            user_uuid: Unique identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation
            llm: LLM instance from openhands-sdk
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
                user_uuid, app_slug, riff_slug, llm, message_callback
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

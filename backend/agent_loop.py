"""
AgentLoop and AgentLoopManager classes for OpenVibe backend.
Manages agent conversations and LLM interactions.
"""

import logging
from typing import Dict, Optional, Tuple
from threading import Lock

logger = logging.getLogger(__name__)


class AgentLoop:
    """
    Represents an agent conversation loop for a specific user, app, and riff.
    Contains an LLM instance for handling conversations.
    """
    
    def __init__(self, user_uuid: str, app_slug: str, riff_slug: str, llm):
        """
        Initialize an AgentLoop instance.
        
        Args:
            user_uuid: Unique identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation
            llm: LLM instance from openhands-sdk
        """
        self.user_uuid = user_uuid
        self.app_slug = app_slug
        self.riff_slug = riff_slug
        self.llm = llm
        
        logger.info(f"🤖 Created AgentLoop for {user_uuid[:8]}/{app_slug}/{riff_slug}")
    
    def get_key(self) -> str:
        """Get the unique key for this agent loop"""
        return f"{self.user_uuid}:{self.app_slug}:{self.riff_slug}"
    
    def send_message(self, message: str) -> str:
        """
        Send a message to the LLM and get a response.
        
        Args:
            message: The user message to send
            
        Returns:
            The LLM's response
        """
        logger.info(f"💬 Sending message to LLM for {self.get_key()}")
        try:
            # Use the LLM to generate a response
            response = self.llm.chat([{"role": "user", "content": message}])
            logger.info(f"✅ Got LLM response for {self.get_key()}")
            return response
        except Exception as e:
            logger.error(f"❌ Error getting LLM response for {self.get_key()}: {e}")
            raise


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
        return f"{user_uuid}:{app_slug}:{riff_slug}"
    
    def create_agent_loop(self, user_uuid: str, app_slug: str, riff_slug: str, llm) -> AgentLoop:
        """
        Create a new AgentLoop and store it in the dictionary.
        
        Args:
            user_uuid: Unique identifier for the user
            app_slug: Slug identifier for the app
            riff_slug: Slug identifier for the riff/conversation
            llm: LLM instance from openhands-sdk
            
        Returns:
            The created AgentLoop instance
        """
        key = self._get_key(user_uuid, app_slug, riff_slug)
        
        with self._lock:
            if key in self.agent_loops:
                logger.warning(f"⚠️ AgentLoop already exists for {key}, replacing it")
            
            agent_loop = AgentLoop(user_uuid, app_slug, riff_slug, llm)
            self.agent_loops[key] = agent_loop
            
            logger.info(f"✅ Created and stored AgentLoop for {key}")
            logger.info(f"📊 Total agent loops: {len(self.agent_loops)}")
            
            return agent_loop
    
    def get_agent_loop(self, user_uuid: str, app_slug: str, riff_slug: str) -> Optional[AgentLoop]:
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
                "active_users": len(set(loop.user_uuid for loop in self.agent_loops.values())),
                "active_apps": len(set(loop.app_slug for loop in self.agent_loops.values())),
            }


# Global instance
agent_loop_manager = AgentLoopManager()
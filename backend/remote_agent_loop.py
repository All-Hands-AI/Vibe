"""
Remote agent loop implementation that connects to external agent server instances.
This is used when Docker-in-Docker is not available (e.g., on Fly.io).
"""

import json
import logging
import os
import requests
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from utils.logging import get_logger

logger = get_logger(__name__)

# Default agent server URL - can be overridden via environment variable
DEFAULT_AGENT_SERVER_URL = os.getenv("AGENT_SERVER_URL", "https://agent-server.all-hands.dev")


class RemoteAgentLoop:
    """
    Remote agent loop that connects to an external agent server.
    Used when Docker-in-Docker is not available.
    """

    def __init__(
        self,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        api_key: str,
        model: str,
        workspace_path: str,
        message_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        agent_server_url: str = DEFAULT_AGENT_SERVER_URL,
    ):
        self.user_uuid = user_uuid
        self.app_slug = app_slug
        self.riff_slug = riff_slug
        self.api_key = api_key
        self.model = model
        self.workspace_path = workspace_path
        self.message_callback = message_callback
        self.agent_server_url = agent_server_url.rstrip("/")
        
        # Session management
        self.session_id = f"{user_uuid}:{app_slug}:{riff_slug}"
        self.conversation_id: Optional[str] = None
        self.is_running = False
        
        # HTTP session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.session_id}",
        })

    def start(self) -> bool:
        """Start the remote agent session."""
        try:
            logger.info(f"🌐 Starting remote agent session for {self.session_id}")
            
            # Create conversation
            conversation_data = {
                "agent": self.model,
                "args": {
                    "api_key": self.api_key,
                    "model": self.model,
                },
                "workspace_path": "/workspace/project",  # Remote workspace path
            }
            
            response = self.session.post(
                f"{self.agent_server_url}/conversations",
                json=conversation_data,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                self.conversation_id = result["conversation_id"]
                self.is_running = True
                logger.info(f"✅ Remote agent session started: {self.conversation_id}")
                return True
            else:
                logger.error(f"❌ Failed to create conversation: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting remote agent: {e}")
            return False

    def send_message(self, message: str) -> bool:
        """Send a message to the remote agent."""
        if not self.is_running or not self.conversation_id:
            logger.error("❌ Agent not running or no conversation ID")
            return False
            
        try:
            event_data = {
                "event": {
                    "kind": "MessageEvent",
                    "source": "user",
                    "llm_message": {
                        "role": "user",
                        "content": [{"type": "text", "text": message}]
                    }
                }
            }
            
            response = self.session.post(
                f"{self.agent_server_url}/conversations/{self.conversation_id}/events",
                json=event_data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"📤 Message sent to remote agent: {message[:100]}...")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            return False

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events from the remote agent."""
        if not self.is_running or not self.conversation_id:
            return []
            
        try:
            response = self.session.get(
                f"{self.agent_server_url}/conversations/{self.conversation_id}/events",
                timeout=30
            )
            
            if response.status_code == 200:
                events = response.json().get("events", [])
                
                # Process events through callback if provided
                if self.message_callback:
                    for event in events:
                        try:
                            self.message_callback(event)
                        except Exception as e:
                            logger.error(f"❌ Error in message callback: {e}")
                
                return events
            else:
                logger.error(f"❌ Failed to get events: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting events: {e}")
            return []

    def get_agent_status(self) -> Dict[str, Any]:
        """Get the status of the remote agent."""
        if not self.is_running or not self.conversation_id:
            return {"status": "stopped", "conversation_id": None}
            
        try:
            response = self.session.get(
                f"{self.agent_server_url}/conversations/{self.conversation_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "status": "running",
                    "conversation_id": self.conversation_id,
                    "agent_server_url": self.agent_server_url,
                    **response.json()
                }
            else:
                return {"status": "error", "conversation_id": self.conversation_id}
                
        except Exception as e:
            logger.error(f"❌ Error getting agent status: {e}")
            return {"status": "error", "conversation_id": self.conversation_id}

    def cleanup(self):
        """Clean up the remote agent session."""
        if self.conversation_id:
            try:
                # Attempt to delete the conversation
                response = self.session.delete(
                    f"{self.agent_server_url}/conversations/{self.conversation_id}",
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info(f"🧹 Remote agent session cleaned up: {self.conversation_id}")
                else:
                    logger.warning(f"⚠️ Failed to delete conversation: {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Error cleaning up remote agent: {e}")
        
        self.is_running = False
        self.conversation_id = None
        self.session.close()


class RemoteAgentLoopManager:
    """
    Manager for remote agent loops.
    """

    def __init__(self):
        self.agent_loops: Dict[str, RemoteAgentLoop] = {}
        self.agent_server_url = DEFAULT_AGENT_SERVER_URL
        logger.info(f"🌐 RemoteAgentLoopManager initialized with server: {self.agent_server_url}")

    def _get_key(self, user_uuid: str, app_slug: str, riff_slug: str) -> str:
        """Generate a unique key for the agent loop."""
        return f"{user_uuid}:{app_slug}:{riff_slug}"

    def get_agent_loop(
        self, user_uuid: str, app_slug: str, riff_slug: str
    ) -> Optional[RemoteAgentLoop]:
        """Get an existing agent loop."""
        key = self._get_key(user_uuid, app_slug, riff_slug)
        agent_loop = self.agent_loops.get(key)
        
        # Check if agent loop is still running
        if agent_loop and not agent_loop.is_running:
            logger.warning(f"⚠️ Agent loop {key} is not running, removing from manager")
            del self.agent_loops[key]
            return None
            
        return agent_loop

    def create_agent_loop(
        self,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        api_key: str,
        model: str,
        workspace_path: str,
        message_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Optional[RemoteAgentLoop]:
        """Create a new remote agent loop."""
        key = self._get_key(user_uuid, app_slug, riff_slug)
        
        # Remove existing agent loop if it exists
        if key in self.agent_loops:
            logger.info(f"🔄 Removing existing agent loop: {key}")
            self.remove_agent_loop(user_uuid, app_slug, riff_slug)

        try:
            # Create new agent loop
            agent_loop = RemoteAgentLoop(
                user_uuid=user_uuid,
                app_slug=app_slug,
                riff_slug=riff_slug,
                api_key=api_key,
                model=model,
                workspace_path=workspace_path,
                message_callback=message_callback,
                agent_server_url=self.agent_server_url,
            )

            # Start the agent loop
            if agent_loop.start():
                self.agent_loops[key] = agent_loop
                logger.info(f"✅ Created remote agent loop: {key}")
                return agent_loop
            else:
                logger.error(f"❌ Failed to start remote agent loop: {key}")
                agent_loop.cleanup()
                return None

        except Exception as e:
            logger.error(f"❌ Error creating remote agent loop {key}: {e}")
            return None

    def remove_agent_loop(self, user_uuid: str, app_slug: str, riff_slug: str) -> bool:
        """Remove and cleanup an agent loop."""
        key = self._get_key(user_uuid, app_slug, riff_slug)
        
        if key in self.agent_loops:
            agent_loop = self.agent_loops[key]
            try:
                agent_loop.cleanup()
                del self.agent_loops[key]
                logger.info(f"🗑️ Removed remote agent loop: {key}")
                return True
            except Exception as e:
                logger.error(f"❌ Error removing remote agent loop {key}: {e}")
                return False
        
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about managed agent loops."""
        running_count = sum(1 for loop in self.agent_loops.values() if loop.is_running)
        
        return {
            "total_loops": len(self.agent_loops),
            "running_loops": running_count,
            "stopped_loops": len(self.agent_loops) - running_count,
            "agent_server_url": self.agent_server_url,
        }

    def cleanup_all(self):
        """Clean up all agent loops."""
        logger.info("🧹 Cleaning up all remote agent loops...")
        
        for key, agent_loop in list(self.agent_loops.items()):
            try:
                agent_loop.cleanup()
            except Exception as e:
                logger.error(f"❌ Error cleaning up agent loop {key}: {e}")
        
        self.agent_loops.clear()
        logger.info("✅ All remote agent loops cleaned up")


# Global manager instance
remote_agent_loop_manager = RemoteAgentLoopManager()
"""
RemoteRuntimeClient for communicating with remote OpenHands Agent Servers.

This module provides a client interface for starting remote runtimes and
communicating with remote agent servers via REST API and WebSocket connections.
"""

import json
import uuid
import asyncio
import websockets
from typing import Dict, Optional, Callable, Any, List
from dataclasses import dataclass
from threading import Thread, Event as ThreadEvent
import requests
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RemoteRuntimeInfo:
    """Information about a started remote runtime."""
    runtime_id: str
    session_api_key: str
    session_id: str
    url: str
    work_hosts: Dict[str, int]


@dataclass
class RemoteConversationInfo:
    """Information about a remote conversation."""
    conversation_id: str
    runtime_info: RemoteRuntimeInfo
    status: str = "idle"


class RemoteRuntimeClient:
    """
    Client for managing remote OpenHands Agent Server runtimes.
    
    This client handles:
    1. Starting remote runtimes via the runtime API
    2. Creating conversations on remote agent servers
    3. Sending messages and receiving events
    4. Managing WebSocket connections for real-time communication
    """

    def __init__(
        self,
        runtime_api_url: str = "https://runtime.staging.all-hands.dev",
        runtime_api_key: str = "ODu0HV9KL1wc1NUerIgZWqn1w8WctjWD",
        agent_server_image: str = "ghcr.io/all-hands-ai/agent-server:85aab73-python",
        event_callback: Optional[Callable] = None,
    ):
        """
        Initialize the RemoteRuntimeClient.
        
        Args:
            runtime_api_url: Base URL for the runtime API
            runtime_api_key: API key for the runtime API
            agent_server_image: Docker image for the agent server
            event_callback: Optional callback for handling events
        """
        self.runtime_api_url = runtime_api_url
        self.runtime_api_key = runtime_api_key
        self.agent_server_image = agent_server_image
        self.event_callback = event_callback
        
        # Track active runtimes and conversations
        self.active_runtimes: Dict[str, RemoteRuntimeInfo] = {}
        self.active_conversations: Dict[str, RemoteConversationInfo] = {}
        
        # WebSocket management
        self.websocket_threads: Dict[str, Thread] = {}
        self.websocket_stop_events: Dict[str, ThreadEvent] = {}

    def start_remote_runtime(
        self,
        working_dir: str = "/workspace",
        environment: Optional[Dict[str, str]] = None,
        resource_factor: int = 1,
    ) -> RemoteRuntimeInfo:
        """
        Start a new remote runtime.
        
        Args:
            working_dir: Working directory for the agent server
            environment: Environment variables for the runtime
            resource_factor: Resource allocation factor
            
        Returns:
            RemoteRuntimeInfo with connection details
            
        Raises:
            Exception: If runtime startup fails
        """
        if environment is None:
            environment = {"DEBUG": "true"}
            
        payload = {
            "image": self.agent_server_image,
            "command": "/usr/local/bin/openhands-agent-server --port 60000 --no-reload",
            "working_dir": working_dir,
            "environment": environment,
            "resource_factor": resource_factor,
        }
        
        headers = {
            "X-API-Key": self.runtime_api_key,
            "Content-Type": "application/json",
        }
        
        try:
            logger.info(f"🚀 Starting remote runtime with payload: {payload}")
            response = requests.post(
                f"{self.runtime_api_url}/start",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            
            runtime_data = response.json()
            runtime_info = RemoteRuntimeInfo(
                runtime_id=runtime_data["runtime_id"],
                session_api_key=runtime_data["session_api_key"],
                session_id=runtime_data["session_id"],
                url=runtime_data["url"],
                work_hosts=runtime_data["work_hosts"],
            )
            
            self.active_runtimes[runtime_info.runtime_id] = runtime_info
            logger.info(f"✅ Remote runtime started: {runtime_info.runtime_id}")
            return runtime_info
            
        except Exception as e:
            logger.error(f"❌ Failed to start remote runtime: {e}")
            raise

    def create_conversation(
        self,
        runtime_info: RemoteRuntimeInfo,
        llm_config: Dict[str, Any],
        workspace_path: str = "/workspace/project",
        initial_message: Optional[str] = None,
    ) -> RemoteConversationInfo:
        """
        Create a new conversation on a remote agent server.
        
        Args:
            runtime_info: Information about the remote runtime
            llm_config: LLM configuration (model, api_key, base_url)
            workspace_path: Workspace path for the agent
            initial_message: Optional initial message to send
            
        Returns:
            RemoteConversationInfo with conversation details
            
        Raises:
            Exception: If conversation creation fails
        """
        # Prepare the agent configuration
        agent_config = {
            "llm": llm_config,
            "tools": [
                {
                    "name": "BashTool",
                    "params": {"working_dir": workspace_path}
                },
                {
                    "name": "FileEditorTool",
                    "params": {"workspace_root": workspace_path}
                },
                {
                    "name": "TaskTrackerTool",
                    "params": {"save_dir": workspace_path}
                },
            ],
        }
        
        # Prepare the conversation request
        conversation_request = {
            "agent": agent_config,
            "max_iterations": 500,
        }
        
        # Add initial message if provided
        if initial_message:
            conversation_request["initial_message"] = {
                "role": "user",
                "content": [{"type": "text", "text": initial_message}],
                "run": True,
            }
        
        headers = {
            "Authorization": f"Bearer {runtime_info.session_api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            logger.info(f"💬 Creating conversation on runtime {runtime_info.runtime_id}")
            response = requests.post(
                f"{runtime_info.url}/conversations",
                headers=headers,
                json=conversation_request,
                timeout=30,
            )
            response.raise_for_status()
            
            conversation_data = response.json()
            conversation_info = RemoteConversationInfo(
                conversation_id=conversation_data["id"],
                runtime_info=runtime_info,
                status=conversation_data.get("status", "idle"),
            )
            
            self.active_conversations[conversation_info.conversation_id] = conversation_info
            logger.info(f"✅ Conversation created: {conversation_info.conversation_id}")
            
            # Start WebSocket connection for real-time events
            self._start_websocket_connection(conversation_info)
            
            return conversation_info
            
        except Exception as e:
            logger.error(f"❌ Failed to create conversation: {e}")
            raise

    def send_message(
        self,
        conversation_info: RemoteConversationInfo,
        message: str,
        run: bool = True,
    ) -> bool:
        """
        Send a message to a remote conversation.
        
        Args:
            conversation_info: Information about the conversation
            message: Message text to send
            run: Whether to immediately run the agent after sending
            
        Returns:
            True if message was sent successfully
            
        Raises:
            Exception: If message sending fails
        """
        message_request = {
            "role": "user",
            "content": [{"type": "text", "text": message}],
            "run": run,
        }
        
        headers = {
            "Authorization": f"Bearer {conversation_info.runtime_info.session_api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            logger.info(f"📤 Sending message to conversation {conversation_info.conversation_id}")
            response = requests.post(
                f"{conversation_info.runtime_info.url}/conversations/{conversation_info.conversation_id}/events",
                headers=headers,
                json=message_request,
                timeout=30,
            )
            response.raise_for_status()
            
            logger.info(f"✅ Message sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            raise

    def get_conversation_events(
        self,
        conversation_info: RemoteConversationInfo,
        limit: int = 100,
        page_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get events from a remote conversation.
        
        Args:
            conversation_info: Information about the conversation
            limit: Maximum number of events to retrieve
            page_id: Optional page ID for pagination
            
        Returns:
            List of event dictionaries
            
        Raises:
            Exception: If event retrieval fails
        """
        params = {"limit": limit}
        if page_id:
            params["page_id"] = page_id
            
        headers = {
            "Authorization": f"Bearer {conversation_info.runtime_info.session_api_key}",
        }
        
        try:
            logger.info(f"📥 Getting events from conversation {conversation_info.conversation_id}")
            response = requests.get(
                f"{conversation_info.runtime_info.url}/conversations/{conversation_info.conversation_id}/events/search",
                headers=headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            
            events_data = response.json()
            events = events_data.get("items", [])
            logger.info(f"✅ Retrieved {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"❌ Failed to get events: {e}")
            raise

    def get_conversation_status(
        self,
        conversation_info: RemoteConversationInfo,
    ) -> Dict[str, Any]:
        """
        Get the status of a remote conversation.
        
        Args:
            conversation_info: Information about the conversation
            
        Returns:
            Dictionary with conversation status information
            
        Raises:
            Exception: If status retrieval fails
        """
        headers = {
            "Authorization": f"Bearer {conversation_info.runtime_info.session_api_key}",
        }
        
        try:
            logger.info(f"📊 Getting status for conversation {conversation_info.conversation_id}")
            response = requests.get(
                f"{conversation_info.runtime_info.url}/conversations/{conversation_info.conversation_id}",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            
            status_data = response.json()
            logger.info(f"✅ Retrieved conversation status: {status_data.get('status', 'unknown')}")
            return status_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get conversation status: {e}")
            raise

    def pause_conversation(
        self,
        conversation_info: RemoteConversationInfo,
    ) -> bool:
        """
        Pause a remote conversation.
        
        Args:
            conversation_info: Information about the conversation
            
        Returns:
            True if conversation was paused successfully
        """
        headers = {
            "Authorization": f"Bearer {conversation_info.runtime_info.session_api_key}",
        }
        
        try:
            logger.info(f"⏸️ Pausing conversation {conversation_info.conversation_id}")
            response = requests.post(
                f"{conversation_info.runtime_info.url}/conversations/{conversation_info.conversation_id}/pause",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            
            logger.info(f"✅ Conversation paused successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to pause conversation: {e}")
            return False

    def resume_conversation(
        self,
        conversation_info: RemoteConversationInfo,
    ) -> bool:
        """
        Resume a paused remote conversation.
        
        Args:
            conversation_info: Information about the conversation
            
        Returns:
            True if conversation was resumed successfully
        """
        headers = {
            "Authorization": f"Bearer {conversation_info.runtime_info.session_api_key}",
        }
        
        try:
            logger.info(f"▶️ Resuming conversation {conversation_info.conversation_id}")
            response = requests.post(
                f"{conversation_info.runtime_info.url}/conversations/{conversation_info.conversation_id}/resume",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            
            logger.info(f"✅ Conversation resumed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to resume conversation: {e}")
            return False

    def _start_websocket_connection(self, conversation_info: RemoteConversationInfo):
        """
        Start a WebSocket connection for real-time events.
        
        Args:
            conversation_info: Information about the conversation
        """
        if not self.event_callback:
            logger.info("🔇 No event callback provided, skipping WebSocket connection")
            return
            
        conversation_id = conversation_info.conversation_id
        
        # Create stop event for this WebSocket
        stop_event = ThreadEvent()
        self.websocket_stop_events[conversation_id] = stop_event
        
        # Start WebSocket thread
        ws_thread = Thread(
            target=self._websocket_worker,
            args=(conversation_info, stop_event),
            daemon=True,
            name=f"WebSocket-{conversation_id[:8]}",
        )
        self.websocket_threads[conversation_id] = ws_thread
        ws_thread.start()
        
        logger.info(f"🔌 Started WebSocket connection for conversation {conversation_id}")

    def _websocket_worker(self, conversation_info: RemoteConversationInfo, stop_event: ThreadEvent):
        """
        WebSocket worker thread for handling real-time events.
        
        Args:
            conversation_info: Information about the conversation
            stop_event: Event to signal when to stop the WebSocket connection
        """
        conversation_id = conversation_info.conversation_id
        runtime_info = conversation_info.runtime_info
        
        # Convert HTTP URL to WebSocket URL
        ws_url = runtime_info.url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/conversations/{conversation_id}/events/socket"
        
        headers = {
            "Authorization": f"Bearer {runtime_info.session_api_key}",
        }
        
        try:
            logger.info(f"🔌 Connecting to WebSocket: {ws_url}")
            
            # Use asyncio in the thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def websocket_handler():
                try:
                    async with websockets.connect(ws_url, extra_headers=headers) as websocket:
                        logger.info(f"✅ WebSocket connected for conversation {conversation_id}")
                        
                        while not stop_event.is_set():
                            try:
                                # Wait for message with timeout
                                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                                event_data = json.loads(message)
                                
                                # Call the event callback
                                if self.event_callback:
                                    try:
                                        self.event_callback(event_data)
                                    except Exception as e:
                                        logger.error(f"❌ Error in event callback: {e}")
                                        
                            except asyncio.TimeoutError:
                                # Timeout is expected, continue loop
                                continue
                            except websockets.exceptions.ConnectionClosed:
                                logger.warning(f"🔌 WebSocket connection closed for conversation {conversation_id}")
                                break
                                
                except Exception as e:
                    logger.error(f"❌ WebSocket error for conversation {conversation_id}: {e}")
                    
            loop.run_until_complete(websocket_handler())
            
        except Exception as e:
            logger.error(f"❌ Failed to start WebSocket worker for conversation {conversation_id}: {e}")
        finally:
            logger.info(f"🔌 WebSocket worker stopped for conversation {conversation_id}")

    def stop_websocket_connection(self, conversation_id: str):
        """
        Stop the WebSocket connection for a conversation.
        
        Args:
            conversation_id: ID of the conversation
        """
        if conversation_id in self.websocket_stop_events:
            logger.info(f"🛑 Stopping WebSocket connection for conversation {conversation_id}")
            self.websocket_stop_events[conversation_id].set()
            
            # Wait for thread to finish
            if conversation_id in self.websocket_threads:
                thread = self.websocket_threads[conversation_id]
                thread.join(timeout=5)
                
                # Clean up
                del self.websocket_threads[conversation_id]
                del self.websocket_stop_events[conversation_id]
                
            logger.info(f"✅ WebSocket connection stopped for conversation {conversation_id}")

    def cleanup_conversation(self, conversation_id: str):
        """
        Clean up resources for a conversation.
        
        Args:
            conversation_id: ID of the conversation to clean up
        """
        logger.info(f"🧹 Cleaning up conversation {conversation_id}")
        
        # Stop WebSocket connection
        self.stop_websocket_connection(conversation_id)
        
        # Remove from active conversations
        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]
            
        logger.info(f"✅ Conversation cleanup completed for {conversation_id}")

    def cleanup_runtime(self, runtime_id: str):
        """
        Clean up resources for a runtime.
        
        Args:
            runtime_id: ID of the runtime to clean up
        """
        logger.info(f"🧹 Cleaning up runtime {runtime_id}")
        
        # Clean up all conversations for this runtime
        conversations_to_cleanup = [
            conv_id for conv_id, conv_info in self.active_conversations.items()
            if conv_info.runtime_info.runtime_id == runtime_id
        ]
        
        for conv_id in conversations_to_cleanup:
            self.cleanup_conversation(conv_id)
            
        # Remove from active runtimes
        if runtime_id in self.active_runtimes:
            del self.active_runtimes[runtime_id]
            
        logger.info(f"✅ Runtime cleanup completed for {runtime_id}")

    def cleanup_all(self):
        """Clean up all resources."""
        logger.info("🧹 Cleaning up all remote runtime resources")
        
        # Clean up all conversations
        conversation_ids = list(self.active_conversations.keys())
        for conv_id in conversation_ids:
            self.cleanup_conversation(conv_id)
            
        # Clean up all runtimes
        runtime_ids = list(self.active_runtimes.keys())
        for runtime_id in runtime_ids:
            self.cleanup_runtime(runtime_id)
            
        logger.info("✅ All remote runtime resources cleaned up")
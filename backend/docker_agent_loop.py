"""
Docker-based AgentLoop implementation for OpenVibe backend.
Manages agent conversations using Docker containers running the agent-server
instead of the openhands-sdk directly.

Key features:
- Each riff gets its own Docker container running agent-server
- HTTP API communication instead of SDK calls
- Proper container lifecycle management
- Resource cleanup and error handling
"""

import os
import uuid
import json
import time
import traceback
import requests
from typing import Dict, Optional, Callable, Any
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, Future
from utils.logging import get_logger

import docker
from docker.models.containers import Container
from docker.errors import DockerException, APIError

logger = get_logger(__name__)

# Docker image to use for agent server - configurable via environment variable
AGENT_SERVER_IMAGE = os.getenv(
    "AGENT_SERVER_IMAGE", 
    "ghcr.io/all-hands-ai/agent-server:v1.0.0_nikolaik_s_python-nodejs_tag_python3.12-nodejs22"
)
CONTAINER_PORT = 8000
CONTAINER_TIMEOUT = 300  # 5 minutes timeout for container operations


class DockerAgentLoop:
    """
    Docker-based agent conversation loop for a specific user, app, and riff.
    Runs an agent-server container and communicates via HTTP API.
    """

    def __init__(
        self,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        api_key: str,
        model: str,
        workspace_path: str,
        message_callback: Optional[Callable] = None,
    ):
        """Initialize a DockerAgentLoop instance."""
        self.user_uuid = user_uuid
        self.app_slug = app_slug
        self.riff_slug = riff_slug
        self.api_key = api_key
        self.model = model
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
        self.conversations_path = os.path.join(workspace_parent, "conversations")

        # Ensure directories exist
        for path in [self.state_path, self.conversations_path]:
            os.makedirs(path, exist_ok=True)

        # Docker client
        try:
            self.docker_client = docker.from_env()
        except DockerException as e:
            logger.error(f"❌ Failed to connect to Docker: {e}")
            raise

        # Container management
        self.container: Optional[Container] = None
        self.container_port: Optional[int] = None
        self.base_url: Optional[str] = None
        self.conversation_id: Optional[str] = None

        # Thread management
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix=f"DockerAgent-{self.get_key()}"
        )
        self._current_task: Optional[Future] = None
        self._lock = Lock()
        self._is_running = False

        logger.info(f"🐳 Created DockerAgentLoop for {self.get_key()}")

    def get_key(self) -> str:
        """Get the unique key for this agent loop"""
        return f"{self.user_uuid}:{self.app_slug}:{self.riff_slug}"

    def _find_free_port(self) -> int:
        """Find a free port for the container."""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    def _create_agent_config(self) -> dict:
        """Create agent configuration for the container."""
        return {
            "session_api_key": f"vibe-{self.get_key()}",
            "allow_cors_origins": ["*"],
            "conversations_path": "/agent-server/conversations",
            "workspace_path": "/agent-server/workspace/project",
        }

    def _ensure_image_available(self) -> bool:
        """Ensure the Docker image is available locally, pull if necessary."""
        try:
            # Check if image exists locally
            try:
                self.docker_client.images.get(AGENT_SERVER_IMAGE)
                logger.info(f"✅ Docker image {AGENT_SERVER_IMAGE} found locally")
                return True
            except docker.errors.ImageNotFound:
                logger.info(f"📥 Docker image {AGENT_SERVER_IMAGE} not found locally, pulling...")
                
                # Pull the image
                self.docker_client.images.pull(AGENT_SERVER_IMAGE)
                logger.info(f"✅ Successfully pulled Docker image {AGENT_SERVER_IMAGE}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to ensure image availability: {e}")
            return False

    def _start_container(self) -> bool:
        """Start the Docker container with agent server."""
        try:
            # Find free port
            self.container_port = self._find_free_port()
            
            # Create config file on host
            config = self._create_agent_config()
            config_path = os.path.join(self.state_path, "config.json")
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            # Container name
            container_name = f"vibe-agent-{self.user_uuid[:8]}-{self.app_slug}-{self.riff_slug}"

            # Environment variables
            environment = {
                "ANTHROPIC_API_KEY": self.api_key,
                "OPENHANDS_AGENT_SERVER_CONFIG_PATH": "/agent-server/config.json",
            }

            # Volume mounts
            volumes = {
                self.workspace_path: {"bind": "/agent-server/workspace", "mode": "rw"},
                self.conversations_path: {"bind": "/agent-server/conversations", "mode": "rw"},
                config_path: {"bind": "/agent-server/config.json", "mode": "ro"},
            }

            logger.info(f"🚀 Starting container {container_name} on port {self.container_port}")
            logger.info(f"🐳 Using Docker image: {AGENT_SERVER_IMAGE}")

            # Pull the image if it doesn't exist locally
            if not self._ensure_image_available():
                logger.error(f"❌ Failed to ensure image {AGENT_SERVER_IMAGE} is available")
                return False

            # Start container
            self.container = self.docker_client.containers.run(
                AGENT_SERVER_IMAGE,
                command=["--host", "0.0.0.0", "--port", str(CONTAINER_PORT), "--no-reload"],
                name=container_name,
                ports={f"{CONTAINER_PORT}/tcp": self.container_port},
                volumes=volumes,
                environment=environment,
                detach=True,
                remove=True,  # Auto-remove when stopped
                network_mode="bridge",
            )

            # Set base URL
            self.base_url = f"http://localhost:{self.container_port}"

            # Wait for container to be ready
            max_retries = 30
            for i in range(max_retries):
                try:
                    response = requests.get(f"{self.base_url}/docs", timeout=5)
                    if response.status_code == 200:
                        logger.info(f"✅ Container {container_name} is ready")
                        return True
                except requests.RequestException:
                    pass
                
                time.sleep(1)

            logger.error(f"❌ Container {container_name} failed to become ready")
            return False

        except Exception as e:
            logger.error(f"❌ Failed to start container: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False

    def _stop_container(self):
        """Stop and cleanup the Docker container."""
        if self.container:
            try:
                logger.info(f"🛑 Stopping container for {self.get_key()}")
                self.container.stop(timeout=10)
                self.container = None
                self.container_port = None
                self.base_url = None
                logger.info(f"✅ Container stopped for {self.get_key()}")
            except Exception as e:
                logger.error(f"❌ Error stopping container: {e}")

    def _create_conversation(self) -> bool:
        """Create a new conversation in the agent server."""
        try:
            if not self.base_url:
                logger.error("❌ Container not started")
                return False

            # Create conversation request
            conversation_request = {
                "llm": {
                    "model": self.model,
                    "api_key": self.api_key,
                    "base_url": None,
                },
                "agent": "CodeActAgent",
                "confirmation_mode": False,
                "max_iterations": 500,
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer vibe-{self.get_key()}",
            }

            response = requests.post(
                f"{self.base_url}/conversations",
                json=conversation_request,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                conversation_data = response.json()
                self.conversation_id = conversation_data["id"]
                logger.info(f"✅ Created conversation {self.conversation_id}")
                return True
            else:
                logger.error(f"❌ Failed to create conversation: {response.status_code} {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error creating conversation: {e}")
            return False

    def start(self) -> bool:
        """Start the Docker agent loop."""
        try:
            # Start container
            if not self._start_container():
                return False

            # Create conversation
            if not self._create_conversation():
                self._stop_container()
                return False

            logger.info(f"🎉 DockerAgentLoop started successfully for {self.get_key()}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start DockerAgentLoop: {e}")
            self.cleanup()
            return False

    def send_message(self, message: str) -> str:
        """Send a message to the agent."""
        try:
            if not self.base_url or not self.conversation_id:
                raise ValueError("Agent loop not started")

            # Create message request
            message_request = {
                "role": "user",
                "content": [{"type": "text", "text": message}],
                "run": True,
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer vibe-{self.get_key()}",
            }

            response = requests.post(
                f"{self.base_url}/conversations/{self.conversation_id}/events",
                json=message_request,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                logger.info(f"✅ Message sent to agent for {self.get_key()}")
                
                # Start monitoring events in background if callback provided
                if self.message_callback:
                    with self._lock:
                        if self._current_task and not self._current_task.done():
                            self._current_task.cancel()
                        
                        self._current_task = self._executor.submit(self._monitor_events)
                        self._is_running = True

                return "Message sent to agent. Response will be processed asynchronously."
            else:
                logger.error(f"❌ Failed to send message: {response.status_code} {response.text}")
                raise Exception(f"Failed to send message: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            raise

    def _monitor_events(self):
        """Monitor events from the agent server and call callbacks."""
        try:
            if not self.base_url or not self.conversation_id:
                return

            headers = {
                "Authorization": f"Bearer vibe-{self.get_key()}",
            }

            # Poll for events
            last_event_count = 0
            while self._is_running:
                try:
                    response = requests.get(
                        f"{self.base_url}/conversations/{self.conversation_id}/events/search",
                        headers=headers,
                        timeout=10,
                    )

                    if response.status_code == 200:
                        events_data = response.json()
                        events = events_data.get("items", [])
                        
                        # Process new events
                        if len(events) > last_event_count:
                            new_events = events[last_event_count:]
                            for event in new_events:
                                if self.message_callback:
                                    try:
                                        self.message_callback(event)
                                    except Exception as e:
                                        logger.error(f"❌ Error in message callback: {e}")
                            
                            last_event_count = len(events)

                    time.sleep(2)  # Poll every 2 seconds

                except requests.RequestException as e:
                    logger.error(f"❌ Error polling events: {e}")
                    time.sleep(5)  # Wait longer on error

        except Exception as e:
            logger.error(f"❌ Error in event monitoring: {e}")
        finally:
            with self._lock:
                self._is_running = False

    def get_all_events(self):
        """Retrieve all events from the agent conversation."""
        try:
            if not self.base_url or not self.conversation_id:
                return []

            headers = {
                "Authorization": f"Bearer vibe-{self.get_key()}",
            }

            response = requests.get(
                f"{self.base_url}/conversations/{self.conversation_id}/events/search",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                events_data = response.json()
                return events_data.get("items", [])
            else:
                logger.error(f"❌ Failed to get events: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Error retrieving events: {e}")
            return []

    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status information."""
        try:
            if not self.base_url or not self.conversation_id:
                return {
                    "status": "not_initialized",
                    "error": "Container not started",
                    "is_running": False,
                    "has_active_task": False,
                    "event_count": 0,
                }

            headers = {
                "Authorization": f"Bearer vibe-{self.get_key()}",
            }

            # Get conversation info
            response = requests.get(
                f"{self.base_url}/conversations/{self.conversation_id}",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                conversation_data = response.json()
                
                with self._lock:
                    has_active_task = (
                        self._current_task is not None and not self._current_task.done()
                    )
                    is_running = self._is_running

                # Get event count
                events = self.get_all_events()

                return {
                    "status": conversation_data.get("status", "idle"),
                    "is_running": is_running,
                    "has_active_task": has_active_task,
                    "conversation_id": self.conversation_id,
                    "event_count": len(events),
                    "workspace_path": self.workspace_path,
                    "container_port": self.container_port,
                    "agent_status": conversation_data.get("status", "idle"),
                }
            else:
                logger.error(f"❌ Failed to get conversation status: {response.status_code}")
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "is_running": False,
                    "has_active_task": False,
                    "event_count": 0,
                }

        except Exception as e:
            logger.error(f"❌ Error getting agent status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "is_running": False,
                "has_active_task": False,
                "event_count": 0,
            }

    def pause_agent(self) -> bool:
        """Pause the agent execution."""
        try:
            if not self.base_url or not self.conversation_id:
                return False

            headers = {
                "Authorization": f"Bearer vibe-{self.get_key()}",
            }

            response = requests.post(
                f"{self.base_url}/conversations/{self.conversation_id}/pause",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                logger.info(f"⏸️ Agent paused for {self.get_key()}")
                return True
            else:
                logger.error(f"❌ Failed to pause agent: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Error pausing agent: {e}")
            return False

    def resume_agent(self) -> bool:
        """Resume the agent execution."""
        try:
            if not self.base_url or not self.conversation_id:
                return False

            headers = {
                "Authorization": f"Bearer vibe-{self.get_key()}",
            }

            response = requests.post(
                f"{self.base_url}/conversations/{self.conversation_id}/resume",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                logger.info(f"▶️ Agent resumed for {self.get_key()}")
                return True
            else:
                logger.error(f"❌ Failed to resume agent: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Error resuming agent: {e}")
            return False

    def cleanup(self):
        """Clean up resources."""
        try:
            logger.info(f"🧹 Cleaning up DockerAgentLoop for {self.get_key()}")

            # Stop event monitoring
            with self._lock:
                self._is_running = False
                if self._current_task and not self._current_task.done():
                    self._current_task.cancel()

            # Stop container
            self._stop_container()

            # Shutdown executor
            if self._executor:
                self._executor.shutdown(wait=True, timeout=10)

        except Exception as e:
            logger.error(f"❌ Error during cleanup for {self.get_key()}: {e}")

        logger.info(f"✅ Cleanup completed for {self.get_key()}")


class DockerAgentLoopManager:
    """
    Singleton manager for DockerAgentLoop instances.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Ensure singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DockerAgentLoopManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the manager (only once due to singleton pattern)"""
        if not self._initialized:
            self.agent_loops: Dict[str, DockerAgentLoop] = {}
            self._initialized = True
            logger.info(f"🏗️ DockerAgentLoopManager initialized with image: {AGENT_SERVER_IMAGE}")
            
            # Pre-pull the agent server image to avoid delays later
            self._pre_pull_image()

    def _pre_pull_image(self):
        """Pre-pull the agent server image to avoid delays during container creation."""
        try:
            docker_client = docker.from_env()
            
            # Check if image exists locally
            try:
                docker_client.images.get(AGENT_SERVER_IMAGE)
                logger.info(f"✅ Agent server image {AGENT_SERVER_IMAGE} already available locally")
            except docker.errors.ImageNotFound:
                logger.info(f"📥 Pre-pulling agent server image {AGENT_SERVER_IMAGE}...")
                docker_client.images.pull(AGENT_SERVER_IMAGE)
                logger.info(f"✅ Successfully pre-pulled agent server image {AGENT_SERVER_IMAGE}")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to pre-pull agent server image: {e}")
            logger.info("🔄 Image will be pulled when needed during container creation")

    def _get_key(self, user_uuid: str, app_slug: str, riff_slug: str) -> str:
        """Generate a unique key for the agent loop"""
        return f"{user_uuid}:{app_slug}:{riff_slug}"

    def create_agent_loop(
        self,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        api_key: str,
        model: str,
        workspace_path: str,
        message_callback: Optional[Callable] = None,
    ) -> DockerAgentLoop:
        """Create a new DockerAgentLoop and store it."""
        key = self._get_key(user_uuid, app_slug, riff_slug)

        with self._lock:
            # Clean up existing agent loop if it exists
            if key in self.agent_loops:
                logger.warning(f"⚠️ DockerAgentLoop already exists for {key}, cleaning up old instance")
                old_loop = self.agent_loops[key]
                try:
                    old_loop.cleanup()
                except Exception as e:
                    logger.error(f"❌ Error cleaning up old agent loop: {e}")

            try:
                agent_loop = DockerAgentLoop(
                    user_uuid,
                    app_slug,
                    riff_slug,
                    api_key,
                    model,
                    workspace_path,
                    message_callback,
                )
                
                # Start the agent loop
                if agent_loop.start():
                    self.agent_loops[key] = agent_loop
                    logger.info(f"✅ Created and stored DockerAgentLoop for {key}")
                    logger.info(f"📊 Total agent loops: {len(self.agent_loops)}")
                    return agent_loop
                else:
                    raise Exception("Failed to start DockerAgentLoop")

            except Exception as e:
                logger.error(f"❌ Failed to create DockerAgentLoop for {key}: {e}")
                raise

    def get_agent_loop(
        self, user_uuid: str, app_slug: str, riff_slug: str
    ) -> Optional[DockerAgentLoop]:
        """Retrieve an existing DockerAgentLoop."""
        key = self._get_key(user_uuid, app_slug, riff_slug)

        with self._lock:
            agent_loop = self.agent_loops.get(key)

            if agent_loop:
                logger.info(f"✅ Retrieved DockerAgentLoop for {key}")
            else:
                logger.warning(f"❌ DockerAgentLoop not found for {key}")

            return agent_loop

    def remove_agent_loop(self, user_uuid: str, app_slug: str, riff_slug: str) -> bool:
        """Remove a DockerAgentLoop."""
        key = self._get_key(user_uuid, app_slug, riff_slug)

        with self._lock:
            if key in self.agent_loops:
                agent_loop = self.agent_loops[key]
                try:
                    agent_loop.cleanup()
                except Exception as e:
                    logger.error(f"❌ Error cleaning up agent loop during removal: {e}")

                del self.agent_loops[key]
                logger.info(f"✅ Removed DockerAgentLoop for {key}")
                logger.info(f"📊 Total agent loops: {len(self.agent_loops)}")
                return True
            else:
                logger.warning(f"❌ DockerAgentLoop not found for removal: {key}")
                return False

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about managed agent loops."""
        with self._lock:
            return {
                "total_loops": len(self.agent_loops),
                "active_loops": list(self.agent_loops.keys()),
            }

    def cleanup_all(self):
        """Clean up all agent loops."""
        with self._lock:
            logger.info(f"🧹 Cleaning up all {len(self.agent_loops)} DockerAgentLoops")
            
            for key, agent_loop in list(self.agent_loops.items()):
                try:
                    agent_loop.cleanup()
                except Exception as e:
                    logger.error(f"❌ Error cleaning up agent loop {key}: {e}")

            self.agent_loops.clear()
            logger.info("✅ All DockerAgentLoops cleaned up")


# Global instance
docker_agent_loop_manager = DockerAgentLoopManager()
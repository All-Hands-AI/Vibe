"""
Hybrid agent loop implementation that tries Docker first, then falls back to remote agent server.
This provides the best of both worlds - local Docker when available, remote when not.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Callable

from docker_agent_loop import DockerAgentLoopManager, docker_agent_loop_manager
from remote_agent_loop import RemoteAgentLoopManager, remote_agent_loop_manager
from utils.logging import get_logger

logger = get_logger(__name__)

# Environment variable to force remote mode
FORCE_REMOTE_MODE = os.getenv("FORCE_REMOTE_AGENT", "false").lower() == "true"


class HybridAgentLoopManager:
    """
    Hybrid manager that tries Docker first, then falls back to remote agent server.
    """

    def __init__(self):
        self.docker_available = False
        self.docker_manager = docker_agent_loop_manager
        self.remote_manager = remote_agent_loop_manager
        
        # Check Docker availability
        if not FORCE_REMOTE_MODE:
            self._check_docker_availability()
        
        mode = "Docker" if self.docker_available else "Remote"
        logger.info(f"🔄 HybridAgentLoopManager initialized in {mode} mode")

    def _check_docker_availability(self) -> bool:
        """Check if Docker is available and working."""
        try:
            import docker
            client = docker.from_env()
            
            # Try to ping Docker daemon
            client.ping()
            
            # Try to list containers (basic functionality test)
            client.containers.list()
            
            self.docker_available = True
            logger.info("🐳 Docker is available and working")
            return True
            
        except Exception as e:
            self.docker_available = False
            logger.info(f"🌐 Docker not available, using remote mode: {e}")
            return False

    def get_agent_loop(self, user_uuid: str, app_slug: str, riff_slug: str):
        """Get an existing agent loop from the appropriate manager."""
        if self.docker_available:
            return self.docker_manager.get_agent_loop(user_uuid, app_slug, riff_slug)
        else:
            return self.remote_manager.get_agent_loop(user_uuid, app_slug, riff_slug)

    def create_agent_loop(
        self,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        api_key: str,
        model: str,
        workspace_path: str,
        message_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        """Create a new agent loop using the appropriate manager."""
        if self.docker_available:
            logger.info(f"🐳 Creating Docker agent loop for {user_uuid}:{app_slug}:{riff_slug}")
            return self.docker_manager.create_agent_loop(
                user_uuid, app_slug, riff_slug, api_key, model, workspace_path, message_callback
            )
        else:
            logger.info(f"🌐 Creating remote agent loop for {user_uuid}:{app_slug}:{riff_slug}")
            return self.remote_manager.create_agent_loop(
                user_uuid, app_slug, riff_slug, api_key, model, workspace_path, message_callback
            )

    def remove_agent_loop(self, user_uuid: str, app_slug: str, riff_slug: str) -> bool:
        """Remove an agent loop from the appropriate manager."""
        # Try both managers to ensure cleanup
        docker_removed = False
        remote_removed = False
        
        if self.docker_available:
            docker_removed = self.docker_manager.remove_agent_loop(user_uuid, app_slug, riff_slug)
        
        remote_removed = self.remote_manager.remove_agent_loop(user_uuid, app_slug, riff_slug)
        
        return docker_removed or remote_removed

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from both managers."""
        stats = {
            "mode": "Docker" if self.docker_available else "Remote",
            "docker_available": self.docker_available,
            "force_remote_mode": FORCE_REMOTE_MODE,
        }
        
        if self.docker_available:
            docker_stats = self.docker_manager.get_stats()
            stats.update({
                "docker_stats": docker_stats,
                "total_loops": docker_stats.get("total_loops", 0),
                "running_loops": docker_stats.get("running_loops", 0),
            })
        
        remote_stats = self.remote_manager.get_stats()
        stats.update({
            "remote_stats": remote_stats,
        })
        
        # If not using Docker, use remote stats as primary
        if not self.docker_available:
            stats.update({
                "total_loops": remote_stats.get("total_loops", 0),
                "running_loops": remote_stats.get("running_loops", 0),
            })
        
        return stats

    def cleanup_all(self):
        """Clean up all agent loops from both managers."""
        logger.info("🧹 Cleaning up all hybrid agent loops...")
        
        if self.docker_available:
            self.docker_manager.cleanup_all()
        
        self.remote_manager.cleanup_all()
        
        logger.info("✅ All hybrid agent loops cleaned up")

    def switch_to_remote_mode(self):
        """Force switch to remote mode (useful for debugging or fallback)."""
        logger.info("🔄 Switching to remote mode...")
        
        # Clean up any Docker containers
        if self.docker_available:
            self.docker_manager.cleanup_all()
        
        self.docker_available = False
        logger.info("🌐 Switched to remote mode")

    def retry_docker_mode(self):
        """Retry Docker mode (useful if Docker becomes available later)."""
        if not FORCE_REMOTE_MODE:
            logger.info("🔄 Retrying Docker mode...")
            if self._check_docker_availability():
                logger.info("🐳 Successfully switched to Docker mode")
            else:
                logger.info("🌐 Still in remote mode")


# Global hybrid manager instance
hybrid_agent_loop_manager = HybridAgentLoopManager()
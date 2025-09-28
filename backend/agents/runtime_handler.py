"""
Runtime handler for managing remote vs local runtime configurations.
Centralizes the logic for determining runtime type and providing appropriate paths and settings.
"""

import os
from typing import Dict, Any
from utils.logging import get_logger

logger = get_logger(__name__)


def ensure_directory_exists(path: str) -> bool:
    """Ensure a directory exists, creating it if necessary."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create directory {path}: {e}")
        return False


class RuntimeHandler:
    """
    Handles runtime-specific configuration and path management.
    Provides a clean interface for remote vs local runtime differences.
    """

    def __init__(
        self, workspace_path: str, runtime_url: str = None, session_api_key: str = None
    ):
        """
        Initialize runtime handler.

        Args:
            workspace_path: Base workspace path for local operations
            runtime_url: Optional URL for remote runtime
            session_api_key: Optional API key for remote runtime
        """
        if not workspace_path:
            raise ValueError("workspace_path is required and cannot be None or empty")

        if not os.path.isabs(workspace_path):
            raise ValueError("workspace_path must be an absolute path")

        self.workspace_path = workspace_path
        self.runtime_url = runtime_url
        self.session_api_key = session_api_key
        self._is_remote = bool(runtime_url and session_api_key)

        # Create state directory as sibling of workspace
        workspace_parent = os.path.dirname(workspace_path)
        self.state_path = os.path.join(workspace_parent, "state")

        if not ensure_directory_exists(self.state_path):
            raise ValueError(f"Cannot create state directory: {self.state_path}")

    @property
    def is_remote(self) -> bool:
        """Check if this is a remote runtime configuration."""
        return self._is_remote

    @property
    def is_local(self) -> bool:
        """Check if this is a local runtime configuration."""
        return not self._is_remote

    def get_runtime_paths(self) -> Dict[str, str]:
        """
        Get runtime-appropriate paths for tools and operations.

        Returns:
            Dictionary with 'project_dir', 'tasks_dir', and 'agent_workspace_path'
        """
        if self.is_remote:
            # For remote runtimes, use fixed paths that match the remote environment
            return {
                "project_dir": "/workspace/project",
                "tasks_dir": "/workspace/tasks",
                "agent_workspace_path": "/workspace",
            }
        else:
            # For local runtimes, use workspace_path-based directories
            # Ensure workspace exists
            if not ensure_directory_exists(self.workspace_path):
                raise ValueError(
                    f"Cannot create workspace directory: {self.workspace_path}"
                )

            # Create project directory if it doesn't exist
            project_dir = os.path.join(self.workspace_path, "project")
            if not ensure_directory_exists(project_dir):
                logger.warning(f"⚠️ Could not create project directory: {project_dir}")
                # Fall back to workspace root for bash operations
                project_dir = self.workspace_path

            # Create tasks directory for TaskTracker
            tasks_dir = os.path.join(self.workspace_path, "tasks")
            if not ensure_directory_exists(tasks_dir):
                logger.warning(f"⚠️ Could not create tasks directory: {tasks_dir}")
                # Fall back to workspace root
                tasks_dir = self.workspace_path

            return {
                "project_dir": project_dir,
                "tasks_dir": tasks_dir,
                "agent_workspace_path": self.workspace_path,
            }

    def get_runtime_info(self) -> Dict[str, Any]:
        """
        Get comprehensive runtime information.

        Returns:
            Dictionary with runtime type, paths, and connection details
        """
        paths = self.get_runtime_paths()

        info = {
            "type": "remote" if self.is_remote else "local",
            "workspace_path": self.workspace_path,
            "state_path": self.state_path,
            **paths,
        }

        if self.is_remote:
            info.update(
                {
                    "runtime_url": self.runtime_url,
                    "has_session_key": bool(self.session_api_key),
                }
            )

        return info

    def log_runtime_info(self, context: str = ""):
        """Log runtime configuration information."""
        runtime_type = "🌐 Remote" if self.is_remote else "🏠 Local"
        paths = self.get_runtime_paths()

        logger.info(f"{runtime_type} runtime configuration {context}")
        logger.info(f"  Project dir: {paths['project_dir']}")
        logger.info(f"  Tasks dir: {paths['tasks_dir']}")
        logger.info(f"  Agent workspace: {paths['agent_workspace_path']}")

        if self.is_remote:
            logger.info(f"  Runtime URL: {self.runtime_url}")

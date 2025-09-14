"""
Repository management utilities for OpenVibe backend.
Handles cloning and managing GitHub repositories for riffs.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
from openvibe_cli.backend_modules.utils.logging import get_logger

logger = get_logger(__name__)


def create_workspace_directory(user_uuid: str, app_slug: str, riff_slug: str) -> str:
    """
    Create workspace directory structure for a riff.

    Args:
        user_uuid: User's UUID
        app_slug: App slug identifier
        riff_slug: Riff slug identifier

    Returns:
        str: Path to the workspace directory
    """
    workspace_path = f"/data/{user_uuid}/apps/{app_slug}/riffs/{riff_slug}/workspace"

    try:
        # Create the directory structure
        Path(workspace_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Created workspace directory: {workspace_path}")
        return workspace_path
    except Exception as e:
        logger.error(f"❌ Failed to create workspace directory {workspace_path}: {e}")
        raise


def clone_repository(
    github_url: str, workspace_path: str, branch_name: str
) -> Tuple[bool, Optional[str]]:
    """
    Clone a GitHub repository to the workspace and checkout the specified branch.

    Args:
        github_url: GitHub repository URL
        workspace_path: Path to the workspace directory
        branch_name: Branch name to checkout (riff name)

    Returns:
        Tuple[bool, Optional[str]]: (success, error_message)
    """
    try:
        # Ensure workspace directory exists
        Path(workspace_path).mkdir(parents=True, exist_ok=True)

        # Define project directory within workspace
        project_path = os.path.join(workspace_path, "project")

        # Remove existing project directory if any
        if os.path.exists(project_path):
            logger.info(f"🧹 Cleaning existing project directory: {project_path}")
            shutil.rmtree(project_path)

        logger.info(f"📥 Cloning repository {github_url} to {project_path}")

        # Clone the repository into the project subdirectory
        clone_cmd = ["git", "clone", github_url, project_path]
        result = subprocess.run(
            clone_cmd, capture_output=True, text=True, timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            error_msg = f"Failed to clone repository: {result.stderr}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

        logger.info(f"✅ Successfully cloned repository to {project_path}")

        # Change to the project directory for git operations
        original_cwd = os.getcwd()
        try:
            os.chdir(project_path)

            # Check if branch exists (try remote first, then local)
            check_remote_branch_cmd = [
                "git",
                "ls-remote",
                "--heads",
                "origin",
                branch_name,
            ]
            remote_result = subprocess.run(
                check_remote_branch_cmd, capture_output=True, text=True, timeout=30
            )

            if remote_result.returncode == 0 and remote_result.stdout.strip():
                # Remote branch exists, checkout and track it
                logger.info(f"🌿 Remote branch '{branch_name}' found, checking out...")
                checkout_cmd = [
                    "git",
                    "checkout",
                    "-b",
                    branch_name,
                    f"origin/{branch_name}",
                ]
            else:
                # Check if local branch exists
                check_local_branch_cmd = ["git", "branch", "--list", branch_name]
                local_result = subprocess.run(
                    check_local_branch_cmd, capture_output=True, text=True, timeout=30
                )

                if local_result.returncode == 0 and local_result.stdout.strip():
                    # Local branch exists, checkout it
                    logger.info(
                        f"🌿 Local branch '{branch_name}' found, checking out..."
                    )
                    checkout_cmd = ["git", "checkout", branch_name]
                else:
                    # Branch doesn't exist, create new branch from main/master
                    logger.info(
                        f"🌿 Branch '{branch_name}' not found, creating new branch..."
                    )

                    # First, determine the default branch
                    default_branch_cmd = [
                        "git",
                        "symbolic-ref",
                        "refs/remotes/origin/HEAD",
                    ]
                    default_result = subprocess.run(
                        default_branch_cmd, capture_output=True, text=True, timeout=30
                    )

                    if default_result.returncode == 0:
                        default_branch = default_result.stdout.strip().split("/")[-1]
                    else:
                        # Fallback to common default branches
                        for candidate in ["main", "master"]:
                            check_cmd = [
                                "git",
                                "ls-remote",
                                "--heads",
                                "origin",
                                candidate,
                            ]
                            check_result = subprocess.run(
                                check_cmd, capture_output=True, text=True, timeout=30
                            )
                            if (
                                check_result.returncode == 0
                                and check_result.stdout.strip()
                            ):
                                default_branch = candidate
                                break
                        else:
                            default_branch = "main"  # Final fallback

                    logger.info(
                        f"🌿 Creating new branch '{branch_name}' from '{default_branch}'"
                    )
                    checkout_cmd = [
                        "git",
                        "checkout",
                        "-b",
                        branch_name,
                        f"origin/{default_branch}",
                    ]

            # Execute the checkout command
            checkout_result = subprocess.run(
                checkout_cmd, capture_output=True, text=True, timeout=60
            )

            if checkout_result.returncode != 0:
                error_msg = f"Failed to checkout branch '{branch_name}': {checkout_result.stderr}"
                logger.error(f"❌ {error_msg}")
                return False, error_msg

            logger.info(f"✅ Successfully checked out branch '{branch_name}'")

            # Verify the current branch
            verify_cmd = ["git", "branch", "--show-current"]
            verify_result = subprocess.run(
                verify_cmd, capture_output=True, text=True, timeout=30
            )

            if verify_result.returncode == 0:
                current_branch = verify_result.stdout.strip()
                logger.info(f"📍 Current branch: {current_branch}")

            return True, None

        finally:
            # Always return to original directory
            os.chdir(original_cwd)

    except subprocess.TimeoutExpired:
        error_msg = "Repository operation timed out"
        logger.error(f"❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error during repository setup: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg


def setup_riff_workspace(
    user_uuid: str, app_slug: str, riff_slug: str, github_url: str
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Complete workspace setup for a riff: create directory and clone repository.

    Args:
        user_uuid: User's UUID
        app_slug: App slug identifier
        riff_slug: Riff slug identifier (used as branch name)
        github_url: GitHub repository URL

    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (success, workspace_path, error_message)
    """
    try:
        # Create workspace directory
        workspace_path = create_workspace_directory(user_uuid, app_slug, riff_slug)

        # Clone repository and checkout branch
        success, error_msg = clone_repository(github_url, workspace_path, riff_slug)

        if success:
            logger.info(f"🎉 Workspace setup complete: {workspace_path}")
            return True, workspace_path, None
        else:
            return False, workspace_path, error_msg

    except Exception as e:
        error_msg = f"Failed to setup workspace: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, None, error_msg

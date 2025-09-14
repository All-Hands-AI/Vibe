"""
Repository management utilities for OpenVibe backend.
Handles cloning and managing GitHub repositories for riffs.

When cloning repositories, the user's stored GitHub token is automatically
embedded in the remote URL to enable authenticated push/pull operations.
"""

import os
import subprocess
import shutil
import requests
import re
from pathlib import Path
from typing import Optional, Tuple
from utils.logging import get_logger
from keys import load_user_keys

logger = get_logger(__name__)


def extract_repo_info(github_url: str) -> Optional[Tuple[str, str]]:
    """
    Extract owner and repository name from GitHub URL.

    Args:
        github_url: GitHub repository URL

    Returns:
        Tuple[str, str]: (owner, repo) or None if invalid URL
    """
    # Handle various GitHub URL formats
    patterns = [
        r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
        r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?/?$",
    ]

    for pattern in patterns:
        match = re.match(pattern, github_url.strip())
        if match:
            owner, repo = match.groups()
            return owner, repo

    logger.error(f"❌ Could not extract repo info from URL: {github_url}")
    return None


def check_branch_exists(
    github_url: str, branch_name: str, github_token: str
) -> Tuple[bool, bool]:
    """
    Check if a branch exists on GitHub (both remote and local).

    Args:
        github_url: GitHub repository URL
        branch_name: Branch name to check
        github_token: GitHub API token

    Returns:
        Tuple[bool, bool]: (remote_exists, local_exists)
    """
    try:
        repo_info = extract_repo_info(github_url)
        if not repo_info:
            return False, False

        owner, repo = repo_info

        # Check remote branch existence via GitHub API
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        api_url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch_name}"
        response = requests.get(api_url, headers=headers, timeout=30)

        remote_exists = response.status_code == 200
        logger.info(f"🌿 Remote branch '{branch_name}' exists: {remote_exists}")

        return remote_exists, False  # We can't check local without being in the repo
    except Exception as e:
        logger.error(f"❌ Error checking branch existence: {str(e)}")
        return False, False


def check_pr_exists(
    github_url: str, branch_name: str, github_token: str
) -> Tuple[bool, Optional[str]]:
    """
    Check if a pull request exists for the given branch.

    Args:
        github_url: GitHub repository URL
        branch_name: Branch name to check for PR
        github_token: GitHub API token

    Returns:
        Tuple[bool, Optional[str]]: (pr_exists, pr_url)
    """
    try:
        repo_info = extract_repo_info(github_url)
        if not repo_info:
            return False, None

        owner, repo = repo_info

        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Search for PRs from this branch as head
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls?head={owner}:{branch_name}&state=open"
        response = requests.get(api_url, headers=headers, timeout=30)

        if response.status_code == 200:
            prs = response.json()
            if prs and len(prs) > 0:
                pr_url = prs[0].get("html_url")
                logger.info(
                    f"🔀 Found existing PR for branch '{branch_name}': {pr_url}"
                )
                return True, pr_url
            else:
                logger.info(f"🔀 No existing PR found for branch '{branch_name}'")
                return False, None
        else:
            logger.error(f"❌ Failed to check PR existence: {response.status_code}")
            return False, None

    except Exception as e:
        logger.error(f"❌ Error checking PR existence: {str(e)}")
        return False, None


def create_pull_request(
    github_url: str, branch_name: str, github_token: str
) -> Tuple[bool, Optional[str]]:
    """
    Create a pull request for the given branch using GitHub API.
    If a PR already exists, return the existing PR URL instead of failing.

    Args:
        github_url: GitHub repository URL
        branch_name: Branch name to create PR for
        github_token: GitHub API token

    Returns:
        Tuple[bool, Optional[str]]: (success, pr_url or error_message)
    """
    try:
        # First check if PR already exists
        pr_exists, existing_pr_url = check_pr_exists(
            github_url, branch_name, github_token
        )
        if pr_exists and existing_pr_url:
            logger.info(f"🔀 Adopting existing pull request: {existing_pr_url}")
            return True, existing_pr_url

        repo_info = extract_repo_info(github_url)
        if not repo_info:
            return False, "Could not extract repository information from URL"

        owner, repo = repo_info

        # GitHub API endpoint for creating pull requests
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

        # PR data with branch name as title
        pr_data = {
            "title": branch_name,
            "head": branch_name,
            "base": "main",  # Default to main branch
            "body": f"Automated pull request for branch: {branch_name}",
            "draft": True,  # Create as draft PR
        }

        logger.info(
            f"🔀 Creating pull request for branch '{branch_name}' in {owner}/{repo}"
        )

        response = requests.post(api_url, headers=headers, json=pr_data, timeout=30)

        if response.status_code == 201:
            pr_data = response.json()
            pr_url = pr_data.get("html_url")
            logger.info(f"✅ Successfully created pull request: {pr_url}")
            return True, pr_url
        elif response.status_code == 422:
            # PR might already exist or other validation error
            error_data = response.json()
            error_message = error_data.get("message", "Validation error")

            # Check if it's a "pull request already exists" error
            if (
                "already exists" in error_message.lower()
                or "pull request" in error_message.lower()
            ):
                # Try to find the existing PR
                pr_exists, existing_pr_url = check_pr_exists(
                    github_url, branch_name, github_token
                )
                if pr_exists and existing_pr_url:
                    logger.info(
                        f"🔀 Found existing pull request after creation attempt: {existing_pr_url}"
                    )
                    return True, existing_pr_url

            logger.warning(f"⚠️ Pull request creation failed: {error_message}")
            return False, f"PR creation failed: {error_message}"
        else:
            error_message = (
                f"GitHub API error: {response.status_code} - {response.text}"
            )
            logger.error(f"❌ {error_message}")
            return False, error_message

    except Exception as e:
        error_message = f"Error creating pull request: {str(e)}"
        logger.error(f"❌ {error_message}")
        return False, error_message


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
    github_url: str, workspace_path: str, branch_name: str, user_uuid: str
) -> Tuple[bool, Optional[str]]:
    """
    Clone a GitHub repository to the workspace and checkout the specified branch.
    If user has a GitHub token, push the branch to remote and create a pull request.

    The cloned repository will have the user's stored GitHub token embedded in its remote URL
    to enable authenticated push/pull operations for all users.

    Args:
        github_url: GitHub repository URL
        workspace_path: Path to the workspace directory
        branch_name: Branch name to checkout (riff name)
        user_uuid: User's UUID to retrieve their stored GitHub token

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

        # Modify GitHub URL to include user's stored token for authentication
        try:
            user_keys = load_user_keys(user_uuid)
            github_token = user_keys.get("github")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load user keys for {user_uuid}: {e}")
            github_token = None

        if github_token and github_url.startswith("https://github.com/"):
            # Insert token into URL for authenticated cloning
            authenticated_url = github_url.replace(
                "https://github.com/", f"https://{github_token}@github.com/"
            )
            logger.info(
                f"📥 Cloning repository with user authentication to {project_path}"
            )
        else:
            authenticated_url = github_url
            if not github_token:
                logger.warning(
                    f"⚠️ No GitHub token found for user {user_uuid}, cloning without authentication"
                )
            logger.info(f"📥 Cloning repository {github_url} to {project_path}")

        # Clone the repository into the project subdirectory
        clone_cmd = ["git", "clone", authenticated_url, project_path]
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

            # Configure git user settings for commits
            git_config_commands = [
                ["git", "config", "user.name", "openhands"],
                ["git", "config", "user.email", "openhands@all-hands.dev"],
            ]

            for config_cmd in git_config_commands:
                config_result = subprocess.run(
                    config_cmd, capture_output=True, text=True, timeout=30
                )
                if config_result.returncode != 0:
                    error_msg = f"Failed to configure git: {config_result.stderr}"
                    logger.error(f"❌ {error_msg}")
                    return False, error_msg

            logger.info("✅ Git configuration set successfully")

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

            # If GitHub token is available, push branch and create PR
            if github_token and current_branch == branch_name:
                logger.info(
                    f"🚀 Preparing branch '{branch_name}' for push and PR creation..."
                )

                # Check if we need to add an empty commit (only for new branches)
                branch_was_created_new = (
                    remote_result.returncode != 0 or not remote_result.stdout.strip()
                )

                if branch_was_created_new:
                    # Add an empty commit to ensure there's always something to create a PR with
                    # This is especially important when the branch is identical to the base branch
                    empty_commit_cmd = [
                        "git",
                        "commit",
                        "--allow-empty",
                        "-m",
                        f"chore: initialize branch '{branch_name}' for development\n\nThis empty commit ensures the branch can have a pull request opened\nfor collaborative development and code review.",
                    ]
                    empty_commit_result = subprocess.run(
                        empty_commit_cmd, capture_output=True, text=True, timeout=30
                    )

                    if empty_commit_result.returncode == 0:
                        logger.info(f"✅ Added empty commit to branch '{branch_name}'")
                    else:
                        # Don't fail if empty commit fails - the branch might already have commits
                        logger.warning(
                            f"⚠️ Could not add empty commit to branch '{branch_name}': {empty_commit_result.stderr}"
                        )

                    # Push the new branch to remote
                    push_cmd = ["git", "push", "-u", "origin", branch_name]
                    push_result = subprocess.run(
                        push_cmd, capture_output=True, text=True, timeout=120
                    )

                    if push_result.returncode == 0:
                        logger.info(
                            f"✅ Successfully pushed branch '{branch_name}' to remote"
                        )
                    else:
                        # Check if it's just because the branch already exists
                        if (
                            "already exists" in push_result.stderr.lower()
                            or "up-to-date" in push_result.stderr.lower()
                        ):
                            logger.info(
                                f"🌿 Branch '{branch_name}' already exists on remote, adopting it"
                            )
                        else:
                            error_msg = f"Failed to push branch '{branch_name}' to remote: {push_result.stderr}"
                            logger.error(f"❌ {error_msg}")
                            return False, error_msg
                else:
                    logger.info(f"🌿 Adopting existing remote branch '{branch_name}'")

                # Create pull request (this will check for existing PR first)
                pr_success, pr_result = create_pull_request(
                    github_url, branch_name, github_token
                )
                if pr_success:
                    logger.info(f"🔀 Pull request ready: {pr_result}")
                else:
                    # Don't fail the entire operation if PR creation fails
                    logger.warning(
                        f"⚠️ Could not create/find pull request for branch '{branch_name}': {pr_result}"
                    )
                    # Continue without failing - the branch is still set up correctly
            elif not github_token:
                logger.info(
                    f"ℹ️ No GitHub token available for user {user_uuid}, skipping push and PR creation"
                )

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
    If user has a GitHub token, push the branch to remote and create a pull request.

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
        success, error_msg = clone_repository(
            github_url, workspace_path, riff_slug, user_uuid
        )

        if success:
            logger.info(f"🎉 Workspace setup complete: {workspace_path}")
            return True, workspace_path, None
        else:
            return False, workspace_path, error_msg

    except Exception as e:
        error_msg = f"Failed to setup workspace: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, None, error_msg

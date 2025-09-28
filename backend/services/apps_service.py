"""
Apps Service - Business logic for app management.

This service handles:
- App CRUD operations
- GitHub repository management
- Fly.io app management
- App deployment status checking
- Initial riff creation for new apps
"""

import re
import time
import uuid
import requests
import logging
from base64 import b64encode
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from nacl import encoding, public

from storage import get_apps_storage, get_riffs_storage
from keys import load_user_keys
from utils.deployment_status import get_deployment_status


logger = logging.getLogger(__name__)


class AppsService:
    """Service for managing apps and their associated resources."""

    def __init__(self):
        pass

    # App CRUD operations
    def load_user_apps(self, user_uuid: str) -> List[Dict[str, Any]]:
        """Load apps for a specific user."""
        storage = get_apps_storage(user_uuid)
        return storage.list_apps()

    def load_user_app(self, user_uuid: str, app_slug: str) -> Optional[Dict[str, Any]]:
        """Load specific app for a user."""
        storage = get_apps_storage(user_uuid)
        return storage.load_app(app_slug)

    def save_user_app(self, user_uuid: str, app_slug: str, app_data: Dict[str, Any]) -> bool:
        """Save app for a specific user."""
        storage = get_apps_storage(user_uuid)
        return storage.save_app(app_slug, app_data)

    def user_app_exists(self, user_uuid: str, app_slug: str) -> bool:
        """Check if app exists for user."""
        storage = get_apps_storage(user_uuid)
        return storage.app_exists(app_slug)

    def delete_user_app(self, user_uuid: str, app_slug: str) -> bool:
        """Delete app for a specific user."""
        storage = get_apps_storage(user_uuid)
        return storage.delete_app(app_slug)

    # Slug validation and creation
    def is_valid_slug(self, slug: str) -> bool:
        """Validate that a slug contains only lowercase letters, numbers, and hyphens."""
        if not slug:
            return False
        # Check if slug matches the pattern: lowercase letters, numbers, and hyphens only
        # Must not start or end with hyphen, and no consecutive hyphens
        pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
        return bool(re.match(pattern, slug))

    def create_slug(self, name: str) -> str:
        """Convert app name to slug format."""
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
        slug = re.sub(r"\s+", "-", slug.strip())
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")

    # Riff operations
    def save_user_riff(self, user_uuid: str, app_slug: str, riff_slug: str, riff_data: Dict[str, Any]) -> bool:
        """Save riff for a specific user."""
        storage = get_riffs_storage(user_uuid)
        return storage.save_riff(app_slug, riff_slug, riff_data)

    def add_user_message(self, user_uuid: str, app_slug: str, riff_slug: str, message: Dict[str, Any]) -> bool:
        """Add a message to a riff for a specific user."""
        storage = get_riffs_storage(user_uuid)
        return storage.add_message(app_slug, riff_slug, message)

    # Fly.io operations
    def get_user_default_org(self, fly_token: str) -> Tuple[bool, str]:
        """
        Get the user's default organization slug by checking their existing apps.
        
        Args:
            fly_token: The user's Fly.io API token
            
        Returns:
            tuple: (success, org_slug_or_error_message)
        """
        if not fly_token:
            return False, "Fly.io API token is required"

        logger.debug("🛩️ Attempting to determine user's organization from existing apps")

        try:
            headers = {
                "Authorization": f"Bearer {fly_token}",
                "Content-Type": "application/json",
                "User-Agent": "OpenVibe-Backend/1.0",
            }

            # Try to list user's existing apps to determine their organization
            response = requests.get(
                "https://api.machines.dev/v1/apps", headers=headers, timeout=10
            )

            if response.status_code == 200:
                apps = response.json()
                if apps and len(apps) > 0:
                    # Get organization from the first app
                    first_app = apps[0]
                    org_slug = first_app.get("organization", {}).get("slug")
                    if org_slug:
                        logger.debug(f"🛩️ Detected user organization from existing apps: {org_slug}")
                        return True, org_slug
                    else:
                        logger.debug("🛩️ No organization info found in existing apps")
                else:
                    logger.debug("🛩️ User has no existing apps")
            else:
                logger.debug(f"🛩️ Failed to list apps: {response.status_code}")

        except Exception as e:
            logger.debug(f"🛩️ Error determining organization from apps: {str(e)}")

        # Fall back to 'personal' as the default organization slug
        logger.debug("🛩️ Falling back to default organization: personal")
        return True, "personal"

    def create_fly_app(self, app_name: str, fly_token: str) -> Tuple[bool, Any]:
        """
        Create a new Fly.io app.
        
        Args:
            app_name: The app name to create
            fly_token: The user's Fly.io API token
            
        Returns:
            tuple: (success, app_data_or_error_message)
        """
        if not fly_token:
            return False, "Fly.io API token is required"

        logger.info(f"🛩️ Creating Fly.io app: {app_name}")

        # First, get the user's default organization
        success, org_slug = self.get_user_default_org(fly_token)
        if not success:
            return False, f"Failed to get user organization: {org_slug}"

        logger.debug(f"🛩️ Using organization: {org_slug}")

        headers = {
            "Authorization": f"Bearer {fly_token}",
            "Content-Type": "application/json",
            "User-Agent": "OpenVibe-Backend/1.0",
        }

        # Check if app already exists first
        try:
            check_response = requests.get(
                f"https://api.machines.dev/v1/apps/{app_name}", headers=headers, timeout=10
            )

            if check_response.status_code == 200:
                # App already exists, check if it's owned by user
                app_data = check_response.json()
                app_org_slug = app_data.get("organization", {}).get("slug")

                logger.info(f"✅ App '{app_name}' already exists and user has access to it")
                logger.debug(f"🛩️ App organization: {app_org_slug}, Expected: {org_slug}")

                # Update our understanding of the user's organization if it differs
                if app_org_slug and app_org_slug != org_slug:
                    logger.debug(f"🛩️ Updating user organization from {org_slug} to {app_org_slug}")

                return True, app_data

            elif check_response.status_code == 403:
                logger.error(f"❌ App '{app_name}' exists but user doesn't have access to it")
                return False, f"App '{app_name}' already exists and is not owned by you"

            elif check_response.status_code == 401:
                logger.error("❌ Invalid Fly.io API token")
                return False, "Invalid Fly.io API token"

            elif check_response.status_code != 404:
                logger.error(f"❌ Error checking app existence: {check_response.status_code} - {check_response.text}")
                return False, f"Error checking app existence: {check_response.status_code}"

        except Exception as e:
            logger.error(f"💥 Error checking app existence: {str(e)}")
            return False, f"Error checking app existence: {str(e)}"

        # App doesn't exist, create it
        try:
            create_data = {"app_name": app_name, "org_slug": org_slug}

            logger.debug(f"🛩️ Creating app with data: {create_data}")

            create_response = requests.post(
                "https://api.machines.dev/v1/apps",
                headers=headers,
                json=create_data,
                timeout=30,
            )

            logger.debug(f"🛩️ App creation response status: {create_response.status_code}")

            if create_response.status_code == 201:
                app_data = create_response.json()
                logger.info(f"✅ Successfully created Fly.io app: {app_name}")
                logger.debug(f"🛩️ Created app data: {app_data}")
                return True, app_data

            elif create_response.status_code == 422:
                error_text = create_response.text
                logger.error(f"❌ App creation failed - name taken or invalid: {error_text}")
                if "already taken" in error_text.lower():
                    return False, f"App name '{app_name}' is already taken"
                else:
                    return False, f"Invalid app name or creation failed: {error_text}"

            elif create_response.status_code == 401:
                logger.error("❌ Unauthorized - invalid Fly.io API token")
                return False, "Invalid Fly.io API token"

            elif create_response.status_code == 403:
                logger.error("❌ Forbidden - insufficient permissions")
                return False, "Insufficient permissions for Fly.io API"

            else:
                logger.error(f"❌ Unexpected response from Fly.io API: {create_response.status_code} - {create_response.text}")
                return False, f"Fly.io API error: {create_response.status_code}"

        except requests.exceptions.Timeout:
            logger.error("❌ Timeout creating Fly.io app")
            return False, "Timeout creating Fly.io app"

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error connecting to Fly.io API: {str(e)}")
            return False, f"Error connecting to Fly.io API: {str(e)}"

        except Exception as e:
            logger.error(f"💥 Unexpected error creating Fly.io app: {str(e)}")
            return False, f"Unexpected error: {str(e)}"

    def delete_fly_app(self, app_name: str, fly_token: str) -> Tuple[bool, str]:
        """Delete a Fly.io app."""
        logger.info(f"🗑️ Deleting Fly.io app: {app_name}")

        try:
            if not fly_token:
                return False, "Fly.io API token is required"

            headers = {
                "Authorization": f"Bearer {fly_token}",
                "Content-Type": "application/json",
                "User-Agent": "OpenVibe-Backend/1.0",
            }

            # First check if app exists
            check_response = requests.get(
                f"https://api.machines.dev/v1/apps/{app_name}", headers=headers, timeout=10
            )

            if check_response.status_code == 404:
                logger.warning(f"⚠️ Fly.io app not found: {app_name}")
                return True, "App not found (may have been already deleted)"
            elif check_response.status_code != 200:
                logger.error(f"❌ Error checking Fly.io app: {check_response.status_code}")
                return False, f"Error checking app status: {check_response.status_code}"

            # Delete the app
            delete_response = requests.delete(
                f"https://api.machines.dev/v1/apps/{app_name}", headers=headers, timeout=30
            )

            if delete_response.status_code in [200, 202, 204]:
                logger.info(f"✅ Successfully deleted Fly.io app: {app_name}")
                return True, "App deleted successfully"
            elif delete_response.status_code == 404:
                logger.warning(f"⚠️ Fly.io app not found during deletion: {app_name}")
                return True, "App not found (may have been already deleted)"
            elif delete_response.status_code == 403:
                logger.error(f"❌ Insufficient permissions to delete Fly.io app: {app_name}")
                return False, "Insufficient permissions to delete app"
            else:
                logger.error(f"❌ Failed to delete Fly.io app: {delete_response.status_code} - {delete_response.text}")
                return False, f"Fly.io API error: {delete_response.status_code}"

        except Exception as e:
            logger.error(f"💥 Error deleting Fly.io app: {str(e)}")
            return False, f"Error deleting app: {str(e)}"

    def get_fly_status(self, project_slug: str, fly_token: str) -> Optional[Dict[str, Any]]:
        """Get Fly.io deployment status."""
        logger.info(f"🚁 Checking Fly.io status for: {project_slug}")

        try:
            if not fly_token:
                logger.warning("❌ No Fly.io token available")
                return None

            headers = {
                "Authorization": f"Bearer {fly_token}",
                "Content-Type": "application/json",
            }

            # Check if app exists and get status
            app_response = requests.get(
                f"https://api.machines.dev/v1/apps/{project_slug}",
                headers=headers,
                timeout=10,
            )

            if app_response.status_code == 404:
                logger.info(f"⚠️ Fly.io app not found: {project_slug}")
                return {"deployed": False, "app_url": None, "status": "not_found"}
            elif app_response.status_code != 200:
                logger.warning(f"❌ Failed to get Fly.io app status: {app_response.status_code}")
                return None

            app_data = app_response.json()
            app_status = app_data.get("status", "unknown")

            # Construct app URL
            app_url = f"https://{project_slug}.fly.dev"

            logger.info(f"✅ Fly.io status retrieved: {app_status}")

            return {
                "deployed": app_status in ["running", "deployed"],
                "app_url": app_url,
                "status": app_status,
                "organization": app_data.get("organization", {}).get("slug"),
            }

        except Exception as e:
            logger.error(f"💥 Fly.io status check error: {str(e)}")
            return None

    # GitHub operations
    def create_github_repo(self, repo_name: str, github_token: str, fly_token: str) -> Tuple[bool, str]:
        """Create a GitHub repository from template and set FLY_API_TOKEN secret."""
        logger.info(f"🐙 Creating GitHub repo: {repo_name}")
        logger.debug(f"🐙 GitHub token length: {len(github_token)}")
        logger.debug(f"🐙 GitHub token prefix: {github_token[:10]}...")
        logger.debug(f"🐙 Fly token provided: {bool(fly_token)}")
        logger.debug(f"🐙 Fly token length: {len(fly_token) if fly_token else 0}")

        try:
            # First, check if repo already exists
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "OpenVibe-Backend/1.0",
            }
            logger.debug(f"🐙 Request headers: {headers}")

            # Get the authenticated user to determine the owner
            logger.debug("🐙 Making request to GitHub user API...")
            user_response = requests.get(
                "https://api.github.com/user", headers=headers, timeout=10
            )
            logger.debug(f"🐙 GitHub user API response: {user_response.status_code}")

            if user_response.status_code != 200:
                logger.error(f"❌ Failed to get GitHub user: {user_response.text}")
                logger.debug(f"🐙 Response content: {user_response.content}")
                return False, "Failed to authenticate with GitHub"

            user_data = user_response.json()
            owner = user_data["login"]
            logger.debug(f"🔍 GitHub owner: {owner}")
            logger.debug(f"🔍 GitHub user authenticated: {user_data.get('login', 'unknown')}")

            # Check if repo already exists
            check_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo_name}",
                headers=headers,
                timeout=10,
            )
            if check_response.status_code == 200:
                # Repository already exists, but that's okay - we'll use the existing one
                repo_data = check_response.json()
                logger.info(f"✅ Repository {owner}/{repo_name} already exists, using existing repository")

                # Still try to set the FLY_API_TOKEN secret if provided
                if fly_token:
                    self._set_github_secret(owner, repo_name, fly_token, headers)

                return True, repo_data["html_url"]

            # Create repo from template
            create_data = {
                "name": repo_name,
                "description": f"OpenVibe app: {repo_name}",
                "private": False,
                "include_all_branches": False,
            }

            template_headers = headers.copy()
            template_headers["Accept"] = "application/vnd.github.baptiste-preview+json"

            create_response = requests.post(
                "https://api.github.com/repos/rbren/openvibe-template/generate",
                headers=template_headers,
                json=create_data,
                timeout=30,
            )

            if create_response.status_code != 201:
                logger.error(f"Failed to create repo from template: {create_response.text}")
                return False, f"Failed to create repository: {create_response.text}"

            repo_data = create_response.json()
            logger.info(f"✅ Created repository: {repo_data['html_url']}")

            # Set FLY_API_TOKEN secret
            if fly_token:
                self._set_github_secret(owner, repo_name, fly_token, headers)

            return True, repo_data["html_url"]

        except Exception as e:
            logger.error(f"💥 Error creating GitHub repo: {str(e)}")
            return False, f"Error creating repository: {str(e)}"

    def _set_github_secret(self, owner: str, repo_name: str, fly_token: str, headers: Dict[str, str]) -> None:
        """Set FLY_API_TOKEN secret for a GitHub repository."""
        logger.info(f"🔐 Setting FLY_API_TOKEN secret for {repo_name}")

        try:
            # Get the repository's public key for encrypting secrets
            key_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/actions/secrets/public-key",
                headers=headers,
                timeout=10,
            )

            if key_response.status_code == 200:
                public_key_data = key_response.json()
                public_key = public.PublicKey(
                    public_key_data["key"].encode("utf-8"), encoding.Base64Encoder()
                )

                # Encrypt the secret
                sealed_box = public.SealedBox(public_key)
                encrypted = sealed_box.encrypt(fly_token.encode("utf-8"))
                encrypted_value = b64encode(encrypted).decode("utf-8")

                # Set the secret
                secret_data = {
                    "encrypted_value": encrypted_value,
                    "key_id": public_key_data["key_id"],
                }

                secret_response = requests.put(
                    f"https://api.github.com/repos/{owner}/{repo_name}/actions/secrets/FLY_API_TOKEN",
                    headers=headers,
                    json=secret_data,
                    timeout=10,
                )

                if secret_response.status_code in [201, 204]:
                    logger.info("✅ FLY_API_TOKEN secret set successfully")
                else:
                    logger.warning(f"⚠️ Failed to set FLY_API_TOKEN secret: {secret_response.text}")
            else:
                logger.warning(f"⚠️ Failed to get public key for secrets: {key_response.text}")

        except Exception as e:
            logger.warning(f"⚠️ Error setting GitHub secret: {str(e)}")

    def delete_github_repo(self, repo_url: str, github_token: str) -> Tuple[bool, str]:
        """Delete a GitHub repository."""
        logger.info(f"🗑️ Deleting GitHub repo: {repo_url}")

        try:
            # Extract owner and repo from URL
            if not repo_url or "github.com" not in repo_url:
                logger.warning(f"❌ Invalid GitHub URL: {repo_url}")
                return False, "Invalid GitHub URL"

            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) < 2:
                logger.warning(f"❌ Cannot parse GitHub URL: {repo_url}")
                return False, "Cannot parse GitHub URL"

            owner, repo = parts[0], parts[1]
            logger.debug(f"🔍 GitHub repo to delete: {owner}/{repo}")

            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "OpenVibe-Backend/1.0",
            }

            # Delete the repository
            delete_response = requests.delete(
                f"https://api.github.com/repos/{owner}/{repo}", headers=headers, timeout=30
            )

            if delete_response.status_code == 204:
                logger.info(f"✅ Successfully deleted GitHub repo: {owner}/{repo}")
                return True, "Repository deleted successfully"
            elif delete_response.status_code == 404:
                logger.warning(f"⚠️ GitHub repo not found: {owner}/{repo}")
                return True, "Repository not found (may have been already deleted)"
            elif delete_response.status_code == 403:
                logger.error(f"❌ Insufficient permissions to delete repo: {owner}/{repo}")
                return False, "Insufficient permissions to delete repository"
            else:
                logger.error(f"❌ Failed to delete GitHub repo: {delete_response.status_code} - {delete_response.text}")
                return False, f"GitHub API error: {delete_response.status_code}"

        except Exception as e:
            logger.error(f"💥 Error deleting GitHub repo: {str(e)}")
            return False, f"Error deleting repository: {str(e)}"

    def get_github_status(self, repo_url: str, github_token: str) -> Optional[Dict[str, Any]]:
        """Get GitHub repository status including CI/CD tests."""
        logger.info(f"🐙 Checking GitHub status for: {repo_url}")

        try:
            # Extract owner and repo from URL
            if not repo_url or "github.com" not in repo_url:
                logger.warning(f"❌ Invalid GitHub URL: {repo_url}")
                return None

            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) < 2:
                logger.warning(f"❌ Cannot parse GitHub URL: {repo_url}")
                return None

            owner, repo = parts[0], parts[1]
            logger.debug(f"🔍 GitHub repo: {owner}/{repo}")

            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "OpenVibe-Backend/1.0",
            }

            # Get latest commit on main branch
            commits_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/commits/main",
                headers=headers,
                timeout=10,
            )

            if commits_response.status_code != 200:
                logger.warning(f"❌ Failed to get commits: {commits_response.status_code}")
                return None

            commit_data = commits_response.json()
            latest_commit_sha = commit_data["sha"]
            logger.debug(f"🔍 Latest commit: {latest_commit_sha[:7]}")

            # Get status checks for the latest commit
            status_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/commits/{latest_commit_sha}/status",
                headers=headers,
                timeout=10,
            )

            if status_response.status_code != 200:
                logger.warning(f"❌ Failed to get status checks: {status_response.status_code}")
                return {
                    "tests_passing": None,
                    "last_commit": latest_commit_sha,
                    "status": "unknown",
                }

            status_data = status_response.json()
            state = status_data.get("state", "unknown")
            total_count = status_data.get("total_count", 0)

            # If status API returns pending with no checks, try GitHub Actions API as fallback
            if state == "pending" and total_count == 0:
                state = self._check_github_actions(owner, repo, latest_commit_sha, headers) or state

            # Handle different CI/CD states properly
            if state == "success":
                tests_passing = True
            elif state in ["pending", "running"]:
                tests_passing = None  # Use None to indicate "in progress"
            else:  # failure, error, or unknown
                tests_passing = False

            logger.info(f"✅ GitHub status retrieved: {state}")

            return {
                "tests_passing": tests_passing,
                "last_commit": latest_commit_sha,
                "status": state,
                "total_count": status_data.get("total_count", 0),
            }

        except Exception as e:
            logger.error(f"💥 GitHub status check error: {str(e)}")
            return None

    def _check_github_actions(self, owner: str, repo: str, commit_sha: str, headers: Dict[str, str]) -> Optional[str]:
        """Check GitHub Actions as fallback for status checks."""
        try:
            actions_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/actions/runs?head_sha={commit_sha}",
                headers=headers,
                timeout=10,
            )

            if actions_response.status_code == 200:
                actions_data = actions_response.json()
                workflow_runs = actions_data.get("workflow_runs", [])

                if workflow_runs:
                    # Check if all workflows are completed and successful
                    all_completed = True
                    all_successful = True

                    for run in workflow_runs:
                        run_status = run.get("status")
                        run_conclusion = run.get("conclusion")

                        if run_status != "completed":
                            all_completed = False
                        if run_conclusion != "success":
                            all_successful = False

                    if all_completed:
                        return "success" if all_successful else "failure"

        except Exception as e:
            logger.warning(f"❌ Error checking GitHub Actions: {str(e)}")

        return None

    # PR operations
    def get_pr_status(self, repo_url: str, github_token: str, branch: str = "main", search_by_base: bool = False) -> Optional[Dict[str, Any]]:
        """Get GitHub Pull Request status for a specific branch."""
        search_type = "base" if search_by_base else "head"
        logger.info(f"🔀 Checking PR status for: {repo_url} (branch: {branch}, search_by: {search_type})")

        if not github_token:
            logger.warning("❌ No GitHub token provided")
            return None

        # Parse GitHub URL to extract owner and repo
        github_pattern = r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"
        match = re.match(github_pattern, repo_url)
        if not match:
            logger.warning(f"❌ Invalid GitHub URL format: {repo_url}")
            return None

        owner, repo = match.groups()
        logger.debug(f"🔍 Parsed GitHub repo: {owner}/{repo}")

        # Set up headers for GitHub API
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OpenVibe-Backend/1.0",
        }

        try:
            # Search for PRs using GitHub API
            if search_by_base:
                api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls?base={branch}&state=open"
            else:
                api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls?head={owner}:{branch}&state=open"

            pr_response = requests.get(api_url, headers=headers, timeout=10)

            if pr_response.status_code != 200:
                logger.warning(f"❌ GitHub API request failed: {pr_response.status_code}")
                return None

            prs = pr_response.json()

            if not prs:
                logger.debug(f"ℹ️ No open PRs found for {search_type} branch '{branch}'")
                return None

            # Get the first valid PR
            pr = None
            for p in prs:
                if isinstance(p, dict) and "number" in p:
                    pr = p
                    break

            if not pr:
                logger.warning("❌ No valid PR data found in response")
                return None

            pr_number = pr["number"]

            # Get PR details including mergeable status
            pr_detail_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=headers,
                timeout=10,
            )

            if pr_detail_response.status_code != 200:
                logger.warning(f"❌ Failed to get PR details: {pr_detail_response.status_code}")
                return None

            pr_details = pr_detail_response.json()

            # Get commit status for the PR head
            head_sha = pr_details["head"]["sha"]
            status_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/commits/{head_sha}/status",
                headers=headers,
                timeout=10,
            )

            ci_status = "unknown"
            if status_response.status_code == 200:
                status_data = status_response.json()
                ci_status = status_data.get("state", "unknown")

            # Get commit details for the PR head
            commit_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/commits/{head_sha}",
                headers=headers,
                timeout=10,
            )

            commit_hash_short = head_sha[:7] if head_sha else ""
            commit_message = ""
            if commit_response.status_code == 200:
                commit_data = commit_response.json()
                commit_message = commit_data.get("commit", {}).get("message", "")
                # Take only the first line of the commit message for display
                commit_message = commit_message.split("\n")[0] if commit_message else ""

            # Get check runs for more detailed CI information
            checks_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/commits/{head_sha}/check-runs",
                headers=headers,
                timeout=10,
            )

            checks = []
            if checks_response.status_code == 200:
                checks_data = checks_response.json()
                for check in checks_data.get("check_runs", []):
                    checks.append({
                        "name": check["name"],
                        "status": check["status"],
                        "conclusion": check.get("conclusion"),
                        "details_url": check.get("details_url"),
                    })

            # Determine deploy status based on checks
            deploy_status = "unknown"
            for check in checks:
                if "deploy" in check["name"].lower():
                    if check["status"] == "completed":
                        deploy_status = check.get("conclusion", "unknown")
                    else:
                        deploy_status = check["status"]
                    break

            pr_status = {
                "number": pr_details["number"],
                "title": pr_details["title"],
                "html_url": pr_details["html_url"],
                "draft": pr_details.get("draft", False),
                "mergeable": pr_details.get("mergeable"),
                "changed_files": pr_details.get("changed_files", 0),
                "ci_status": ci_status,
                "deploy_status": deploy_status,
                "checks": checks,
                "commit_hash": head_sha,
                "commit_hash_short": commit_hash_short,
                "commit_message": commit_message,
            }

            logger.info(f"✅ PR status retrieved for #{pr_number}")
            return pr_status

        except Exception as e:
            logger.error(f"❌ Unexpected error while fetching PR status: {str(e)}")
            return None

    def close_github_pr(self, repo_url: str, github_token: str, branch_name: str) -> Tuple[bool, str]:
        """Close GitHub Pull Request for a specific branch."""
        logger.info(f"🔀 Closing PR for branch: {branch_name} in {repo_url}")

        try:
            # Extract owner and repo from URL
            if not repo_url or "github.com" not in repo_url:
                logger.warning(f"❌ Invalid GitHub URL: {repo_url}")
                return False, "Invalid GitHub URL"

            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) < 2:
                logger.warning(f"❌ Cannot parse GitHub URL: {repo_url}")
                return False, "Cannot parse GitHub URL"

            owner, repo = parts[0], parts[1]

            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "OpenVibe-Backend/1.0",
            }

            # Find open PRs for this branch
            pr_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls?head={owner}:{branch_name}&state=open",
                headers=headers,
                timeout=10,
            )

            if pr_response.status_code != 200:
                logger.warning(f"❌ Failed to get PRs: {pr_response.status_code}")
                return False, f"Failed to get PRs: {pr_response.status_code}"

            prs = pr_response.json()

            if not prs:
                logger.debug(f"ℹ️ No open PRs found for branch: {branch_name}")
                return True, "No open PRs found for this branch"

            # Close each PR found (usually there should be only one)
            closed_prs = []
            for pr in prs:
                pr_number = pr["number"]
                logger.info(f"🔀 Closing PR #{pr_number} for branch: {branch_name}")

                close_data = {"state": "closed"}
                close_response = requests.patch(
                    f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
                    headers=headers,
                    json=close_data,
                    timeout=10,
                )

                if close_response.status_code == 200:
                    logger.info(f"✅ Successfully closed PR #{pr_number}")
                    closed_prs.append(pr_number)
                else:
                    logger.error(f"❌ Failed to close PR #{pr_number}: {close_response.status_code}")
                    return False, f"Failed to close PR #{pr_number}"

            if closed_prs:
                return True, f"Closed PR(s): {', '.join(map(str, closed_prs))}"
            else:
                return True, "No PRs needed to be closed"

        except Exception as e:
            logger.error(f"💥 Error closing GitHub PR: {str(e)}")
            return False, f"Error closing PR: {str(e)}"

    def delete_github_branch(self, repo_url: str, github_token: str, branch_name: str) -> Tuple[bool, str]:
        """Delete a GitHub branch."""
        logger.info(f"🌿 Deleting branch: {branch_name} from {repo_url}")

        try:
            # Extract owner and repo from URL
            if not repo_url or "github.com" not in repo_url:
                logger.warning(f"❌ Invalid GitHub URL: {repo_url}")
                return False, "Invalid GitHub URL"

            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) < 2:
                logger.warning(f"❌ Cannot parse GitHub URL: {repo_url}")
                return False, "Cannot parse GitHub URL"

            owner, repo = parts[0], parts[1]

            # Don't delete main/master branches
            if branch_name.lower() in ["main", "master"]:
                logger.warning(f"⚠️ Cannot delete protected branch: {branch_name}")
                return False, f"Cannot delete protected branch: {branch_name}"

            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "OpenVibe-Backend/1.0",
            }

            # Delete the branch
            delete_response = requests.delete(
                f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch_name}",
                headers=headers,
                timeout=10,
            )

            if delete_response.status_code == 204:
                logger.info(f"✅ Successfully deleted branch: {branch_name}")
                return True, f"Branch '{branch_name}' deleted successfully"
            elif delete_response.status_code == 404:
                logger.warning(f"⚠️ Branch not found: {branch_name}")
                return True, f"Branch '{branch_name}' not found (may have been already deleted)"
            elif delete_response.status_code == 422:
                logger.warning(f"⚠️ Cannot delete branch: {branch_name} (may be protected)")
                return False, f"Cannot delete branch '{branch_name}' (may be protected)"
            else:
                logger.error(f"❌ Failed to delete branch: {delete_response.status_code} - {delete_response.text}")
                return False, f"GitHub API error: {delete_response.status_code}"

        except Exception as e:
            logger.error(f"💥 Error deleting GitHub branch: {str(e)}")
            return False, f"Error deleting branch: {str(e)}"

    # App creation workflow
    def create_initial_riff_and_message(self, user_uuid: str, app_slug: str, app_slug_for_message: str, github_url: str) -> Tuple[bool, Any]:
        """Create initial riff and message for a new app."""
        try:
            # Import here to avoid circular imports
            from routes.riffs import create_agent_for_user

            # Create riff name and slug using branch name format
            riff_name = f"rename-to-{app_slug}"
            riff_slug = riff_name  # Already in slug format since app_slug is validated

            logger.info(f"🔄 Creating initial riff: {riff_name} -> {riff_slug} for app {app_slug}")

            # Create riff record
            riff = {
                "slug": riff_slug,
                "app_slug": app_slug,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user_uuid,
                "last_message_at": None,
                "message_count": 0,
            }

            # Save riff
            if not self.save_user_riff(user_uuid, app_slug, riff_slug, riff):
                logger.error("❌ Failed to save initial riff")
                return False, "Failed to save initial riff"

            # Create initial message with instructions
            message_id = str(uuid.uuid4())
            created_at = datetime.now(timezone.utc).isoformat()

            initial_message_content = f"""
We need to customize this app template by renaming everything to "{app_slug_for_message}".
Read TEMPLATE.md and run the command there to rename everything. Then commit and push your changes.
Update the corresponding PR title and description but be brief.
"""

            message = {
                "id": message_id,
                "content": initial_message_content,
                "riff_slug": riff_slug,
                "app_slug": app_slug,
                "created_at": created_at,
                "created_by": user_uuid,
                "type": "user",
                "metadata": {"initial_setup": True},
            }

            # Add message
            if not self.add_user_message(user_uuid, app_slug, riff_slug, message):
                logger.error("❌ Failed to save initial message")
                return False, "Failed to save initial message"

            # Create agent for the riff using the working function from riffs.py
            logger.info(f"🤖 Creating agent for initial riff: {riff_slug}")
            agent_success, agent_error = create_agent_for_user(user_uuid, app_slug, riff_slug)

            if not agent_success:
                logger.warning(f"⚠️ Failed to create agent for initial riff: {agent_error}")
                # Don't fail the entire process if agent creation fails
                return True, {
                    "riff": riff,
                    "message": message,
                    "agent_warning": f"Agent creation failed: {agent_error}",
                }

            # Send initial message to agent
            try:
                from agents import agent_loop_manager
                agent_loop = agent_loop_manager.get_agent_loop(user_uuid, app_slug, riff_slug)
                if agent_loop:
                    logger.info(f"🤖 Sending initial message to agent for {user_uuid[:8]}/{app_slug}/{riff_slug}")
                    confirmation = agent_loop.send_message(initial_message_content)
                    logger.info(f"✅ Initial message sent to agent: {confirmation}")
                else:
                    logger.warning(f"❌ AgentLoop not found after creation for {user_uuid[:8]}:{app_slug}:{riff_slug}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to send initial message to agent: {str(e)}")

            logger.info(f"✅ Created initial riff and message for app: {app_slug_for_message}")
            return True, {"riff": riff, "message": message}

        except Exception as e:
            logger.error(f"💥 Error creating initial riff and message: {str(e)}")
            return False, f"Error creating initial riff: {str(e)}"

    def create_app(self, user_uuid: str, app_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Create a new app with GitHub repo and Fly.io app."""
        try:
            # Validate and create slug
            if not app_name or not app_name.strip():
                return False, {"error": "App name is required"}

            app_slug = self.create_slug(app_name.strip())

            if not self.is_valid_slug(app_slug):
                return False, {"error": f"Invalid app name. Generated slug '{app_slug}' is not valid."}

            # Check if app already exists for this user
            if self.user_app_exists(user_uuid, app_slug):
                return False, {"error": f"App '{app_slug}' already exists"}

            # Get user's API keys
            user_keys = load_user_keys(user_uuid)
            github_token = user_keys.get("github")
            fly_token = user_keys.get("fly")

            if not github_token:
                return False, {"error": "GitHub API key is required. Please set it in integrations first."}

            if not fly_token:
                return False, {"error": "Fly.io API key is required. Please set it in integrations first."}

            # Create GitHub repository
            logger.info(f"🐙 Creating GitHub repository: {app_slug}")
            github_success, github_result = self.create_github_repo(app_slug, github_token, fly_token)

            if not github_success:
                logger.error(f"❌ GitHub repo creation failed: {github_result}")
                return False, {"error": f"Failed to create GitHub repository: {github_result}"}

            github_url = github_result
            logger.info(f"✅ GitHub repository created: {github_url}")

            # Create Fly.io app
            logger.info(f"🛩️ Creating Fly.io app: {app_slug}")
            fly_success, fly_result = self.create_fly_app(app_slug, fly_token)

            warnings = []
            if not fly_success:
                logger.error(f"❌ Fly.io app creation failed: {fly_result}")
                # Don't fail the entire app creation if Fly.io fails
                logger.warning("⚠️ Continuing with app creation despite Fly.io failure")
                fly_app_name = None
                warnings.append(f"Fly.io app creation failed: {fly_result}")
            else:
                fly_app_name = app_slug
                logger.info(f"✅ Fly.io app created: {fly_app_name}")

            # Create app record
            app = {
                "slug": app_slug,
                "github_url": github_url,
                "fly_app_name": fly_app_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user_uuid,
            }

            # Save app for this user
            if not self.save_user_app(user_uuid, app_slug, app):
                logger.error("❌ Failed to save app to file")
                return False, {"error": "Failed to save app"}

            # Wait 5 seconds before creating the first riff to allow for proper setup
            logger.info(f"⏳ Waiting 5 seconds before creating initial riff for app: {app_slug}")
            time.sleep(5)

            # Create initial riff and message for the new app
            logger.info(f"🆕 Creating initial riff for app: {app_slug}")
            riff_success, riff_result = self.create_initial_riff_and_message(
                user_uuid, app_slug, app_slug, github_url
            )

            if not riff_success:
                logger.warning(f"⚠️ Failed to create initial riff: {riff_result}")
                warnings.append(f"Initial riff creation failed: {riff_result}")
            else:
                logger.info(f"✅ Initial riff created successfully for app: {app_slug}")

            logger.info(f"✅ App created successfully: {app_slug}")
            return True, {
                "message": "App created successfully",
                "app": app,
                "warnings": warnings,
                "initial_riff": riff_result if riff_success else None,
            }

        except Exception as e:
            logger.error(f"💥 Error creating app: {str(e)}")
            return False, {"error": "Failed to create app"}

    def delete_app(self, user_uuid: str, app_slug: str) -> Tuple[bool, Dict[str, Any]]:
        """Delete an app and its associated GitHub repo and Fly.io app."""
        try:
            # Load app for this user
            app = self.load_user_app(user_uuid, app_slug)
            if not app:
                return False, {"error": "App not found"}

            logger.debug(f"🔍 Found app to delete: {app['slug']} for user {user_uuid[:8]}")

            # Get user's API keys
            user_keys = load_user_keys(user_uuid)
            github_token = user_keys.get("github")
            fly_token = user_keys.get("fly")

            deletion_results = {
                "github_success": False,
                "github_error": None,
                "fly_success": False,
                "fly_error": None,
            }

            # Delete GitHub repository if URL exists and token is available
            if app.get("github_url") and github_token:
                logger.info(f"🐙 Deleting GitHub repository: {app['github_url']}")
                github_success, github_message = self.delete_github_repo(app["github_url"], github_token)
                deletion_results["github_success"] = github_success
                if not github_success:
                    deletion_results["github_error"] = github_message
                    logger.warning(f"⚠️ GitHub deletion failed: {github_message}")
                else:
                    logger.info(f"✅ GitHub repository deleted: {github_message}")
            else:
                logger.info("⚠️ Skipping GitHub deletion (no URL or token)")

            # Delete Fly.io app if name exists and token is available
            if app.get("fly_app_name") and fly_token:
                logger.info(f"🛩️ Deleting Fly.io app: {app['fly_app_name']}")
                fly_success, fly_message = self.delete_fly_app(app["fly_app_name"], fly_token)
                deletion_results["fly_success"] = fly_success
                if not fly_success:
                    deletion_results["fly_error"] = fly_message
                    logger.warning(f"⚠️ Fly.io deletion failed: {fly_message}")
                else:
                    logger.info(f"✅ Fly.io app deleted: {fly_message}")
            else:
                logger.info("⚠️ Skipping Fly.io deletion (no app name or token)")

            # Delete app and all its data (including riffs)
            if self.delete_user_app(user_uuid, app_slug):
                logger.info(f"✅ App {app_slug} and all associated data deleted for user {user_uuid[:8]}")
            else:
                logger.error("❌ Failed to delete app data")
                return False, {"error": "Failed to delete app data"}

            # Prepare response
            response_data = {
                "message": f'App "{app.get("name")}" deleted successfully',
                "app_name": app.get("name"),
                "app_slug": app_slug,
                "deletion_results": deletion_results,
            }

            # Add warnings if some deletions failed
            warnings = []
            if deletion_results["github_error"]:
                warnings.append(f"GitHub repository deletion failed: {deletion_results['github_error']}")
            if deletion_results["fly_error"]:
                warnings.append(f"Fly.io app deletion failed: {deletion_results['fly_error']}")

            if warnings:
                response_data["warnings"] = warnings

            logger.info(f"✅ App deletion completed: {app_slug}")
            return True, response_data

        except Exception as e:
            logger.error(f"💥 Error deleting app: {str(e)}")
            return False, {"error": "Failed to delete app"}

    def get_app_deployment_status(self, user_uuid: str, app_slug: str) -> Tuple[bool, Dict[str, Any]]:
        """Get deployment status for an app (checks main branch)."""
        try:
            # Load app for this user
            app = self.load_user_app(user_uuid, app_slug)
            if not app:
                return False, {"error": "App not found"}

            # Check if app has GitHub URL
            github_url = app.get("github_url")
            if not github_url:
                return True, {
                    "status": "error",
                    "message": "No GitHub URL configured for this app",
                    "details": {"error": "no_github_url"},
                }

            # Get user's GitHub token
            user_keys = load_user_keys(user_uuid)
            github_token = user_keys.get("github")

            if not github_token:
                return True, {
                    "status": "error",
                    "message": "No GitHub token configured",
                    "details": {"error": "no_github_token"},
                }

            # Check deployment status for main branch
            branch_name = "main"
            logger.info(f"🔍 Checking deployment status for app '{app_slug}' on branch '{branch_name}'")

            deployment_status = get_deployment_status(github_url, github_token, branch_name)

            logger.info(f"✅ Deployment status retrieved for app {app_slug}: {deployment_status['status']}")
            return True, deployment_status

        except Exception as e:
            logger.error(f"💥 Error getting app deployment status: {str(e)}")
            return False, {"error": "Failed to get deployment status"}


# Create a singleton instance
apps_service = AppsService()
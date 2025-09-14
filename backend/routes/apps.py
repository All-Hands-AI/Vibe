from flask import Blueprint, jsonify, request
import requests
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from keys import load_user_keys
from storage import get_apps_storage, get_riffs_storage
from agent_loop import agent_loop_manager
from utils.deployment_status import get_deployment_status

logger = logging.getLogger(__name__)

# Create Blueprint for apps
apps_bp = Blueprint("apps", __name__)


def load_user_apps(user_uuid):
    """Load apps for a specific user"""
    storage = get_apps_storage(user_uuid)
    return storage.list_apps()


def load_user_app(user_uuid, app_slug):
    """Load specific app for a user"""
    storage = get_apps_storage(user_uuid)
    return storage.load_app(app_slug)


def save_user_app(user_uuid, app_slug, app_data):
    """Save app for a specific user"""
    storage = get_apps_storage(user_uuid)
    return storage.save_app(app_slug, app_data)


def user_app_exists(user_uuid, app_slug):
    """Check if app exists for user"""
    storage = get_apps_storage(user_uuid)
    return storage.app_exists(app_slug)


def delete_user_app(user_uuid, app_slug):
    """Delete app for a specific user"""
    storage = get_apps_storage(user_uuid)
    return storage.delete_app(app_slug)


# Legacy functions for backward compatibility during migration
def load_apps():
    """Load apps from legacy file - DEPRECATED"""
    logger.warning("⚠️ Using deprecated load_apps() function")
    legacy_file = Path("/data/apps.json")
    if legacy_file.exists():
        try:
            with open(legacy_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load legacy apps: {e}")
    return []


def save_apps(apps):
    """Save apps to legacy file - DEPRECATED"""
    logger.warning("⚠️ Using deprecated save_apps() function")
    return False  # Disable legacy saving


def is_valid_slug(slug):
    """Validate that a slug contains only lowercase letters, numbers, and hyphens"""
    if not slug:
        return False
    # Check if slug matches the pattern: lowercase letters, numbers, and hyphens only
    # Must not start or end with hyphen, and no consecutive hyphens
    pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    return bool(re.match(pattern, slug))


def create_slug(name):
    """Convert app name to slug format"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def save_user_riff(user_uuid, app_slug, riff_slug, riff_data):
    """Save riff for a specific user"""
    storage = get_riffs_storage(user_uuid)
    return storage.save_riff(app_slug, riff_slug, riff_data)


def add_user_message(user_uuid, app_slug, riff_slug, message):
    """Add a message to a riff for a specific user"""
    storage = get_riffs_storage(user_uuid)
    return storage.add_message(app_slug, riff_slug, message)


def create_initial_riff_and_message(user_uuid, app_slug, app_slug_for_message, github_url):
    """Create initial riff and message for a new app"""
    try:
        # Import here to avoid circular imports
        from routes.riffs import create_agent_for_user

        # Create riff name and slug using branch name format
        riff_name = f"rename-to-{app_slug}"
        riff_slug = riff_name  # Already in slug format since app_slug is validated

        logger.info(
            f"🔄 Creating initial riff: {riff_name} -> {riff_slug} for app {app_slug}"
        )

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
        if not save_user_riff(user_uuid, app_slug, riff_slug, riff):
            logger.error("❌ Failed to save initial riff")
            return False, "Failed to save initial riff"

        # Create initial message with instructions
        message_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        initial_message_content = f"""Please complete the following tasks to customize this app template for "{app_slug_for_message}":

1. **Read TEMPLATE.md** - First, read the TEMPLATE.md file to understand the specific instructions for this template.

2. **Follow the template instructions** - Execute the instructions in TEMPLATE.md to change the app name everywhere in the repository. The template should contain a helpful command or script to automate this process.

3. **Change the app name** - Update all references from the template name to "{app_slug_for_message}" throughout the codebase. This typically includes:
   - Package.json or similar dependency files
   - Configuration files
   - README files
   - HTML title tags
   - Any hardcoded app names in the code

4. **Verify the changes** - Check that the app name has been successfully changed in key locations:
   - Check the main package.json or equivalent
   - Check the README.md file
   - Check any configuration files
   - Search for any remaining references to the old template name

5. **Delete TEMPLATE.md** - Once you've followed all the instructions, delete the TEMPLATE.md file as it's no longer needed.

6. **Commit and push changes** - Commit all your changes with a descriptive message and push them to the remote repository.

Please work through these steps systematically and let me know if you encounter any issues or need clarification on any step."""

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
        if not add_user_message(user_uuid, app_slug, riff_slug, message):
            logger.error("❌ Failed to save initial message")
            return False, "Failed to save initial message"

        # Create agent for the riff using the working function from riffs.py
        logger.info(f"🤖 Creating agent for initial riff: {riff_slug}")
        agent_success, agent_error = create_agent_for_user(
            user_uuid, app_slug, riff_slug
        )

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
            agent_loop = agent_loop_manager.get_agent_loop(
                user_uuid, app_slug, riff_slug
            )
            if agent_loop:
                logger.info(
                    f"🤖 Sending initial message to agent for {user_uuid[:8]}/{app_slug}/{riff_slug}"
                )
                confirmation = agent_loop.send_message(initial_message_content)
                logger.info(f"✅ Initial message sent to agent: {confirmation}")
            else:
                logger.warning(
                    f"❌ AgentLoop not found after creation for {user_uuid[:8]}:{app_slug}:{riff_slug}"
                )
        except Exception as e:
            logger.warning(f"⚠️ Failed to send initial message to agent: {str(e)}")

        logger.info(f"✅ Created initial riff and message for app: {app_slug_for_message}")
        return True, {"riff": riff, "message": message}

    except Exception as e:
        logger.error(f"💥 Error creating initial riff and message: {str(e)}")
        return False, f"Error creating initial riff: {str(e)}"


def get_user_default_org(fly_token):
    """
    Get the user's default organization slug by checking their existing apps.

    This function tries to determine the user's actual organization slug
    by listing their existing apps and extracting the organization information.
    Falls back to 'personal' if no apps exist or API call fails.

    Args:
        fly_token (str): The user's Fly.io API token

    Returns:
        tuple: (success, org_slug_or_error_message)
    """
    if not fly_token:
        return False, "Fly.io API token is required"

    logger.debug(f"🛩️ Attempting to determine user's organization from existing apps")

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
                    logger.debug(
                        f"🛩️ Detected user organization from existing apps: {org_slug}"
                    )
                    return True, org_slug
                else:
                    logger.debug(f"🛩️ No organization info found in existing apps")
            else:
                logger.debug(f"🛩️ User has no existing apps")
        else:
            logger.debug(f"🛩️ Failed to list apps: {response.status_code}")

    except Exception as e:
        logger.debug(f"🛩️ Error determining organization from apps: {str(e)}")

    # Fall back to 'personal' as the default organization slug
    logger.debug(f"🛩️ Falling back to default organization: personal")
    return True, "personal"


def create_fly_app(app_name, fly_token):
    """
    Create a new Fly.io app.

    Args:
        app_name (str): The app name to create
        fly_token (str): The user's Fly.io API token

    Returns:
        tuple: (success, app_data_or_error_message)
    """
    if not fly_token:
        return False, "Fly.io API token is required"

    logger.info(f"🛩️ Creating Fly.io app: {app_name}")

    # First, get the user's default organization
    success, org_slug = get_user_default_org(fly_token)
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

            # If the user can successfully retrieve the app details with their token,
            # it means they have access to it. This is a strong indicator of ownership.
            # We'll accept this as ownership regardless of organization slug mismatch,
            # since the organization detection might not be perfect.
            logger.info(f"✅ App '{app_name}' already exists and user has access to it")
            logger.debug(f"🛩️ App organization: {app_org_slug}, Expected: {org_slug}")

            # Update our understanding of the user's organization if it differs
            if app_org_slug and app_org_slug != org_slug:
                logger.debug(
                    f"🛩️ Updating user organization from {org_slug} to {app_org_slug}"
                )

            return True, app_data

        elif check_response.status_code == 403:
            # App exists but user doesn't have access - this means it's owned by someone else
            logger.error(
                f"❌ App '{app_name}' exists but user doesn't have access to it"
            )
            return False, f"App '{app_name}' already exists and is not owned by you"

        elif check_response.status_code == 401:
            # Unauthorized - invalid token
            logger.error(f"❌ Invalid Fly.io API token")
            return False, "Invalid Fly.io API token"

        elif check_response.status_code != 404:
            # Some other error occurred
            logger.error(
                f"❌ Error checking app existence: {check_response.status_code} - {check_response.text}"
            )
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
            # App name might be taken or invalid
            error_text = create_response.text
            logger.error(
                f"❌ App creation failed - name taken or invalid: {error_text}"
            )
            if "already taken" in error_text.lower():
                return False, f"App name '{app_name}' is already taken"
            else:
                return False, f"Invalid app name or creation failed: {error_text}"

        elif create_response.status_code == 401:
            logger.error(f"❌ Unauthorized - invalid Fly.io API token")
            return False, "Invalid Fly.io API token"

        elif create_response.status_code == 403:
            logger.error(f"❌ Forbidden - insufficient permissions")
            return False, "Insufficient permissions for Fly.io API"

        else:
            logger.error(
                f"❌ Unexpected response from Fly.io API: {create_response.status_code} - {create_response.text}"
            )
            return False, f"Fly.io API error: {create_response.status_code}"

    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout creating Fly.io app")
        return False, "Timeout creating Fly.io app"

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error connecting to Fly.io API: {str(e)}")
        return False, f"Error connecting to Fly.io API: {str(e)}"

    except Exception as e:
        logger.error(f"💥 Unexpected error creating Fly.io app: {str(e)}")
        return False, f"Unexpected error: {str(e)}"


def get_github_status(repo_url, github_token):
    """Get GitHub repository status including CI/CD tests"""
    logger.info(f"🐙 Checking GitHub status for: {repo_url}")

    try:
        # Extract owner and repo from URL
        # Expected format: https://github.com/owner/repo
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

        logger.info(f"🔍 Request headers: {dict(headers)}")
        logger.info(
            f"🔍 Making request to: https://api.github.com/repos/{owner}/{repo}/commits/main"
        )

        # Get latest commit on main branch
        commits_response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/commits/main",
            headers=headers,
            timeout=10,
        )

        if commits_response.status_code != 200:
            logger.warning(f"❌ Failed to get commits: {commits_response.status_code}")
            logger.warning(f"❌ Response body: {commits_response.text[:500]}")
            logger.debug(f"❌ Response headers count: {len(commits_response.headers)}")
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

        logger.info(
            f"🔍 GitHub status API response code: {status_response.status_code}"
        )

        if status_response.status_code != 200:
            logger.warning(
                f"❌ Failed to get status checks: {status_response.status_code}"
            )
            logger.warning(f"❌ Response body: {status_response.text[:500]}")
            # Return basic info even if status checks fail
            return {
                "tests_passing": None,
                "last_commit": latest_commit_sha,
                "status": "unknown",
            }

        status_data = status_response.json()
        logger.debug(
            f"🔍 GitHub status response received with {len(status_data)} fields"
        )

        state = status_data.get("state", "unknown")
        total_count = status_data.get("total_count", 0)
        logger.info(
            f"🔍 Extracted state from GitHub: '{state}', total_count: {total_count}"
        )

        # If status API returns pending with no checks, try GitHub Actions API as fallback
        if state == "pending" and total_count == 0:
            logger.info(
                f"🔍 Status API shows pending with no checks, trying GitHub Actions API..."
            )
            try:
                actions_response = requests.get(
                    f"https://api.github.com/repos/{owner}/{repo}/actions/runs?head_sha={latest_commit_sha}",
                    headers=headers,
                    timeout=10,
                )

                if actions_response.status_code == 200:
                    actions_data = actions_response.json()
                    workflow_runs = actions_data.get("workflow_runs", [])
                    logger.info(f"🔍 Found {len(workflow_runs)} workflow runs")

                    if workflow_runs:
                        # Check if all workflows are completed and successful
                        all_completed = True
                        all_successful = True

                        for run in workflow_runs:
                            run_status = run.get("status")
                            run_conclusion = run.get("conclusion")
                            logger.info(
                                f"🔍 Workflow '{run.get('name')}': status={run_status}, conclusion={run_conclusion}"
                            )

                            if run_status != "completed":
                                all_completed = False
                            if run_conclusion != "success":
                                all_successful = False

                        if all_completed:
                            if all_successful:
                                state = "success"
                                logger.info(
                                    f"🔍 All workflows completed successfully, overriding state to: {state}"
                                )
                            else:
                                state = "failure"
                                logger.info(
                                    f"🔍 Some workflows failed, overriding state to: {state}"
                                )
                        else:
                            # Keep as pending since some workflows are still running
                            logger.info(
                                f"🔍 Some workflows still running, keeping state as: {state}"
                            )
                else:
                    logger.warning(
                        f"❌ Failed to get GitHub Actions: {actions_response.status_code}"
                    )
            except Exception as e:
                logger.warning(f"❌ Error checking GitHub Actions: {str(e)}")

        # Handle different CI/CD states properly
        if state == "success":
            tests_passing = True
        elif state in ["pending", "running"]:
            tests_passing = None  # Use None to indicate "in progress"
        else:  # failure, error, or unknown
            tests_passing = False

        logger.info(f"✅ GitHub status retrieved: {state}")

        result = {
            "tests_passing": tests_passing,
            "last_commit": latest_commit_sha,
            "status": state,
            "total_count": status_data.get("total_count", 0),
        }

        logger.debug(f"🔍 Returning GitHub status: {result.get('status', 'unknown')}")

        return result

    except Exception as e:
        logger.error(f"💥 GitHub status check error: {str(e)}")
        return None


def get_fly_status(project_slug, fly_token):
    """Get Fly.io deployment status"""
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
            logger.warning(
                f"❌ Failed to get Fly.io app status: {app_response.status_code}"
            )
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


def get_pr_status(repo_url, github_token, branch="main", search_by_base=False):
    """
    Get GitHub Pull Request status for a specific branch.

    Args:
        repo_url: GitHub repository URL
        github_token: GitHub API token
        branch: Branch name to search for
        search_by_base: If True, search for PRs targeting this branch as base.
                       If False, search for PRs from this branch as head.

    Returns:
        dict: PR status information or None if no PR found
    """

    search_type = "base" if search_by_base else "head"
    logger.info(
        f"🔀 Checking PR status for: {repo_url} (branch: {branch}, search_by: {search_type})"
    )
    logger.info(
        f"🔑 GitHub token provided: {bool(github_token)} (length: {len(github_token) if github_token else 0})"
    )

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
    logger.info(f"🔍 Parsed GitHub repo: {owner}/{repo}")
    logger.info(f"🌿 Looking for PRs with branch: '{branch}'")

    # Set up headers for GitHub API
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OpenVibe-Backend/1.0",
    }

    try:
        # Search for PRs using GitHub API
        if search_by_base:
            # Search for PRs targeting this branch as base
            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls?base={branch}&state=open"
            logger.info(f"🔍 Searching for PRs targeting base branch '{branch}'")
        else:
            # Search for PRs from this branch as head
            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls?head={owner}:{branch}&state=open"
            logger.info(f"🔍 Searching for PRs from head branch '{owner}:{branch}'")

        logger.info(f"🔍 API URL: {api_url}")

        pr_response = requests.get(api_url, headers=headers, timeout=10)
        logger.info(f"🔍 Response status: {pr_response.status_code}")

        if pr_response.status_code != 200:
            logger.warning(
                f"❌ GitHub API request failed: {pr_response.status_code} - {pr_response.text[:200]}"
            )
            return None

        prs = pr_response.json()
        logger.info(f"🔍 Found {len(prs)} PRs")

        if not prs:
            logger.info(f"ℹ️ No open PRs found for {search_type} branch '{branch}'")
            return None

        # Log details of found PRs
        for pr in prs:
            # Handle case where mock returns strings instead of dicts
            if isinstance(pr, str):
                logger.warning(f"🔍 PR data is string instead of dict: {pr}")
                continue

            head_info = pr.get("head", {})
            base_info = pr.get("base", {})
            logger.info(
                f"🔍 PR #{pr.get('number', 'unknown')}: {pr.get('title', 'unknown')}"
            )
            logger.info(
                f"🔍   Head: {head_info.get('label', 'unknown')} (ref: {head_info.get('ref', 'unknown')})"
            )
            logger.info(
                f"🔍   Base: {base_info.get('label', 'unknown')} (ref: {base_info.get('ref', 'unknown')})"
            )

        # Get the first (most recent) PR that's a valid dict
        pr = None
        for p in prs:
            if isinstance(p, dict) and "number" in p:
                pr = p
                break

        if not pr:
            logger.warning("❌ No valid PR data found in response")
            return None

        pr_number = pr["number"]

        logger.debug(f"🔍 Selected PR #{pr_number}: {pr['title']}")
        logger.debug(f"🔍 PR head: {pr.get('head', {}).get('label', 'unknown')}")
        logger.debug(f"🔍 PR base: {pr.get('base', {}).get('label', 'unknown')}")

        # Get PR details including mergeable status
        pr_detail_response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
            headers=headers,
            timeout=10,
        )

        if pr_detail_response.status_code != 200:
            logger.warning(
                f"❌ Failed to get PR details: {pr_detail_response.status_code}"
            )
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
                checks.append(
                    {
                        "name": check["name"],
                        "status": check["status"],
                        "conclusion": check.get("conclusion"),
                        "details_url": check.get("details_url"),
                    }
                )

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
        }

        logger.info(f"✅ PR status retrieved for #{pr_number}")
        return pr_status

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while fetching PR status: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error while fetching PR status: {str(e)}")
        return None


def close_github_pr(repo_url, github_token, branch_name):
    """Close GitHub Pull Request for a specific branch"""
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
        logger.debug(f"🔍 GitHub repo: {owner}/{repo}, branch: {branch_name}")

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
            logger.info(f"ℹ️ No open PRs found for branch: {branch_name}")
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
                logger.error(
                    f"❌ Failed to close PR #{pr_number}: {close_response.status_code}"
                )
                return False, f"Failed to close PR #{pr_number}"

        if closed_prs:
            return True, f"Closed PR(s): {', '.join(map(str, closed_prs))}"
        else:
            return True, "No PRs needed to be closed"

    except Exception as e:
        logger.error(f"💥 Error closing GitHub PR: {str(e)}")
        return False, f"Error closing PR: {str(e)}"


def delete_github_branch(repo_url, github_token, branch_name):
    """Delete a GitHub branch"""
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
        logger.debug(f"🔍 GitHub repo: {owner}/{repo}, branch: {branch_name}")

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
            return (
                True,
                f"Branch '{branch_name}' not found (may have been already deleted)",
            )
        elif delete_response.status_code == 422:
            logger.warning(f"⚠️ Cannot delete branch: {branch_name} (may be protected)")
            return False, f"Cannot delete branch '{branch_name}' (may be protected)"
        else:
            logger.error(
                f"❌ Failed to delete branch: {delete_response.status_code} - {delete_response.text}"
            )
            return False, f"GitHub API error: {delete_response.status_code}"

    except Exception as e:
        logger.error(f"💥 Error deleting GitHub branch: {str(e)}")
        return False, f"Error deleting branch: {str(e)}"


def delete_github_repo(repo_url, github_token):
    """Delete a GitHub repository"""
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
            logger.error(
                f"❌ Failed to delete GitHub repo: {delete_response.status_code} - {delete_response.text}"
            )
            return False, f"GitHub API error: {delete_response.status_code}"

    except Exception as e:
        logger.error(f"💥 Error deleting GitHub repo: {str(e)}")
        return False, f"Error deleting repository: {str(e)}"


def delete_fly_app(app_name, fly_token):
    """Delete a Fly.io app"""
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
            logger.error(
                f"❌ Insufficient permissions to delete Fly.io app: {app_name}"
            )
            return False, "Insufficient permissions to delete app"
        else:
            logger.error(
                f"❌ Failed to delete Fly.io app: {delete_response.status_code} - {delete_response.text}"
            )
            return False, f"Fly.io API error: {delete_response.status_code}"

    except Exception as e:
        logger.error(f"💥 Error deleting Fly.io app: {str(e)}")
        return False, f"Error deleting app: {str(e)}"


def create_github_repo(repo_name, github_token, fly_token):
    """Create a GitHub repository from template and set FLY_API_TOKEN secret"""
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
        logger.debug(f"🐙 Making request to GitHub user API...")
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
        logger.info(f"🔍 GitHub owner: {owner}")
        logger.debug(
            f"🔍 GitHub user authenticated: {user_data.get('login', 'unknown')}"
        )

        # Check if repo already exists
        check_response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo_name}",
            headers=headers,
            timeout=10,
        )
        if check_response.status_code == 200:
            # Repository already exists, but that's okay - we'll use the existing one
            repo_data = check_response.json()
            logger.info(
                f"✅ Repository {owner}/{repo_name} already exists, using existing repository"
            )

            # Still try to set the FLY_API_TOKEN secret if provided
            if fly_token:
                logger.info(
                    f"🔐 Setting FLY_API_TOKEN secret for existing repo {repo_name}"
                )

                # Get the repository's public key for encrypting secrets
                key_response = requests.get(
                    f"https://api.github.com/repos/{owner}/{repo_name}/actions/secrets/public-key",
                    headers=headers,
                    timeout=10,
                )

                if key_response.status_code == 200:
                    from base64 import b64encode
                    from nacl import encoding, public

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
                        logger.info(
                            "✅ FLY_API_TOKEN secret set successfully for existing repo"
                        )
                    else:
                        logger.warning(
                            f"⚠️ Failed to set FLY_API_TOKEN secret for existing repo: {secret_response.text}"
                        )
                else:
                    logger.warning(
                        f"⚠️ Failed to get public key for secrets on existing repo: {key_response.text}"
                    )

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
            logger.info(f"🔐 Setting FLY_API_TOKEN secret for {repo_name}")

            # Get the repository's public key for encrypting secrets
            key_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/actions/secrets/public-key",
                headers=headers,
                timeout=10,
            )

            if key_response.status_code == 200:
                from base64 import b64encode
                from nacl import encoding, public

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
                    logger.warning(
                        f"⚠️ Failed to set FLY_API_TOKEN secret: {secret_response.text}"
                    )
            else:
                logger.warning(
                    f"⚠️ Failed to get public key for secrets: {key_response.text}"
                )

        return True, repo_data["html_url"]

    except Exception as e:
        logger.error(f"💥 GitHub repo creation error: {str(e)}")
        return False, f"Error creating repository: {str(e)}"


@apps_bp.route("/api/apps", methods=["GET"])
def get_apps():
    """Get all apps for a user, ordered alphabetically"""
    logger.info("📋 GET /api/apps - Fetching user apps")

    try:
        # Get UUID from headers
        user_uuid = request.headers.get("X-User-UUID")
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            return jsonify({"error": "X-User-UUID header is required"}), 400

        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({"error": "UUID cannot be empty"}), 400

        apps = load_user_apps(user_uuid)
        # Sort apps alphabetically by name
        apps.sort(key=lambda x: x.get("name", "").lower())

        logger.info(f"📊 Returning {len(apps)} apps for user {user_uuid[:8]}")
        return jsonify({"apps": apps, "count": len(apps)})
    except Exception as e:
        logger.error(f"💥 Error fetching apps: {str(e)}")
        return jsonify({"error": "Failed to fetch apps"}), 500


@apps_bp.route("/api/apps/<slug>", methods=["GET"])
def get_app(slug):
    """Get a specific app by slug with status information"""
    logger.info(f"📋 GET /api/apps/{slug} - Fetching app details")

    try:
        # Get UUID from headers
        user_uuid = request.headers.get("X-User-UUID")
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            return jsonify({"error": "X-User-UUID header is required"}), 400

        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({"error": "UUID cannot be empty"}), 400

        # Load app for this user
        app = load_user_app(user_uuid, slug)
        if not app:
            logger.warning(f"❌ App not found: {slug} for user {user_uuid[:8]}")
            return jsonify({"error": "App not found"}), 404

        logger.info(f"📊 Found app: {app['slug']} for user {user_uuid[:8]}")

        # Get user's API keys for status information
        github_status = None
        fly_status = None
        pr_status = None

        try:
            user_keys = load_user_keys(user_uuid)
            github_token = user_keys.get("github")
            fly_token = user_keys.get("fly")

            # Get GitHub status if token is available
            if github_token and app.get("github_url"):
                logger.info(f"🔍 GitHub token length: {len(github_token)} characters")
                logger.info(f"🔍 GitHub token starts with: {github_token[:10]}...")
                github_status = get_github_status(app["github_url"], github_token)

                # Get PR status for the current branch
                branch = app.get("branch", "main")
                logger.info(
                    f"🔍 APPS ENDPOINT: Getting PR status for app branch: {branch}"
                )
                pr_status = get_pr_status(app["github_url"], github_token, branch)

            # Get Fly.io status if token is available
            if fly_token and app.get("slug"):
                fly_status = get_fly_status(app["slug"], fly_token)

        except Exception as e:
            logger.warning(f"⚠️ Error getting status information: {str(e)}")

        # Add status information to app
        app_with_status = app.copy()
        if github_status:
            app_with_status["github_status"] = github_status
            logger.debug(
                f"🔍 Added GitHub status: {github_status.get('status', 'unknown')}"
            )
        else:
            logger.info(f"🔍 No github_status to add (github_status is None or empty)")
        if fly_status:
            app_with_status["fly_status"] = fly_status
        if pr_status:
            app_with_status["pr_status"] = pr_status
            logger.info(f"🔍 Adding pr_status to response")

        logger.debug(f"🔍 Returning app {slug} with status information")
        return jsonify(app_with_status)
    except Exception as e:
        logger.error(f"💥 Error fetching app: {str(e)}")
        return jsonify({"error": "Failed to fetch app"}), 500


@apps_bp.route("/api/apps", methods=["POST"])
def create_app():
    """Create a new app with GitHub repo and Fly.io app"""
    logger.info("🆕 POST /api/apps - Creating new app")

    try:
        # Get UUID from headers
        user_uuid = request.headers.get("X-User-UUID")
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            return jsonify({"error": "X-User-UUID header is required"}), 400

        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({"error": "UUID cannot be empty"}), 400

        # Get request data
        data = request.get_json()
        if not data or "slug" not in data:
            logger.warning("❌ App slug is required")
            return jsonify({"error": "App slug is required"}), 400

        app_slug = data["slug"].strip()
        if not app_slug:
            logger.warning("❌ App slug cannot be empty")
            return jsonify({"error": "App slug cannot be empty"}), 400



        # Validate slug format
        if not is_valid_slug(app_slug):
            logger.warning(f"❌ Invalid app slug format: {app_slug}")
            return (
                jsonify(
                    {
                        "error": "App slug must contain only lowercase letters, numbers, and hyphens (no consecutive hyphens, no leading/trailing hyphens)"
                    }
                ),
                400,
            )

        logger.info(
            f"🔄 Creating app: {app_slug} for user {user_uuid[:8]}"
        )

        # Check if app with same slug already exists for this user
        if user_app_exists(user_uuid, app_slug):
            logger.warning(
                f"❌ App with slug '{app_slug}' already exists for user {user_uuid[:8]}"
            )
            return jsonify({"error": f'App with slug "{app_slug}" already exists'}), 409

        # Get user's API keys
        user_keys = load_user_keys(user_uuid)
        github_token = user_keys.get("github")
        fly_token = user_keys.get("fly")

        if not github_token:
            logger.warning("❌ GitHub API key is required")
            return (
                jsonify(
                    {
                        "error": "GitHub API key is required. Please set it in integrations first."
                    }
                ),
                400,
            )

        if not fly_token:
            logger.warning("❌ Fly.io API key is required")
            return (
                jsonify(
                    {
                        "error": "Fly.io API key is required. Please set it in integrations first."
                    }
                ),
                400,
            )

        # Create GitHub repository
        logger.info(f"🐙 Creating GitHub repository: {app_slug}")
        github_success, github_result = create_github_repo(
            app_slug, github_token, fly_token
        )

        if not github_success:
            logger.error(f"❌ GitHub repo creation failed: {github_result}")
            return (
                jsonify(
                    {"error": f"Failed to create GitHub repository: {github_result}"}
                ),
                500,
            )

        github_url = github_result
        logger.info(f"✅ GitHub repository created: {github_url}")

        # Create Fly.io app
        logger.info(f"🛩️ Creating Fly.io app: {app_slug}")
        fly_success, fly_result = create_fly_app(app_slug, fly_token)

        if not fly_success:
            logger.error(f"❌ Fly.io app creation failed: {fly_result}")
            # Don't fail the entire app creation if Fly.io fails
            # The user can manually create the app later
            logger.warning(f"⚠️ Continuing with app creation despite Fly.io failure")
            fly_app_name = None
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
        if not save_user_app(user_uuid, app_slug, app):
            logger.error("❌ Failed to save app to file")
            return jsonify({"error": "Failed to save app"}), 500

        # Create initial riff and message for the new app
        logger.info(f"🆕 Creating initial riff for app: {app_slug}")
        riff_success, riff_result = create_initial_riff_and_message(
            user_uuid, app_slug, app_slug, github_url
        )

        warnings = []
        if not fly_success:
            warnings.append(f"Fly.io app creation failed: {fly_result}")

        if not riff_success:
            logger.warning(f"⚠️ Failed to create initial riff: {riff_result}")
            warnings.append(f"Initial riff creation failed: {riff_result}")
        else:
            logger.info(f"✅ Initial riff created successfully for app: {app_slug}")

        logger.info(f"✅ App created successfully: {app_slug}")
        return (
            jsonify(
                {
                    "message": "App created successfully",
                    "app": app,
                    "warnings": warnings,
                    "initial_riff": riff_result if riff_success else None,
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"💥 Error creating app: {str(e)}")
        return jsonify({"error": "Failed to create app"}), 500


@apps_bp.route("/api/apps/<slug>", methods=["DELETE"])
def delete_app(slug):
    """Delete a app and its associated GitHub repo and Fly.io app"""
    logger.info(f"🗑️ DELETE /api/apps/{slug} - Deleting app")

    try:
        # Get UUID from headers
        user_uuid = request.headers.get("X-User-UUID")
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            return jsonify({"error": "X-User-UUID header is required"}), 400

        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({"error": "UUID cannot be empty"}), 400

        # Load app for this user
        app = load_user_app(user_uuid, slug)
        if not app:
            logger.warning(f"❌ App not found: {slug} for user {user_uuid[:8]}")
            return jsonify({"error": "App not found"}), 404

        logger.info(f"🔍 Found app to delete: {app['slug']} for user {user_uuid[:8]}")

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
            github_success, github_message = delete_github_repo(
                app["github_url"], github_token
            )
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
            fly_success, fly_message = delete_fly_app(app["fly_app_name"], fly_token)
            deletion_results["fly_success"] = fly_success
            if not fly_success:
                deletion_results["fly_error"] = fly_message
                logger.warning(f"⚠️ Fly.io deletion failed: {fly_message}")
            else:
                logger.info(f"✅ Fly.io app deleted: {fly_message}")
        else:
            logger.info("⚠️ Skipping Fly.io deletion (no app name or token)")

        # Delete app and all its data (including riffs)
        if delete_user_app(user_uuid, slug):
            logger.info(
                f"✅ App {slug} and all associated data deleted for user {user_uuid[:8]}"
            )
        else:
            logger.error(f"❌ Failed to delete app data")
            return jsonify({"error": "Failed to delete app data"}), 500

        # Prepare response
        response_data = {
            "message": f'App "{app.get("name")}" deleted successfully',
            "app_name": app.get("name"),
            "app_slug": slug,
            "deletion_results": deletion_results,
        }

        # Add warnings if some deletions failed
        warnings = []
        if deletion_results["github_error"]:
            warnings.append(
                f"GitHub repository deletion failed: {deletion_results['github_error']}"
            )
        if deletion_results["fly_error"]:
            warnings.append(
                f"Fly.io app deletion failed: {deletion_results['fly_error']}"
            )

        if warnings:
            response_data["warnings"] = warnings

        logger.info(f"✅ App deletion completed: {slug}")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"💥 Error deleting app: {str(e)}")
        return jsonify({"error": "Failed to delete app"}), 500


@apps_bp.route("/api/apps/<slug>/deployment", methods=["GET"])
def get_app_deployment_status(slug):
    """Get deployment status for an app (checks main branch)"""
    logger.info(f"🚀 GET /api/apps/{slug}/deployment - Getting app deployment status")

    try:
        # Get UUID from headers
        user_uuid = request.headers.get("X-User-UUID")
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            return jsonify({"error": "X-User-UUID header is required"}), 400

        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({"error": "UUID cannot be empty"}), 400

        # Load app for this user
        app = load_user_app(user_uuid, slug)
        if not app:
            logger.warning(f"❌ App not found: {slug} for user {user_uuid[:8]}")
            return jsonify({"error": "App not found"}), 404

        # Check if app has GitHub URL
        github_url = app.get("github_url")
        if not github_url:
            logger.info(f"ℹ️ No GitHub URL configured for app {slug}")
            return jsonify(
                {
                    "status": "error",
                    "message": "No GitHub URL configured for this app",
                    "details": {"error": "no_github_url"},
                }
            )

        # Get user's GitHub token
        user_keys = load_user_keys(user_uuid)
        github_token = user_keys.get("github")

        if not github_token:
            logger.info(f"ℹ️ No GitHub token found for user {user_uuid[:8]}")
            return jsonify(
                {
                    "status": "error",
                    "message": "No GitHub token configured",
                    "details": {"error": "no_github_token"},
                }
            )

        # Check deployment status for main branch
        branch_name = "main"
        logger.info(
            f"🔍 Checking deployment status for app '{slug}' on branch '{branch_name}'"
        )

        deployment_status = get_deployment_status(github_url, github_token, branch_name)

        logger.info(
            f"✅ Deployment status retrieved for app {slug}: {deployment_status['status']}"
        )
        return jsonify(deployment_status)

    except Exception as e:
        logger.error(f"💥 Error getting app deployment status: {str(e)}")
        return jsonify({"error": "Failed to get deployment status"}), 500

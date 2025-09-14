"""
Shared utility functions for checking deployment status via GitHub Actions.
"""

import requests
import re
import logging

logger = logging.getLogger(__name__)


def get_deployment_status(repo_url, github_token, branch_name):
    """
    Get deployment status by checking GitHub Actions for "Deploy to Fly.io" job.

    Args:
        repo_url: GitHub repository URL
        github_token: GitHub API token
        branch_name: Branch name to check (e.g., "main" for app, riff slug for riff)

    Returns:
        dict: Deployment status with keys:
            - status: "success", "pending", or "error"
            - message: Human-readable status message
            - details: Additional details (commit SHA, job URL, etc.)
    """
    logger.info(
        f"🚀 Checking deployment status for branch '{branch_name}' in {repo_url}"
    )

    if not github_token:
        return {
            "status": "error",
            "message": "No GitHub token available",
            "details": {"error": "github_token_missing"},
        }

    # Parse GitHub URL to extract owner and repo
    github_pattern = r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"
    match = re.match(github_pattern, repo_url)
    if not match:
        return {
            "status": "error",
            "message": f"Invalid GitHub URL format: {repo_url}",
            "details": {"error": "invalid_github_url"},
        }

    owner, repo = match.groups()
    logger.info(f"🔍 Parsed GitHub repo: {owner}/{repo}, branch: {branch_name}")

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OpenVibe-Backend/1.0",
    }

    try:
        # Step 1: Get the latest commit on the specified branch
        branch_response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/branches/{branch_name}",
            headers=headers,
            timeout=10,
        )

        if branch_response.status_code == 404:
            return {
                "status": "error",
                "message": f"Branch '{branch_name}' not found",
                "details": {"error": "branch_not_found", "branch": branch_name},
            }
        elif branch_response.status_code != 200:
            logger.warning(
                f"❌ Failed to get branch info: {branch_response.status_code}"
            )
            return {
                "status": "error",
                "message": f"Failed to get branch info: {branch_response.status_code}",
                "details": {
                    "error": "github_api_error",
                    "status_code": branch_response.status_code,
                },
            }

        branch_data = branch_response.json()
        commit_sha = branch_data["commit"]["sha"]
        logger.info(f"📝 Latest commit on '{branch_name}': {commit_sha[:8]}")

        # Step 2: Get workflow runs for this commit
        runs_response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/actions/runs",
            headers=headers,
            params={
                "head_sha": commit_sha,
                "per_page": 50,  # Get more runs to ensure we find the right one
            },
            timeout=10,
        )

        if runs_response.status_code != 200:
            logger.warning(
                f"❌ Failed to get workflow runs: {runs_response.status_code}"
            )
            return {
                "status": "error",
                "message": f"Failed to get workflow runs: {runs_response.status_code}",
                "details": {
                    "error": "github_api_error",
                    "status_code": runs_response.status_code,
                },
            }

        runs_data = runs_response.json()
        workflow_runs = runs_data.get("workflow_runs", [])
        logger.info(
            f"🔍 Found {len(workflow_runs)} workflow runs for commit {commit_sha[:8]}"
        )

        # Step 3: Look for "Deploy to Fly.io" job in the workflow runs
        deploy_run = None
        for run in workflow_runs:
            run_name = run.get("name", "")
            if "Deploy to Fly.io" in run_name:
                deploy_run = run
                logger.info(f"✅ Found 'Deploy to Fly.io' workflow: {run_name}")
                break

        if not deploy_run:
            logger.info(
                f"❌ No 'Deploy to Fly.io' workflow found for commit {commit_sha[:8]}"
            )
            return {
                "status": "error",
                "message": f"No 'Deploy to Fly.io' workflow found for commit {commit_sha[:8]}",
                "details": {
                    "error": "deploy_workflow_not_found",
                    "commit_sha": commit_sha,
                    "available_workflows": [
                        run.get("name", "unnamed") for run in workflow_runs[:5]
                    ],
                },
            }

        # Step 4: Check the status of the deploy workflow
        run_status = deploy_run.get("status")  # queued, in_progress, completed
        run_conclusion = deploy_run.get(
            "conclusion"
        )  # success, failure, cancelled, etc.
        run_url = deploy_run.get("html_url")

        logger.info(
            f"🔍 Deploy workflow status: {run_status}, conclusion: {run_conclusion}"
        )

        # Determine final status based on GitHub Actions status
        if run_status == "completed":
            if run_conclusion == "success":
                return {
                    "status": "success",
                    "message": "Deployment completed successfully",
                    "details": {
                        "commit_sha": commit_sha,
                        "workflow_url": run_url,
                        "workflow_name": deploy_run.get("name"),
                        "completed_at": deploy_run.get("updated_at"),
                    },
                }
            else:
                return {
                    "status": "error",
                    "message": f"Deployment failed: {run_conclusion}",
                    "details": {
                        "commit_sha": commit_sha,
                        "workflow_url": run_url,
                        "workflow_name": deploy_run.get("name"),
                        "conclusion": run_conclusion,
                        "completed_at": deploy_run.get("updated_at"),
                    },
                }
        else:
            # Status is queued or in_progress
            return {
                "status": "pending",
                "message": f"Deployment is {run_status.replace('_', ' ')}",
                "details": {
                    "commit_sha": commit_sha,
                    "workflow_url": run_url,
                    "workflow_name": deploy_run.get("name"),
                    "status": run_status,
                    "started_at": deploy_run.get("created_at"),
                },
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while checking deployment status: {str(e)}")
        return {
            "status": "error",
            "message": f"Network error: {str(e)}",
            "details": {"error": "network_error", "exception": str(e)},
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error while checking deployment status: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "details": {"error": "unexpected_error", "exception": str(e)},
        }

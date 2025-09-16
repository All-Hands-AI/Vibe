"""
Utility functions for fetching comprehensive riff status information.
Includes PR status, CI status, deployment status, and agent status.
"""

import requests
import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from utils.deployment_status import get_deployment_status
from utils.repository import extract_repo_info
from agent_loop import agent_loop_manager
from openhands.sdk.conversation.state import AgentExecutionStatus

logger = logging.getLogger(__name__)


def get_github_pr_status(repo_url: str, github_token: str, branch_name: str) -> Dict[str, Any]:
    """
    Get PR information for a branch from GitHub API.
    
    Args:
        repo_url: GitHub repository URL
        github_token: GitHub API token
        branch_name: Branch name to check for PRs
        
    Returns:
        dict: PR status with keys:
            - has_pr: bool
            - pr_number: int or None
            - pr_title: str or None
            - pr_url: str or None
            - pr_state: "open", "closed", "merged", or None
    """
    if not github_token:
        return {
            "has_pr": False,
            "pr_number": None,
            "pr_title": None,
            "pr_url": None,
            "pr_state": None,
            "error": "No GitHub token available"
        }
    
    repo_info = extract_repo_info(repo_url)
    if not repo_info:
        return {
            "has_pr": False,
            "pr_number": None,
            "pr_title": None,
            "pr_url": None,
            "pr_state": None,
            "error": "Invalid GitHub URL"
        }
    
    owner, repo = repo_info
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OpenVibe-Backend/1.0",
    }
    
    try:
        # Search for PRs from this branch
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls",
            headers=headers,
            params={
                "head": f"{owner}:{branch_name}",
                "state": "all",  # Include open, closed, and merged PRs
                "per_page": 1
            },
            timeout=10,
        )
        
        if response.status_code != 200:
            logger.warning(f"❌ Failed to get PR info: {response.status_code}")
            return {
                "has_pr": False,
                "pr_number": None,
                "pr_title": None,
                "pr_url": None,
                "pr_state": None,
                "error": f"GitHub API error: {response.status_code}"
            }
        
        prs = response.json()
        if not prs:
            return {
                "has_pr": False,
                "pr_number": None,
                "pr_title": None,
                "pr_url": None,
                "pr_state": None
            }
        
        # Get the most recent PR for this branch
        pr = prs[0]
        return {
            "has_pr": True,
            "pr_number": pr["number"],
            "pr_title": pr["title"],
            "pr_url": pr["html_url"],
            "pr_state": pr["state"]
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while checking PR status: {str(e)}")
        return {
            "has_pr": False,
            "pr_number": None,
            "pr_title": None,
            "pr_url": None,
            "pr_state": None,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error while checking PR status: {str(e)}")
        return {
            "has_pr": False,
            "pr_number": None,
            "pr_title": None,
            "pr_url": None,
            "pr_state": None,
            "error": f"Unexpected error: {str(e)}"
        }


def get_github_commit_info(repo_url: str, github_token: str, branch_name: str) -> Dict[str, Any]:
    """
    Get commit information for a branch from GitHub API.
    
    Args:
        repo_url: GitHub repository URL
        github_token: GitHub API token
        branch_name: Branch name to get commit info for
        
    Returns:
        dict: Commit info with keys:
            - commit_sha: str or None
            - commit_message: str or None
            - commit_author: str or None
            - commit_date: str or None
            - commit_url: str or None
    """
    if not github_token:
        return {
            "commit_sha": None,
            "commit_message": None,
            "commit_author": None,
            "commit_date": None,
            "commit_url": None,
            "error": "No GitHub token available"
        }
    
    repo_info = extract_repo_info(repo_url)
    if not repo_info:
        return {
            "commit_sha": None,
            "commit_message": None,
            "commit_author": None,
            "commit_date": None,
            "commit_url": None,
            "error": "Invalid GitHub URL"
        }
    
    owner, repo = repo_info
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OpenVibe-Backend/1.0",
    }
    
    try:
        # Get the latest commit on the branch
        branch_response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/branches/{branch_name}",
            headers=headers,
            timeout=10,
        )
        
        if branch_response.status_code == 404:
            return {
                "commit_sha": None,
                "commit_message": None,
                "commit_author": None,
                "commit_date": None,
                "commit_url": None,
                "error": f"Branch '{branch_name}' not found"
            }
        elif branch_response.status_code != 200:
            return {
                "commit_sha": None,
                "commit_message": None,
                "commit_author": None,
                "commit_date": None,
                "commit_url": None,
                "error": f"GitHub API error: {branch_response.status_code}"
            }
        
        branch_data = branch_response.json()
        commit_data = branch_data["commit"]
        
        return {
            "commit_sha": commit_data["sha"],
            "commit_message": commit_data["commit"]["message"],
            "commit_author": commit_data["commit"]["author"]["name"],
            "commit_date": commit_data["commit"]["author"]["date"],
            "commit_url": commit_data["html_url"]
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while getting commit info: {str(e)}")
        return {
            "commit_sha": None,
            "commit_message": None,
            "commit_author": None,
            "commit_date": None,
            "commit_url": None,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error while getting commit info: {str(e)}")
        return {
            "commit_sha": None,
            "commit_message": None,
            "commit_author": None,
            "commit_date": None,
            "commit_url": None,
            "error": f"Unexpected error: {str(e)}"
        }


def get_github_ci_status(repo_url: str, github_token: str, branch_name: str) -> Dict[str, Any]:
    """
    Get CI status for a branch from GitHub Actions.
    
    Args:
        repo_url: GitHub repository URL
        github_token: GitHub API token
        branch_name: Branch name to check CI for
        
    Returns:
        dict: CI status with keys:
            - status: "success", "pending", "failure", "error", or "unknown"
            - message: Human-readable status message
            - details: Additional details (commit SHA, workflow URL, etc.)
    """
    if not github_token:
        return {
            "status": "error",
            "message": "No GitHub token available",
            "details": {"error": "github_token_missing"}
        }
    
    repo_info = extract_repo_info(repo_url)
    if not repo_info:
        return {
            "status": "error",
            "message": "Invalid GitHub URL",
            "details": {"error": "invalid_github_url"}
        }
    
    owner, repo = repo_info
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OpenVibe-Backend/1.0",
    }
    
    try:
        # Get the latest commit on the branch
        branch_response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/branches/{branch_name}",
            headers=headers,
            timeout=10,
        )
        
        if branch_response.status_code == 404:
            return {
                "status": "error",
                "message": f"Branch '{branch_name}' not found",
                "details": {"error": "branch_not_found", "branch": branch_name}
            }
        elif branch_response.status_code != 200:
            return {
                "status": "error",
                "message": f"Failed to get branch info: {branch_response.status_code}",
                "details": {"error": "github_api_error", "status_code": branch_response.status_code}
            }
        
        branch_data = branch_response.json()
        commit_sha = branch_data["commit"]["sha"]
        
        # Get workflow runs for this commit
        runs_response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/actions/runs",
            headers=headers,
            params={
                "head_sha": commit_sha,
                "per_page": 10
            },
            timeout=10,
        )
        
        if runs_response.status_code != 200:
            return {
                "status": "error",
                "message": f"Failed to get workflow runs: {runs_response.status_code}",
                "details": {"error": "github_api_error", "status_code": runs_response.status_code}
            }
        
        runs_data = runs_response.json()
        workflow_runs = runs_data.get("workflow_runs", [])
        
        if not workflow_runs:
            return {
                "status": "unknown",
                "message": "No CI workflows found",
                "details": {"commit_sha": commit_sha}
            }
        
        # Analyze all workflow runs to determine overall CI status
        success_count = 0
        failure_count = 0
        pending_count = 0
        
        latest_run = None
        for run in workflow_runs:
            if not latest_run or run["created_at"] > latest_run["created_at"]:
                latest_run = run
                
            status = run.get("status")
            conclusion = run.get("conclusion")
            
            if status == "completed":
                if conclusion == "success":
                    success_count += 1
                elif conclusion in ["failure", "cancelled", "timed_out"]:
                    failure_count += 1
            else:
                pending_count += 1
        
        # Determine overall status
        if pending_count > 0:
            ci_status = "pending"
            message = f"CI is running ({pending_count} pending)"
        elif failure_count > 0:
            ci_status = "failure"
            message = f"CI failed ({failure_count} failed, {success_count} passed)"
        elif success_count > 0:
            ci_status = "success"
            message = f"CI passed ({success_count} workflows)"
        else:
            ci_status = "unknown"
            message = "No CI results available"
        
        return {
            "status": ci_status,
            "message": message,
            "details": {
                "commit_sha": commit_sha,
                "total_runs": len(workflow_runs),
                "success_count": success_count,
                "failure_count": failure_count,
                "pending_count": pending_count,
                "latest_run_url": latest_run.get("html_url") if latest_run else None,
                "latest_run_name": latest_run.get("name") if latest_run else None
            }
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while checking CI status: {str(e)}")
        return {
            "status": "error",
            "message": f"Network error: {str(e)}",
            "details": {"error": "network_error", "exception": str(e)}
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error while checking CI status: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "details": {"error": "unexpected_error", "exception": str(e)}
        }


def get_agent_status(app_slug: str, riff_slug: str, user_uuid: str) -> Dict[str, Any]:
    """
    Get agent status for a riff.
    
    Args:
        app_slug: Application slug
        riff_slug: Riff slug
        user_uuid: User UUID
        
    Returns:
        dict: Agent status with keys:
            - status: "idle", "running", "error", "unknown"
            - message: Human-readable status message
            - details: Additional details
    """
    try:
        # Check if agent loop exists for this riff
        agent_key = f"{user_uuid}:{app_slug}:{riff_slug}"
        
        if agent_key in agent_loop_manager.loops:
            agent_loop = agent_loop_manager.loops[agent_key]
            
            # Get the current execution status
            if hasattr(agent_loop, 'conversation') and agent_loop.conversation:
                execution_status = agent_loop.conversation.get_execution_status()
                
                if execution_status == AgentExecutionStatus.RUNNING:
                    return {
                        "status": "running",
                        "message": "Agent is actively working",
                        "details": {"execution_status": execution_status.value}
                    }
                elif execution_status == AgentExecutionStatus.STOPPED:
                    return {
                        "status": "idle",
                        "message": "Agent is idle",
                        "details": {"execution_status": execution_status.value}
                    }
                elif execution_status == AgentExecutionStatus.ERROR:
                    return {
                        "status": "error",
                        "message": "Agent encountered an error",
                        "details": {"execution_status": execution_status.value}
                    }
                else:
                    return {
                        "status": "unknown",
                        "message": f"Agent status: {execution_status.value}",
                        "details": {"execution_status": execution_status.value}
                    }
            else:
                return {
                    "status": "idle",
                    "message": "Agent loop exists but no active conversation",
                    "details": {"has_conversation": False}
                }
        else:
            return {
                "status": "idle",
                "message": "No active agent session",
                "details": {"agent_loop_exists": False}
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting agent status: {str(e)}")
        return {
            "status": "error",
            "message": f"Error checking agent status: {str(e)}",
            "details": {"error": "agent_status_error", "exception": str(e)}
        }


def get_comprehensive_riff_status(
    riff: Dict[str, Any], 
    app: Dict[str, Any], 
    user_uuid: str, 
    github_token: str
) -> Dict[str, Any]:
    """
    Get comprehensive status information for a single riff.
    
    Args:
        riff: Riff data dictionary
        app: App data dictionary
        user_uuid: User UUID
        github_token: GitHub API token
        
    Returns:
        dict: Comprehensive riff status
    """
    riff_slug = riff["slug"]
    app_slug = app["slug"]
    repo_url = app.get("github_url", "")
    
    logger.info(f"🔍 Getting comprehensive status for riff: {app_slug}/{riff_slug}")
    
    # Get commit information
    commit_info = get_github_commit_info(repo_url, github_token, riff_slug)
    
    # Get PR status
    pr_status = get_github_pr_status(repo_url, github_token, riff_slug)
    
    # Get CI status
    ci_status = get_github_ci_status(repo_url, github_token, riff_slug)
    
    # Get deployment status
    deploy_status = get_deployment_status(repo_url, github_token, riff_slug)
    
    # Get agent status
    agent_status = get_agent_status(app_slug, riff_slug, user_uuid)
    
    return {
        "riff": {
            "slug": riff_slug,
            "name": riff.get("name", riff_slug),
            "created_at": riff.get("created_at"),
            "last_message_at": riff.get("last_message_at"),
            "message_count": riff.get("message_count", 0)
        },
        "commit": commit_info,
        "pr": pr_status,
        "ci": ci_status,
        "deploy": deploy_status,
        "agent": agent_status,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


def get_all_riffs_status(
    riffs: List[Dict[str, Any]], 
    app: Dict[str, Any], 
    user_uuid: str, 
    github_token: str
) -> List[Dict[str, Any]]:
    """
    Get comprehensive status information for all riffs in an app.
    
    Args:
        riffs: List of riff data dictionaries
        app: App data dictionary
        user_uuid: User UUID
        github_token: GitHub API token
        
    Returns:
        list: List of comprehensive riff statuses
    """
    logger.info(f"🔍 Getting status for {len(riffs)} riffs in app: {app['slug']}")
    
    statuses = []
    for riff in riffs:
        try:
            status = get_comprehensive_riff_status(riff, app, user_uuid, github_token)
            statuses.append(status)
        except Exception as e:
            logger.error(f"❌ Error getting status for riff {riff['slug']}: {str(e)}")
            # Add a minimal status entry with error information
            statuses.append({
                "riff": {
                    "slug": riff["slug"],
                    "name": riff.get("name", riff["slug"]),
                    "created_at": riff.get("created_at"),
                    "last_message_at": riff.get("last_message_at"),
                    "message_count": riff.get("message_count", 0)
                },
                "commit": {"commit_sha": None, "error": "Failed to fetch commit info"},
                "pr": {"has_pr": False, "error": "Failed to fetch PR status"},
                "ci": {"status": "error", "message": "Failed to fetch CI status"},
                "deploy": {"status": "error", "message": "Failed to fetch deploy status"},
                "agent": {"status": "error", "message": "Failed to fetch agent status"},
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            })
    
    return statuses
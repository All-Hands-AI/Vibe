"""
Mock responses for external API calls when MOCK_MODE is enabled.
Provides realistic mock responses for GitHub, Fly.io, and Anthropic APIs.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Check if we're running in mock mode
MOCK_MODE = os.environ.get("MOCK_MODE", "false").lower() == "true"


class MockResponse:
    """Mock HTTP response object"""

    def __init__(
        self,
        status_code: int,
        json_data: Optional[Dict[str, Any]] = None,
        text: str = "",
        headers: Optional[Dict[str, str]] = None,
    ):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._json_data


def mock_github_user_response():
    """Mock GitHub user API response"""
    return MockResponse(
        200,
        {
            "login": "mockuser",
            "id": 12345,
            "name": "Mock User",
            "email": "mock@example.com",
            "public_repos": 10,
            "followers": 5,
            "following": 3,
        },
    )


def mock_github_commits_response(owner: str, repo: str):
    """Mock GitHub commits API response"""
    return MockResponse(
        200,
        {
            "sha": "abc123def456789012345678901234567890abcd",
            "commit": {
                "message": "Mock commit message",
                "author": {
                    "name": "Mock User",
                    "email": "mock@example.com",
                    "date": "2024-01-01T12:00:00Z",
                },
            },
            "author": {"login": "mockuser", "id": 12345},
        },
    )


def mock_github_status_response():
    """Mock GitHub status checks API response"""
    return MockResponse(
        200,
        {
            "state": "success",
            "total_count": 2,
            "statuses": [
                {
                    "state": "success",
                    "description": "Build passed",
                    "context": "continuous-integration/mock-ci",
                },
                {
                    "state": "success",
                    "description": "Tests passed",
                    "context": "continuous-integration/mock-tests",
                },
            ],
        },
    )


def mock_github_repo_delete_response():
    """Mock GitHub repository deletion response"""
    return MockResponse(204)


def mock_github_repo_create_response(repo_name: str):
    """Mock GitHub repository creation response"""
    return MockResponse(
        201,
        {
            "id": 123456,
            "name": repo_name,
            "full_name": f"mockuser/{repo_name}",
            "html_url": f"https://github.com/mockuser/{repo_name}",
            "clone_url": f"https://github.com/mockuser/{repo_name}.git",
            "private": False,
            "default_branch": "main",
        },
    )


def mock_fly_apps_list_response():
    """Mock Fly.io apps list API response"""
    return MockResponse(
        200,
        [
            {
                "id": "mock-app-1",
                "name": "mock-app-1",
                "status": "running",
                "organization": {"slug": "personal"},
                "hostname": "mock-app-1.fly.dev",
            }
        ],
    )


def mock_fly_app_get_response(app_name: str):
    """Mock Fly.io app get API response"""
    return MockResponse(
        200,
        {
            "id": app_name,
            "name": app_name,
            "status": "running",
            "organization": {"slug": "personal"},
            "hostname": f"{app_name}.fly.dev",
        },
    )


def mock_fly_app_create_response(app_name: str):
    """Mock Fly.io app creation API response"""
    return MockResponse(
        201,
        {
            "id": app_name,
            "name": app_name,
            "status": "pending",
            "organization": {"slug": "personal"},
            "hostname": f"{app_name}.fly.dev",
        },
    )


def mock_fly_app_delete_response():
    """Mock Fly.io app deletion response"""
    return MockResponse(204)


def mock_fly_app_not_found_response():
    """Mock Fly.io app not found response"""
    return MockResponse(404, {"error": "App not found"})


def mock_github_secrets_public_key_response():
    """Mock GitHub secrets public key API response"""
    # This is a valid base64-encoded 32-byte public key for NaCl
    return MockResponse(
        200,
        {
            "key_id": "012345678912345678",
            "key": "2Sg8iYjAxxmI2LvUXpJjkYrMxURPc8r+dB7TJyvvcDA=",
        },
    )


def mock_github_secrets_create_response():
    """Mock GitHub secrets creation response"""
    return MockResponse(201)


def mock_anthropic_messages_response():
    """Mock Anthropic messages API response"""
    return MockResponse(
        200,
        {
            "id": "msg_mock123456",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Mock response from Claude"}],
            "model": "claude-3-haiku-20240307",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        },
    )


def get_mock_response(method: str, url: str, **kwargs) -> MockResponse:
    """
    Get appropriate mock response based on the request method and URL.

    Args:
        method: HTTP method (GET, POST, DELETE, etc.)
        url: Request URL
        **kwargs: Additional request parameters

    Returns:
        MockResponse object
    """
    if not MOCK_MODE:
        raise ValueError("get_mock_response should only be called in MOCK_MODE")

    logger.debug(f"🎭 MOCK_MODE: {method} {url}")

    # GitHub API mocks
    if "api.github.com" in url:
        if url.endswith("/user") and method == "GET":
            return mock_github_user_response()
        elif "/commits/" in url and method == "GET":
            return mock_github_commits_response("mockuser", "mockrepo")
        elif "/status" in url and method == "GET":
            return mock_github_status_response()
        elif method == "DELETE" and "/repos/" in url:
            return mock_github_repo_delete_response()
        elif method == "POST" and "/user/repos" in url:
            repo_name = kwargs.get("json", {}).get("name", "mock-repo")
            return mock_github_repo_create_response(repo_name)
        elif method == "GET" and "/actions/secrets/public-key" in url:
            return mock_github_secrets_public_key_response()
        elif method == "PUT" and "/actions/secrets/" in url:
            return mock_github_secrets_create_response()
        elif method == "GET" and "/repos/" in url and "/actions/secrets" not in url:
            # Mock repository existence check - extract repo name from URL
            repo_name = (
                url.split("/repos/")[1].split("/")[1]
                if "/repos/" in url
                else "mock-repo"
            )
            return MockResponse(
                200,
                {
                    "id": 123456,
                    "name": repo_name,
                    "full_name": f"mockuser/{repo_name}",
                    "html_url": f"https://github.com/mockuser/{repo_name}",
                    "clone_url": f"https://github.com/mockuser/{repo_name}.git",
                    "private": False,
                    "default_branch": "main",
                },
            )
        else:
            return MockResponse(404, {"message": "Not Found"})

    # Fly.io API mocks
    elif "api.machines.dev" in url:
        if "/apps" in url and method == "GET":
            if url.endswith("/apps"):
                return mock_fly_apps_list_response()
            else:
                # Get specific app
                app_name = url.split("/apps/")[-1]
                return mock_fly_app_get_response(app_name)
        elif "/apps" in url and method == "POST":
            app_name = kwargs.get("json", {}).get("app_name", "mock-app")
            return mock_fly_app_create_response(app_name)
        elif "/apps/" in url and method == "DELETE":
            return mock_fly_app_delete_response()
        else:
            return MockResponse(404, {"error": "Not Found"})

    # Anthropic API mocks
    elif "api.anthropic.com" in url:
        if "/messages" in url and method == "POST":
            return mock_anthropic_messages_response()
        else:
            return MockResponse(404, {"error": "Not Found"})

    # Default mock response for unknown URLs
    else:
        logger.debug(f"🎭 MOCK_MODE: No mock defined for {method} {url}")
        return MockResponse(404, {"error": "Mock not implemented"})


def patch_requests_for_mock_mode():
    """
    Patch the requests module to use mock responses when MOCK_MODE is enabled.
    This should be called at the start of tests.
    """
    if not MOCK_MODE:
        return

    import requests

    # Store original methods
    original_get = requests.get
    original_post = requests.post
    original_delete = requests.delete
    original_put = requests.put

    def mock_get(url, **kwargs):
        return get_mock_response("GET", url, **kwargs)

    def mock_post(url, **kwargs):
        return get_mock_response("POST", url, **kwargs)

    def mock_delete(url, **kwargs):
        return get_mock_response("DELETE", url, **kwargs)

    def mock_put(url, **kwargs):
        return get_mock_response("PUT", url, **kwargs)

    # Patch requests methods
    requests.get = mock_get
    requests.post = mock_post
    requests.delete = mock_delete
    requests.put = mock_put

    logger.debug("🎭 MOCK_MODE: Patched requests module with mock responses")

    # Return a function to restore original methods
    def restore_requests():
        requests.get = original_get
        requests.post = original_post
        requests.delete = original_delete
        requests.put = original_put
        logger.debug("🎭 MOCK_MODE: Restored original requests module")

    return restore_requests

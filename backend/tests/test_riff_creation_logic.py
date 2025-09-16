"""
Test for the conditional riff creation logic.
Tests that rename-to riff is only created when GitHub repo is newly created.
"""

import pytest
import requests
from unittest.mock import patch
from mocks import MockResponse


class TestRiffCreationLogic:
    """Test conditional riff creation based on GitHub repo status"""

    def test_create_app_with_new_repo_creates_riff(self, client, mock_api_keys):
        """Test that creating app with new GitHub repo creates rename-to riff"""
        unique_headers = {
            "X-User-UUID": "test-new-repo-creates-riff-uuid",
            "Content-Type": "application/json",
        }
        
        # Set up API keys
        for provider, key in mock_api_keys.items():
            client.post(
                f"/integrations/{provider}",
                headers=unique_headers,
                json={"api_key": key},
            )

        app_data = {"slug": "new-repo-test-app"}

        # Mock the GitHub repo check to return 404 (repo doesn't exist)
        # and then repo creation to return 201 (repo created)
        with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
            # First call: GitHub user API
            mock_get.side_effect = [
                MockResponse(200, {"login": "mockuser"}),  # User API
                MockResponse(404),  # Repo doesn't exist
                MockResponse(200, {"key": "mock-key", "key_id": "123"}),  # Public key for secrets
            ]
            
            # Repo creation call
            mock_post.return_value = MockResponse(201, {
                "id": 123456,
                "name": "new-repo-test-app",
                "full_name": "mockuser/new-repo-test-app",
                "html_url": "https://github.com/mockuser/new-repo-test-app",
                "clone_url": "https://github.com/mockuser/new-repo-test-app.git",
                "private": False,
                "default_branch": "main",
            })

            response = client.post("/api/apps", headers=unique_headers, json=app_data)

        assert response.status_code == 201
        data = response.get_json()

        assert data["message"] == "App created successfully"
        assert data["repo_was_created"] is True
        assert "initial_riff" in data
        assert data["initial_riff"] is not None

    def test_create_app_with_existing_repo_skips_riff(self, client, mock_api_keys):
        """Test that creating app with existing GitHub repo skips rename-to riff"""
        unique_headers = {
            "X-User-UUID": "test-existing-repo-skips-riff-uuid",
            "Content-Type": "application/json",
        }
        
        # Set up API keys
        for provider, key in mock_api_keys.items():
            client.post(
                f"/integrations/{provider}",
                headers=unique_headers,
                json={"api_key": key},
            )

        app_data = {"slug": "existing-repo-test-app"}

        # Mock the GitHub repo check to return 200 (repo exists)
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [
                MockResponse(200, {"login": "mockuser"}),  # User API
                MockResponse(200, {  # Repo exists
                    "id": 123456,
                    "name": "existing-repo-test-app",
                    "full_name": "mockuser/existing-repo-test-app",
                    "html_url": "https://github.com/mockuser/existing-repo-test-app",
                    "clone_url": "https://github.com/mockuser/existing-repo-test-app.git",
                    "private": False,
                    "default_branch": "main",
                }),
                MockResponse(200, {"key": "mock-key", "key_id": "123"}),  # Public key for secrets
            ]

            response = client.post("/api/apps", headers=unique_headers, json=app_data)

        assert response.status_code == 201
        data = response.get_json()

        assert data["message"] == "App created successfully"
        assert data["repo_was_created"] is False
        assert "initial_riff" not in data  # Should not be present when repo already exists

    def test_create_github_repo_function_returns_correct_status(self):
        """Test that create_github_repo function returns correct was_created status"""
        from routes.apps import create_github_repo
        
        # Test with new repo (404 then 201)
        with patch('requests.get') as mock_get, patch('requests.post') as mock_post, patch('requests.put') as mock_put:
            mock_get.side_effect = [
                MockResponse(200, {"login": "mockuser"}),  # User API
                MockResponse(404),  # Repo doesn't exist
                MockResponse(200, {"key": "mock-key", "key_id": "123"}),  # Public key
            ]
            mock_post.return_value = MockResponse(201, {
                "html_url": "https://github.com/mockuser/test-repo"
            })
            mock_put.return_value = MockResponse(201)  # Secret creation
            
            success, url, was_created = create_github_repo("test-repo", "mock-token", "mock-fly-token")
            
            assert success is True
            assert url == "https://github.com/mockuser/test-repo"
            assert was_created is True

        # Test with existing repo (200)
        with patch('requests.get') as mock_get, patch('requests.put') as mock_put:
            mock_get.side_effect = [
                MockResponse(200, {"login": "mockuser"}),  # User API
                MockResponse(200, {  # Repo exists
                    "html_url": "https://github.com/mockuser/existing-repo"
                }),
                MockResponse(200, {"key": "mock-key", "key_id": "123"}),  # Public key
            ]
            mock_put.return_value = MockResponse(201)  # Secret creation
            
            success, url, was_created = create_github_repo("existing-repo", "mock-token", "mock-fly-token")
            
            assert success is True
            assert url == "https://github.com/mockuser/existing-repo"
            assert was_created is False
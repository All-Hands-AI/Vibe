"""
End-to-end tests for integrations endpoints.
Tests API key validation, storage, and retrieval in MOCK_MODE.
"""

import pytest
import json
import os


class TestIntegrationsEndpoints:
    """Test integrations API endpoints for API key management"""

    def test_mock_mode_enabled(self):
        """Verify that MOCK_MODE is enabled for tests"""
        assert os.environ.get("MOCK_MODE", "false").lower() == "true"

    @pytest.mark.parametrize("provider", ["anthropic", "github", "fly"])
    def test_set_valid_api_key(self, client, sample_headers, mock_api_keys, provider):
        """Test setting valid API keys for all providers in MOCK_MODE"""
        api_key = mock_api_keys[provider]
        
        response = client.post(
            f"/integrations/{provider}",
            headers=sample_headers,
            json={"api_key": api_key}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["valid"] is True
        assert data["message"] == f"{provider.title()} API key is valid"

    @pytest.mark.parametrize("provider", ["anthropic", "github", "fly"])
    def test_set_empty_api_key(self, client, sample_headers, provider):
        """Test setting empty API keys returns error"""
        response = client.post(
            f"/integrations/{provider}",
            headers=sample_headers,
            json={"api_key": ""}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["error"] == "API key cannot be empty"

    @pytest.mark.parametrize("provider", ["anthropic", "github", "fly"])
    def test_set_whitespace_api_key(self, client, sample_headers, provider):
        """Test setting whitespace-only API keys returns error"""
        response = client.post(
            f"/integrations/{provider}",
            headers=sample_headers,
            json={"api_key": "   "}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["error"] == "API key cannot be empty"

    def test_set_api_key_invalid_provider(self, client, sample_headers):
        """Test setting API key for invalid provider"""
        response = client.post(
            "/integrations/invalid_provider",
            headers=sample_headers,
            json={"api_key": "test-key"}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["error"] == "Invalid provider"

    def test_set_api_key_missing_uuid_header(self, client):
        """Test setting API key without UUID header"""
        response = client.post(
            "/integrations/anthropic",
            json={"api_key": "test-key"}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["error"] == "X-User-UUID header is required"

    def test_set_api_key_empty_uuid_header(self, client):
        """Test setting API key with empty UUID header"""
        response = client.post(
            "/integrations/anthropic",
            headers={"X-User-UUID": ""},
            json={"api_key": "test-key"}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["error"] == "X-User-UUID header is required"

    def test_set_api_key_missing_body(self, client, sample_headers):
        """Test setting API key without request body"""
        response = client.post(
            "/integrations/anthropic",
            headers=sample_headers,
            json={}  # Empty JSON object
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["error"] == "API key is required"

    def test_set_api_key_missing_api_key_field(self, client, sample_headers):
        """Test setting API key without api_key field in body"""
        response = client.post(
            "/integrations/anthropic",
            headers=sample_headers,
            json={"other_field": "value"}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["error"] == "API key is required"

    @pytest.mark.parametrize("provider", ["anthropic", "github", "fly"])
    def test_check_api_key_not_set(self, client, provider):
        """Test checking API key status when not set"""
        # Use a unique UUID for this test to avoid state leakage
        unique_headers = {
            "X-User-UUID": f"test-check-not-set-{provider}-uuid",
            "Content-Type": "application/json"
        }
        
        response = client.get(
            f"/integrations/{provider}",
            headers=unique_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["valid"] is False
        assert data["message"] == f"{provider.title()} API key not set"

    @pytest.mark.parametrize("provider", ["anthropic", "github", "fly"])
    def test_set_and_check_api_key(self, client, sample_headers, mock_api_keys, provider):
        """Test setting API key and then checking its status"""
        api_key = mock_api_keys[provider]
        
        # First set the API key
        set_response = client.post(
            f"/integrations/{provider}",
            headers=sample_headers,
            json={"api_key": api_key}
        )
        
        assert set_response.status_code == 200
        
        # Then check the API key status
        check_response = client.get(
            f"/integrations/{provider}",
            headers=sample_headers
        )
        
        assert check_response.status_code == 200
        data = check_response.get_json()
        
        assert data["valid"] is True
        assert data["message"] == f"{provider.title()} API key is valid"

    def test_check_api_key_invalid_provider(self, client, sample_headers):
        """Test checking API key for invalid provider"""
        response = client.get(
            "/integrations/invalid_provider",
            headers=sample_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["error"] == "Invalid provider"

    def test_check_api_key_missing_uuid_header(self, client):
        """Test checking API key without UUID header"""
        response = client.get("/integrations/anthropic")
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["error"] == "X-User-UUID header is required"

    def test_check_api_key_empty_uuid_header(self, client):
        """Test checking API key with empty UUID header"""
        response = client.get(
            "/integrations/anthropic",
            headers={"X-User-UUID": ""}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["error"] == "X-User-UUID header is required"

    def test_multiple_providers_same_user(self, client, sample_headers, mock_api_keys):
        """Test setting API keys for multiple providers for the same user"""
        providers = ["anthropic", "github", "fly"]
        
        # Set API keys for all providers
        for provider in providers:
            response = client.post(
                f"/integrations/{provider}",
                headers=sample_headers,
                json={"api_key": mock_api_keys[provider]}
            )
            assert response.status_code == 200
        
        # Check all API keys are set
        for provider in providers:
            response = client.get(
                f"/integrations/{provider}",
                headers=sample_headers
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data["valid"] is True

    def test_different_users_isolated_keys(self, client, mock_api_keys):
        """Test that API keys are isolated between different users"""
        user1_headers = {"X-User-UUID": "user1-uuid", "Content-Type": "application/json"}
        user2_headers = {"X-User-UUID": "user2-uuid", "Content-Type": "application/json"}
        
        # Set API key for user1
        response = client.post(
            "/integrations/anthropic",
            headers=user1_headers,
            json={"api_key": mock_api_keys["anthropic"]}
        )
        assert response.status_code == 200
        
        # Check that user2 doesn't have the key
        response = client.get(
            "/integrations/anthropic",
            headers=user2_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["valid"] is False
        assert data["message"] == "Anthropic API key not set"
        
        # Check that user1 still has the key
        response = client.get(
            "/integrations/anthropic",
            headers=user1_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["valid"] is True
"""
End-to-end tests for LLM readiness endpoints.
Tests the /ready and /reset endpoints for riff LLM management.
"""

import os


class TestLLMReadinessEndpoints:
    """Test LLM readiness API endpoints"""

    def test_mock_mode_enabled(self):
        """Verify that MOCK_MODE is enabled for tests"""
        assert os.environ.get("MOCK_MODE", "false").lower() == "true"

    def setup_app_and_riff_for_llm_tests(
        self,
        client,
        headers,
        mock_api_keys,
        app_name="LLM Test App",
        riff_name="LLM Test Riff",
    ):
        """Helper method to set up an app and riff for LLM readiness tests"""
        # Set up API keys
        for provider, key in mock_api_keys.items():
            client.post(
                f"/integrations/{provider}",
                headers=headers,
                json={"api_key": key},
            )

        # Create an app
        app_data = {"name": app_name}
        app_response = client.post("/api/apps", headers=headers, json=app_data)
        assert app_response.status_code == 201
        app_slug = app_response.get_json()["app"]["slug"]

        # Create a riff
        riff_data = {"name": riff_name, "description": "A test riff for LLM testing"}
        riff_response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=headers, json=riff_data
        )
        assert riff_response.status_code == 201
        riff_slug = riff_response.get_json()["riff"]["slug"]

        return app_slug, riff_slug

    # /ready endpoint tests

    def test_check_riff_ready_missing_uuid_header(self, client):
        """Test checking riff readiness without UUID header"""
        response = client.get("/api/apps/test-app/riffs/test-riff/ready")

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "X-User-UUID header is required"

    def test_check_riff_ready_empty_uuid_header(self, client):
        """Test checking riff readiness with empty UUID header"""
        response = client.get(
            "/api/apps/test-app/riffs/test-riff/ready", headers={"X-User-UUID": "   "}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "UUID cannot be empty"

    def test_check_riff_ready_nonexistent_app(self, client, sample_headers):
        """Test checking riff readiness for nonexistent app"""
        response = client.get(
            "/api/apps/nonexistent-app/riffs/test-riff/ready", headers=sample_headers
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "App not found"

    def test_check_riff_ready_nonexistent_riff(self, client, mock_api_keys):
        """Test checking riff readiness for nonexistent riff"""
        unique_headers = {
            "X-User-UUID": "test-ready-nonexistent-riff-uuid",
            "Content-Type": "application/json",
        }
        app_slug, _ = self.setup_app_and_riff_for_llm_tests(
            client, unique_headers, mock_api_keys, "Ready Test App"
        )

        response = client.get(
            f"/api/apps/{app_slug}/riffs/nonexistent-riff/ready", headers=unique_headers
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Riff not found"

    def test_check_riff_ready_after_creation(self, client, mock_api_keys):
        """Test checking riff readiness after riff creation (should be ready)"""
        unique_headers = {
            "X-User-UUID": "test-ready-after-creation-uuid",
            "Content-Type": "application/json",
        }
        app_slug, riff_slug = self.setup_app_and_riff_for_llm_tests(
            client, unique_headers, mock_api_keys, "Ready After Creation App"
        )

        response = client.get(
            f"/api/apps/{app_slug}/riffs/{riff_slug}/ready", headers=unique_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "ready" in data
        assert isinstance(data["ready"], bool)
        # In mock mode with proper API keys, LLM should be ready after creation
        assert data["ready"] is True

    def test_check_riff_ready_without_api_keys(self, client):
        """Test checking riff readiness without setting up API keys first"""
        unique_headers = {
            "X-User-UUID": "test-ready-no-keys-uuid",
            "Content-Type": "application/json",
        }

        # Create app without setting up API keys
        app_data = {"name": "No Keys App"}
        app_response = client.post("/api/apps", headers=unique_headers, json=app_data)
        # This should fail because no API keys are set up
        assert app_response.status_code == 400
        data = app_response.get_json()
        assert "GitHub API key is required" in data["error"]

    # /reset endpoint tests

    def test_reset_riff_llm_missing_uuid_header(self, client):
        """Test resetting riff LLM without UUID header"""
        response = client.post("/api/apps/test-app/riffs/test-riff/reset")

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "X-User-UUID header is required"

    def test_reset_riff_llm_empty_uuid_header(self, client):
        """Test resetting riff LLM with empty UUID header"""
        response = client.post(
            "/api/apps/test-app/riffs/test-riff/reset", headers={"X-User-UUID": "   "}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "UUID cannot be empty"

    def test_reset_riff_llm_nonexistent_app(self, client, sample_headers):
        """Test resetting riff LLM for nonexistent app"""
        response = client.post(
            "/api/apps/nonexistent-app/riffs/test-riff/reset", headers=sample_headers
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "App not found"

    def test_reset_riff_llm_nonexistent_riff(self, client, mock_api_keys):
        """Test resetting riff LLM for nonexistent riff"""
        unique_headers = {
            "X-User-UUID": "test-reset-nonexistent-riff-uuid",
            "Content-Type": "application/json",
        }
        app_slug, _ = self.setup_app_and_riff_for_llm_tests(
            client, unique_headers, mock_api_keys, "Reset Test App"
        )

        response = client.post(
            f"/api/apps/{app_slug}/riffs/nonexistent-riff/reset", headers=unique_headers
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Riff not found"

    def test_reset_riff_llm_success(self, client, mock_api_keys):
        """Test successfully resetting riff LLM"""
        unique_headers = {
            "X-User-UUID": "test-reset-success-uuid",
            "Content-Type": "application/json",
        }
        app_slug, riff_slug = self.setup_app_and_riff_for_llm_tests(
            client, unique_headers, mock_api_keys, "Reset Success App"
        )

        # Reset the LLM
        response = client.post(
            f"/api/apps/{app_slug}/riffs/{riff_slug}/reset", headers=unique_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "LLM reset successfully"
        assert data["ready"] is True

    def test_reset_riff_llm_without_api_keys(self, client):
        """Test resetting riff LLM without API keys"""
        unique_headers = {
            "X-User-UUID": "test-reset-no-keys-uuid",
            "Content-Type": "application/json",
        }

        # Try to create app without API keys (should fail)
        app_data = {"name": "Reset No Keys App"}
        app_response = client.post("/api/apps", headers=unique_headers, json=app_data)
        assert app_response.status_code == 400

        # Since we can't create an app without API keys, we can't test reset without them
        # This is expected behavior - the system requires API keys for LLM operations

    # Integration tests combining /ready and /reset

    def test_ready_reset_ready_flow(self, client, mock_api_keys):
        """Test the complete flow: check ready -> reset -> check ready again"""
        unique_headers = {
            "X-User-UUID": "test-ready-reset-flow-uuid",
            "Content-Type": "application/json",
        }
        app_slug, riff_slug = self.setup_app_and_riff_for_llm_tests(
            client, unique_headers, mock_api_keys, "Ready Reset Flow App"
        )

        # 1. Check initial readiness (should be ready after creation)
        ready_response_1 = client.get(
            f"/api/apps/{app_slug}/riffs/{riff_slug}/ready", headers=unique_headers
        )
        assert ready_response_1.status_code == 200
        ready_data_1 = ready_response_1.get_json()
        assert ready_data_1["ready"] is True

        # 2. Reset the LLM
        reset_response = client.post(
            f"/api/apps/{app_slug}/riffs/{riff_slug}/reset", headers=unique_headers
        )
        assert reset_response.status_code == 200
        reset_data = reset_response.get_json()
        assert reset_data["message"] == "LLM reset successfully"
        assert reset_data["ready"] is True

        # 3. Check readiness again (should still be ready after reset)
        ready_response_2 = client.get(
            f"/api/apps/{app_slug}/riffs/{riff_slug}/ready", headers=unique_headers
        )
        assert ready_response_2.status_code == 200
        ready_data_2 = ready_response_2.get_json()
        assert ready_data_2["ready"] is True

    def test_multiple_resets_same_riff(self, client, mock_api_keys):
        """Test multiple consecutive resets on the same riff"""
        unique_headers = {
            "X-User-UUID": "test-multiple-resets-uuid",
            "Content-Type": "application/json",
        }
        app_slug, riff_slug = self.setup_app_and_riff_for_llm_tests(
            client, unique_headers, mock_api_keys, "Multiple Resets App"
        )

        # Perform multiple resets
        for i in range(3):
            reset_response = client.post(
                f"/api/apps/{app_slug}/riffs/{riff_slug}/reset", headers=unique_headers
            )
            assert reset_response.status_code == 200
            reset_data = reset_response.get_json()
            assert reset_data["message"] == "LLM reset successfully"
            assert reset_data["ready"] is True

            # Verify readiness after each reset
            ready_response = client.get(
                f"/api/apps/{app_slug}/riffs/{riff_slug}/ready", headers=unique_headers
            )
            assert ready_response.status_code == 200
            ready_data = ready_response.get_json()
            assert ready_data["ready"] is True

    def test_reset_different_users_same_riff_name(self, client, mock_api_keys):
        """Test that resets are properly isolated between different users"""
        # User 1
        headers_1 = {
            "X-User-UUID": "test-reset-isolation-user1-uuid",
            "Content-Type": "application/json",
        }
        app_slug_1, riff_slug_1 = self.setup_app_and_riff_for_llm_tests(
            client, headers_1, mock_api_keys, "Isolation App 1", "Same Riff Name"
        )

        # User 2
        headers_2 = {
            "X-User-UUID": "test-reset-isolation-user2-uuid",
            "Content-Type": "application/json",
        }
        app_slug_2, riff_slug_2 = self.setup_app_and_riff_for_llm_tests(
            client, headers_2, mock_api_keys, "Isolation App 2", "Same Riff Name"
        )

        # Both should have the same riff slug since they have the same name
        assert riff_slug_1 == riff_slug_2

        # Reset User 1's riff
        reset_response_1 = client.post(
            f"/api/apps/{app_slug_1}/riffs/{riff_slug_1}/reset", headers=headers_1
        )
        assert reset_response_1.status_code == 200

        # Reset User 2's riff
        reset_response_2 = client.post(
            f"/api/apps/{app_slug_2}/riffs/{riff_slug_2}/reset", headers=headers_2
        )
        assert reset_response_2.status_code == 200

        # Both should be ready
        ready_response_1 = client.get(
            f"/api/apps/{app_slug_1}/riffs/{riff_slug_1}/ready", headers=headers_1
        )
        assert ready_response_1.status_code == 200
        assert ready_response_1.get_json()["ready"] is True

        ready_response_2 = client.get(
            f"/api/apps/{app_slug_2}/riffs/{riff_slug_2}/ready", headers=headers_2
        )
        assert ready_response_2.status_code == 200
        assert ready_response_2.get_json()["ready"] is True

    def test_cross_user_access_prevention(self, client, mock_api_keys):
        """Test that users cannot access each other's riff LLM endpoints"""
        # User 1 creates app and riff
        headers_1 = {
            "X-User-UUID": "test-cross-user-owner-uuid",
            "Content-Type": "application/json",
        }
        app_slug, riff_slug = self.setup_app_and_riff_for_llm_tests(
            client, headers_1, mock_api_keys, "Cross User App"
        )

        # User 2 tries to access User 1's riff
        headers_2 = {
            "X-User-UUID": "test-cross-user-intruder-uuid",
            "Content-Type": "application/json",
        }

        # User 2 tries to check readiness of User 1's riff
        ready_response = client.get(
            f"/api/apps/{app_slug}/riffs/{riff_slug}/ready", headers=headers_2
        )
        assert ready_response.status_code == 404
        assert ready_response.get_json()["error"] == "App not found"

        # User 2 tries to reset User 1's riff
        reset_response = client.post(
            f"/api/apps/{app_slug}/riffs/{riff_slug}/reset", headers=headers_2
        )
        assert reset_response.status_code == 404
        assert reset_response.get_json()["error"] == "App not found"

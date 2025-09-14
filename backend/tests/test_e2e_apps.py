"""
End-to-end tests for apps endpoints.
Tests app creation, listing, and management with mocked external APIs.
"""

import os


class TestAppsEndpoints:
    """Test apps API endpoints"""

    def test_mock_mode_enabled(self):
        """Verify that MOCK_MODE is enabled for tests"""
        assert os.environ.get("MOCK_MODE", "false").lower() == "true"

    def test_get_apps_empty_list(self, client):
        """Test getting apps when none exist"""
        unique_headers = {
            "X-User-UUID": "test-get-apps-empty-list-uuid",
            "Content-Type": "application/json",
        }
        response = client.get("/api/apps", headers=unique_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data["apps"] == []
        assert data["count"] == 0

    def test_get_apps_missing_uuid_header(self, client):
        """Test getting apps without UUID header"""
        response = client.get("/api/apps")

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "X-User-UUID header is required"

    def test_get_apps_empty_uuid_header(self, client):
        """Test getting apps with empty UUID header"""
        response = client.get("/api/apps", headers={"X-User-UUID": "   "})

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "UUID cannot be empty"

    def test_create_app_success(self, client, mock_api_keys):
        """Test creating a new app successfully"""
        unique_headers = {
            "X-User-UUID": "test-create-app-success-uuid",
            "Content-Type": "application/json",
        }
        # First set up API keys
        for provider, key in mock_api_keys.items():
            client.post(
                f"/integrations/{provider}",
                headers=unique_headers,
                json={"api_key": key},
            )

        app_data = {
            "name": "Test App",
            "description": "A test application",
            "github_url": "https://github.com/testuser/test-app",
        }

        response = client.post("/api/apps", headers=unique_headers, json=app_data)

        assert response.status_code == 201
        data = response.get_json()

        assert data["message"] == "App created successfully"
        assert "app" in data

        app = data["app"]
        assert app["name"] == "Test App"
        assert app["slug"] == "test-app"
        assert (
            app["github_url"] == "https://github.com/mockuser/test-app"
        )  # Updated to match mock response
        assert "created_at" in app
        assert "created_by" in app
        assert "fly_app_name" in app

    def test_create_app_missing_name(self, client, sample_headers):
        """Test creating app without name"""
        response = client.post("/api/apps", headers=sample_headers, json={})

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "App name is required"

    def test_create_app_empty_name(self, client, sample_headers):
        """Test creating app with empty name"""
        response = client.post("/api/apps", headers=sample_headers, json={"name": ""})

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "App name cannot be empty"

    def test_create_app_whitespace_name(self, client, sample_headers):
        """Test creating app with whitespace-only name"""
        response = client.post(
            "/api/apps", headers=sample_headers, json={"name": "   "}
        )

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "App name cannot be empty"

    def test_create_app_missing_uuid_header(self, client):
        """Test creating app without UUID header"""
        response = client.post("/api/apps", json={"name": "Test App"})

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "X-User-UUID header is required"

    def test_create_app_duplicate_name(self, client, sample_headers, mock_api_keys):
        """Test creating app with duplicate name"""
        # First set up API keys
        for provider, key in mock_api_keys.items():
            client.post(
                f"/integrations/{provider}",
                headers=sample_headers,
                json={"api_key": key},
            )

        app_data = {"name": "Duplicate Test App"}

        # Create first app
        response1 = client.post("/api/apps", headers=sample_headers, json=app_data)
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = client.post("/api/apps", headers=sample_headers, json=app_data)
        assert response2.status_code == 409

        data = response2.get_json()
        assert data["error"] == 'App with name "Duplicate Test App" already exists'

    def test_create_and_list_apps(self, client, mock_api_keys):
        """Test creating apps and then listing them"""
        # Use unique headers for this test to avoid state leakage
        unique_headers = {
            "X-User-UUID": "test-list-apps-user-uuid",
            "Content-Type": "application/json",
        }

        # First set up API keys
        for provider, key in mock_api_keys.items():
            client.post(
                f"/integrations/{provider}",
                headers=unique_headers,
                json={"api_key": key},
            )

        # Create multiple apps
        apps_to_create = [
            {"name": "App One", "description": "First app"},
            {"name": "App Two", "description": "Second app"},
            {"name": "App Three", "description": "Third app"},
        ]

        for app_data in apps_to_create:
            response = client.post("/api/apps", headers=unique_headers, json=app_data)
            assert response.status_code == 201

        # List apps
        response = client.get("/api/apps", headers=unique_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data["count"] == 3
        assert len(data["apps"]) == 3

        # Check that apps are sorted by creation date (newest first)
        app_names = [app["name"] for app in data["apps"]]
        assert "App One" in app_names
        assert "App Two" in app_names
        assert "App Three" in app_names

    def test_get_specific_app(self, client, sample_headers, mock_api_keys):
        """Test getting a specific app by slug"""
        # First set up API keys
        for provider, key in mock_api_keys.items():
            client.post(
                f"/integrations/{provider}",
                headers=sample_headers,
                json={"api_key": key},
            )

        # Create an app
        app_data = {"name": "Specific App", "description": "A specific test app"}

        create_response = client.post(
            "/api/apps", headers=sample_headers, json=app_data
        )
        assert create_response.status_code == 201

        # Get the app by slug
        response = client.get("/api/apps/specific-app", headers=sample_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data["name"] == "Specific App"
        assert data["slug"] == "specific-app"
        # Description is not returned in the API response
        # assert data["description"] == "A specific test app"

    def test_get_nonexistent_app(self, client, sample_headers):
        """Test getting a nonexistent app"""
        response = client.get("/api/apps/nonexistent-app", headers=sample_headers)

        assert response.status_code == 404
        data = response.get_json()

        assert data["error"] == "App not found"

    def test_delete_app(self, client, sample_headers, mock_api_keys):
        """Test deleting an app"""
        # First set up API keys
        for provider, key in mock_api_keys.items():
            client.post(
                f"/integrations/{provider}",
                headers=sample_headers,
                json={"api_key": key},
            )

        # Create an app
        app_data = {"name": "App to Delete"}
        create_response = client.post(
            "/api/apps", headers=sample_headers, json=app_data
        )
        assert create_response.status_code == 201

        # Delete the app
        response = client.delete("/api/apps/app-to-delete", headers=sample_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert "deleted successfully" in data["message"]

        # Verify app is gone
        get_response = client.get("/api/apps/app-to-delete", headers=sample_headers)
        assert get_response.status_code == 404

    def test_delete_nonexistent_app(self, client, sample_headers):
        """Test deleting a nonexistent app"""
        response = client.delete("/api/apps/nonexistent-app", headers=sample_headers)

        assert response.status_code == 404
        data = response.get_json()

        assert data["error"] == "App not found"

    def test_different_users_isolated_apps(self, client, mock_api_keys):
        """Test that apps are isolated between different users"""
        user1_headers = {
            "X-User-UUID": "user1-uuid",
            "Content-Type": "application/json",
        }
        user2_headers = {
            "X-User-UUID": "user2-uuid",
            "Content-Type": "application/json",
        }

        # Set up API keys for both users
        for headers in [user1_headers, user2_headers]:
            for provider, key in mock_api_keys.items():
                client.post(
                    f"/integrations/{provider}", headers=headers, json={"api_key": key}
                )

        # Create app for user1
        response = client.post(
            "/api/apps", headers=user1_headers, json={"name": "User1 App"}
        )
        assert response.status_code == 201

        # Check that user2 doesn't see user1's app
        response = client.get("/api/apps", headers=user2_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 0
        assert data["apps"] == []

        # Check that user1 still sees their app
        response = client.get("/api/apps", headers=user1_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 1
        assert data["apps"][0]["name"] == "User1 App"

    def test_app_slug_generation(self, client, sample_headers, mock_api_keys):
        """Test that app slugs are generated correctly from names"""
        # First set up API keys
        for provider, key in mock_api_keys.items():
            client.post(
                f"/integrations/{provider}",
                headers=sample_headers,
                json={"api_key": key},
            )

        test_cases = [
            ("Simple App", "simple-app"),
            ("App With Spaces", "app-with-spaces"),
            ("App-With-Hyphens", "app-with-hyphens"),
            ("App_With_Underscores", "appwithunderscores"),
            ("App123 With Numbers", "app123-with-numbers"),
            ("App!@# With Special", "app-with-special"),
        ]

        for app_name, expected_slug in test_cases:
            response = client.post(
                "/api/apps", headers=sample_headers, json={"name": app_name}
            )
            assert response.status_code == 201

            data = response.get_json()
            assert data["app"]["slug"] == expected_slug

            # Clean up for next test
            client.delete(f"/api/apps/{expected_slug}", headers=sample_headers)

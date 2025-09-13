"""
End-to-end tests for riffs endpoints.
Tests riff creation, listing, and management within apps.
"""

import os


class TestRiffsEndpoints:
    """Test riffs API endpoints"""

    def test_mock_mode_enabled(self):
        """Verify that MOCK_MODE is enabled for tests"""
        assert os.environ.get("MOCK_MODE", "false").lower() == "true"

    def setup_app_for_riffs(self, client, headers, mock_api_keys, app_name="Test App"):
        """Helper method to set up an app for riff tests"""
        # Set up API keys
        for provider, key in mock_api_keys.items():
            client.post(
                f"/integrations/{provider}",
                headers=headers,
                json={"api_key": key},
            )

        # Create an app
        app_data = {"name": app_name}
        response = client.post("/api/apps", headers=headers, json=app_data)
        assert response.status_code == 201

        return response.get_json()["app"]["slug"]

    def test_get_riffs_empty_list(self, client, mock_api_keys):
        """Test getting riffs when none exist"""
        unique_headers = {
            "X-User-UUID": "test-riffs-empty-list-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "Empty List App"
        )

        response = client.get(f"/api/apps/{app_slug}/riffs", headers=unique_headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data["riffs"] == []
        assert data["count"] == 0
        assert data["app_slug"] == app_slug

    def test_get_riffs_nonexistent_app(self, client, sample_headers):
        """Test getting riffs for nonexistent app"""
        response = client.get("/api/apps/nonexistent-app/riffs", headers=sample_headers)

        assert response.status_code == 404
        data = response.get_json()

        assert data["error"] == "App not found"

    def test_get_riffs_missing_uuid_header(self, client):
        """Test getting riffs without UUID header"""
        response = client.get("/api/apps/test-app/riffs")

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "X-User-UUID header is required"

    def test_get_riffs_empty_uuid_header(self, client):
        """Test getting riffs with empty UUID header"""
        response = client.get(
            "/api/apps/test-app/riffs", headers={"X-User-UUID": "   "}
        )

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "UUID cannot be empty"

    def test_create_riff_success(self, client, mock_api_keys):
        """Test creating a new riff successfully"""
        unique_headers = {
            "X-User-UUID": "test-create-riff-success-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "Create Riff App"
        )

        riff_data = {"name": "Test Riff", "description": "A test riff"}

        response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=unique_headers, json=riff_data
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data["message"] == "Riff created successfully"
        assert "riff" in data

        riff = data["riff"]
        assert riff["name"] == "Test Riff"
        assert riff["slug"] == "test-riff"
        assert riff["app_slug"] == app_slug
        assert "created_at" in riff
        assert "created_by" in riff
        assert riff["message_count"] == 0
        assert riff["last_message_at"] is None

    def test_create_riff_missing_name(self, client, mock_api_keys):
        """Test creating riff without name"""
        unique_headers = {
            "X-User-UUID": "test-riff-missing-name-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "Missing Name App"
        )

        response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=unique_headers, json={}
        )

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "Riff name is required"

    def test_create_riff_empty_name(self, client, mock_api_keys):
        """Test creating riff with empty name"""
        unique_headers = {
            "X-User-UUID": "test-riff-empty-name-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "Empty Name App"
        )

        response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=unique_headers, json={"name": ""}
        )

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "Riff name cannot be empty"

    def test_create_riff_whitespace_name(self, client, sample_headers, mock_api_keys):
        """Test creating riff with whitespace-only name"""
        app_slug = self.setup_app_for_riffs(client, sample_headers, mock_api_keys)

        response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=sample_headers, json={"name": "   "}
        )

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "Riff name cannot be empty"

    def test_create_riff_nonexistent_app(self, client, sample_headers):
        """Test creating riff for nonexistent app"""
        response = client.post(
            "/api/apps/nonexistent-app/riffs",
            headers=sample_headers,
            json={"name": "Test Riff"},
        )

        assert response.status_code == 404
        data = response.get_json()

        assert data["error"] == "App not found"

    def test_create_riff_missing_uuid_header(self, client):
        """Test creating riff without UUID header"""
        response = client.post("/api/apps/test-app/riffs", json={"name": "Test Riff"})

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "X-User-UUID header is required"

    def test_create_riff_duplicate_name(self, client, sample_headers, mock_api_keys):
        """Test creating riff with duplicate name"""
        app_slug = self.setup_app_for_riffs(client, sample_headers, mock_api_keys)

        riff_data = {"name": "Duplicate Riff"}

        # Create first riff
        response1 = client.post(
            f"/api/apps/{app_slug}/riffs", headers=sample_headers, json=riff_data
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = client.post(
            f"/api/apps/{app_slug}/riffs", headers=sample_headers, json=riff_data
        )
        assert response2.status_code == 409

        data = response2.get_json()
        assert data["error"] == 'Riff with name "Duplicate Riff" already exists'

    def test_create_and_list_riffs(self, client, sample_headers, mock_api_keys):
        """Test creating riffs and then listing them"""
        app_slug = self.setup_app_for_riffs(client, sample_headers, mock_api_keys)

        # Create multiple riffs
        riffs_to_create = [
            {"name": "Riff One"},
            {"name": "Riff Two"},
            {"name": "Riff Three"},
        ]

        for riff_data in riffs_to_create:
            response = client.post(
                f"/api/apps/{app_slug}/riffs", headers=sample_headers, json=riff_data
            )
            assert response.status_code == 201

        # List riffs
        response = client.get(f"/api/apps/{app_slug}/riffs", headers=sample_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data["count"] == 3
        assert len(data["riffs"]) == 3
        assert data["app_slug"] == app_slug

        # Check that riffs are present
        riff_names = [riff["name"] for riff in data["riffs"]]
        assert "Riff One" in riff_names
        assert "Riff Two" in riff_names
        assert "Riff Three" in riff_names

    def test_riff_slug_generation(self, client, sample_headers, mock_api_keys):
        """Test that riff slugs are generated correctly from names"""
        app_slug = self.setup_app_for_riffs(client, sample_headers, mock_api_keys)

        test_cases = [
            ("Simple Riff", "simple-riff"),
            ("Riff With Spaces", "riff-with-spaces"),
            ("Riff-With-Hyphens", "riff-with-hyphens"),
            ("Riff_With_Underscores", "riffwithunderscores"),
            ("Riff123 With Numbers", "riff123-with-numbers"),
            ("Riff!@# With Special", "riff-with-special"),
        ]

        for riff_name, expected_slug in test_cases:
            response = client.post(
                f"/api/apps/{app_slug}/riffs",
                headers=sample_headers,
                json={"name": riff_name},
            )
            assert response.status_code == 201

            data = response.get_json()
            assert data["riff"]["slug"] == expected_slug

    def test_custom_riff_slug(self, client, sample_headers, mock_api_keys):
        """Test creating riff with custom slug"""
        app_slug = self.setup_app_for_riffs(client, sample_headers, mock_api_keys)

        riff_data = {"name": "Custom Slug Riff", "slug": "my-custom-slug"}

        response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=sample_headers, json=riff_data
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data["riff"]["slug"] == "my-custom-slug"
        assert data["riff"]["name"] == "Custom Slug Riff"

    def test_different_users_isolated_riffs(self, client, mock_api_keys):
        """Test that riffs are isolated between different users"""
        user1_headers = {
            "X-User-UUID": "user1-uuid",
            "Content-Type": "application/json",
        }
        user2_headers = {
            "X-User-UUID": "user2-uuid",
            "Content-Type": "application/json",
        }

        # Set up apps for both users
        app1_slug = self.setup_app_for_riffs(
            client, user1_headers, mock_api_keys, "User1 App"
        )
        app2_slug = self.setup_app_for_riffs(
            client, user2_headers, mock_api_keys, "User2 App"
        )

        # Create riff for user1
        response = client.post(
            f"/api/apps/{app1_slug}/riffs",
            headers=user1_headers,
            json={"name": "User1 Riff"},
        )
        assert response.status_code == 201

        # Check that user2 doesn't see user1's riff in their app
        response = client.get(f"/api/apps/{app2_slug}/riffs", headers=user2_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 0
        assert data["riffs"] == []

        # Check that user1 still sees their riff
        response = client.get(f"/api/apps/{app1_slug}/riffs", headers=user1_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 1
        assert data["riffs"][0]["name"] == "User1 Riff"

    def test_riffs_different_apps_same_user(
        self, client, sample_headers, mock_api_keys
    ):
        """Test that riffs are isolated between different apps for the same user"""
        # Create two apps
        app1_slug = self.setup_app_for_riffs(
            client, sample_headers, mock_api_keys, "App One"
        )
        app2_slug = self.setup_app_for_riffs(
            client, sample_headers, mock_api_keys, "App Two"
        )

        # Create riff in first app
        response = client.post(
            f"/api/apps/{app1_slug}/riffs",
            headers=sample_headers,
            json={"name": "App1 Riff"},
        )
        assert response.status_code == 201

        # Check that second app doesn't have the riff
        response = client.get(f"/api/apps/{app2_slug}/riffs", headers=sample_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 0

        # Check that first app still has the riff
        response = client.get(f"/api/apps/{app1_slug}/riffs", headers=sample_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 1
        assert data["riffs"][0]["name"] == "App1 Riff"

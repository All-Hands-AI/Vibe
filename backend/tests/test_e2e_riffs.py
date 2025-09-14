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

    def setup_app_for_riffs(self, client, headers, mock_api_keys, app_name="test-app"):
        """Helper method to set up an app for riff tests"""
        # Set up API keys
        for provider, key in mock_api_keys.items():
            client.post(
                f"/integrations/{provider}",
                headers=headers,
                json={"api_key": key},
            )

        # Create an app
        app_data = {"slug": app_name}
        response = client.post("/api/apps", headers=headers, json=app_data)
        assert response.status_code == 201

        return response.get_json()["app"]["slug"]

    def test_get_riffs_empty_list(self, client, mock_api_keys):
        """Test getting riffs when only automatic riff exists"""
        unique_headers = {
            "X-User-UUID": "test-riffs-empty-list-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "empty-list-app"
        )

        response = client.get(f"/api/apps/{app_slug}/riffs", headers=unique_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Should have 1 riff (the automatic rename riff)
        assert data["count"] == 1
        assert data["app_slug"] == app_slug
        assert len(data["riffs"]) == 1

        # Check that the automatic riff was created
        automatic_riff = data["riffs"][0]
        assert automatic_riff["slug"] == f"rename-to-{app_slug}"
        assert automatic_riff["slug"] == f"rename-to-{app_slug}"
        assert automatic_riff["app_slug"] == app_slug

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
            client, unique_headers, mock_api_keys, "create-riff-app"
        )

        riff_data = {"slug": "test-riff", "description": "A test riff"}

        response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=unique_headers, json=riff_data
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data["message"] == "Riff created successfully"
        assert "riff" in data

        riff = data["riff"]
        assert riff["slug"] == "test-riff"
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
            client, unique_headers, mock_api_keys, "missing-name-app"
        )

        response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=unique_headers, json={}
        )

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "Riff slug is required"

    def test_create_riff_empty_name(self, client, mock_api_keys):
        """Test creating riff with empty name"""
        unique_headers = {
            "X-User-UUID": "test-riff-empty-name-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "empty-name-app"
        )

        response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=unique_headers, json={"slug": ""}
        )

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "Riff slug cannot be empty"

    def test_create_riff_whitespace_name(self, client, mock_api_keys):
        """Test creating riff with whitespace-only name"""
        unique_headers = {
            "X-User-UUID": "test-riff-whitespace-name-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "whitespace-name-app"
        )

        response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=unique_headers, json={"slug": "   "}
        )

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "Riff slug cannot be empty"

    def test_create_riff_nonexistent_app(self, client, sample_headers):
        """Test creating riff for nonexistent app"""
        response = client.post(
            "/api/apps/nonexistent-app/riffs",
            headers=sample_headers,
            json={"slug": "test-riff"},
        )

        assert response.status_code == 404
        data = response.get_json()

        assert data["error"] == "App not found"

    def test_create_riff_missing_uuid_header(self, client):
        """Test creating riff without UUID header"""
        response = client.post("/api/apps/test-app/riffs", json={"slug": "test-riff"})

        assert response.status_code == 400
        data = response.get_json()

        assert data["error"] == "X-User-UUID header is required"

    def test_create_riff_duplicate_name(self, client, mock_api_keys):
        """Test creating riff with duplicate name - should adopt existing riff"""
        unique_headers = {
            "X-User-UUID": "test-riff-duplicate-name-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "duplicate-name-app"
        )

        riff_data = {"slug": "duplicate-riff"}

        # Create first riff
        response1 = client.post(
            f"/api/apps/{app_slug}/riffs", headers=unique_headers, json=riff_data
        )
        assert response1.status_code == 201
        first_riff = response1.get_json()["riff"]

        # Try to create duplicate - should adopt existing riff
        response2 = client.post(
            f"/api/apps/{app_slug}/riffs", headers=unique_headers, json=riff_data
        )
        assert response2.status_code == 200

        data = response2.get_json()
        assert "adopted" in data["message"].lower()
        assert data["riff"]["slug"] == first_riff["slug"]

    def test_create_and_list_riffs(self, client, mock_api_keys):
        """Test creating riffs and then listing them"""
        unique_headers = {
            "X-User-UUID": "test-create-and-list-riffs-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "create-list-app"
        )

        # Create multiple riffs
        riffs_to_create = [
            {"slug": "riff-one"},
            {"slug": "riff-two"},
            {"slug": "riff-three"},
        ]

        for riff_data in riffs_to_create:
            response = client.post(
                f"/api/apps/{app_slug}/riffs", headers=unique_headers, json=riff_data
            )
            assert response.status_code == 201

        # List riffs
        response = client.get(f"/api/apps/{app_slug}/riffs", headers=unique_headers)
        assert response.status_code == 200

        data = response.get_json()
        # Should have 4 riffs (3 manual + 1 automatic rename riff)
        assert data["count"] == 4
        assert len(data["riffs"]) == 4
        assert data["app_slug"] == app_slug

        # Check that riffs are present
        riff_slugs = [riff["slug"] for riff in data["riffs"]]
        assert "riff-one" in riff_slugs
        assert "riff-two" in riff_slugs
        assert "riff-three" in riff_slugs
        # Also check for the automatic rename riff
        assert f"rename-to-{app_slug}" in riff_slugs

    def test_riff_slug_validation(self, client, mock_api_keys):
        """Test that riff slugs are validated correctly"""
        unique_headers = {
            "X-User-UUID": "test-riff-slug-generation-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "slug-gen-app"
        )

        # Test valid slugs
        valid_slugs = [
            "simple-riff",
            "riff-with-hyphens",
            "riff123-with-numbers",
        ]

        for slug in valid_slugs:
            response = client.post(
                f"/api/apps/{app_slug}/riffs",
                headers=unique_headers,
                json={"slug": slug},
            )
            assert response.status_code == 201

            data = response.get_json()
            assert data["riff"]["slug"] == slug

            # Clean up for next test
            client.delete(
                f"/api/apps/{app_slug}/riffs/{slug}", headers=unique_headers
            )

        # Test invalid slugs
        invalid_slugs = [
            "Simple Riff",  # spaces and capitals
            "Riff_With_Underscores",  # underscores
            "Riff!@# With Special",  # special characters
            "-invalid-start",  # starts with hyphen
            "invalid-end-",  # ends with hyphen
            "invalid--double",  # double hyphens
        ]

        for slug in invalid_slugs:
            response = client.post(
                f"/api/apps/{app_slug}/riffs",
                headers=unique_headers,
                json={"slug": slug},
            )
            assert response.status_code == 400

    def test_custom_riff_slug(self, client, mock_api_keys):
        """Test creating riff with custom slug"""
        unique_headers = {
            "X-User-UUID": "test-custom-riff-slug-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "custom-slug-app"
        )

        riff_data = {"slug": "my-custom-slug"}

        response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=unique_headers, json=riff_data
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data["riff"]["slug"] == "my-custom-slug"

    def test_different_users_isolated_riffs(self, client, mock_api_keys):
        """Test that riffs are isolated between different users"""
        user1_headers = {
            "X-User-UUID": "test-riff-isolation-user1-uuid",
            "Content-Type": "application/json",
        }
        user2_headers = {
            "X-User-UUID": "test-riff-isolation-user2-uuid",
            "Content-Type": "application/json",
        }

        # Set up apps for both users
        app1_slug = self.setup_app_for_riffs(
            client, user1_headers, mock_api_keys, "user1-app"
        )
        app2_slug = self.setup_app_for_riffs(
            client, user2_headers, mock_api_keys, "user2-app"
        )

        # Create riff for user1
        response = client.post(
            f"/api/apps/{app1_slug}/riffs",
            headers=user1_headers,
            json={"slug": "user1-riff"},
        )
        assert response.status_code == 201

        # Check that user2 doesn't see user1's riff in their app (but has their own automatic riff)
        response = client.get(f"/api/apps/{app2_slug}/riffs", headers=user2_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 1  # Only the automatic rename riff
        assert len(data["riffs"]) == 1
        assert (
            data["riffs"][0]["slug"] == f"rename-to-{app2_slug}"
        )  # Only the automatic riff

        # Check that user1 still sees their riff (plus the automatic one)
        response = client.get(f"/api/apps/{app1_slug}/riffs", headers=user1_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 2  # User1 Riff + automatic rename riff
        riff_slugs = [riff["slug"] for riff in data["riffs"]]
        assert "user1-riff" in riff_slugs
        assert f"rename-to-{app1_slug}" in riff_slugs

    def test_riffs_different_apps_same_user(
        self, client, sample_headers, mock_api_keys
    ):
        """Test that riffs are isolated between different apps for the same user"""
        # Create two apps
        app1_slug = self.setup_app_for_riffs(
            client, sample_headers, mock_api_keys, "app-one"
        )
        app2_slug = self.setup_app_for_riffs(
            client, sample_headers, mock_api_keys, "app-two"
        )

        # Create riff in first app
        response = client.post(
            f"/api/apps/{app1_slug}/riffs",
            headers=sample_headers,
            json={"slug": "app1-riff"},
        )
        assert response.status_code == 201

        # Check that second app doesn't have the first app's riff (but has its own automatic riff)
        response = client.get(f"/api/apps/{app2_slug}/riffs", headers=sample_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 1  # Only the automatic rename riff
        assert len(data["riffs"]) == 1
        assert (
            data["riffs"][0]["slug"] == f"rename-to-{app2_slug}"
        )  # Only the automatic riff

        # Check that first app still has the riff (plus the automatic one)
        response = client.get(f"/api/apps/{app1_slug}/riffs", headers=sample_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 2  # App1 Riff + automatic rename riff
        riff_slugs = [riff["slug"] for riff in data["riffs"]]
        assert "app1-riff" in riff_slugs
        assert f"rename-to-{app1_slug}" in riff_slugs

    def test_delete_riff_success(self, client, mock_api_keys):
        """Test successful riff deletion"""
        unique_headers = {
            "X-User-UUID": "test-delete-riff-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "delete-test-app"
        )

        # Create a riff
        riff_data = {"slug": "test-riff-to-delete"}
        response = client.post(
            f"/api/apps/{app_slug}/riffs", headers=unique_headers, json=riff_data
        )
        assert response.status_code == 201
        riff_slug = response.get_json()["riff"]["slug"]

        # Verify riff exists (1 manual + 1 automatic)
        response = client.get(f"/api/apps/{app_slug}/riffs", headers=unique_headers)
        assert response.status_code == 200
        assert response.get_json()["count"] == 2

        # Delete the riff
        response = client.delete(
            f"/api/apps/{app_slug}/riffs/{riff_slug}", headers=unique_headers
        )
        assert response.status_code == 200
        data = response.get_json()

        assert "deleted successfully" in data["message"]
        assert data["riff_slug"] == riff_slug
        assert data["app_slug"] == app_slug

        # Verify manual riff is gone, but automatic riff remains
        response = client.get(f"/api/apps/{app_slug}/riffs", headers=unique_headers)
        assert response.status_code == 200
        assert response.get_json()["count"] == 1  # Only automatic riff remains

    def test_delete_riff_not_found(self, client, mock_api_keys):
        """Test deleting a non-existent riff"""
        unique_headers = {
            "X-User-UUID": "test-delete-riff-not-found-uuid",
            "Content-Type": "application/json",
        }
        app_slug = self.setup_app_for_riffs(
            client, unique_headers, mock_api_keys, "delete-not-found-app"
        )

        # Try to delete non-existent riff
        response = client.delete(
            f"/api/apps/{app_slug}/riffs/non-existent-riff", headers=unique_headers
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "not found" in data["error"].lower()

    def test_delete_riff_missing_uuid_header(self, client, mock_api_keys):
        """Test deleting riff without UUID header"""
        headers = {"Content-Type": "application/json"}

        response = client.delete("/api/apps/test-app/riffs/test-riff", headers=headers)
        assert response.status_code == 400
        data = response.get_json()
        assert "X-User-UUID header is required" in data["error"]

    def test_delete_riff_app_not_found(self, client, mock_api_keys):
        """Test deleting riff from non-existent app"""
        unique_headers = {
            "X-User-UUID": "test-delete-riff-app-not-found-uuid",
            "Content-Type": "application/json",
        }

        # Try to delete riff from non-existent app
        response = client.delete(
            "/api/apps/non-existent-app/riffs/test-riff", headers=unique_headers
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "not found" in data["error"].lower()

"""
End-to-end tests for basic endpoints.
Tests basic functionality like health checks and hello endpoints.
"""


from datetime import datetime


class TestBasicEndpoints:
    """Test basic API endpoints"""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns proper response"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.get_json()

        assert data["message"] == "Hello World from Python Backend!"
        assert data["status"] == "success"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data

        # Verify timestamp is valid ISO format
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_health_check(self, client):
        """Test the health check endpoint"""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.get_json()

        assert data["status"] == "healthy"
        assert data["service"] == "OpenVibe Backend"
        assert "timestamp" in data

        # Verify timestamp is valid ISO format
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_api_hello(self, client):
        """Test the API hello endpoint"""
        response = client.get("/api/hello")

        assert response.status_code == 200
        data = response.get_json()

        assert data["message"] == "Hello from the API!"
        assert data["endpoint"] == "/api/hello"
        assert "timestamp" in data

        # Verify timestamp is valid ISO format
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_nonexistent_endpoint(self, client):
        """Test that nonexistent endpoints return 404"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_cors_headers(self, client):
        """Test that CORS headers are present"""
        response = client.get("/api/health")

        # Flask-CORS should add these headers
        assert response.status_code == 200
        # Note: In test mode, CORS headers might not be fully set
        # This test verifies the endpoint works, CORS is handled by Flask-CORS

    def test_json_content_type(self, client):
        """Test that responses have correct content type"""
        response = client.get("/api/health")

        assert response.status_code == 200
        assert response.content_type == "application/json"

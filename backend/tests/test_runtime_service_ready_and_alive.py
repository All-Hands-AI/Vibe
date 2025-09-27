"""
Tests for RuntimeService ready and alive functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from services.runtime_service import runtime_service


class TestRuntimeServiceReadyAndAlive:
    """Test the new ready and alive functionality in RuntimeService."""

    def test_check_runtime_alive_success(self):
        """Test successful runtime alive check."""
        with patch("services.runtime_service.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            success, response = runtime_service.check_runtime_alive(
                "https://test-runtime.example.com"
            )

            assert success is True
            assert response["status"] == "alive"
            assert response["url"] == "https://test-runtime.example.com"

    def test_check_runtime_alive_failure(self):
        """Test runtime alive check failure."""
        with patch("services.runtime_service.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            success, response = runtime_service.check_runtime_alive(
                "https://test-runtime.example.com"
            )

            assert success is False
            assert "Runtime alive check failed: 500" in response["error"]

    def test_check_runtime_alive_timeout(self):
        """Test runtime alive check timeout."""
        with patch("services.runtime_service.requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection timeout")

            success, response = runtime_service.check_runtime_alive(
                "https://test-runtime.example.com"
            )

            assert success is False
            assert "Runtime alive check failed: Connection timeout" in response["error"]

    def test_check_runtime_alive_no_url(self):
        """Test runtime alive check with no URL."""
        success, response = runtime_service.check_runtime_alive("")

        assert success is False
        assert response["error"] == "Runtime URL not provided"

    def test_wait_for_runtime_ready_and_alive_success(self):
        """Test successful wait for runtime ready and alive."""
        with patch.object(
            runtime_service, "get_runtime_status"
        ) as mock_get_status, patch.object(
            runtime_service, "check_runtime_alive"
        ) as mock_check_alive:

            # Mock runtime status as running
            mock_get_status.return_value = (
                True,
                {
                    "status": "running",
                    "url": "https://test-runtime.example.com",
                    "runtime_id": "test-runtime-123",
                },
            )

            # Mock alive check as successful
            mock_check_alive.return_value = (True, {"status": "alive"})

            success, response = runtime_service.wait_for_runtime_ready_and_alive(
                "test-user", "test-app", "test-riff", timeout=10, check_interval=1
            )

            assert success is True
            assert response["status"] == "running"
            assert response["url"] == "https://test-runtime.example.com"
            assert response["alive_status"] == "alive"

    def test_wait_for_runtime_ready_and_alive_not_running(self):
        """Test wait for runtime when it's not running yet."""
        with patch.object(
            runtime_service, "get_runtime_status"
        ) as mock_get_status, patch("services.runtime_service.time.sleep"):

            # Mock runtime status as starting (not running)
            mock_get_status.return_value = (
                True,
                {"status": "starting", "url": "https://test-runtime.example.com"},
            )

            success, response = runtime_service.wait_for_runtime_ready_and_alive(
                "test-user", "test-app", "test-riff", timeout=1, check_interval=1
            )

            assert success is False
            assert "Timeout waiting for runtime to be ready and alive" in response["error"]

    def test_wait_for_runtime_ready_and_alive_error_status(self):
        """Test wait for runtime when it has error status."""
        with patch.object(runtime_service, "get_runtime_status") as mock_get_status:

            # Mock runtime status as error
            mock_get_status.return_value = (True, {"status": "error"})

            success, response = runtime_service.wait_for_runtime_ready_and_alive(
                "test-user", "test-app", "test-riff", timeout=10, check_interval=1
            )

            assert success is False
            assert response["error"] == "Runtime failed to start"
            assert response["status"] == "error"

    def test_wait_for_runtime_ready_and_alive_not_alive_yet(self):
        """Test wait for runtime when it's running but not alive yet."""
        with patch.object(
            runtime_service, "get_runtime_status"
        ) as mock_get_status, patch.object(
            runtime_service, "check_runtime_alive"
        ) as mock_check_alive, patch(
            "services.runtime_service.time.sleep"
        ):

            # Mock runtime status as running
            mock_get_status.return_value = (
                True,
                {
                    "status": "running",
                    "url": "https://test-runtime.example.com",
                    "runtime_id": "test-runtime-123",
                },
            )

            # Mock alive check as failing
            mock_check_alive.return_value = (False, {"error": "Not alive yet"})

            success, response = runtime_service.wait_for_runtime_ready_and_alive(
                "test-user", "test-app", "test-riff", timeout=1, check_interval=1
            )

            assert success is False
            assert "Timeout waiting for runtime to be ready and alive" in response["error"]

    def test_wait_for_runtime_alive_success(self):
        """Test successful wait for runtime alive."""
        with patch.object(runtime_service, "check_runtime_alive") as mock_check_alive:

            # Mock alive check as successful
            mock_check_alive.return_value = (True, {"status": "alive"})

            success, response = runtime_service.wait_for_runtime_alive(
                "https://test-runtime.example.com", timeout=10, check_interval=1
            )

            assert success is True
            assert response["status"] == "alive"

    def test_wait_for_runtime_alive_timeout(self):
        """Test timeout waiting for runtime alive."""
        with patch.object(runtime_service, "check_runtime_alive") as mock_check_alive, patch(
            "services.runtime_service.time.sleep"
        ):

            # Mock alive check as always failing
            mock_check_alive.return_value = (False, {"error": "Not alive"})

            success, response = runtime_service.wait_for_runtime_alive(
                "https://test-runtime.example.com", timeout=1, check_interval=1
            )

            assert success is False
            assert "Timeout waiting for runtime to be alive" in response["error"]
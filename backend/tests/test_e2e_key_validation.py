"""
End-to-end tests for API key validation functionality.
Tests the key validation system in MOCK_MODE vs normal mode.
"""

import pytest
import os
from unittest.mock import patch
from keys import (
    validate_anthropic_key,
    validate_github_key,
    validate_fly_key,
    is_mock_mode,
)


class TestKeyValidation:
    """Test API key validation functionality"""

    def test_mock_mode_enabled(self):
        """Verify that MOCK_MODE is enabled for tests"""
        assert is_mock_mode() is True
        assert os.environ.get("MOCK_MODE", "false").lower() == "true"

    def test_anthropic_key_validation_mock_mode(self):
        """Test Anthropic key validation in MOCK_MODE"""
        # Valid keys should pass
        assert validate_anthropic_key("valid-anthropic-key") is True
        assert validate_anthropic_key("sk-ant-api03-1234567890abcdef") is True
        assert validate_anthropic_key("any-non-empty-string") is True

        # Empty/None keys should fail
        assert validate_anthropic_key("") is False
        assert validate_anthropic_key("   ") is False
        assert validate_anthropic_key(None) is False

    def test_github_key_validation_mock_mode(self):
        """Test GitHub key validation in MOCK_MODE"""
        # Valid keys should pass
        assert validate_github_key("valid-github-token") is True
        assert validate_github_key("ghp_1234567890abcdef") is True
        assert validate_github_key("github_pat_1234567890abcdef") is True
        assert validate_github_key("any-non-empty-string") is True

        # Empty/None keys should fail
        assert validate_github_key("") is False
        assert validate_github_key("   ") is False
        assert validate_github_key(None) is False

    def test_fly_key_validation_mock_mode(self):
        """Test Fly.io key validation in MOCK_MODE"""
        # Valid keys should pass
        assert validate_fly_key("valid-fly-token") is True
        assert validate_fly_key("fo1_1234567890abcdef") is True
        assert validate_fly_key("fm1_1234567890abcdef") is True
        assert validate_fly_key("any-non-empty-string") is True

        # Empty/None keys should fail
        assert validate_fly_key("") is False
        assert validate_fly_key("   ") is False
        assert validate_fly_key(None) is False

    @patch.dict(os.environ, {"MOCK_MODE": "false"})
    def test_anthropic_key_validation_real_mode_mock_request(self):
        """Test Anthropic key validation in real mode with mocked requests"""
        # Import after patching environment
        import importlib
        import keys

        importlib.reload(keys)

        with patch("keys.requests.post") as mock_post:
            # Mock successful response
            mock_response = type(
                "MockResponse", (), {"status_code": 200, "text": "Success"}
            )()
            mock_post.return_value = mock_response

            result = keys.validate_anthropic_key("test-key")
            assert result is True

            # Verify the request was made with correct parameters
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "https://api.anthropic.com/v1/messages" in call_args[0]
            assert "x-api-key" in call_args[1]["headers"]
            assert call_args[1]["headers"]["x-api-key"] == "test-key"

    @patch.dict(os.environ, {"MOCK_MODE": "false"})
    def test_github_key_validation_real_mode_mock_request(self):
        """Test GitHub key validation in real mode with mocked requests"""
        # Import after patching environment
        import importlib
        import keys

        importlib.reload(keys)

        with patch("keys.requests.get") as mock_get:
            # Mock successful response
            mock_response = type(
                "MockResponse", (), {"status_code": 200, "text": "Success"}
            )()
            mock_get.return_value = mock_response

            result = keys.validate_github_key("test-token")
            assert result is True

            # Verify the request was made with correct parameters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "https://api.github.com/user" in call_args[0]
            assert "Authorization" in call_args[1]["headers"]
            assert call_args[1]["headers"]["Authorization"] == "token test-token"

    @patch.dict(os.environ, {"MOCK_MODE": "false"})
    def test_fly_key_validation_real_mode_mock_request(self):
        """Test Fly.io key validation in real mode with mocked requests"""
        # Import after patching environment
        import importlib
        import keys

        importlib.reload(keys)

        with patch("keys.requests.get") as mock_get:
            # Mock successful response
            mock_response = type(
                "MockResponse", (), {"status_code": 200, "text": "Success"}
            )()
            mock_get.return_value = mock_response

            result = keys.validate_fly_key("fo1_test-token-1234567890")
            assert result is True

            # Verify the request was made with correct parameters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "https://api.machines.dev/v1/apps" in call_args[0]
            assert "Authorization" in call_args[1]["headers"]
            expected_auth = "FlyV1 fo1_test-token-1234567890"
            assert call_args[1]["headers"]["Authorization"] == expected_auth

    def test_key_validation_error_handling(self):
        """Test key validation handles various error conditions"""
        # Test with different types of invalid input
        invalid_inputs = [None, "", "   ", "\t\n", False, 0, []]

        for invalid_input in invalid_inputs:
            # All validation functions should handle invalid input gracefully
            try:
                result = validate_anthropic_key(invalid_input)
                assert result is False, f"Expected False for input: {invalid_input}"
            except Exception as e:
                pytest.fail(
                    f"validate_anthropic_key raised exception for {invalid_input}: {e}"
                )

            try:
                result = validate_github_key(invalid_input)
                assert result is False, f"Expected False for input: {invalid_input}"
            except Exception as e:
                pytest.fail(
                    f"validate_github_key raised exception for {invalid_input}: {e}"
                )

            try:
                result = validate_fly_key(invalid_input)
                assert result is False, f"Expected False for input: {invalid_input}"
            except Exception as e:
                pytest.fail(
                    f"validate_fly_key raised exception for {invalid_input}: {e}"
                )

    def test_mock_mode_logging(self, caplog):
        """Test that MOCK_MODE validation includes appropriate logging"""
        with caplog.at_level("INFO"):
            validate_anthropic_key("test-key")
            validate_github_key("test-key")
            validate_fly_key("test-key")

        # Check that mock mode logging is present
        log_messages = [record.message for record in caplog.records]
        mock_messages = [msg for msg in log_messages if "MOCK_MODE" in msg]

        assert len(mock_messages) >= 3, "Expected at least 3 MOCK_MODE log messages"

        # Check specific providers are mentioned
        anthropic_logs = [msg for msg in mock_messages if "Anthropic" in msg]
        github_logs = [msg for msg in mock_messages if "GitHub" in msg]
        fly_logs = [msg for msg in mock_messages if "Fly.io" in msg]

        assert len(anthropic_logs) >= 1, "Expected Anthropic MOCK_MODE log"
        assert len(github_logs) >= 1, "Expected GitHub MOCK_MODE log"
        assert len(fly_logs) >= 1, "Expected Fly.io MOCK_MODE log"

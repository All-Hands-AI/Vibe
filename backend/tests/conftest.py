"""
Pytest configuration and fixtures for e2e tests.
Sets up test environment with MOCK_MODE enabled.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
import requests


@pytest.fixture(scope="session", autouse=True)
def setup_mock_mode():
    """Enable MOCK_MODE for all tests in this session"""
    os.environ["MOCK_MODE"] = "true"
    yield
    # Cleanup after all tests
    if "MOCK_MODE" in os.environ:
        del os.environ["MOCK_MODE"]


@pytest.fixture(autouse=True)
def mock_requests(monkeypatch):
    """Mock all requests for external APIs"""
    from mocks import get_mock_response
    
    def mock_get(url, **kwargs):
        return get_mock_response("GET", url, **kwargs)
    
    def mock_post(url, **kwargs):
        return get_mock_response("POST", url, **kwargs)
    
    def mock_delete(url, **kwargs):
        return get_mock_response("DELETE", url, **kwargs)
    
    def mock_put(url, **kwargs):
        return get_mock_response("PUT", url, **kwargs)
    
    # Patch requests methods
    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr(requests, "post", mock_post)
    monkeypatch.setattr(requests, "delete", mock_delete)
    monkeypatch.setattr(requests, "put", mock_put)


@pytest.fixture(scope="function")
def temp_data_dir():
    """Create a temporary data directory for each test"""
    temp_dir = tempfile.mkdtemp()
    original_data_dir = os.environ.get("DATA_DIR")
    
    # Set the temporary directory as the data directory
    os.environ["DATA_DIR"] = temp_dir
    
    # Create the data directory structure
    data_path = Path(temp_dir)
    data_path.mkdir(exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    if original_data_dir:
        os.environ["DATA_DIR"] = original_data_dir
    elif "DATA_DIR" in os.environ:
        del os.environ["DATA_DIR"]


@pytest.fixture
def client(temp_data_dir):
    """Create a test client for the Flask application with temporary data directory"""
    # Import app after mocking is set up
    from app import app
    
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def sample_user_uuid():
    """Provide a sample user UUID for testing"""
    return "test-user-12345678-1234-1234-1234-123456789abc"


@pytest.fixture
def sample_headers(sample_user_uuid):
    """Provide sample headers with user UUID"""
    return {
        "X-User-UUID": sample_user_uuid,
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_api_keys():
    """Provide mock API keys for testing"""
    return {
        "anthropic": "mock-anthropic-key-12345",
        "github": "mock-github-token-67890",
        "fly": "mock-fly-token-abcdef"
    }


@pytest.fixture
def sample_app_data():
    """Provide sample app data for testing"""
    return {
        "name": "Test App",
        "slug": "test-app",
        "description": "A test application",
        "github_url": "https://github.com/testuser/test-app",
        "fly_app_name": "test-app-fly"
    }


@pytest.fixture
def sample_riff_data():
    """Provide sample riff data for testing"""
    return {
        "name": "Test Riff",
        "slug": "test-riff",
        "description": "A test riff"
    }
"""
Tests for the storage classes.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from storage import KeysStorage, AppsStorage, RiffsStorage
from storage import get_keys_storage, get_apps_storage, get_riffs_storage


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing"""
    temp_dir = tempfile.mkdtemp()
    with patch("storage.base_storage.DATA_DIR", Path(temp_dir)):
        yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_uuid():
    """Test user UUID"""
    return "test-user-12345"


class TestKeysStorage:
    """Test KeysStorage class"""

    def test_save_and_load_keys(self, temp_data_dir, test_uuid):
        """Test saving and loading keys"""
        storage = KeysStorage(test_uuid)
        test_keys = {"github": "test-token", "anthropic": "test-key"}

        # Save keys
        assert storage.save_keys(test_keys) is True

        # Load keys
        loaded_keys = storage.load_keys()
        assert loaded_keys == test_keys

    def test_has_keys(self, temp_data_dir, test_uuid):
        """Test checking if user has keys"""
        storage = KeysStorage(test_uuid)

        # Initially no keys
        assert storage.has_keys() is False

        # After saving keys
        storage.save_keys({"github": "test-token"})
        assert storage.has_keys() is True

    def test_get_set_key(self, temp_data_dir, test_uuid):
        """Test getting and setting individual keys"""
        storage = KeysStorage(test_uuid)

        # Set a key
        assert storage.set_key("github", "test-token") is True

        # Get the key
        assert storage.get_key("github") == "test-token"
        assert storage.get_key("nonexistent") is None

    def test_remove_key(self, temp_data_dir, test_uuid):
        """Test removing a key"""
        storage = KeysStorage(test_uuid)

        # Set keys
        storage.save_keys({"github": "test-token", "anthropic": "test-key"})

        # Remove one key
        assert storage.remove_key("github") is True

        # Check remaining keys
        keys = storage.load_keys()
        assert keys == {"anthropic": "test-key"}


class TestAppsStorage:
    """Test AppsStorage class"""

    def test_save_and_load_app(self, temp_data_dir, test_uuid):
        """Test saving and loading an app"""
        storage = AppsStorage(test_uuid)
        test_app = {
            "name": "Test App",
            "slug": "test-app",
            "created_at": "2025-09-13T19:00:00",
        }

        # Save app
        assert storage.save_app("test-app", test_app) is True

        # Load app
        loaded_app = storage.load_app("test-app")
        assert loaded_app == test_app

    def test_app_exists(self, temp_data_dir, test_uuid):
        """Test checking if app exists"""
        storage = AppsStorage(test_uuid)

        # Initially no app
        assert storage.app_exists("test-app") is False

        # After saving app
        test_app = {"name": "Test App", "slug": "test-app"}
        storage.save_app("test-app", test_app)
        assert storage.app_exists("test-app") is True

    def test_list_apps(self, temp_data_dir, test_uuid):
        """Test listing apps"""
        storage = AppsStorage(test_uuid)

        # Initially empty
        assert storage.list_apps() == []

        # Add apps
        app1 = {"name": "App 1", "slug": "app-1"}
        app2 = {"name": "App 2", "slug": "app-2"}
        storage.save_app("app-1", app1)
        storage.save_app("app-2", app2)

        # List apps
        apps = storage.list_apps()
        assert len(apps) == 2
        assert app1 in apps
        assert app2 in apps

    def test_delete_app(self, temp_data_dir, test_uuid):
        """Test deleting an app"""
        storage = AppsStorage(test_uuid)

        # Save app
        test_app = {"name": "Test App", "slug": "test-app"}
        storage.save_app("test-app", test_app)
        assert storage.app_exists("test-app") is True

        # Delete app
        assert storage.delete_app("test-app") is True
        assert storage.app_exists("test-app") is False


class TestRiffsStorage:
    """Test RiffsStorage class"""

    def test_save_and_load_riff(self, temp_data_dir, test_uuid):
        """Test saving and loading a riff"""
        storage = RiffsStorage(test_uuid)
        test_riff = {
            "name": "Test Riff",
            "slug": "test-riff",
            "app_slug": "test-app",
            "created_at": "2025-09-13T19:00:00",
        }

        # Save riff
        assert storage.save_riff("test-app", "test-riff", test_riff) is True

        # Load riff
        loaded_riff = storage.load_riff("test-app", "test-riff")
        assert loaded_riff == test_riff

    def test_riff_exists(self, temp_data_dir, test_uuid):
        """Test checking if riff exists"""
        storage = RiffsStorage(test_uuid)

        # Initially no riff
        assert storage.riff_exists("test-app", "test-riff") is False

        # After saving riff
        test_riff = {"name": "Test Riff", "slug": "test-riff"}
        storage.save_riff("test-app", "test-riff", test_riff)
        assert storage.riff_exists("test-app", "test-riff") is True

    def test_list_riffs(self, temp_data_dir, test_uuid):
        """Test listing riffs for an app"""
        storage = RiffsStorage(test_uuid)

        # Initially empty
        assert storage.list_riffs("test-app") == []

        # Add riffs
        riff1 = {"name": "Riff 1", "slug": "riff-1", "app_slug": "test-app"}
        riff2 = {"name": "Riff 2", "slug": "riff-2", "app_slug": "test-app"}
        storage.save_riff("test-app", "riff-1", riff1)
        storage.save_riff("test-app", "riff-2", riff2)

        # List riffs
        riffs = storage.list_riffs("test-app")
        assert len(riffs) == 2
        assert riff1 in riffs
        assert riff2 in riffs

    def test_delete_riff(self, temp_data_dir, test_uuid):
        """Test deleting a riff"""
        storage = RiffsStorage(test_uuid)

        # Save riff
        test_riff = {"name": "Test Riff", "slug": "test-riff"}
        storage.save_riff("test-app", "test-riff", test_riff)
        assert storage.riff_exists("test-app", "test-riff") is True

        # Delete riff
        assert storage.delete_riff("test-app", "test-riff") is True
        assert storage.riff_exists("test-app", "test-riff") is False


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_get_storage_functions(self, temp_data_dir, test_uuid):
        """Test convenience functions return correct storage instances"""
        keys_storage = get_keys_storage(test_uuid)
        apps_storage = get_apps_storage(test_uuid)
        riffs_storage = get_riffs_storage(test_uuid)

        assert isinstance(keys_storage, KeysStorage)
        assert isinstance(apps_storage, AppsStorage)
        assert isinstance(riffs_storage, RiffsStorage)

        assert keys_storage.user_uuid == test_uuid
        assert apps_storage.user_uuid == test_uuid
        assert riffs_storage.user_uuid == test_uuid
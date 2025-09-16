"""
Storage package for openvibe backend.
Provides user-specific file-based storage for keys, apps, and riffs.
"""

from .base_storage import BaseStorage
from .keys_storage import KeysStorage
from .apps_storage import AppsStorage
from .riffs_storage import RiffsStorage


# Convenience functions for backward compatibility and easy access
def get_keys_storage(user_uuid: str) -> KeysStorage:
    """Get KeysStorage instance for user"""
    return KeysStorage(user_uuid)


def get_apps_storage(user_uuid: str) -> AppsStorage:
    """Get AppsStorage instance for user"""
    return AppsStorage(user_uuid)


def get_riffs_storage(user_uuid: str) -> RiffsStorage:
    """Get RiffsStorage instance for user"""
    return RiffsStorage(user_uuid)


__all__ = [
    "BaseStorage",
    "KeysStorage",
    "AppsStorage",
    "RiffsStorage",
    "get_keys_storage",
    "get_apps_storage",
    "get_riffs_storage",
]

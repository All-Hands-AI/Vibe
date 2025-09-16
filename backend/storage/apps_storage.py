"""
Apps storage class for openvibe backend.
Handles user app data storage and management.
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_storage import BaseStorage

logger = logging.getLogger(__name__)


class AppsStorage(BaseStorage):
    """Storage class for user apps"""

    def get_app_dir_path(self, app_slug: str) -> Path:
        """Get path to app directory"""
        return self.user_dir / "apps" / app_slug

    def get_app_file_path(self, app_slug: str) -> Path:
        """Get path to app.json file"""
        return self.get_app_dir_path(app_slug) / "app.json"

    def load_app(self, app_slug: str) -> Optional[Dict[str, Any]]:
        """Load specific app data"""
        logger.info(f"📱 Loading app: {app_slug} for user {self.user_uuid[:8]}...")

        app_file = self.get_app_file_path(app_slug)
        data = self.read_json_file(app_file)

        if data is None:
            logger.debug(f"📱 App not found: {app_slug}")
            return None

        if not isinstance(data, dict):
            logger.error(f"❌ Invalid app data format for {app_slug}")
            return None

        logger.info(f"📱 Successfully loaded app: {app_slug}")
        return data

    def save_app(self, app_slug: str, app_data: Dict[str, Any]) -> bool:
        """Save app data"""
        logger.info(f"💾 Saving app: {app_slug} for user {self.user_uuid[:8]}...")

        app_file = self.get_app_file_path(app_slug)
        success = self.write_json_file(app_file, app_data)

        if success:
            logger.info(f"✅ App saved successfully: {app_slug}")
        else:
            logger.error(f"❌ Failed to save app: {app_slug}")

        return success

    def list_apps(self) -> List[Dict[str, Any]]:
        """List all apps for user"""
        logger.info(f"📋 Listing apps for user {self.user_uuid[:8]}...")

        apps_dir = self.user_dir / "apps"
        if not apps_dir.exists():
            logger.debug(
                f"📋 Apps directory doesn't exist for user {self.user_uuid[:8]}"
            )
            return []

        apps = []
        try:
            for app_dir in apps_dir.iterdir():
                if app_dir.is_dir():
                    app_file = app_dir / "app.json"
                    if app_file.exists():
                        app_data = self.read_json_file(app_file)
                        if app_data and isinstance(app_data, dict):
                            apps.append(app_data)
                        else:
                            logger.warning(f"⚠️ Invalid app data in {app_file}")
                    else:
                        logger.debug(f"📋 No app.json found in {app_dir}")
        except Exception as e:
            logger.error(f"❌ Error listing apps: {e}")
            return []

        logger.info(f"📋 Found {len(apps)} apps for user {self.user_uuid[:8]}")
        return apps

    def app_exists(self, app_slug: str) -> bool:
        """Check if app exists"""
        app_file = self.get_app_file_path(app_slug)
        return app_file.exists()

    def delete_app(self, app_slug: str) -> bool:
        """Delete app and all its data"""
        logger.info(f"🗑️ Deleting app: {app_slug} for user {self.user_uuid[:8]}...")

        app_dir = self.get_app_dir_path(app_slug)
        if not app_dir.exists():
            logger.debug(f"🗑️ App directory doesn't exist: {app_slug}")
            return True  # Already deleted

        try:
            shutil.rmtree(app_dir)
            logger.info(f"✅ App deleted successfully: {app_slug}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete app {app_slug}: {e}")
            return False

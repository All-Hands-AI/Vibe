"""
Riffs storage class for OpenVibe backend.
Handles user riff (conversation) data storage and management.
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_storage import BaseStorage

logger = logging.getLogger(__name__)


class RiffsStorage(BaseStorage):
    """Storage class for app riffs (conversations)"""

    def get_riff_dir_path(self, app_slug: str, riff_slug: str) -> Path:
        """Get path to riff directory"""
        return self.user_dir / "apps" / app_slug / "riffs" / riff_slug

    def get_riff_file_path(self, app_slug: str, riff_slug: str) -> Path:
        """Get path to riff.json file"""
        return self.get_riff_dir_path(app_slug, riff_slug) / "riff.json"

    def load_riff(self, app_slug: str, riff_slug: str) -> Optional[Dict[str, Any]]:
        """Load specific riff data"""
        logger.info(
            f"💬 Loading riff: {app_slug}/{riff_slug} for user {self.user_uuid[:8]}..."
        )

        riff_file = self.get_riff_file_path(app_slug, riff_slug)
        data = self.read_json_file(riff_file)

        if data is None:
            logger.debug(f"💬 Riff not found: {app_slug}/{riff_slug}")
            return None

        if not isinstance(data, dict):
            logger.error(f"❌ Invalid riff data format for {app_slug}/{riff_slug}")
            return None

        logger.info(f"💬 Successfully loaded riff: {app_slug}/{riff_slug}")
        return data

    def save_riff(
        self, app_slug: str, riff_slug: str, riff_data: Dict[str, Any]
    ) -> bool:
        """Save riff data"""
        logger.info(
            f"💾 Saving riff: {app_slug}/{riff_slug} for user {self.user_uuid[:8]}..."
        )

        riff_file = self.get_riff_file_path(app_slug, riff_slug)
        success = self.write_json_file(riff_file, riff_data)

        if success:
            logger.info(f"✅ Riff saved successfully: {app_slug}/{riff_slug}")
        else:
            logger.error(f"❌ Failed to save riff: {app_slug}/{riff_slug}")

        return success

    def list_riffs(self, app_slug: str) -> List[Dict[str, Any]]:
        """List all riffs for an app"""
        logger.info(
            f"📋 Listing riffs for app: {app_slug} for user {self.user_uuid[:8]}..."
        )

        riffs_dir = self.user_dir / "apps" / app_slug / "riffs"
        if not riffs_dir.exists():
            logger.debug(f"📋 Riffs directory doesn't exist for app: {app_slug}")
            return []

        riffs = []
        try:
            for riff_dir in riffs_dir.iterdir():
                if riff_dir.is_dir():
                    riff_file = riff_dir / "riff.json"
                    if riff_file.exists():
                        riff_data = self.read_json_file(riff_file)
                        if riff_data and isinstance(riff_data, dict):
                            riffs.append(riff_data)
                        else:
                            logger.warning(f"⚠️ Invalid riff data in {riff_file}")
                    else:
                        logger.debug(f"📋 No riff.json found in {riff_dir}")
        except Exception as e:
            logger.error(f"❌ Error listing riffs for app {app_slug}: {e}")
            return []

        logger.info(f"📋 Found {len(riffs)} riffs for app: {app_slug}")
        return riffs

    def riff_exists(self, app_slug: str, riff_slug: str) -> bool:
        """Check if riff exists"""
        riff_file = self.get_riff_file_path(app_slug, riff_slug)
        return riff_file.exists()

    def delete_riff(self, app_slug: str, riff_slug: str) -> bool:
        """Delete riff and all its data"""
        logger.info(
            f"🗑️ Deleting riff: {app_slug}/{riff_slug} for user {self.user_uuid[:8]}..."
        )

        riff_dir = self.get_riff_dir_path(app_slug, riff_slug)
        if not riff_dir.exists():
            logger.debug(f"🗑️ Riff directory doesn't exist: {app_slug}/{riff_slug}")
            return True  # Already deleted

        try:
            shutil.rmtree(riff_dir)
            logger.info(f"✅ Riff deleted successfully: {app_slug}/{riff_slug}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete riff {app_slug}/{riff_slug}: {e}")
            return False

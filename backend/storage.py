"""
Storage classes for OpenVibe backend.
Handles file-based JSON storage for keys, apps, and riffs with user-specific directory structure.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import shutil

logger = logging.getLogger(__name__)

# Base data directory
DATA_DIR = Path('/data')


class BaseStorage:
    """Base storage class with common file operations"""
    
    def __init__(self, user_uuid: str):
        self.user_uuid = user_uuid
        self.user_dir = DATA_DIR / user_uuid
        
    def ensure_directory(self, path: Path) -> bool:
        """Ensure directory exists"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Directory ensured: {path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create directory {path}: {e}")
            return False
    
    def read_json_file(self, file_path: Path) -> Optional[Any]:
        """Read JSON data from file"""
        logger.debug(f"📖 Reading JSON file: {file_path}")
        
        if not file_path.exists():
            logger.debug(f"📖 File doesn't exist: {file_path}")
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.debug(f"📖 File content length: {len(content)} characters")
                
                if not content.strip():
                    logger.debug(f"📖 Empty file: {file_path}")
                    return None
                    
                data = json.loads(content)
                logger.debug(f"📖 Successfully loaded JSON from: {file_path}")
                return data
                
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Failed to read JSON file {file_path}: {e}")
            return None
    
    def write_json_file(self, file_path: Path, data: Any, create_backup: bool = True) -> bool:
        """Write JSON data to file with atomic operation"""
        logger.debug(f"💾 Writing JSON file: {file_path}")
        
        # Ensure parent directory exists
        if not self.ensure_directory(file_path.parent):
            return False
        
        try:
            # Create backup if file exists and backup is requested
            if create_backup and file_path.exists():
                backup_file = file_path.with_suffix('.json.backup')
                logger.debug(f"💾 Creating backup: {backup_file}")
                shutil.copy2(file_path, backup_file)
            
            # Write to temporary file first for atomic operation
            temp_file = file_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_file.replace(file_path)
            
            logger.debug(f"💾 Successfully wrote JSON to: {file_path}")
            logger.debug(f"💾 File size: {file_path.stat().st_size} bytes")
            return True
            
        except (IOError, OSError) as e:
            logger.error(f"❌ Failed to write JSON file {file_path}: {e}")
            # Clean up temp file if it exists
            temp_file = file_path.with_suffix('.tmp')
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
            return False


class KeysStorage(BaseStorage):
    """Storage class for user API keys"""
    
    def get_keys_file_path(self) -> Path:
        """Get path to user's keys.json file"""
        return self.user_dir / 'keys.json'
    
    def load_keys(self) -> Dict[str, str]:
        """Load user's API keys"""
        logger.info(f"🔑 Loading keys for user {self.user_uuid[:8]}...")
        
        keys_file = self.get_keys_file_path()
        data = self.read_json_file(keys_file)
        
        if data is None:
            logger.debug(f"🔑 No keys found for user {self.user_uuid[:8]}")
            return {}
        
        if not isinstance(data, dict):
            logger.error(f"❌ Invalid keys data format for user {self.user_uuid[:8]}")
            return {}
        
        logger.info(f"🔑 Successfully loaded keys for providers: {list(data.keys())}")
        return data
    
    def save_keys(self, keys: Dict[str, str]) -> bool:
        """Save user's API keys"""
        logger.info(f"💾 Saving keys for user {self.user_uuid[:8]}...")
        logger.debug(f"💾 Providers: {list(keys.keys())}")
        
        keys_file = self.get_keys_file_path()
        success = self.write_json_file(keys_file, keys)
        
        if success:
            logger.info(f"✅ Keys saved successfully for user {self.user_uuid[:8]}")
        else:
            logger.error(f"❌ Failed to save keys for user {self.user_uuid[:8]}")
        
        return success
    
    def has_keys(self) -> bool:
        """Check if user has any keys stored"""
        keys_file = self.get_keys_file_path()
        return keys_file.exists()
    
    def get_key(self, provider: str) -> Optional[str]:
        """Get API key for specific provider"""
        keys = self.load_keys()
        return keys.get(provider)
    
    def set_key(self, provider: str, api_key: str) -> bool:
        """Set API key for specific provider"""
        keys = self.load_keys()
        keys[provider] = api_key
        return self.save_keys(keys)
    
    def remove_key(self, provider: str) -> bool:
        """Remove API key for specific provider"""
        keys = self.load_keys()
        if provider in keys:
            del keys[provider]
            return self.save_keys(keys)
        return True  # Key doesn't exist, consider it removed


class AppsStorage(BaseStorage):
    """Storage class for user apps"""
    
    def get_app_dir_path(self, app_slug: str) -> Path:
        """Get path to app directory"""
        return self.user_dir / 'apps' / app_slug
    
    def get_app_file_path(self, app_slug: str) -> Path:
        """Get path to app.json file"""
        return self.get_app_dir_path(app_slug) / 'app.json'
    
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
        
        apps_dir = self.user_dir / 'apps'
        if not apps_dir.exists():
            logger.debug(f"📋 Apps directory doesn't exist for user {self.user_uuid[:8]}")
            return []
        
        apps = []
        try:
            for app_dir in apps_dir.iterdir():
                if app_dir.is_dir():
                    app_file = app_dir / 'app.json'
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


class RiffsStorage(BaseStorage):
    """Storage class for app riffs (conversations)"""
    
    def get_riff_dir_path(self, app_slug: str, riff_slug: str) -> Path:
        """Get path to riff directory"""
        return self.user_dir / 'apps' / app_slug / 'riffs' / riff_slug
    
    def get_riff_file_path(self, app_slug: str, riff_slug: str) -> Path:
        """Get path to riff.json file"""
        return self.get_riff_dir_path(app_slug, riff_slug) / 'riff.json'
    
    def load_riff(self, app_slug: str, riff_slug: str) -> Optional[Dict[str, Any]]:
        """Load specific riff data"""
        logger.info(f"💬 Loading riff: {app_slug}/{riff_slug} for user {self.user_uuid[:8]}...")
        
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
    
    def save_riff(self, app_slug: str, riff_slug: str, riff_data: Dict[str, Any]) -> bool:
        """Save riff data"""
        logger.info(f"💾 Saving riff: {app_slug}/{riff_slug} for user {self.user_uuid[:8]}...")
        
        riff_file = self.get_riff_file_path(app_slug, riff_slug)
        success = self.write_json_file(riff_file, riff_data)
        
        if success:
            logger.info(f"✅ Riff saved successfully: {app_slug}/{riff_slug}")
        else:
            logger.error(f"❌ Failed to save riff: {app_slug}/{riff_slug}")
        
        return success
    
    def list_riffs(self, app_slug: str) -> List[Dict[str, Any]]:
        """List all riffs for an app"""
        logger.info(f"📋 Listing riffs for app: {app_slug} for user {self.user_uuid[:8]}...")
        
        riffs_dir = self.user_dir / 'apps' / app_slug / 'riffs'
        if not riffs_dir.exists():
            logger.debug(f"📋 Riffs directory doesn't exist for app: {app_slug}")
            return []
        
        riffs = []
        try:
            for riff_dir in riffs_dir.iterdir():
                if riff_dir.is_dir():
                    riff_file = riff_dir / 'riff.json'
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
        logger.info(f"🗑️ Deleting riff: {app_slug}/{riff_slug} for user {self.user_uuid[:8]}...")
        
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
"""
Keys storage class for OpenVibe backend.
Handles user API key storage and management.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from .base_storage import BaseStorage

logger = logging.getLogger(__name__)


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
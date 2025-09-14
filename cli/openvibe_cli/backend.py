"""Direct backend interface for OpenVibe CLI.

This module provides direct access to OpenVibe backend functionality
without requiring a running server. It imports and uses the backend
modules directly for better performance and reliability.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import backend modules from local copy
from openvibe_cli.backend_modules.storage.apps_storage import AppsStorage
from openvibe_cli.backend_modules.storage.riffs_storage import RiffsStorage
from openvibe_cli.backend_modules.storage.keys_storage import KeysStorage
from openvibe_cli.backend_modules.agent_loop import AgentLoopManager

from openvibe_cli.config import Config

logger = logging.getLogger(__name__)


class OpenVibeBackend:
    """Direct backend interface for CLI operations."""
    
    def __init__(self, config: Config):
        """Initialize backend with CLI configuration."""
        self.config = config
        self.user_uuid = config.user_uuid
        
        # Set up data directory
        self.data_dir = Path.home() / ".openvibe" / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Set environment variable for backend storage
        os.environ["DATA_DIR"] = str(self.data_dir)
        
        # Initialize storage classes
        self.apps_storage = AppsStorage(self.user_uuid)
        self.riffs_storage = RiffsStorage(self.user_uuid)
        self.keys_storage = KeysStorage(self.user_uuid)
        
        # Initialize agent loop manager
        self.agent_manager = None
    
    def _ensure_agent_manager(self):
        """Lazy initialization of agent manager."""
        if self.agent_manager is None:
            self.agent_manager = AgentLoopManager()
    
    # Apps Management
    def list_apps(self) -> List[Dict[str, Any]]:
        """List all user apps."""
        try:
            apps = self.apps_storage.list_apps()
            return apps
        except Exception as e:
            logger.error(f"Failed to list apps: {e}")
            return []
    
    def get_app(self, app_slug: str) -> Optional[Dict[str, Any]]:
        """Get specific app details."""
        try:
            app = self.apps_storage.load_app(app_slug)
            if app:
                # Add deployment status (simplified for CLI)
                app["deployment_status"] = {
                    "github_status": "unknown",
                    "fly_status": "unknown",
                    "pr_status": "none"
                }
            return app
        except Exception as e:
            logger.error(f"Failed to get app {app_slug}: {e}")
            return None
    
    def create_app(self, name: str, slug: str) -> Dict[str, Any]:
        """Create a new app."""
        try:
            # Create app data structure
            app_data = {
                "name": name,
                "slug": slug,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "github_repo": f"https://github.com/mockuser/{slug}",  # Mock for CLI
                "fly_app_name": slug,
                "status": "active"
            }
            
            # Save app
            self.apps_storage.save_app(slug, app_data)
            
            logger.info(f"✅ App created successfully: {name}")
            return app_data
            
        except Exception as e:
            logger.error(f"Failed to create app {name}: {e}")
            raise
    
    def delete_app(self, app_slug: str) -> bool:
        """Delete an app."""
        try:
            success = self.apps_storage.delete_app(app_slug)
            if success:
                logger.info(f"✅ App deleted successfully: {app_slug}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete app {app_slug}: {e}")
            return False
    
    # Riffs Management
    def list_riffs(self, app_slug: str) -> List[Dict[str, Any]]:
        """List riffs for an app."""
        try:
            riffs = self.riffs_storage.list_riffs(app_slug)
            return riffs
        except Exception as e:
            logger.error(f"Failed to list riffs for {app_slug}: {e}")
            return []
    
    def get_riff(self, app_slug: str, riff_slug: str) -> Optional[Dict[str, Any]]:
        """Get specific riff details."""
        try:
            riff = self.riffs_storage.load_riff(app_slug, riff_slug)
            return riff
        except Exception as e:
            logger.error(f"Failed to get riff {app_slug}/{riff_slug}: {e}")
            return None
    
    def create_riff(self, app_slug: str, name: str, slug: str) -> Dict[str, Any]:
        """Create a new riff."""
        try:
            # Create riff data structure
            riff_data = {
                "name": name,
                "slug": slug,
                "app_slug": app_slug,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "status": "active",
                "agent_status": "idle"
            }
            
            # Save riff
            self.riffs_storage.save_riff(app_slug, slug, riff_data)
            
            logger.info(f"✅ Riff created successfully: {name}")
            return riff_data
            
        except Exception as e:
            logger.error(f"Failed to create riff {name}: {e}")
            raise
    
    # Messages and Chat
    def get_messages(self, app_slug: str, riff_slug: str) -> List[Dict[str, Any]]:
        """Get messages for a riff."""
        try:
            # Load riff to get messages
            riff = self.riffs_storage.load_riff(app_slug, riff_slug)
            if riff and "messages" in riff:
                return riff["messages"]
            return []
        except Exception as e:
            logger.error(f"Failed to get messages for {app_slug}/{riff_slug}: {e}")
            return []
    
    def send_message(self, app_slug: str, riff_slug: str, content: str) -> Dict[str, Any]:
        """Send a message to a riff."""
        try:
            # Create message
            message = {
                "id": f"msg_{datetime.utcnow().timestamp()}",
                "content": content,
                "role": "user",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            # Load riff
            riff = self.riffs_storage.load_riff(app_slug, riff_slug)
            if not riff:
                raise ValueError(f"Riff {riff_slug} not found")
            
            # Add message to riff
            if "messages" not in riff:
                riff["messages"] = []
            riff["messages"].append(message)
            
            # Save updated riff
            self.riffs_storage.save_riff(app_slug, riff_slug, riff)
            
            # TODO: Integrate with agent loop for responses
            # For now, just return the user message
            logger.info(f"✅ Message sent to {app_slug}/{riff_slug}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to send message to {app_slug}/{riff_slug}: {e}")
            raise
    
    # Integration Management
    def get_integration_status(self, provider: str) -> Dict[str, Any]:
        """Get integration status for a provider."""
        try:
            keys = self.keys_storage.load_keys()
            provider_key = f"{provider}_token" if provider == "github" else f"{provider}_api_key"
            
            has_key = provider_key in keys and keys[provider_key]
            
            return {
                "provider": provider,
                "valid": has_key,
                "configured": has_key
            }
        except Exception as e:
            logger.error(f"Failed to get integration status for {provider}: {e}")
            return {"provider": provider, "valid": False, "configured": False}
    
    def set_integration_key(self, provider: str, key: str) -> bool:
        """Set integration key for a provider."""
        try:
            keys = self.keys_storage.load_keys()
            
            # Map provider to key name
            key_mapping = {
                "github": "github_token",
                "fly": "fly_api_token", 
                "anthropic": "anthropic_api_key"
            }
            
            if provider not in key_mapping:
                raise ValueError(f"Unknown provider: {provider}")
            
            key_name = key_mapping[provider]
            keys[key_name] = key
            
            # Save keys
            self.keys_storage.save_keys(keys)
            
            logger.info(f"✅ {provider} key set successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set {provider} key: {e}")
            return False
    
    def setup_mock_keys(self) -> bool:
        """Set up mock API keys for testing."""
        try:
            mock_keys = {
                "github_token": "mock_github_token_12345",
                "fly_api_token": "mock_fly_token_67890", 
                "anthropic_api_key": "mock_anthropic_key_abcdef"
            }
            
            self.keys_storage.save_keys(mock_keys)
            logger.info("✅ Mock API keys set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up mock keys: {e}")
            return False


def get_backend() -> OpenVibeBackend:
    """Get backend instance with current configuration."""
    config = Config.load()
    return OpenVibeBackend(config)
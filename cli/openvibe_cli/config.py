"""Configuration management for OpenVibe CLI."""

import json
import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class Config(BaseModel):
    """Configuration model for OpenVibe CLI."""
    
    user_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    backend_url: str = Field(default="http://localhost:8000")
    github_token: Optional[str] = None
    fly_token: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    @classmethod
    def get_config_path(cls) -> Path:
        """Get the path to the configuration file."""
        config_dir = Path.home() / '.openvibe'
        config_dir.mkdir(exist_ok=True)
        return config_dir / 'config.json'
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from file or create default."""
        config_path = cls.get_config_path()
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                return cls(**data)
            except (json.JSONDecodeError, Exception):
                # If config is corrupted, create new one
                pass
        
        # Create new config with defaults
        config = cls()
        config.save()
        return config
    
    def save(self) -> None:
        """Save configuration to file."""
        config_path = self.get_config_path()
        
        with open(config_path, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)
    
    def update(self, **kwargs) -> None:
        """Update configuration values and save."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
    
    def is_setup_complete(self) -> bool:
        """Check if basic setup is complete."""
        # At minimum, we need a user UUID (which is auto-generated)
        # Additional setup might require API keys depending on usage
        return bool(self.user_uuid)
    
    def get_missing_setup(self) -> Dict[str, str]:
        """Get dictionary of missing setup items with descriptions."""
        missing = {}
        
        if not self.github_token:
            missing['github_token'] = 'GitHub Personal Access Token (for repository management)'
        
        if not self.fly_token:
            missing['fly_token'] = 'Fly.io API Token (for app deployment)'
        
        if not self.openai_api_key and not self.anthropic_api_key:
            missing['llm_api_key'] = 'OpenAI API Key or Anthropic API Key (for AI functionality)'
        
        return missing
"""
Key management utilities for OpenVibe backend.
Handles API key storage, validation, and user-specific key operations.
"""

import json
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

# File-based storage utilities
DATA_DIR = Path('/data')

def get_user_keys_file(uuid):
    """Get the path to a user's keys.json file"""
    user_dir = DATA_DIR / uuid
    return user_dir / 'keys.json'

def ensure_user_directory(uuid):
    """Ensure user directory exists"""
    user_dir = DATA_DIR / uuid
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

def load_user_keys(uuid):
    """Load user's API keys from file"""
    keys_file = get_user_keys_file(uuid)
    logger.debug(f"🔑 Loading keys for user {uuid[:8]}...")
    logger.debug(f"🔑 Keys file path: {keys_file}")
    logger.debug(f"🔑 Keys file exists: {keys_file.exists()}")
    
    if keys_file.exists():
        try:
            logger.debug(f"🔑 File size: {keys_file.stat().st_size} bytes")
            logger.debug(f"🔑 File permissions: {oct(keys_file.stat().st_mode)[-3:]}")
            
            with open(keys_file, 'r') as f:
                content = f.read()
                logger.debug(f"🔑 File content length: {len(content)} characters")
                
                keys = json.loads(content)
                logger.debug(f"🔑 Loaded keys for providers: {list(keys.keys())}")
                logger.info(f"🔑 Successfully loaded keys for user {uuid[:8]}")
                return keys
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Failed to load keys for user {uuid}: {e}")
            logger.debug(f"🔑 Error type: {type(e).__name__}")
            return {}
    else:
        logger.debug(f"🔑 Keys file doesn't exist for user {uuid[:8]}")
    return {}

def save_user_keys(uuid, keys):
    """Save user's API keys to file"""
    ensure_user_directory(uuid)
    keys_file = get_user_keys_file(uuid)
    try:
        with open(keys_file, 'w') as f:
            json.dump(keys, f, indent=2)
        logger.info(f"💾 Saved keys for user {uuid}")
        return True
    except IOError as e:
        logger.error(f"Failed to save keys for user {uuid}: {e}")
        return False

def user_has_keys(uuid):
    """Check if user has any keys stored"""
    keys_file = get_user_keys_file(uuid)
    return keys_file.exists()

def validate_anthropic_key(api_key):
    """Validate Anthropic API key by making a test request"""
    logger.info(f"🤖 Validating Anthropic API key (length: {len(api_key)})")
    try:
        headers = {
            'x-api-key': api_key,
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        # Make a simple request to validate the key
        logger.info("🔍 Making test request to Anthropic API...")
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json={
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 1,
                'messages': [{'role': 'user', 'content': 'Hi'}]
            },
            timeout=10
        )
        logger.info(f"📡 Anthropic API response: {response.status_code}")
        if response.status_code != 200:
            logger.warning(f"❌ Anthropic API error: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"💥 Anthropic API validation error: {str(e)}")
        return False

def validate_github_key(api_key):
    """Validate GitHub API key by making a test request"""
    logger.info(f"🐙 Validating GitHub API key (length: {len(api_key)})")
    try:
        headers = {
            'Authorization': f'token {api_key}',
            'Accept': 'application/vnd.github.v3+json'
        }
        logger.info("🔍 Making test request to GitHub API...")
        response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
        logger.info(f"📡 GitHub API response: {response.status_code}")
        if response.status_code != 200:
            logger.warning(f"❌ GitHub API error: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"💥 GitHub API validation error: {str(e)}")
        return False

def validate_fly_key(api_key):
    """Validate Fly.io API key by checking format and making a test request"""
    logger.info(f"🪰 Validating Fly.io API key (length: {len(api_key)})")
    try:
        # First, validate the token format
        if not api_key or len(api_key.strip()) < 10:
            logger.warning("❌ Fly.io token too short or empty")
            return False
            
        # Check for valid Fly.io token prefixes
        valid_prefixes = ['fo1_', 'fm1_', 'fm2_', 'ft1_', 'ft2_']
        has_valid_prefix = any(api_key.startswith(prefix) for prefix in valid_prefixes)
        
        logger.info(f"🔍 Token prefix check - has valid prefix: {has_valid_prefix}")
        if has_valid_prefix:
            logger.info(f"✅ Found valid prefix: {api_key[:4]}...")
        
        # If it doesn't have a known prefix, it might be a personal auth token
        # Personal tokens are typically longer and don't have specific prefixes
        if not has_valid_prefix and len(api_key) < 20:
            logger.warning("❌ No valid prefix and token too short for personal token")
            return False
            
        # Determine the correct authorization format based on token type
        if has_valid_prefix:
            # Tokens created with 'fly tokens create' use FlyV1 format
            auth_header = f'FlyV1 {api_key}'
            logger.info("🔑 Using FlyV1 authentication format")
        else:
            # Personal auth tokens use Bearer format
            auth_header = f'Bearer {api_key}'
            logger.info("🔑 Using Bearer authentication format")
            
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
        
        # Try a simple API call to validate the token
        # Use the apps endpoint which should work for most token types
        logger.info("🔍 Making test request to Fly.io API...")
        response = requests.get('https://api.machines.dev/v1/apps', headers=headers, timeout=10)
        
        logger.info(f"📡 Fly.io API response: {response.status_code}")
        if response.status_code not in [200, 403, 404]:
            logger.warning(f"❌ Fly.io API error: {response.text[:200]}")
        
        # Accept both 200 (success) and 403 (forbidden but authenticated)
        # 403 might occur if the token doesn't have permission to list apps
        # but it's still a valid token
        if response.status_code in [200, 403]:
            logger.info("✅ Fly.io token validated successfully")
            return True
        elif response.status_code == 401:
            # 401 means authentication failed - invalid token
            logger.warning("❌ Fly.io authentication failed (401)")
            return False
        elif response.status_code == 404:
            # 404 might mean the endpoint doesn't exist or the token is valid
            # but doesn't have access. For safety, we'll accept this as valid
            # since the token format passed our initial checks
            logger.info("⚠️ Fly.io API returned 404, accepting as valid due to format check")
            return True
        else:
            # Other status codes (500, etc.) - assume invalid for safety
            logger.warning(f"❌ Fly.io API returned unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"💥 Fly.io API validation error: {str(e)}")
        return False

def validate_api_key(provider, api_key):
    """Validate API key for a specific provider"""
    if provider == 'anthropic':
        return validate_anthropic_key(api_key)
    elif provider == 'github':
        return validate_github_key(api_key)
    elif provider == 'fly':
        return validate_fly_key(api_key)
    else:
        logger.warning(f"❌ Unknown provider: {provider}")
        return False

def get_supported_providers():
    """Get list of supported API key providers"""
    return ['anthropic', 'github', 'fly']

def is_valid_provider(provider):
    """Check if provider is supported"""
    return provider in get_supported_providers()
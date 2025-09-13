from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/backend.log') if os.path.exists('/var/log') else logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Log startup
logger.info("🚀 OpenVibe Backend starting up...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Flask app name: {app.name}")
logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")

# Store API keys in memory (in production, use a secure storage solution)
api_keys = {
    'anthropic': None,
    'github': None,
    'fly': None
}

logger.info(f"📊 API keys storage initialized: {list(api_keys.keys())}")

@app.route('/')
def hello_world():
    logger.info("📍 Root endpoint accessed")
    return jsonify({
        'message': 'Hello World from Python Backend!',
        'status': 'success',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/health')
def health_check():
    logger.info("🏥 Health check endpoint accessed")
    return jsonify({
        'status': 'healthy',
        'service': 'OpenVibe Backend',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/hello')
def api_hello():
    logger.info("👋 Hello API endpoint accessed")
    return jsonify({
        'message': 'Hello from the API!',
        'endpoint': '/api/hello',
        'timestamp': datetime.utcnow().isoformat()
    })

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

@app.route('/integrations/<provider>', methods=['POST'])
def set_api_key(provider):
    """Set API key for a provider"""
    logger.info(f"🔑 POST /integrations/{provider} - Setting API key")
    
    if provider not in ['anthropic', 'github', 'fly']:
        logger.warning(f"❌ Invalid provider requested: {provider}")
        return jsonify({'error': 'Invalid provider'}), 400
    
    data = request.get_json()
    if not data or 'api_key' not in data:
        logger.warning("❌ No API key provided in request")
        return jsonify({'error': 'API key is required'}), 400
    
    api_key = data['api_key'].strip()
    if not api_key:
        logger.warning("❌ Empty API key provided")
        return jsonify({'error': 'API key cannot be empty'}), 400
    
    logger.info(f"🔍 Validating {provider} API key...")
    
    # Validate the API key
    is_valid = False
    if provider == 'anthropic':
        is_valid = validate_anthropic_key(api_key)
    elif provider == 'github':
        is_valid = validate_github_key(api_key)
    elif provider == 'fly':
        is_valid = validate_fly_key(api_key)
    
    if is_valid:
        api_keys[provider] = api_key
        logger.info(f"✅ {provider} API key validated and stored successfully")
        return jsonify({'valid': True, 'message': f'{provider.title()} API key is valid'})
    else:
        logger.warning(f"❌ {provider} API key validation failed")
        return jsonify({'valid': False, 'message': f'{provider.title()} API key is invalid'}), 400

@app.route('/integrations/<provider>', methods=['GET'])
def check_api_key(provider):
    """Check if API key is set and valid for a provider"""
    logger.info(f"🔍 GET /integrations/{provider} - Checking API key status")
    
    if provider not in ['anthropic', 'github', 'fly']:
        logger.warning(f"❌ Invalid provider requested: {provider}")
        return jsonify({'error': 'Invalid provider'}), 400
    
    api_key = api_keys.get(provider)
    if not api_key:
        logger.info(f"⚠️ {provider} API key not set")
        return jsonify({'valid': False, 'message': f'{provider.title()} API key not set'})
    
    logger.info(f"🔍 Re-validating stored {provider} API key...")
    
    # Re-validate the stored key
    is_valid = False
    if provider == 'anthropic':
        is_valid = validate_anthropic_key(api_key)
    elif provider == 'github':
        is_valid = validate_github_key(api_key)
    elif provider == 'fly':
        is_valid = validate_fly_key(api_key)
    
    result = {
        'valid': is_valid,
        'message': f'{provider.title()} API key is {"valid" if is_valid else "invalid"}'
    }
    
    logger.info(f"📊 {provider} API key check result: {result}")
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"🚀 Starting Flask server on port {port}")
    logger.info(f"🌐 Server will be accessible at http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
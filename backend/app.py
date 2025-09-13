from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging
import sys
from datetime import datetime
from keys import (
    load_user_keys, save_user_keys, user_has_keys,
    validate_api_key, get_supported_providers, is_valid_provider
)

# Configure logging for Fly.io - stdout only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Test logging
logger.info("Flask app starting up...")
logger.info(f"Environment: {os.environ.get('FLY_APP_NAME', 'local')}")

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



@app.route('/integrations/<provider>', methods=['POST'])
def set_api_key(provider):
    """Set API key for a provider"""
    logger.info(f"🔑 POST /integrations/{provider} - Setting API key")
    
    if not is_valid_provider(provider):
        logger.warning(f"❌ Invalid provider requested: {provider}")
        return jsonify({'error': 'Invalid provider'}), 400
    
    # Get UUID from headers
    user_uuid = request.headers.get('X-User-UUID')
    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        return jsonify({'error': 'X-User-UUID header is required'}), 400
    
    user_uuid = user_uuid.strip()
    if not user_uuid:
        logger.warning("❌ Empty UUID provided in header")
        return jsonify({'error': 'UUID cannot be empty'}), 400
    
    data = request.get_json()
    if not data or 'api_key' not in data:
        logger.warning("❌ API key is required in request body")
        return jsonify({'error': 'API key is required'}), 400
    
    api_key = data['api_key'].strip()
    if not api_key:
        logger.warning("❌ Empty API key provided")
        return jsonify({'error': 'API key cannot be empty'}), 400
    
    logger.info(f"🔍 Validating {provider} API key for user {user_uuid[:8]}...")
    
    # Validate the API key using the keys module
    is_valid = validate_api_key(provider, api_key)
    
    if is_valid:
        # Load existing keys for this user
        user_keys = load_user_keys(user_uuid)
        user_keys[provider] = api_key
        
        # Save to file
        if save_user_keys(user_uuid, user_keys):
            # Also store in memory for backward compatibility
            api_keys[provider] = api_key
            logger.info(f"✅ {provider} API key validated and stored for user {user_uuid[:8]}")
            return jsonify({'valid': True, 'message': f'{provider.title()} API key is valid'})
        else:
            logger.error(f"❌ Failed to save {provider} API key for user {user_uuid[:8]}")
            return jsonify({'valid': False, 'message': 'Failed to save API key'}), 500
    else:
        logger.warning(f"❌ {provider} API key validation failed for user {user_uuid[:8]}")
        return jsonify({'valid': False, 'message': f'{provider.title()} API key is invalid'}), 400

@app.route('/integrations/<provider>', methods=['GET'])
def check_api_key(provider):
    """Check if API key is set and valid for a provider"""
    logger.info(f"🔍 GET /integrations/{provider} - Checking API key status")
    
    if not is_valid_provider(provider):
        logger.warning(f"❌ Invalid provider requested: {provider}")
        return jsonify({'error': 'Invalid provider'}), 400
    
    # Get UUID from headers
    user_uuid = request.headers.get('X-User-UUID')
    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        return jsonify({'error': 'X-User-UUID header is required'}), 400
    
    user_uuid = user_uuid.strip()
    if not user_uuid:
        logger.warning("❌ Empty UUID provided in header")
        return jsonify({'error': 'UUID cannot be empty'}), 400
    
    logger.info(f"🔍 Checking {provider} API key status for user {user_uuid[:8]}...")
    
    # Check if user has keys file
    if not user_has_keys(user_uuid):
        logger.info(f"⚠️ No keys file found for user {user_uuid[:8]}")
        return jsonify({'valid': False, 'message': f'{provider.title()} API key not set'})
    
    # Load user's keys
    user_keys = load_user_keys(user_uuid)
    api_key = user_keys.get(provider)
    
    if not api_key:
        logger.info(f"⚠️ {provider} API key not set for user {user_uuid[:8]}")
        return jsonify({'valid': False, 'message': f'{provider.title()} API key not set'})
    
    logger.info(f"🔍 Re-validating stored {provider} API key for user {user_uuid[:8]}...")
    
    # Re-validate the stored key using the keys module
    is_valid = validate_api_key(provider, api_key)
    
    result = {
        'valid': is_valid,
        'message': f'{provider.title()} API key is {"valid" if is_valid else "invalid"}'
    }
    
    logger.info(f"📊 {provider} API key check result for user {user_uuid[:8]}: {result}")
    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"🚀 Starting Flask server on port {port}")
    logger.info(f"🌐 Server will be accessible at http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
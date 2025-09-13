from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import json

app = Flask(__name__)
CORS(app)

# Store API keys in memory (in production, use a secure storage solution)
api_keys = {
    'anthropic': None,
    'github': None,
    'fly': None
}

@app.route('/')
def hello_world():
    return jsonify({
        'message': 'Hello World from Python Backend!',
        'status': 'success',
        'version': '1.0.0'
    })

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'OpenVibe Backend'
    })

@app.route('/api/hello')
def api_hello():
    return jsonify({
        'message': 'Hello from the API!',
        'endpoint': '/api/hello'
    })

def validate_anthropic_key(api_key):
    """Validate Anthropic API key by making a test request"""
    try:
        headers = {
            'x-api-key': api_key,
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        # Make a simple request to validate the key
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
        return response.status_code == 200
    except Exception:
        return False

def validate_github_key(api_key):
    """Validate GitHub API key by making a test request"""
    try:
        headers = {
            'Authorization': f'token {api_key}',
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def validate_fly_key(api_key):
    """Validate Fly.io API key by making a test request"""
    try:
        # Determine the correct authorization format based on token type
        # FlyV1 format for tokens created with 'fly tokens create'
        # Bearer format for tokens from 'flyctl auth token'
        if api_key.startswith('fo1_'):
            # Org tokens created with 'fly tokens create org' use FlyV1 format
            auth_header = f'FlyV1 {api_key}'
        else:
            # Personal auth tokens use Bearer format
            auth_header = f'Bearer {api_key}'
            
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
        response = requests.get('https://api.fly.io/v1/apps', headers=headers, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

@app.route('/integrations/<provider>', methods=['POST'])
def set_api_key(provider):
    """Set API key for a provider"""
    if provider not in ['anthropic', 'github', 'fly']:
        return jsonify({'error': 'Invalid provider'}), 400
    
    data = request.get_json()
    if not data or 'api_key' not in data:
        return jsonify({'error': 'API key is required'}), 400
    
    api_key = data['api_key'].strip()
    if not api_key:
        return jsonify({'error': 'API key cannot be empty'}), 400
    
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
        return jsonify({'valid': True, 'message': f'{provider.title()} API key is valid'})
    else:
        return jsonify({'valid': False, 'message': f'{provider.title()} API key is invalid'}), 400

@app.route('/integrations/<provider>', methods=['GET'])
def check_api_key(provider):
    """Check if API key is set and valid for a provider"""
    if provider not in ['anthropic', 'github', 'fly']:
        return jsonify({'error': 'Invalid provider'}), 400
    
    api_key = api_keys.get(provider)
    if not api_key:
        return jsonify({'valid': False, 'message': f'{provider.title()} API key not set'})
    
    # Re-validate the stored key
    is_valid = False
    if provider == 'anthropic':
        is_valid = validate_anthropic_key(api_key)
    elif provider == 'github':
        is_valid = validate_github_key(api_key)
    elif provider == 'fly':
        is_valid = validate_fly_key(api_key)
    
    return jsonify({
        'valid': is_valid,
        'message': f'{provider.title()} API key is {"valid" if is_valid else "invalid"}'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
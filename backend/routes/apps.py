from flask import Blueprint, jsonify, request
import os
import requests
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from keys import load_user_keys

logger = logging.getLogger(__name__)

# Create Blueprint for apps
apps_bp = Blueprint('apps', __name__)

# File-based storage utilities
DATA_DIR = Path('/data')

def get_apps_file():
    """Get the path to the apps.json file"""
    return DATA_DIR / 'apps.json'

def get_riffs_file(app_slug):
    """Get the path to the riffs.json file for a specific app"""
    return DATA_DIR / f'riffs_{app_slug}.json'

def load_apps():
    """Load apps from file"""
    apps_file = get_apps_file()
    logger.debug(f"📁 Loading apps from: {apps_file}")
    logger.debug(f"📁 File exists: {apps_file.exists()}")
    
    if apps_file.exists():
        try:
            logger.debug(f"📁 File size: {apps_file.stat().st_size} bytes")
            logger.debug(f"📁 File permissions: {oct(apps_file.stat().st_mode)[-3:]}")
            
            with open(apps_file, 'r') as f:
                content = f.read()
                logger.debug(f"📁 File content length: {len(content)} characters")
                logger.debug(f"📁 File content preview: {content[:200]}...")
                
                apps = json.loads(content)
                logger.info(f"📁 Successfully loaded {len(apps)} apps")
                return apps
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Failed to load apps: {e}")
            logger.debug(f"📁 Error type: {type(e).__name__}")
            return []
    else:
        logger.info(f"📁 Apps file doesn't exist, returning empty list")
    return []

def save_apps(apps):
    """Save apps to file"""
    logger.debug(f"💾 Saving {len(apps)} apps")
    logger.debug(f"💾 Data directory: {DATA_DIR}")
    logger.debug(f"💾 Data directory exists: {DATA_DIR.exists()}")
    
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"💾 Data directory created/verified")
    except Exception as e:
        logger.error(f"❌ Failed to create data directory: {e}")
        return False
    
    apps_file = get_apps_file()
    logger.debug(f"💾 Apps file path: {apps_file}")
    
    try:
        # Create backup if file exists
        if apps_file.exists():
            backup_file = apps_file.with_suffix('.json.backup')
            logger.debug(f"💾 Creating backup: {backup_file}")
            apps_file.rename(backup_file)
        
        with open(apps_file, 'w') as f:
            json.dump(apps, f, indent=2)
        
        logger.info(f"💾 Successfully saved {len(apps)} apps")
        logger.debug(f"💾 File size: {apps_file.stat().st_size} bytes")
        return True
    except IOError as e:
        logger.error(f"❌ Failed to save apps: {e}")
        logger.debug(f"💾 Error type: {type(e).__name__}")
        return False

def create_slug(name):
    """Convert app name to slug format"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

def get_user_default_org(fly_token):
    """
    Get the user's default organization slug by checking their existing apps.
    
    This function tries to determine the user's actual organization slug
    by listing their existing apps and extracting the organization information.
    Falls back to 'personal' if no apps exist or API call fails.
    
    Args:
        fly_token (str): The user's Fly.io API token
    
    Returns:
        tuple: (success, org_slug_or_error_message)
    """
    if not fly_token:
        return False, "Fly.io API token is required"
    
    logger.debug(f"🛩️ Attempting to determine user's organization from existing apps")
    
    try:
        headers = {
            'Authorization': f'Bearer {fly_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'OpenVibe-Backend/1.0'
        }
        
        # Try to list user's existing apps to determine their organization
        response = requests.get(
            'https://api.machines.dev/v1/apps',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            apps = response.json()
            if apps and len(apps) > 0:
                # Get organization from the first app
                first_app = apps[0]
                org_slug = first_app.get('organization', {}).get('slug')
                if org_slug:
                    logger.debug(f"🛩️ Detected user organization from existing apps: {org_slug}")
                    return True, org_slug
                else:
                    logger.debug(f"🛩️ No organization info found in existing apps")
            else:
                logger.debug(f"🛩️ User has no existing apps")
        else:
            logger.debug(f"🛩️ Failed to list apps: {response.status_code}")
    
    except Exception as e:
        logger.debug(f"🛩️ Error determining organization from apps: {str(e)}")
    
    # Fall back to 'personal' as the default organization slug
    logger.debug(f"🛩️ Falling back to default organization: personal")
    return True, "personal"

def create_fly_app(app_name, fly_token):
    """
    Create a new Fly.io app.
    
    Args:
        app_name (str): The app name to create
        fly_token (str): The user's Fly.io API token
    
    Returns:
        tuple: (success, app_data_or_error_message)
    """
    if not fly_token:
        return False, "Fly.io API token is required"
    
    logger.info(f"🛩️ Creating Fly.io app: {app_name}")
    
    # First, get the user's default organization
    success, org_slug = get_user_default_org(fly_token)
    if not success:
        return False, f"Failed to get user organization: {org_slug}"
    
    logger.debug(f"🛩️ Using organization: {org_slug}")
    
    headers = {
        'Authorization': f'Bearer {fly_token}',
        'Content-Type': 'application/json',
        'User-Agent': 'OpenVibe-Backend/1.0'
    }
    
    # Check if app already exists first
    try:
        check_response = requests.get(
            f'https://api.machines.dev/v1/apps/{app_name}',
            headers=headers,
            timeout=10
        )
        
        if check_response.status_code == 200:
            # App already exists, check if it's owned by user
            app_data = check_response.json()
            app_org_slug = app_data.get('organization', {}).get('slug')
            
            # If the user can successfully retrieve the app details with their token,
            # it means they have access to it. This is a strong indicator of ownership.
            # We'll accept this as ownership regardless of organization slug mismatch,
            # since the organization detection might not be perfect.
            logger.info(f"✅ App '{app_name}' already exists and user has access to it")
            logger.debug(f"🛩️ App organization: {app_org_slug}, Expected: {org_slug}")
            
            # Update our understanding of the user's organization if it differs
            if app_org_slug and app_org_slug != org_slug:
                logger.debug(f"🛩️ Updating user organization from {org_slug} to {app_org_slug}")
            
            return True, app_data
        
        elif check_response.status_code == 403:
            # App exists but user doesn't have access - this means it's owned by someone else
            logger.error(f"❌ App '{app_name}' exists but user doesn't have access to it")
            return False, f"App '{app_name}' already exists and is not owned by you"
        
        elif check_response.status_code == 401:
            # Unauthorized - invalid token
            logger.error(f"❌ Invalid Fly.io API token")
            return False, "Invalid Fly.io API token"
        
        elif check_response.status_code != 404:
            # Some other error occurred
            logger.error(f"❌ Error checking app existence: {check_response.status_code} - {check_response.text}")
            return False, f"Error checking app existence: {check_response.status_code}"
    
    except Exception as e:
        logger.error(f"💥 Error checking app existence: {str(e)}")
        return False, f"Error checking app existence: {str(e)}"
    
    # App doesn't exist, create it
    try:
        create_data = {
            'app_name': app_name,
            'org_slug': org_slug
        }
        
        logger.debug(f"🛩️ Creating app with data: {create_data}")
        
        create_response = requests.post(
            'https://api.machines.dev/v1/apps',
            headers=headers,
            json=create_data,
            timeout=30
        )
        
        logger.debug(f"🛩️ App creation response status: {create_response.status_code}")
        
        if create_response.status_code == 201:
            app_data = create_response.json()
            logger.info(f"✅ Successfully created Fly.io app: {app_name}")
            logger.debug(f"🛩️ Created app data: {app_data}")
            return True, app_data
        
        elif create_response.status_code == 422:
            # App name might be taken or invalid
            error_text = create_response.text
            logger.error(f"❌ App creation failed - name taken or invalid: {error_text}")
            if "already taken" in error_text.lower():
                return False, f"App name '{app_name}' is already taken"
            else:
                return False, f"Invalid app name or creation failed: {error_text}"
        
        elif create_response.status_code == 401:
            logger.error(f"❌ Unauthorized - invalid Fly.io API token")
            return False, "Invalid Fly.io API token"
        
        elif create_response.status_code == 403:
            logger.error(f"❌ Forbidden - insufficient permissions")
            return False, "Insufficient permissions for Fly.io API"
        
        else:
            logger.error(f"❌ Unexpected response from Fly.io API: {create_response.status_code} - {create_response.text}")
            return False, f"Fly.io API error: {create_response.status_code}"
    
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout creating Fly.io app")
        return False, "Timeout creating Fly.io app"
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error connecting to Fly.io API: {str(e)}")
        return False, f"Error connecting to Fly.io API: {str(e)}"
    
    except Exception as e:
        logger.error(f"💥 Unexpected error creating Fly.io app: {str(e)}")
        return False, f"Unexpected error: {str(e)}"

def get_github_status(repo_url, github_token):
    """Get GitHub repository status including CI/CD tests"""
    logger.info(f"🐙 Checking GitHub status for: {repo_url}")
    
    try:
        # Extract owner and repo from URL
        # Expected format: https://github.com/owner/repo
        if not repo_url or 'github.com' not in repo_url:
            logger.warning(f"❌ Invalid GitHub URL: {repo_url}")
            return None
            
        parts = repo_url.replace('https://github.com/', '').split('/')
        if len(parts) < 2:
            logger.warning(f"❌ Cannot parse GitHub URL: {repo_url}")
            return None
            
        owner, repo = parts[0], parts[1]
        logger.debug(f"🔍 GitHub repo: {owner}/{repo}")
        
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'OpenVibe-Backend/1.0'
        }
        
        # Get latest commit on main branch
        commits_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo}/commits/main',
            headers=headers,
            timeout=10
        )
        
        if commits_response.status_code != 200:
            logger.warning(f"❌ Failed to get commits: {commits_response.status_code}")
            return None
            
        commit_data = commits_response.json()
        latest_commit_sha = commit_data['sha']
        logger.debug(f"🔍 Latest commit: {latest_commit_sha[:7]}")
        
        # Get status checks for the latest commit
        status_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo}/commits/{latest_commit_sha}/status',
            headers=headers,
            timeout=10
        )
        
        if status_response.status_code != 200:
            logger.warning(f"❌ Failed to get status checks: {status_response.status_code}")
            # Return basic info even if status checks fail
            return {
                'tests_passing': None,
                'last_commit': latest_commit_sha,
                'status': 'unknown'
            }
            
        status_data = status_response.json()
        state = status_data.get('state', 'unknown')
        
        # Handle different CI/CD states properly
        if state == 'success':
            tests_passing = True
        elif state in ['pending', 'running']:
            tests_passing = None  # Use None to indicate "in progress"
        else:  # failure, error, or unknown
            tests_passing = False
        
        logger.info(f"✅ GitHub status retrieved: {state}")
        
        return {
            'tests_passing': tests_passing,
            'last_commit': latest_commit_sha,
            'status': state,
            'total_count': status_data.get('total_count', 0)
        }
        
    except Exception as e:
        logger.error(f"💥 GitHub status check error: {str(e)}")
        return None

def get_fly_status(project_slug, fly_token):
    """Get Fly.io deployment status"""
    logger.info(f"🚁 Checking Fly.io status for: {project_slug}")
    
    try:
        if not fly_token:
            logger.warning("❌ No Fly.io token available")
            return None
            
        headers = {
            'Authorization': f'Bearer {fly_token}',
            'Content-Type': 'application/json'
        }
        
        # Check if app exists and get status
        app_response = requests.get(
            f'https://api.machines.dev/v1/apps/{app_slug}',
            headers=headers,
            timeout=10
        )
        
        if app_response.status_code == 404:
            logger.info(f"⚠️ Fly.io app not found: {app_slug}")
            return {
                'deployed': False,
                'app_url': None,
                'status': 'not_found'
            }
        elif app_response.status_code != 200:
            logger.warning(f"❌ Failed to get Fly.io app status: {app_response.status_code}")
            return None
            
        app_data = app_response.json()
        app_status = app_data.get('status', 'unknown')
        
        # Construct app URL
        app_url = f"https://{app_slug}.fly.dev"
        
        logger.info(f"✅ Fly.io status retrieved: {app_status}")
        
        return {
            'deployed': app_status in ['running', 'deployed'],
            'app_url': app_url,
            'status': app_status,
            'name': app_data.get('name'),
            'organization': app_data.get('organization', {}).get('slug')
        }
        
    except Exception as e:
        logger.error(f"💥 Fly.io status check error: {str(e)}")
        return None

def delete_github_repo(repo_url, github_token):
    """Delete a GitHub repository"""
    logger.info(f"🗑️ Deleting GitHub repo: {repo_url}")
    
    try:
        # Extract owner and repo from URL
        if not repo_url or 'github.com' not in repo_url:
            logger.warning(f"❌ Invalid GitHub URL: {repo_url}")
            return False, "Invalid GitHub URL"
            
        parts = repo_url.replace('https://github.com/', '').split('/')
        if len(parts) < 2:
            logger.warning(f"❌ Cannot parse GitHub URL: {repo_url}")
            return False, "Cannot parse GitHub URL"
            
        owner, repo = parts[0], parts[1]
        logger.debug(f"🔍 GitHub repo to delete: {owner}/{repo}")
        
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'OpenVibe-Backend/1.0'
        }
        
        # Delete the repository
        delete_response = requests.delete(
            f'https://api.github.com/repos/{owner}/{repo}',
            headers=headers,
            timeout=30
        )
        
        if delete_response.status_code == 204:
            logger.info(f"✅ Successfully deleted GitHub repo: {owner}/{repo}")
            return True, "Repository deleted successfully"
        elif delete_response.status_code == 404:
            logger.warning(f"⚠️ GitHub repo not found: {owner}/{repo}")
            return True, "Repository not found (may have been already deleted)"
        elif delete_response.status_code == 403:
            logger.error(f"❌ Insufficient permissions to delete repo: {owner}/{repo}")
            return False, "Insufficient permissions to delete repository"
        else:
            logger.error(f"❌ Failed to delete GitHub repo: {delete_response.status_code} - {delete_response.text}")
            return False, f"GitHub API error: {delete_response.status_code}"
            
    except Exception as e:
        logger.error(f"💥 Error deleting GitHub repo: {str(e)}")
        return False, f"Error deleting repository: {str(e)}"

def delete_fly_app(app_name, fly_token):
    """Delete a Fly.io app"""
    logger.info(f"🗑️ Deleting Fly.io app: {app_name}")
    
    try:
        if not fly_token:
            return False, "Fly.io API token is required"
        
        headers = {
            'Authorization': f'Bearer {fly_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'OpenVibe-Backend/1.0'
        }
        
        # First check if app exists
        check_response = requests.get(
            f'https://api.machines.dev/v1/apps/{app_name}',
            headers=headers,
            timeout=10
        )
        
        if check_response.status_code == 404:
            logger.warning(f"⚠️ Fly.io app not found: {app_name}")
            return True, "App not found (may have been already deleted)"
        elif check_response.status_code != 200:
            logger.error(f"❌ Error checking Fly.io app: {check_response.status_code}")
            return False, f"Error checking app status: {check_response.status_code}"
        
        # Delete the app
        delete_response = requests.delete(
            f'https://api.machines.dev/v1/apps/{app_name}',
            headers=headers,
            timeout=30
        )
        
        if delete_response.status_code in [200, 202, 204]:
            logger.info(f"✅ Successfully deleted Fly.io app: {app_name}")
            return True, "App deleted successfully"
        elif delete_response.status_code == 404:
            logger.warning(f"⚠️ Fly.io app not found during deletion: {app_name}")
            return True, "App not found (may have been already deleted)"
        elif delete_response.status_code == 403:
            logger.error(f"❌ Insufficient permissions to delete Fly.io app: {app_name}")
            return False, "Insufficient permissions to delete app"
        else:
            logger.error(f"❌ Failed to delete Fly.io app: {delete_response.status_code} - {delete_response.text}")
            return False, f"Fly.io API error: {delete_response.status_code}"
            
    except Exception as e:
        logger.error(f"💥 Error deleting Fly.io app: {str(e)}")
        return False, f"Error deleting app: {str(e)}"

def create_github_repo(repo_name, github_token, fly_token):
    """Create a GitHub repository from template and set FLY_API_TOKEN secret"""
    logger.info(f"🐙 Creating GitHub repo: {repo_name}")
    logger.debug(f"🐙 GitHub token length: {len(github_token)}")
    logger.debug(f"🐙 GitHub token prefix: {github_token[:10]}...")
    logger.debug(f"🐙 Fly token provided: {bool(fly_token)}")
    logger.debug(f"🐙 Fly token length: {len(fly_token) if fly_token else 0}")
    
    try:
        # First, check if repo already exists
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'OpenVibe-Backend/1.0'
        }
        logger.debug(f"🐙 Request headers: {headers}")
        
        # Get the authenticated user to determine the owner
        logger.debug(f"🐙 Making request to GitHub user API...")
        user_response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
        logger.debug(f"🐙 GitHub user API response status: {user_response.status_code}")
        logger.debug(f"🐙 GitHub user API response headers: {dict(user_response.headers)}")
        
        if user_response.status_code != 200:
            logger.error(f"❌ Failed to get GitHub user: {user_response.text}")
            logger.debug(f"🐙 Response content: {user_response.content}")
            return False, "Failed to authenticate with GitHub"
        
        user_data = user_response.json()
        owner = user_data['login']
        logger.info(f"🔍 GitHub owner: {owner}")
        logger.debug(f"🔍 GitHub user data: {user_data}")
        
        # Check if repo already exists
        check_response = requests.get(f'https://api.github.com/repos/{owner}/{repo_name}', headers=headers, timeout=10)
        if check_response.status_code == 200:
            # Repository already exists, but that's okay - we'll use the existing one
            repo_data = check_response.json()
            logger.info(f"✅ Repository {owner}/{repo_name} already exists, using existing repository")
            
            # Still try to set the FLY_API_TOKEN secret if provided
            if fly_token:
                logger.info(f"🔐 Setting FLY_API_TOKEN secret for existing repo {repo_name}")
                
                # Get the repository's public key for encrypting secrets
                key_response = requests.get(
                    f'https://api.github.com/repos/{owner}/{repo_name}/actions/secrets/public-key',
                    headers=headers,
                    timeout=10
                )
                
                if key_response.status_code == 200:
                    from base64 import b64encode
                    from nacl import encoding, public
                    
                    public_key_data = key_response.json()
                    public_key = public.PublicKey(public_key_data['key'].encode('utf-8'), encoding.Base64Encoder())
                    
                    # Encrypt the secret
                    sealed_box = public.SealedBox(public_key)
                    encrypted = sealed_box.encrypt(fly_token.encode('utf-8'))
                    encrypted_value = b64encode(encrypted).decode('utf-8')
                    
                    # Set the secret
                    secret_data = {
                        'encrypted_value': encrypted_value,
                        'key_id': public_key_data['key_id']
                    }
                    
                    secret_response = requests.put(
                        f'https://api.github.com/repos/{owner}/{repo_name}/actions/secrets/FLY_API_TOKEN',
                        headers=headers,
                        json=secret_data,
                        timeout=10
                    )
                    
                    if secret_response.status_code in [201, 204]:
                        logger.info("✅ FLY_API_TOKEN secret set successfully for existing repo")
                    else:
                        logger.warning(f"⚠️ Failed to set FLY_API_TOKEN secret for existing repo: {secret_response.text}")
                else:
                    logger.warning(f"⚠️ Failed to get public key for secrets on existing repo: {key_response.text}")
            
            return True, repo_data['html_url']
        
        # Create repo from template
        create_data = {
            'name': repo_name,
            'description': f'OpenVibe app: {repo_name}',
            'private': False,
            'include_all_branches': False
        }
        
        template_headers = headers.copy()
        template_headers['Accept'] = 'application/vnd.github.baptiste-preview+json'
        
        create_response = requests.post(
            'https://api.github.com/repos/rbren/openvibe-template/generate',
            headers=template_headers,
            json=create_data,
            timeout=30
        )
        
        if create_response.status_code != 201:
            logger.error(f"Failed to create repo from template: {create_response.text}")
            return False, f"Failed to create repository: {create_response.text}"
        
        repo_data = create_response.json()
        logger.info(f"✅ Created repository: {repo_data['html_url']}")
        
        # Set FLY_API_TOKEN secret
        if fly_token:
            logger.info(f"🔐 Setting FLY_API_TOKEN secret for {repo_name}")
            
            # Get the repository's public key for encrypting secrets
            key_response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo_name}/actions/secrets/public-key',
                headers=headers,
                timeout=10
            )
            
            if key_response.status_code == 200:
                from base64 import b64encode
                from nacl import encoding, public
                
                public_key_data = key_response.json()
                public_key = public.PublicKey(public_key_data['key'].encode('utf-8'), encoding.Base64Encoder())
                
                # Encrypt the secret
                sealed_box = public.SealedBox(public_key)
                encrypted = sealed_box.encrypt(fly_token.encode('utf-8'))
                encrypted_value = b64encode(encrypted).decode('utf-8')
                
                # Set the secret
                secret_data = {
                    'encrypted_value': encrypted_value,
                    'key_id': public_key_data['key_id']
                }
                
                secret_response = requests.put(
                    f'https://api.github.com/repos/{owner}/{repo_name}/actions/secrets/FLY_API_TOKEN',
                    headers=headers,
                    json=secret_data,
                    timeout=10
                )
                
                if secret_response.status_code in [201, 204]:
                    logger.info("✅ FLY_API_TOKEN secret set successfully")
                else:
                    logger.warning(f"⚠️ Failed to set FLY_API_TOKEN secret: {secret_response.text}")
            else:
                logger.warning(f"⚠️ Failed to get public key for secrets: {key_response.text}")
        
        return True, repo_data['html_url']
        
    except Exception as e:
        logger.error(f"💥 GitHub repo creation error: {str(e)}")
        return False, f"Error creating repository: {str(e)}"

@apps_bp.route('/api/apps', methods=['GET'])
def get_apps():
    """Get all apps, ordered alphabetically"""
    logger.info("📋 GET /api/apps - Fetching all apps")
    
    try:
        apps = load_apps()
        # Sort apps alphabetically by name
        apps.sort(key=lambda x: x.get('name', '').lower())
        
        logger.info(f"📊 Returning {len(apps)} apps")
        return jsonify({
            'apps': apps,
            'count': len(apps)
        })
    except Exception as e:
        logger.error(f"💥 Error fetching apps: {str(e)}")
        return jsonify({'error': 'Failed to fetch apps'}), 500

@apps_bp.route('/api/apps/<slug>', methods=['GET'])
def get_app(slug):
    """Get a specific app by slug with status information"""
    logger.info(f"📋 GET /api/apps/{slug} - Fetching app details")
    
    try:
        # Get UUID from headers for API keys
        user_uuid = request.headers.get('X-User-UUID')
        if user_uuid:
            user_uuid = user_uuid.strip()
        
        apps = load_apps()
        
        # Find app by slug
        app = next((a for a in apps if a.get('slug') == slug), None)
        if not app:
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({'error': 'App not found'}), 404
        
        logger.info(f"📊 Found app: {app['name']}")
        
        # Get user's API keys if UUID is provided
        github_status = None
        fly_status = None
        
        if user_uuid:
            try:
                user_keys = load_user_keys(user_uuid)
                github_token = user_keys.get('github')
                fly_token = user_keys.get('fly')
                
                # Get GitHub status if token is available
                if github_token and app.get('github_url'):
                    github_status = get_github_status(app['github_url'], github_token)
                
                # Get Fly.io status if token is available
                if fly_token and app.get('slug'):
                    fly_status = get_fly_status(app['slug'], fly_token)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error getting status information: {str(e)}")
        
        # Add status information to app
        app_with_status = app.copy()
        if github_status:
            app_with_status['github_status'] = github_status
        if fly_status:
            app_with_status['fly_status'] = fly_status
        
        return jsonify(app_with_status)
    except Exception as e:
        logger.error(f"💥 Error fetching app: {str(e)}")
        return jsonify({'error': 'Failed to fetch app'}), 500

@apps_bp.route('/api/apps', methods=['POST'])
def create_app():
    """Create a new app with GitHub repo and Fly.io app"""
    logger.info("🆕 POST /api/apps - Creating new app")
    
    try:
        # Get UUID from headers
        user_uuid = request.headers.get('X-User-UUID')
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            return jsonify({'error': 'X-User-UUID header is required'}), 400
        
        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({'error': 'UUID cannot be empty'}), 400
        
        # Get request data
        data = request.get_json()
        if not data or 'name' not in data:
            logger.warning("❌ App name is required")
            return jsonify({'error': 'App name is required'}), 400
        
        app_name = data['name'].strip()
        if not app_name:
            logger.warning("❌ App name cannot be empty")
            return jsonify({'error': 'App name cannot be empty'}), 400
        
        # Create slug from name (use provided slug if available, otherwise generate)
        app_slug = data.get('slug', create_slug(app_name)).strip()
        if not app_slug:
            app_slug = create_slug(app_name)
        
        if not app_slug:
            logger.warning("❌ Invalid app name - cannot create slug")
            return jsonify({'error': 'Invalid app name'}), 400
        
        logger.info(f"🔄 Creating app: {app_name} -> {app_slug}")
        
        # Load existing apps
        apps = load_apps()
        
        # Check if app with same slug already exists
        existing_app = next((p for p in apps if p.get('slug') == app_slug), None)
        if existing_app:
            logger.warning(f"❌ App with slug '{app_slug}' already exists")
            return jsonify({'error': f'App with name "{app_name}" already exists'}), 409
        
        # Get user's API keys
        user_keys = load_user_keys(user_uuid)
        github_token = user_keys.get('github')
        fly_token = user_keys.get('fly')
        
        if not github_token:
            logger.warning("❌ GitHub API key is required")
            return jsonify({'error': 'GitHub API key is required. Please set it in integrations first.'}), 400
        
        if not fly_token:
            logger.warning("❌ Fly.io API key is required")
            return jsonify({'error': 'Fly.io API key is required. Please set it in integrations first.'}), 400
        
        # Create GitHub repository
        logger.info(f"🐙 Creating GitHub repository: {app_slug}")
        github_success, github_result = create_github_repo(app_slug, github_token, fly_token)
        
        if not github_success:
            logger.error(f"❌ GitHub repo creation failed: {github_result}")
            return jsonify({'error': f'Failed to create GitHub repository: {github_result}'}), 500
        
        github_url = github_result
        logger.info(f"✅ GitHub repository created: {github_url}")
        
        # Create Fly.io app
        logger.info(f"🛩️ Creating Fly.io app: {app_slug}")
        fly_success, fly_result = create_fly_app(app_slug, fly_token)
        
        if not fly_success:
            logger.error(f"❌ Fly.io app creation failed: {fly_result}")
            # Don't fail the entire app creation if Fly.io fails
            # The user can manually create the app later
            logger.warning(f"⚠️ Continuing with app creation despite Fly.io failure")
            fly_app_name = None
        else:
            fly_app_name = app_slug
            logger.info(f"✅ Fly.io app created: {fly_app_name}")
        
        # Create app record
        app = {
            'name': app_name,
            'slug': app_slug,
            'github_url': github_url,
            'fly_app_name': fly_app_name,
            'created_at': datetime.utcnow().isoformat(),
            'created_by': user_uuid
        }
        
        # Add to apps list
        apps.append(app)
        
        # Save to file
        if not save_apps(apps):
            logger.error("❌ Failed to save app to file")
            return jsonify({'error': 'Failed to save app'}), 500
        
        logger.info(f"✅ App created successfully: {app_name}")
        return jsonify({
            'message': 'App created successfully',
            'app': app,
            'warnings': [] if fly_success else [f'Fly.io app creation failed: {fly_result}']
        }), 201
        
    except Exception as e:
        logger.error(f"💥 Error creating app: {str(e)}")
        return jsonify({'error': 'Failed to create app'}), 500

@apps_bp.route('/api/apps/<slug>', methods=['DELETE'])
def delete_app(slug):
    """Delete a app and its associated GitHub repo and Fly.io app"""
    logger.info(f"🗑️ DELETE /api/apps/{slug} - Deleting app")
    
    try:
        # Get UUID from headers
        user_uuid = request.headers.get('X-User-UUID')
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            return jsonify({'error': 'X-User-UUID header is required'}), 400
        
        user_uuid = user_uuid.strip()
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({'error': 'UUID cannot be empty'}), 400
        
        # Load apps
        apps = load_apps()
        
        # Find app by slug
        app = next((p for p in apps if p.get('slug') == slug), None)
        if not app:
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({'error': 'App not found'}), 404
        
        logger.info(f"🔍 Found app to delete: {app['name']}")
        
        # Get user's API keys
        user_keys = load_user_keys(user_uuid)
        github_token = user_keys.get('github')
        fly_token = user_keys.get('fly')
        
        deletion_results = {
            'github_success': False,
            'github_error': None,
            'fly_success': False,
            'fly_error': None
        }
        
        # Delete GitHub repository if URL exists and token is available
        if app.get('github_url') and github_token:
            logger.info(f"🐙 Deleting GitHub repository: {app['github_url']}")
            github_success, github_message = delete_github_repo(app['github_url'], github_token)
            deletion_results['github_success'] = github_success
            if not github_success:
                deletion_results['github_error'] = github_message
                logger.warning(f"⚠️ GitHub deletion failed: {github_message}")
            else:
                logger.info(f"✅ GitHub repository deleted: {github_message}")
        else:
            logger.info("⚠️ Skipping GitHub deletion (no URL or token)")
        
        # Delete Fly.io app if name exists and token is available
        if app.get('fly_app_name') and fly_token:
            logger.info(f"🛩️ Deleting Fly.io app: {app['fly_app_name']}")
            fly_success, fly_message = delete_fly_app(app['fly_app_name'], fly_token)
            deletion_results['fly_success'] = fly_success
            if not fly_success:
                deletion_results['fly_error'] = fly_message
                logger.warning(f"⚠️ Fly.io deletion failed: {fly_message}")
            else:
                logger.info(f"✅ Fly.io app deleted: {fly_message}")
        else:
            logger.info("⚠️ Skipping Fly.io deletion (no app name or token)")
        
        # Remove app from list
        apps = [p for p in apps if p.get('slug') != slug]
        
        # Save updated apps list
        if save_apps(apps):
            logger.info(f"✅ App {slug} removed from database")
        else:
            logger.error(f"❌ Failed to save apps after deletion")
            return jsonify({'error': 'Failed to update app database'}), 500
        
        # Delete associated riffs file
        try:
            riffs_file = get_riffs_file(slug)
            if riffs_file.exists():
                riffs_file.unlink()
                logger.info(f"✅ Deleted riffs file for app {slug}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete riffs file: {str(e)}")
        
        # Prepare response
        response_data = {
            'message': f'App "{app.get("name")}" deleted successfully',
            'app_name': app.get('name'),
            'app_slug': slug,
            'deletion_results': deletion_results
        }
        
        # Add warnings if some deletions failed
        warnings = []
        if deletion_results['github_error']:
            warnings.append(f"GitHub repository deletion failed: {deletion_results['github_error']}")
        if deletion_results['fly_error']:
            warnings.append(f"Fly.io app deletion failed: {deletion_results['fly_error']}")
        
        if warnings:
            response_data['warnings'] = warnings
        
        logger.info(f"✅ App deletion completed: {slug}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"💥 Error deleting app: {str(e)}")
        return jsonify({'error': 'Failed to delete app'}), 500
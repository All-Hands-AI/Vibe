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

# Create Blueprint for projects
projects_bp = Blueprint('projects', __name__)

# File-based storage utilities
DATA_DIR = Path('/data')

def get_projects_file():
    """Get the path to the projects.json file"""
    return DATA_DIR / 'projects.json'

def get_conversations_file(project_id):
    """Get the path to the conversations.json file for a specific project"""
    return DATA_DIR / f'conversations_{project_id}.json'

def load_projects():
    """Load projects from file"""
    projects_file = get_projects_file()
    logger.debug(f"📁 Loading projects from: {projects_file}")
    logger.debug(f"📁 File exists: {projects_file.exists()}")
    
    if projects_file.exists():
        try:
            logger.debug(f"📁 File size: {projects_file.stat().st_size} bytes")
            logger.debug(f"📁 File permissions: {oct(projects_file.stat().st_mode)[-3:]}")
            
            with open(projects_file, 'r') as f:
                content = f.read()
                logger.debug(f"📁 File content length: {len(content)} characters")
                logger.debug(f"📁 File content preview: {content[:200]}...")
                
                projects = json.loads(content)
                logger.info(f"📁 Successfully loaded {len(projects)} projects")
                return projects
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Failed to load projects: {e}")
            logger.debug(f"📁 Error type: {type(e).__name__}")
            return []
    else:
        logger.info(f"📁 Projects file doesn't exist, returning empty list")
    return []

def save_projects(projects):
    """Save projects to file"""
    logger.debug(f"💾 Saving {len(projects)} projects")
    logger.debug(f"💾 Data directory: {DATA_DIR}")
    logger.debug(f"💾 Data directory exists: {DATA_DIR.exists()}")
    
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"💾 Data directory created/verified")
    except Exception as e:
        logger.error(f"❌ Failed to create data directory: {e}")
        return False
    
    projects_file = get_projects_file()
    logger.debug(f"💾 Projects file path: {projects_file}")
    
    try:
        # Create backup if file exists
        if projects_file.exists():
            backup_file = projects_file.with_suffix('.json.backup')
            logger.debug(f"💾 Creating backup: {backup_file}")
            projects_file.rename(backup_file)
        
        with open(projects_file, 'w') as f:
            json.dump(projects, f, indent=2)
        
        logger.info(f"💾 Successfully saved {len(projects)} projects")
        logger.debug(f"💾 File size: {projects_file.stat().st_size} bytes")
        return True
    except IOError as e:
        logger.error(f"❌ Failed to save projects: {e}")
        logger.debug(f"💾 Error type: {type(e).__name__}")
        return False

def create_slug(name):
    """Convert project name to slug format"""
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
            f'https://api.machines.dev/v1/apps/{project_slug}',
            headers=headers,
            timeout=10
        )
        
        if app_response.status_code == 404:
            logger.info(f"⚠️ Fly.io app not found: {project_slug}")
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
        app_url = f"https://{project_slug}.fly.dev"
        
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
            'description': f'OpenVibe project: {repo_name}',
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

@projects_bp.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects, ordered alphabetically"""
    logger.info("📋 GET /api/projects - Fetching all projects")
    
    try:
        projects = load_projects()
        # Sort projects alphabetically by name
        projects.sort(key=lambda x: x.get('name', '').lower())
        
        logger.info(f"📊 Returning {len(projects)} projects")
        return jsonify({
            'projects': projects,
            'count': len(projects)
        })
    except Exception as e:
        logger.error(f"💥 Error fetching projects: {str(e)}")
        return jsonify({'error': 'Failed to fetch projects'}), 500

@projects_bp.route('/api/projects/<slug>', methods=['GET'])
def get_project(slug):
    """Get a specific project by slug with status information"""
    logger.info(f"📋 GET /api/projects/{slug} - Fetching project details")
    
    try:
        # Get UUID from headers for API keys
        user_uuid = request.headers.get('X-User-UUID')
        if user_uuid:
            user_uuid = user_uuid.strip()
        
        projects = load_projects()
        
        # Find project by slug
        project = next((p for p in projects if p.get('slug') == slug), None)
        if not project:
            logger.warning(f"❌ Project not found: {slug}")
            return jsonify({'error': 'Project not found'}), 404
        
        logger.info(f"📊 Found project: {project['name']}")
        
        # Get user's API keys if UUID is provided
        github_status = None
        fly_status = None
        
        if user_uuid:
            try:
                user_keys = load_user_keys(user_uuid)
                github_token = user_keys.get('github')
                fly_token = user_keys.get('fly')
                
                # Get GitHub status if token is available
                if github_token and project.get('github_url'):
                    github_status = get_github_status(project['github_url'], github_token)
                
                # Get Fly.io status if token is available
                if fly_token and project.get('slug'):
                    fly_status = get_fly_status(project['slug'], fly_token)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error getting status information: {str(e)}")
        
        # Add status information to project
        project_with_status = project.copy()
        if github_status:
            project_with_status['github_status'] = github_status
        if fly_status:
            project_with_status['fly_status'] = fly_status
        
        return jsonify(project_with_status)
    except Exception as e:
        logger.error(f"💥 Error fetching project: {str(e)}")
        return jsonify({'error': 'Failed to fetch project'}), 500

@projects_bp.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project with GitHub repo and Fly.io app"""
    logger.info("🆕 POST /api/projects - Creating new project")
    
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
            logger.warning("❌ Project name is required")
            return jsonify({'error': 'Project name is required'}), 400
        
        project_name = data['name'].strip()
        if not project_name:
            logger.warning("❌ Project name cannot be empty")
            return jsonify({'error': 'Project name cannot be empty'}), 400
        
        # Create slug from name (use provided slug if available, otherwise generate)
        project_slug = data.get('slug', create_slug(project_name)).strip()
        if not project_slug:
            project_slug = create_slug(project_name)
        
        if not project_slug:
            logger.warning("❌ Invalid project name - cannot create slug")
            return jsonify({'error': 'Invalid project name'}), 400
        
        logger.info(f"🔄 Creating project: {project_name} -> {project_slug}")
        
        # Load existing projects
        projects = load_projects()
        
        # Check if project with same slug already exists
        existing_project = next((p for p in projects if p.get('slug') == project_slug), None)
        if existing_project:
            logger.warning(f"❌ Project with slug '{project_slug}' already exists")
            return jsonify({'error': f'Project with name "{project_name}" already exists'}), 409
        
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
        logger.info(f"🐙 Creating GitHub repository: {project_slug}")
        github_success, github_result = create_github_repo(project_slug, github_token, fly_token)
        
        if not github_success:
            logger.error(f"❌ GitHub repo creation failed: {github_result}")
            return jsonify({'error': f'Failed to create GitHub repository: {github_result}'}), 500
        
        github_url = github_result
        logger.info(f"✅ GitHub repository created: {github_url}")
        
        # Create Fly.io app
        logger.info(f"🛩️ Creating Fly.io app: {project_slug}")
        fly_success, fly_result = create_fly_app(project_slug, fly_token)
        
        if not fly_success:
            logger.error(f"❌ Fly.io app creation failed: {fly_result}")
            # Don't fail the entire project creation if Fly.io fails
            # The user can manually create the app later
            logger.warning(f"⚠️ Continuing with project creation despite Fly.io failure")
            fly_app_name = None
        else:
            fly_app_name = project_slug
            logger.info(f"✅ Fly.io app created: {fly_app_name}")
        
        # Create project record
        project = {
            'id': len(projects) + 1,
            'name': project_name,
            'slug': project_slug,
            'github_url': github_url,
            'fly_app_name': fly_app_name,
            'created_at': datetime.utcnow().isoformat(),
            'created_by': user_uuid
        }
        
        # Add to projects list
        projects.append(project)
        
        # Save to file
        if not save_projects(projects):
            logger.error("❌ Failed to save project to file")
            return jsonify({'error': 'Failed to save project'}), 500
        
        logger.info(f"✅ Project created successfully: {project_name}")
        return jsonify({
            'message': 'Project created successfully',
            'project': project,
            'warnings': [] if fly_success else [f'Fly.io app creation failed: {fly_result}']
        }), 201
        
    except Exception as e:
        logger.error(f"💥 Error creating project: {str(e)}")
        return jsonify({'error': 'Failed to create project'}), 500

@projects_bp.route('/api/projects/<slug>', methods=['DELETE'])
def delete_project(slug):
    """Delete a project and its associated GitHub repo and Fly.io app"""
    logger.info(f"🗑️ DELETE /api/projects/{slug} - Deleting project")
    
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
        
        # Load projects
        projects = load_projects()
        
        # Find project by slug
        project = next((p for p in projects if p.get('slug') == slug), None)
        if not project:
            logger.warning(f"❌ Project not found: {slug}")
            return jsonify({'error': 'Project not found'}), 404
        
        logger.info(f"🔍 Found project to delete: {project['name']}")
        
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
        if project.get('github_url') and github_token:
            logger.info(f"🐙 Deleting GitHub repository: {project['github_url']}")
            github_success, github_message = delete_github_repo(project['github_url'], github_token)
            deletion_results['github_success'] = github_success
            if not github_success:
                deletion_results['github_error'] = github_message
                logger.warning(f"⚠️ GitHub deletion failed: {github_message}")
            else:
                logger.info(f"✅ GitHub repository deleted: {github_message}")
        else:
            logger.info("⚠️ Skipping GitHub deletion (no URL or token)")
        
        # Delete Fly.io app if name exists and token is available
        if project.get('fly_app_name') and fly_token:
            logger.info(f"🛩️ Deleting Fly.io app: {project['fly_app_name']}")
            fly_success, fly_message = delete_fly_app(project['fly_app_name'], fly_token)
            deletion_results['fly_success'] = fly_success
            if not fly_success:
                deletion_results['fly_error'] = fly_message
                logger.warning(f"⚠️ Fly.io deletion failed: {fly_message}")
            else:
                logger.info(f"✅ Fly.io app deleted: {fly_message}")
        else:
            logger.info("⚠️ Skipping Fly.io deletion (no app name or token)")
        
        # Remove project from list
        projects = [p for p in projects if p.get('slug') != slug]
        
        # Save updated projects list
        if save_projects(projects):
            logger.info(f"✅ Project {slug} removed from database")
        else:
            logger.error(f"❌ Failed to save projects after deletion")
            return jsonify({'error': 'Failed to update project database'}), 500
        
        # Delete associated conversations file
        try:
            conversations_file = get_conversations_file(project.get('id'))
            if conversations_file.exists():
                conversations_file.unlink()
                logger.info(f"✅ Deleted conversations file for project {slug}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete conversations file: {str(e)}")
        
        # Prepare response
        response_data = {
            'message': f'Project "{project.get("name")}" deleted successfully',
            'project_name': project.get('name'),
            'project_slug': slug,
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
        
        logger.info(f"✅ Project deletion completed: {slug}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"💥 Error deleting project: {str(e)}")
        return jsonify({'error': 'Failed to delete project'}), 500
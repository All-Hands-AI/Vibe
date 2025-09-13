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

def load_conversations(project_id):
    """Load conversations for a specific project from file"""
    conversations_file = get_conversations_file(project_id)
    logger.debug(f"📁 Loading conversations from: {conversations_file}")
    logger.debug(f"📁 File exists: {conversations_file.exists()}")
    
    if conversations_file.exists():
        try:
            logger.debug(f"📁 File size: {conversations_file.stat().st_size} bytes")
            
            with open(conversations_file, 'r') as f:
                content = f.read()
                logger.debug(f"📁 File content length: {len(content)} characters")
                
                conversations = json.loads(content)
                logger.info(f"📁 Successfully loaded {len(conversations)} conversations for project {project_id}")
                return conversations
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Failed to load conversations for project {project_id}: {e}")
            return []
    else:
        logger.info(f"📁 Conversations file doesn't exist for project {project_id}, returning empty list")
    return []

def save_conversations(project_id, conversations):
    """Save conversations for a specific project to file"""
    logger.debug(f"💾 Saving {len(conversations)} conversations for project {project_id}")
    
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"💾 Data directory created/verified")
    except Exception as e:
        logger.error(f"❌ Failed to create data directory: {e}")
        return False
    
    conversations_file = get_conversations_file(project_id)
    logger.debug(f"💾 Conversations file path: {conversations_file}")
    
    try:
        # Create backup if file exists
        if conversations_file.exists():
            backup_file = conversations_file.with_suffix('.json.backup')
            logger.debug(f"💾 Creating backup: {backup_file}")
            conversations_file.rename(backup_file)
        
        with open(conversations_file, 'w') as f:
            json.dump(conversations, f, indent=2)
        
        logger.info(f"💾 Successfully saved {len(conversations)} conversations for project {project_id}")
        logger.debug(f"💾 File size: {conversations_file.stat().st_size} bytes")
        return True
    except IOError as e:
        logger.error(f"❌ Failed to save conversations for project {project_id}: {e}")
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
                    logger.info(f"🔍 Checking GitHub status for {project['name']}")
                    github_status = get_github_status(project['github_url'], github_token)
                
                # Get Fly.io status if token is available
                if fly_token:
                    logger.info(f"🔍 Checking Fly.io status for {project['name']}")
                    fly_status = get_fly_status(project['slug'], fly_token)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error getting status information: {str(e)}")
                # Continue without status info
        
        # Add status information to project
        project_with_status = project.copy()
        project_with_status['github_status'] = github_status
        project_with_status['fly_status'] = fly_status
        
        logger.info(f"✅ Returning project details for: {project['name']}")
        return jsonify({
            'project': project_with_status
        })
        
    except Exception as e:
        logger.error(f"💥 Error fetching project: {str(e)}")
        return jsonify({'error': 'Failed to fetch project'}), 500

@projects_bp.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    logger.info("🆕 POST /api/projects - Creating new project")
    logger.debug(f"📥 Request headers: {dict(request.headers)}")
    logger.debug(f"📥 Request remote addr: {request.remote_addr}")
    logger.debug(f"📥 Request content type: {request.content_type}")
    
    try:
        # Get UUID from headers
        user_uuid = request.headers.get('X-User-UUID')
        logger.debug(f"🆔 Raw UUID from header: '{user_uuid}'")
        
        if not user_uuid:
            logger.warning("❌ X-User-UUID header is required")
            logger.debug(f"📋 Available headers: {list(request.headers.keys())}")
            return jsonify({'error': 'X-User-UUID header is required'}), 400
        
        user_uuid = user_uuid.strip()
        logger.debug(f"🆔 Cleaned UUID: '{user_uuid}' (length: {len(user_uuid)})")
        
        if not user_uuid:
            logger.warning("❌ Empty UUID provided in header")
            return jsonify({'error': 'UUID cannot be empty'}), 400
        
        # Get request data
        data = request.get_json()
        logger.debug(f"📥 Request data: {data}")
        
        if not data or 'name' not in data:
            logger.warning("❌ Project name is required")
            logger.debug(f"📥 Request data keys: {list(data.keys()) if data else 'None'}")
            return jsonify({'error': 'Project name is required'}), 400
        
        project_name = data['name'].strip()
        logger.debug(f"📝 Project name: '{project_name}' (length: {len(project_name)})")
        
        if not project_name:
            logger.warning("❌ Project name cannot be empty")
            return jsonify({'error': 'Project name cannot be empty'}), 400
        
        # Create slug from name
        slug = create_slug(project_name)
        if not slug:
            logger.warning("❌ Invalid project name - cannot create slug")
            return jsonify({'error': 'Invalid project name'}), 400
        
        logger.info(f"🔄 Creating project: {project_name} -> {slug}")
        
        # Load existing projects
        projects = load_projects()
        
        # Check if project with same slug already exists
        existing_project = next((p for p in projects if p.get('slug') == slug), None)
        if existing_project:
            logger.warning(f"❌ Project with slug '{slug}' already exists")
            return jsonify({'error': f'Project with name "{project_name}" already exists'}), 409
        
        # Get user's API keys for GitHub and Fly.io
        user_keys = load_user_keys(user_uuid)
        github_token = user_keys.get('github')
        fly_token = user_keys.get('fly')
        
        if not github_token:
            logger.warning(f"❌ GitHub API key not found for user {user_uuid[:8]}")
            return jsonify({'error': 'GitHub API key is required. Please set it up in integrations.'}), 400
        
        # Create Fly.io app first (only if Fly.io token is provided)
        fly_app_data = None
        if fly_token:
            logger.info(f"🛩️ Creating Fly.io app: {slug}")
            success, result = create_fly_app(slug, fly_token)
            
            if not success:
                logger.error(f"❌ Fly.io app creation failed: {result}")
                return jsonify({'error': result}), 409
            
            fly_app_data = result
            logger.info(f"✅ Fly.io app created successfully: {slug}")
        else:
            logger.warning(f"⚠️ No Fly.io token provided - skipping Fly.io app creation")
        
        # Create GitHub repository
        success, result = create_github_repo(slug, github_token, fly_token)
        if not success:
            logger.error(f"❌ Failed to create GitHub repo: {result}")
            
            # If we created a Fly.io app but GitHub repo creation failed, 
            # we should note this in the error but not delete the Fly.io app
            # as the user might want to use it manually
            if fly_app_data:
                logger.warning(f"⚠️ Fly.io app '{slug}' was created but GitHub repo creation failed")
                error_msg = f"GitHub repository creation failed: {result}. Note: Fly.io app '{slug}' was created successfully and can be used manually."
                return jsonify({'error': error_msg}), 500
            
            return jsonify({'error': result}), 500
        
        # Create project record
        project = {
            'id': len(projects) + 1,
            'name': project_name,
            'slug': slug,
            'github_url': result,
            'created_at': datetime.utcnow().isoformat(),
            'created_by': user_uuid
        }
        
        # Add Fly.io app information if available
        if fly_app_data:
            project['fly_app'] = {
                'id': fly_app_data.get('id'),
                'name': slug,
                'organization': fly_app_data.get('organization', {}).get('slug'),
                'created_at': fly_app_data.get('created_at')
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
            'project': project
        }), 201
        
    except Exception as e:
        logger.error(f"💥 Error creating project: {str(e)}")
        return jsonify({'error': 'Failed to create project'}), 500

@projects_bp.route('/api/projects/<int:project_id>/conversations', methods=['GET'])
def get_conversations(project_id):
    """Get all conversations for a specific project"""
    logger.info(f"📋 GET /api/projects/{project_id}/conversations - Fetching conversations")
    
    try:
        # Verify project exists
        projects = load_projects()
        project = next((p for p in projects if p.get('id') == project_id), None)
        if not project:
            logger.warning(f"❌ Project not found: {project_id}")
            return jsonify({'error': 'Project not found'}), 404
        
        conversations = load_conversations(project_id)
        # Sort conversations by creation date (newest first)
        conversations.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        logger.info(f"📊 Returning {len(conversations)} conversations for project {project_id}")
        return jsonify({
            'conversations': conversations,
            'count': len(conversations),
            'project_id': project_id
        })
    except Exception as e:
        logger.error(f"💥 Error fetching conversations: {str(e)}")
        return jsonify({'error': 'Failed to fetch conversations'}), 500

@projects_bp.route('/api/projects/<int:project_id>/conversations', methods=['POST'])
def create_conversation(project_id):
    """Create a new conversation for a specific project"""
    logger.info(f"🆕 POST /api/projects/{project_id}/conversations - Creating new conversation")
    
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
        
        # Verify project exists
        projects = load_projects()
        project = next((p for p in projects if p.get('id') == project_id), None)
        if not project:
            logger.warning(f"❌ Project not found: {project_id}")
            return jsonify({'error': 'Project not found'}), 404
        
        # Get request data
        data = request.get_json()
        if not data or 'name' not in data:
            logger.warning("❌ Conversation name is required")
            return jsonify({'error': 'Conversation name is required'}), 400
        
        conversation_name = data['name'].strip()
        if not conversation_name:
            logger.warning("❌ Conversation name cannot be empty")
            return jsonify({'error': 'Conversation name cannot be empty'}), 400
        
        # Create slug from name (use provided slug if available, otherwise generate)
        conversation_slug = data.get('slug', create_slug(conversation_name)).strip()
        if not conversation_slug:
            conversation_slug = create_slug(conversation_name)
        
        if not conversation_slug:
            logger.warning("❌ Invalid conversation name - cannot create slug")
            return jsonify({'error': 'Invalid conversation name'}), 400
        
        logger.info(f"🔄 Creating conversation: {conversation_name} -> {conversation_slug}")
        
        # Load existing conversations
        conversations = load_conversations(project_id)
        
        # Check if conversation with same slug already exists
        existing_conversation = next((c for c in conversations if c.get('slug') == conversation_slug), None)
        if existing_conversation:
            logger.warning(f"❌ Conversation with slug '{conversation_slug}' already exists")
            return jsonify({'error': f'Conversation with name "{conversation_name}" already exists'}), 409
        
        # Create conversation record
        conversation = {
            'id': len(conversations) + 1,
            'name': conversation_name,
            'slug': conversation_slug,
            'project_id': project_id,
            'created_at': datetime.utcnow().isoformat(),
            'created_by': user_uuid,
            'last_message_at': None,
            'message_count': 0
        }
        
        # Add to conversations list
        conversations.append(conversation)
        
        # Save to file
        if not save_conversations(project_id, conversations):
            logger.error("❌ Failed to save conversation to file")
            return jsonify({'error': 'Failed to save conversation'}), 500
        
        logger.info(f"✅ Conversation created successfully: {conversation_name}")
        return jsonify({
            'message': 'Conversation created successfully',
            'conversation': conversation
        }), 201
        
    except Exception as e:
        logger.error(f"💥 Error creating conversation: {str(e)}")
        return jsonify({'error': 'Failed to create conversation'}), 500
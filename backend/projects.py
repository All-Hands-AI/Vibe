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
            logger.warning(f"❌ Repository {owner}/{repo_name} already exists")
            return False, f"Repository {repo_name} already exists"
        
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
        
        # Create GitHub repository
        success, result = create_github_repo(slug, github_token, fly_token)
        if not success:
            logger.error(f"❌ Failed to create GitHub repo: {result}")
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
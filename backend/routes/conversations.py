from flask import Blueprint, jsonify, request
import json
import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Create Blueprint for conversations
conversations_bp = Blueprint('conversations', __name__)

# File-based storage utilities
DATA_DIR = Path('/data')

def get_conversations_file(project_id):
    """Get the path to the conversations.json file for a specific project"""
    return DATA_DIR / f'conversations_{project_id}.json'

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

@conversations_bp.route('/api/projects/<int:project_id>/conversations', methods=['GET'])
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

@conversations_bp.route('/api/projects/<int:project_id>/conversations', methods=['POST'])
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
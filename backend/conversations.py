"""
Conversations API endpoints for OpenHands Agent integration

This module provides REST API endpoints for managing conversations with OpenHands agents,
including conversation creation, message handling, and event tracking.
"""

from flask import Blueprint, jsonify, request
import os
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from keys import load_user_keys
logger = logging.getLogger(__name__)

# Create Blueprint for conversations
conversations_bp = Blueprint('conversations', __name__)

# Global agent loop manager instance
from agent_loop import AgentLoopManager, OPENHANDS_AVAILABLE

if OPENHANDS_AVAILABLE:
    agent_manager = AgentLoopManager()
    AGENT_MANAGER_AVAILABLE = True
    logger.info("✅ AgentLoopManager initialized successfully")
else:
    agent_manager = None
    AGENT_MANAGER_AVAILABLE = False
    logger.warning("⚠️ OpenHands SDK not available - conversation features disabled")

# File-based storage utilities
DATA_DIR = Path('/data')

def get_conversations_file(project_id):
    """Get the path to the conversations.json file for a specific project"""
    return DATA_DIR / f'conversations_{project_id}.json'

def load_conversations(project_id):
    """Load conversations for a specific project from file"""
    conversations_file = get_conversations_file(project_id)
    logger.debug(f"📁 Loading conversations from: {conversations_file}")
    
    if conversations_file.exists():
        try:
            with open(conversations_file, 'r') as f:
                conversations = json.load(f)
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
    except Exception as e:
        logger.error(f"❌ Failed to create data directory: {e}")
        return False
    
    conversations_file = get_conversations_file(project_id)
    
    try:
        # Create backup if file exists
        if conversations_file.exists():
            backup_file = conversations_file.with_suffix('.json.backup')
            conversations_file.rename(backup_file)
        
        with open(conversations_file, 'w') as f:
            json.dump(conversations, f, indent=2)
        
        logger.info(f"💾 Successfully saved {len(conversations)} conversations for project {project_id}")
        return True
    except IOError as e:
        logger.error(f"❌ Failed to save conversations for project {project_id}: {e}")
        return False

def get_user_api_keys(user_uuid):
    """Get API keys for a user"""
    user_keys = load_user_keys(user_uuid)
    return {
        'anthropic': user_keys.get('anthropic'),
        'github': user_keys.get('github'),
    }

@conversations_bp.route('/projects/<project_id>/conversations', methods=['POST'])
def create_conversation(project_id):
    """
    Create a new conversation for a project
    
    POST /projects/{id}/conversations
    - Creates a new conversation with ID
    - Creates a new branch on GitHub (adopts if already exists)
    - Creates a new PR for the branch (adopts if already exists)
    """
    logger.info(f"🎯 POST /projects/{project_id}/conversations - Creating new conversation")
    
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
    if not data:
        logger.warning("❌ Request body is required")
        return jsonify({'error': 'Request body is required'}), 400
    
    initial_message = data.get('message', '')
    if not initial_message:
        logger.warning("❌ Initial message is required")
        return jsonify({'error': 'Initial message is required'}), 400
    
    conversation_id = data.get('conversation_id') or str(uuid.uuid4())
    repo_url = data.get('repo_url')
    
    logger.info(f"🎯 Creating conversation {conversation_id} for project {project_id}")
    logger.debug(f"📝 Initial message: {initial_message[:100]}...")
    
    # Check if agent manager is available
    if not AGENT_MANAGER_AVAILABLE or agent_manager is None:
        logger.error("❌ OpenHands Agent SDK not available")
        return jsonify({
            'error': 'OpenHands Agent SDK not available. Please install the SDK to use conversation features.',
            'setup_instructions': 'See backend/OPENHANDS_INTEGRATION.md for setup instructions'
        }), 503
    
    # Get user API keys
    user_keys = get_user_api_keys(user_uuid)
    anthropic_key = user_keys.get('anthropic')
    github_token = user_keys.get('github')
    
    if not anthropic_key:
        logger.warning(f"❌ Anthropic API key not found for user {user_uuid[:8]}")
        return jsonify({'error': 'Anthropic API key is required. Please set it in integrations.'}), 400
    
    # Start the conversation with agent loop manager
    success, message, actual_conversation_id = agent_manager.start_conversation(
        project_id=project_id,
        initial_message=initial_message,
        api_key=anthropic_key,
        repo_url=repo_url,
        github_token=github_token,
        conversation_id=conversation_id
    )
    
    if not success:
        logger.error(f"❌ Failed to start conversation: {message}")
        return jsonify({'error': f'Failed to start conversation: {message}'}), 500
    
    # Load existing conversations
    conversations = load_conversations(project_id)
    
    # Create conversation record
    conversation_record = {
        'id': actual_conversation_id,
        'project_id': project_id,
        'user_uuid': user_uuid,
        'initial_message': initial_message,
        'repo_url': repo_url,
        'created_at': datetime.utcnow().isoformat(),
        'status': 'running',
        'branch_name': f"conversation-{actual_conversation_id[:8]}" if repo_url else None,
        'pr_number': None,  # Will be updated when PR is created
        'messages': [
            {
                'role': 'user',
                'content': initial_message,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
    }
    
    # Add to conversations list
    conversations.append(conversation_record)
    
    # Save conversations
    if not save_conversations(project_id, conversations):
        logger.error(f"❌ Failed to save conversation record")
        return jsonify({'error': 'Failed to save conversation record'}), 500
    
    logger.info(f"✅ Successfully created conversation {actual_conversation_id}")
    
    return jsonify({
        'id': actual_conversation_id,
        'project_id': project_id,
        'status': 'running',
        'message': message,
        'created_at': conversation_record['created_at'],
        'branch_name': conversation_record['branch_name'],
        'pr_number': conversation_record['pr_number']
    }), 201

@conversations_bp.route('/projects/<project_id>/conversations', methods=['GET'])
def list_conversations(project_id):
    """
    Get list of conversations for a project
    
    GET /projects/{id}/conversations
    - Retrieves list of conversations
    """
    logger.info(f"📋 GET /projects/{project_id}/conversations - Listing conversations")
    
    # Get UUID from headers
    user_uuid = request.headers.get('X-User-UUID')
    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        return jsonify({'error': 'X-User-UUID header is required'}), 400
    
    user_uuid = user_uuid.strip()
    
    # Load conversations from file
    conversations = load_conversations(project_id)
    
    # Filter conversations by user (optional - you might want all conversations for a project)
    # user_conversations = [conv for conv in conversations if conv.get('user_uuid') == user_uuid]
    
    # Get live status from agent manager (if available)
    for conversation in conversations:
        conv_id = conversation['id']
        if AGENT_MANAGER_AVAILABLE and agent_manager:
            live_status = agent_manager.get_conversation_status(conv_id)
            if live_status:
                conversation['live_status'] = live_status
            else:
                conversation['live_status'] = {'status': 'not_found', 'is_alive': False}
        else:
            conversation['live_status'] = {'status': 'sdk_unavailable', 'is_alive': False}
    
    logger.info(f"📋 Returning {len(conversations)} conversations for project {project_id}")
    
    return jsonify({
        'conversations': conversations,
        'total': len(conversations)
    })

@conversations_bp.route('/projects/<project_id>/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id, project_id):
    """
    Get a specific conversation
    
    GET /projects/{id}/conversations/{id}
    - Retrieves conversation including associated PR number
    """
    logger.info(f"🔍 GET /projects/{project_id}/conversations/{conversation_id} - Getting conversation")
    
    # Get UUID from headers
    user_uuid = request.headers.get('X-User-UUID')
    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        return jsonify({'error': 'X-User-UUID header is required'}), 400
    
    user_uuid = user_uuid.strip()
    
    # Load conversations from file
    conversations = load_conversations(project_id)
    
    # Find the conversation
    conversation = None
    for conv in conversations:
        if conv['id'] == conversation_id:
            conversation = conv
            break
    
    if not conversation:
        logger.warning(f"❌ Conversation {conversation_id} not found")
        return jsonify({'error': 'Conversation not found'}), 404
    
    # Get live status from agent manager (if available)
    if AGENT_MANAGER_AVAILABLE and agent_manager:
        live_status = agent_manager.get_conversation_status(conversation_id)
        if live_status:
            conversation['live_status'] = live_status
        else:
            conversation['live_status'] = {'status': 'not_found', 'is_alive': False}
    else:
        conversation['live_status'] = {'status': 'sdk_unavailable', 'is_alive': False}
    
    logger.info(f"✅ Found conversation {conversation_id}")
    
    return jsonify(conversation)

@conversations_bp.route('/projects/<project_id>/conversations/<conversation_id>', methods=['POST'])
def modify_conversation(conversation_id, project_id):
    """
    Modify a conversation
    
    POST /projects/{id}/conversations/{id}
    - Modifies conversation (currently not implemented for running conversations)
    """
    logger.info(f"✏️ POST /projects/{project_id}/conversations/{conversation_id} - Modifying conversation")
    
    # Get UUID from headers
    user_uuid = request.headers.get('X-User-UUID')
    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        return jsonify({'error': 'X-User-UUID header is required'}), 400
    
    # For now, return not implemented
    return jsonify({'error': 'Modifying running conversations is not yet implemented'}), 501

@conversations_bp.route('/projects/<project_id>/conversations/<conversation_id>/messages', methods=['POST'])
def create_message(conversation_id, project_id):
    """
    Create a new message in a conversation
    
    POST /projects/{id}/conversations/{id}/messages
    - Creates a new message
    """
    logger.info(f"💬 POST /projects/{project_id}/conversations/{conversation_id}/messages - Creating message")
    
    # Get UUID from headers
    user_uuid = request.headers.get('X-User-UUID')
    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        return jsonify({'error': 'X-User-UUID header is required'}), 400
    
    user_uuid = user_uuid.strip()
    
    # Get request data
    data = request.get_json()
    if not data:
        logger.warning("❌ Request body is required")
        return jsonify({'error': 'Request body is required'}), 400
    
    message_content = data.get('message', '')
    if not message_content:
        logger.warning("❌ Message content is required")
        return jsonify({'error': 'Message content is required'}), 400
    
    # Check if agent manager is available
    if not AGENT_MANAGER_AVAILABLE or agent_manager is None:
        logger.error("❌ OpenHands Agent SDK not available")
        return jsonify({
            'error': 'OpenHands Agent SDK not available. Please install the SDK to use conversation features.',
            'setup_instructions': 'See backend/OPENHANDS_INTEGRATION.md for setup instructions'
        }), 503
    
    # Try to send message to the running conversation
    success, result_message = agent_manager.send_message_to_conversation(conversation_id, message_content)
    
    if not success:
        logger.warning(f"❌ Failed to send message: {result_message}")
        return jsonify({'error': result_message}), 501
    
    # Load conversations and update the message history
    conversations = load_conversations(project_id)
    
    # Find and update the conversation
    for conversation in conversations:
        if conversation['id'] == conversation_id:
            conversation['messages'].append({
                'role': 'user',
                'content': message_content,
                'timestamp': datetime.utcnow().isoformat()
            })
            break
    
    # Save updated conversations
    save_conversations(project_id, conversations)
    
    logger.info(f"✅ Message sent to conversation {conversation_id}")
    
    return jsonify({
        'message': 'Message sent successfully',
        'conversation_id': conversation_id,
        'timestamp': datetime.utcnow().isoformat()
    }), 201

@conversations_bp.route('/projects/<project_id>/conversations/<conversation_id>/events', methods=['GET'])
def get_conversation_events(conversation_id, project_id):
    """
    Get events for a conversation
    
    GET /projects/{id}/conversations/{id}/events
    - Retrieves a list of all events that have happened in this conversation
    """
    logger.info(f"📊 GET /projects/{project_id}/conversations/{conversation_id}/events - Getting events")
    
    # Get UUID from headers
    user_uuid = request.headers.get('X-User-UUID')
    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        return jsonify({'error': 'X-User-UUID header is required'}), 400
    
    user_uuid = user_uuid.strip()
    
    # Check if agent manager is available
    if not AGENT_MANAGER_AVAILABLE or agent_manager is None:
        logger.error("❌ OpenHands Agent SDK not available")
        return jsonify({
            'error': 'OpenHands Agent SDK not available. Please install the SDK to use conversation features.',
            'setup_instructions': 'See backend/OPENHANDS_INTEGRATION.md for setup instructions'
        }), 503
    
    # Get events from agent manager
    events = agent_manager.get_conversation_events(conversation_id)
    
    logger.info(f"📊 Returning {len(events)} events for conversation {conversation_id}")
    
    return jsonify({
        'conversation_id': conversation_id,
        'events': events,
        'total': len(events)
    })

@conversations_bp.route('/conversations/cleanup', methods=['POST'])
def cleanup_conversations():
    """
    Clean up finished conversations
    
    POST /conversations/cleanup
    - Removes finished conversation threads from memory
    """
    logger.info("🧹 POST /conversations/cleanup - Cleaning up finished conversations")
    
    # Get UUID from headers
    user_uuid = request.headers.get('X-User-UUID')
    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        return jsonify({'error': 'X-User-UUID header is required'}), 400
    
    # Check if agent manager is available
    if not AGENT_MANAGER_AVAILABLE or agent_manager is None:
        logger.warning("⚠️ OpenHands Agent SDK not available - no cleanup needed")
        return jsonify({'message': 'OpenHands Agent SDK not available - no active conversations to cleanup'})
    
    # Cleanup finished conversations
    agent_manager.cleanup_finished_conversations()
    
    logger.info("✅ Cleanup completed")
    
    return jsonify({'message': 'Cleanup completed successfully'})

@conversations_bp.route('/conversations/status', methods=['GET'])
def get_all_conversation_status():
    """
    Get status of all running conversations
    
    GET /conversations/status
    - Returns status of all conversations across all projects
    """
    logger.info("📊 GET /conversations/status - Getting all conversation status")
    
    # Get UUID from headers
    user_uuid = request.headers.get('X-User-UUID')
    if not user_uuid:
        logger.warning("❌ X-User-UUID header is required")
        return jsonify({'error': 'X-User-UUID header is required'}), 400
    
    # Check if agent manager is available
    if not AGENT_MANAGER_AVAILABLE or agent_manager is None:
        logger.warning("⚠️ OpenHands Agent SDK not available")
        return jsonify({
            'conversations': [],
            'total': 0,
            'message': 'OpenHands Agent SDK not available - no active conversations'
        })
    
    # Get all conversations from agent manager
    all_conversations = agent_manager.list_conversations()
    
    logger.info(f"📊 Returning status for {len(all_conversations)} conversations")
    
    return jsonify({
        'conversations': all_conversations,
        'total': len(all_conversations)
    })
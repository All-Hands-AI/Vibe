from flask import Blueprint, jsonify, request
import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Create Blueprint for riffs
riffs_bp = Blueprint('riffs', __name__)

# File-based storage utilities
DATA_DIR = Path('/data')

def get_riffs_file(app_slug):
    """Get the path to the riffs.json file for a specific app"""
    return DATA_DIR / f'riffs_{app_slug}.json'

def get_apps_file():
    """Get the path to the apps.json file"""
    return DATA_DIR / 'apps.json'

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

def load_riffs(app_slug):
    """Load riffs for a specific app from file"""
    riffs_file = get_riffs_file(app_slug)
    logger.debug(f"📁 Loading riffs from: {riffs_file}")
    logger.debug(f"📁 File exists: {riffs_file.exists()}")
    
    if riffs_file.exists():
        try:
            logger.debug(f"📁 File size: {riffs_file.stat().st_size} bytes")
            
            with open(riffs_file, 'r') as f:
                content = f.read()
                logger.debug(f"📁 File content length: {len(content)} characters")
                
                riffs = json.loads(content)
                logger.info(f"📁 Successfully loaded {len(riffs)} riffs for app {app_slug}")
                return riffs
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Failed to load riffs for app {app_slug}: {e}")
            return []
    else:
        logger.info(f"📁 Riffs file doesn't exist for app {app_slug}, returning empty list")
    return []

def save_riffs(app_slug, riffs):
    """Save riffs for a specific app to file"""
    logger.debug(f"💾 Saving {len(riffs)} riffs for app {app_slug}")
    
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"💾 Data directory created/verified")
    except Exception as e:
        logger.error(f"❌ Failed to create data directory: {e}")
        return False
    
    riffs_file = get_riffs_file(app_slug)
    logger.debug(f"💾 Riffs file path: {riffs_file}")
    
    try:
        # Create backup if file exists
        if riffs_file.exists():
            backup_file = riffs_file.with_suffix('.json.backup')
            logger.debug(f"💾 Creating backup: {backup_file}")
            riffs_file.rename(backup_file)
        
        with open(riffs_file, 'w') as f:
            json.dump(riffs, f, indent=2)
        
        logger.info(f"💾 Successfully saved {len(riffs)} riffs for app {app_slug}")
        logger.debug(f"💾 File size: {riffs_file.stat().st_size} bytes")
        return True
    except IOError as e:
        logger.error(f"❌ Failed to save riffs for app {app_slug}: {e}")
        return False

def create_slug(name):
    """Convert riff name to slug format"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

@riffs_bp.route('/api/apps/<slug>/riffs', methods=['GET'])
def get_riffs(slug):
    """Get all riffs for a specific app"""
    logger.info(f"📋 GET /api/apps/{slug}/riffs - Fetching riffs")
    
    try:
        # Verify app exists
        apps = load_apps()
        app = next((a for a in apps if a.get('slug') == slug), None)
        if not app:
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({'error': 'App not found'}), 404
        
        riffs = load_riffs(slug)
        # Sort riffs by creation date (newest first)
        riffs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        logger.info(f"📊 Returning {len(riffs)} riffs for app {slug}")
        return jsonify({
            'riffs': riffs,
            'count': len(riffs),
            'app_slug': slug
        })
    except Exception as e:
        logger.error(f"💥 Error fetching riffs: {str(e)}")
        return jsonify({'error': 'Failed to fetch riffs'}), 500

@riffs_bp.route('/api/apps/<slug>/riffs', methods=['POST'])
def create_riff(slug):
    """Create a new riff for a specific app"""
    logger.info(f"🆕 POST /api/apps/{slug}/riffs - Creating new riff")
    
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
        
        # Verify app exists
        apps = load_apps()
        app = next((a for a in apps if a.get('slug') == slug), None)
        if not app:
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({'error': 'App not found'}), 404
        
        # Get request data
        data = request.get_json()
        if not data or 'name' not in data:
            logger.warning("❌ Riff name is required")
            return jsonify({'error': 'Riff name is required'}), 400
        
        riff_name = data['name'].strip()
        if not riff_name:
            logger.warning("❌ Riff name cannot be empty")
            return jsonify({'error': 'Riff name cannot be empty'}), 400
        
        # Create slug from name (use provided slug if available, otherwise generate)
        riff_slug = data.get('slug', create_slug(riff_name)).strip()
        if not riff_slug:
            riff_slug = create_slug(riff_name)
        
        if not riff_slug:
            logger.warning("❌ Invalid riff name - cannot create slug")
            return jsonify({'error': 'Invalid riff name'}), 400
        
        logger.info(f"🔄 Creating riff: {riff_name} -> {riff_slug}")
        
        # Load existing riffs
        riffs = load_riffs(slug)
        
        # Check if riff with same slug already exists
        existing_riff = next((r for r in riffs if r.get('slug') == riff_slug), None)
        if existing_riff:
            logger.warning(f"❌ Riff with slug '{riff_slug}' already exists")
            return jsonify({'error': f'Riff with name "{riff_name}" already exists'}), 409
        
        # Create riff record
        riff = {
            'slug': riff_slug,
            'name': riff_name,
            'app_slug': slug,
            'created_at': datetime.utcnow().isoformat(),
            'created_by': user_uuid,
            'last_message_at': None,
            'message_count': 0
        }
        
        # Add to riffs list
        riffs.append(riff)
        
        # Save to file
        if not save_riffs(slug, riffs):
            logger.error("❌ Failed to save riff to file")
            return jsonify({'error': 'Failed to save riff'}), 500
        
        logger.info(f"✅ Riff created successfully: {riff_name}")
        return jsonify({
            'message': 'Riff created successfully',
            'riff': riff
        }), 201
        
    except Exception as e:
        logger.error(f"💥 Error creating riff: {str(e)}")
        return jsonify({'error': 'Failed to create riff'}), 500

# Message storage utilities
def get_messages_dir(user_uuid, app_slug, riff_slug):
    """Get the directory path for messages"""
    return DATA_DIR / user_uuid / 'apps' / app_slug / 'riffs' / riff_slug / 'messages'

def get_messages_file(user_uuid, app_slug, riff_slug):
    """Get the path to the messages.json file for a specific riff"""
    return get_messages_dir(user_uuid, app_slug, riff_slug) / 'messages.json'

def load_messages(user_uuid, app_slug, riff_slug):
    """Load messages for a specific riff from file"""
    messages_file = get_messages_file(user_uuid, app_slug, riff_slug)
    logger.debug(f"📁 Loading messages from: {messages_file}")
    
    if messages_file.exists():
        try:
            with open(messages_file, 'r') as f:
                content = f.read()
                messages = json.loads(content)
                logger.info(f"📁 Successfully loaded {len(messages)} messages for riff {riff_slug}")
                return messages
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Failed to load messages for riff {riff_slug}: {e}")
            return []
    else:
        logger.info(f"📁 Messages file doesn't exist for riff {riff_slug}, returning empty list")
    return []

def save_messages(user_uuid, app_slug, riff_slug, messages):
    """Save messages for a specific riff to file"""
    logger.debug(f"💾 Saving {len(messages)} messages for riff {riff_slug}")
    
    try:
        messages_dir = get_messages_dir(user_uuid, app_slug, riff_slug)
        messages_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"💾 Messages directory created/verified: {messages_dir}")
    except Exception as e:
        logger.error(f"❌ Failed to create messages directory: {e}")
        return False
    
    messages_file = get_messages_file(user_uuid, app_slug, riff_slug)
    logger.debug(f"💾 Messages file path: {messages_file}")
    
    try:
        # Create backup if file exists
        if messages_file.exists():
            backup_file = messages_file.with_suffix('.json.backup')
            logger.debug(f"💾 Creating backup: {backup_file}")
            messages_file.rename(backup_file)
        
        with open(messages_file, 'w') as f:
            json.dump(messages, f, indent=2)
        
        logger.info(f"💾 Successfully saved {len(messages)} messages for riff {riff_slug}")
        return True
    except IOError as e:
        logger.error(f"❌ Failed to save messages for riff {riff_slug}: {e}")
        return False

def update_riff_message_stats(app_slug, riff_slug, message_count, last_message_at):
    """Update riff statistics with message count and last message time"""
    try:
        riffs = load_riffs(app_slug)
        riff = next((r for r in riffs if r.get('slug') == riff_slug), None)
        if riff:
            riff['message_count'] = message_count
            riff['last_message_at'] = last_message_at
            save_riffs(app_slug, riffs)
            logger.debug(f"📊 Updated riff stats: {message_count} messages, last at {last_message_at}")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to update riff stats: {e}")
    return False

@riffs_bp.route('/api/apps/<slug>/riffs/<riff_slug>/messages', methods=['GET'])
def get_messages(slug, riff_slug):
    """Get all messages for a specific riff"""
    logger.info(f"📋 GET /api/apps/{slug}/riffs/{riff_slug}/messages - Fetching messages")
    
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
        
        # Verify app exists
        apps = load_apps()
        app = next((a for a in apps if a.get('slug') == slug), None)
        if not app:
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({'error': 'App not found'}), 404
        
        # Verify riff exists
        riffs = load_riffs(slug)
        riff = next((r for r in riffs if r.get('slug') == riff_slug), None)
        if not riff:
            logger.warning(f"❌ Riff not found: {riff_slug}")
            return jsonify({'error': 'Riff not found'}), 404
        
        messages = load_messages(user_uuid, slug, riff_slug)
        # Sort messages by creation time (oldest first for chat display)
        messages.sort(key=lambda x: x.get('created_at', ''))
        
        logger.info(f"📊 Returning {len(messages)} messages for riff {riff_slug}")
        return jsonify({
            'messages': messages,
            'count': len(messages),
            'app_slug': slug,
            'riff_slug': riff_slug
        })
    except Exception as e:
        logger.error(f"💥 Error fetching messages: {str(e)}")
        return jsonify({'error': 'Failed to fetch messages'}), 500

@riffs_bp.route('/api/apps/<slug>/riffs/messages', methods=['POST'])
def create_message(slug):
    """Create a new message for a specific riff"""
    logger.info(f"🆕 POST /api/apps/{slug}/riffs/messages - Creating new message")
    
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
        
        # Verify app exists
        apps = load_apps()
        app = next((a for a in apps if a.get('slug') == slug), None)
        if not app:
            logger.warning(f"❌ App not found: {slug}")
            return jsonify({'error': 'App not found'}), 404
        
        # Get request data
        data = request.get_json()
        if not data:
            logger.warning("❌ Request body is required")
            return jsonify({'error': 'Request body is required'}), 400
        
        riff_slug = data.get('riff_slug', '').strip()
        if not riff_slug:
            logger.warning("❌ Riff slug is required")
            return jsonify({'error': 'Riff slug is required'}), 400
        
        content = data.get('content', '').strip()
        if not content:
            logger.warning("❌ Message content is required")
            return jsonify({'error': 'Message content is required'}), 400
        
        # Verify riff exists
        riffs = load_riffs(slug)
        riff = next((r for r in riffs if r.get('slug') == riff_slug), None)
        if not riff:
            logger.warning(f"❌ Riff not found: {riff_slug}")
            return jsonify({'error': 'Riff not found'}), 404
        
        logger.info(f"🔄 Creating message for riff: {riff_slug}")
        
        # Load existing messages
        messages = load_messages(user_uuid, slug, riff_slug)
        
        # Create message record
        message_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        message = {
            'id': message_id,
            'content': content,
            'riff_slug': riff_slug,
            'app_slug': slug,
            'created_at': created_at,
            'created_by': user_uuid,
            'type': data.get('type', 'text'),  # text, file, etc.
            'metadata': data.get('metadata', {})  # Additional data like file info
        }
        
        # Add to messages list
        messages.append(message)
        
        # Save to file
        if not save_messages(user_uuid, slug, riff_slug, messages):
            logger.error("❌ Failed to save message to file")
            return jsonify({'error': 'Failed to save message'}), 500
        
        # Update riff statistics
        update_riff_message_stats(slug, riff_slug, len(messages), created_at)
        
        logger.info(f"✅ Message created successfully for riff: {riff_slug}")
        return jsonify({
            'message': 'Message created successfully',
            'data': message
        }), 201
        
    except Exception as e:
        logger.error(f"💥 Error creating message: {str(e)}")
        return jsonify({'error': 'Failed to create message'}), 500
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging
import sys
from datetime import datetime
from routes.basic import basic_bp
from routes.integrations import integrations_bp
from routes.projects import projects_bp
from routes.conversations import conversations_bp

# No-op import to ensure agent-sdk loads properly
import openhands.sdk  # noqa: F401

# Configure logging for Fly.io - stdout only with enhanced formatting
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(basic_bp)
app.register_blueprint(integrations_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(conversations_bp)

# Enhanced startup logging
logger.info("=" * 80)
logger.info("🚀 OpenVibe Backend starting up...")
logger.info("=" * 80)

# Environment information
logger.info(f"🌍 Environment Variables:")
logger.info(f"  - FLY_APP_NAME: {os.environ.get('FLY_APP_NAME', 'local')}")
logger.info(f"  - FLASK_ENV: {os.environ.get('FLASK_ENV', 'production')}")
logger.info(f"  - PORT: {os.environ.get('PORT', '8000')}")
logger.info(f"  - PWD: {os.environ.get('PWD', 'unknown')}")

# System information
logger.info(f"🐍 Python version: {sys.version}")
logger.info(f"📦 Flask app name: {app.name}")

# File system checks
from pathlib import Path
data_dir = Path('/data')
logger.info(f"📁 Data directory status:")
logger.info(f"  - Path: {data_dir}")
logger.info(f"  - Exists: {data_dir.exists()}")
logger.info(f"  - Is directory: {data_dir.is_dir() if data_dir.exists() else 'N/A'}")
logger.info(f"  - Permissions: {oct(data_dir.stat().st_mode)[-3:] if data_dir.exists() else 'N/A'}")

if data_dir.exists():
    try:
        subdirs = list(data_dir.iterdir())
        logger.info(f"  - Subdirectories: {len(subdirs)}")
        for subdir in subdirs[:5]:  # Show first 5 subdirs
            logger.info(f"    - {subdir.name}")
        if len(subdirs) > 5:
            logger.info(f"    - ... and {len(subdirs) - 5} more")
    except Exception as e:
        logger.error(f"  - Error reading directory: {e}")

logger.info("=" * 80)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"🚀 Starting Flask server on port {port}")
    logger.info(f"🌐 Server will be accessible at http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
from flask import Flask
from flask_cors import CORS
import os
import logging
import sys
from routes.basic import basic_bp
from routes.integrations import integrations_bp
from routes.apps import apps_bp
from routes.riffs import riffs_bp
from utils.logging import get_logger, log_system_info

# No-op import to ensure agent-sdk loads properly
try:
    import openhands.sdk  # noqa: F401
except ImportError:
    # SDK not available, continue without it (useful for testing)
    pass

# Initialize mock mode if needed for development/testing
if os.environ.get("MOCK_MODE", "false").lower() == "true":
    try:
        from mocks import patch_requests_for_mock_mode
        patch_requests_for_mock_mode()
        print("🎭 MOCK_MODE enabled - API calls will be mocked")
    except ImportError:
        print("⚠️ MOCK_MODE enabled but mocks module not available")

# Configure logging for Fly.io - stdout only with simplified formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname).1s %(message)s",
    stream=sys.stdout,
)

logger = get_logger(__name__)

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(basic_bp)
app.register_blueprint(integrations_bp)
app.register_blueprint(apps_bp)
app.register_blueprint(riffs_bp)

# Enhanced startup logging using centralized utility
log_system_info(logger)
logger.info(f"📦 Flask app name: {app.name}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Starting Flask server on port {port}")
    logger.info(f"🌐 Server will be accessible at http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)

import logging
import sys
import os

# Configure logging FIRST, before any other imports that might use logging
# Fly.io already adds timestamps and log levels, so we only need the message
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    stream=sys.stdout,
    force=True,  # Force reconfiguration even if logging was already configured
)

# Also configure the root logger explicitly to ensure our format is used
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Remove any existing handlers and add our own
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Add a single StreamHandler with our minimal format
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(message)s"))
root_logger.addHandler(handler)

# Now import everything else
from flask import Flask
from flask_cors import CORS
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

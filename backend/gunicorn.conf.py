"""
Gunicorn configuration for OpenVibe backend.

This configuration disables gunicorn's default logging to prevent
interference with Flask's logging configuration, which is optimized
for Fly.io deployment.
"""

import sys
import logging

# Server socket
bind = "0.0.0.0:8000"
workers = 1

# Completely disable gunicorn's logging
accesslog = None
errorlog = None
disable_redirect_access_to_syslog = True

# Don't capture output - let Flask handle it directly
capture_output = False

# Disable gunicorn's loggers
def on_starting(server):
    """Disable gunicorn's loggers when starting."""
    # Get gunicorn's loggers and disable them
    gunicorn_logger = logging.getLogger("gunicorn")
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    gunicorn_access_logger = logging.getLogger("gunicorn.access")
    
    # Set them to a high level to effectively disable them
    gunicorn_logger.setLevel(logging.CRITICAL + 1)
    gunicorn_error_logger.setLevel(logging.CRITICAL + 1)
    gunicorn_access_logger.setLevel(logging.CRITICAL + 1)
    
    # Remove all handlers
    gunicorn_logger.handlers = []
    gunicorn_error_logger.handlers = []
    gunicorn_access_logger.handlers = []
"""
Centralized logging utilities for OpenVibe backend.

This module provides a consistent logging interface across the application.
The logging configuration is centralized in app.py using the minimal format:
"%(message)s" which shows only the message content since Fly.io already
provides timestamps and log levels in its output.

Usage:
    from utils.logging import get_logger

    logger = get_logger(__name__)
    logger.info("This is an info message")
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    This function ensures all loggers use the centralized configuration
    from app.py with the minimal format optimized for Fly.io.

    Args:
        name: The logger name, typically __name__ from the calling module

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)


def log_system_info(logger: logging.Logger) -> None:
    """
    Log system information for debugging purposes.

    Args:
        logger: The logger instance to use
    """
    import sys
    import os
    from pathlib import Path

    logger.info("🚀 OpenVibe Backend System Information")
    logger.info("=" * 50)

    # Python information
    logger.info(f"🐍 Python version: {sys.version}")
    logger.info(f"📦 Python executable: {sys.executable}")

    # Environment information
    logger.info(f"🌍 Environment Variables:")
    logger.info(f"  - FLY_APP_NAME: {os.environ.get('FLY_APP_NAME', 'local')}")
    logger.info(f"  - FLASK_ENV: {os.environ.get('FLASK_ENV', 'production')}")
    logger.info(f"  - PORT: {os.environ.get('PORT', '8000')}")
    logger.info(f"  - PWD: {os.environ.get('PWD', 'unknown')}")

    # File system information
    data_dir = Path("/data")
    logger.info(f"📁 Data directory status:")
    logger.info(f"  - Path: {data_dir}")
    logger.info(f"  - Exists: {data_dir.exists()}")
    logger.info(
        f"  - Is directory: {data_dir.is_dir() if data_dir.exists() else 'N/A'}"
    )

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

    logger.info("=" * 50)


# Convenience function for common logging patterns
def log_api_request(
    logger: logging.Logger, method: str, endpoint: str, user_id: str = None
) -> None:
    """
    Log an API request in a consistent format.

    Args:
        logger: The logger instance to use
        method: HTTP method (GET, POST, etc.)
        endpoint: The API endpoint
        user_id: Optional user identifier
    """
    user_info = f" (user: {user_id[:8]})" if user_id else ""
    logger.info(f"📡 {method} {endpoint}{user_info}")


def log_api_response(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    user_id: str = None,
) -> None:
    """
    Log an API response in a consistent format.

    Args:
        logger: The logger instance to use
        method: HTTP method (GET, POST, etc.)
        endpoint: The API endpoint
        status_code: HTTP status code
        user_id: Optional user identifier
    """
    user_info = f" (user: {user_id[:8]})" if user_id else ""
    status_emoji = (
        "✅" if 200 <= status_code < 300 else "❌" if status_code >= 400 else "⚠️"
    )
    logger.info(f"{status_emoji} {method} {endpoint} -> {status_code}{user_info}")

"""
Base storage class for OpenVibe backend.
Provides common file operations and utilities for all storage classes.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional
import shutil

logger = logging.getLogger(__name__)

# Base data directory
DATA_DIR = Path("/data")


class BaseStorage:
    """Base storage class with common file operations"""

    def __init__(self, user_uuid: str):
        self.user_uuid = user_uuid
        self.user_dir = DATA_DIR / user_uuid

    def ensure_directory(self, path: Path) -> bool:
        """Ensure directory exists"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Directory ensured: {path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create directory {path}: {e}")
            return False

    def read_json_file(self, file_path: Path) -> Optional[Any]:
        """Read JSON data from file"""
        logger.debug(f"📖 Reading JSON file: {file_path}")

        if not file_path.exists():
            logger.debug(f"📖 File doesn't exist: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                logger.debug(f"📖 File content length: {len(content)} characters")

                if not content.strip():
                    logger.debug(f"📖 Empty file: {file_path}")
                    return None

                data = json.loads(content)
                logger.debug(f"📖 Successfully loaded JSON from: {file_path}")
                return data

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Failed to read JSON file {file_path}: {e}")
            return None

    def write_json_file(
        self, file_path: Path, data: Any, create_backup: bool = True
    ) -> bool:
        """Write JSON data to file with atomic operation"""
        logger.debug(f"💾 Writing JSON file: {file_path}")

        # Ensure parent directory exists
        if not self.ensure_directory(file_path.parent):
            return False

        try:
            # Create backup if file exists and backup is requested
            if create_backup and file_path.exists():
                backup_file = file_path.with_suffix(".json.backup")
                logger.debug(f"💾 Creating backup: {backup_file}")
                shutil.copy2(file_path, backup_file)

            # Write to temporary file first for atomic operation
            temp_file = file_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic move
            temp_file.replace(file_path)

            logger.debug(f"💾 Successfully wrote JSON to: {file_path}")
            logger.debug(f"💾 File size: {file_path.stat().st_size} bytes")
            return True

        except (IOError, OSError) as e:
            logger.error(f"❌ Failed to write JSON file {file_path}: {e}")
            # Clean up temp file if it exists
            temp_file = file_path.with_suffix(".tmp")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False

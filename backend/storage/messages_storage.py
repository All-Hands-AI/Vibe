"""
Messages storage class for OpenVibe backend.
Handles message data storage and management within riffs.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from .base_storage import BaseStorage

logger = logging.getLogger(__name__)


class MessagesStorage(BaseStorage):
    """Storage class for messages within riffs"""

    def get_messages_file_path(self, app_slug: str, riff_slug: str) -> Path:
        """Get path to messages.json file"""
        return self.user_dir / "apps" / app_slug / "riffs" / riff_slug / "messages.json"

    def load_messages(self, app_slug: str, riff_slug: str) -> List[Dict[str, Any]]:
        """Load all messages for a specific riff"""
        logger.info(
            f"💬 Loading messages for riff: {app_slug}/{riff_slug} for user {self.user_uuid[:8]}..."
        )

        messages_file = self.get_messages_file_path(app_slug, riff_slug)
        data = self.read_json_file(messages_file)

        if data is None:
            logger.debug(f"💬 No messages file found for riff: {app_slug}/{riff_slug}")
            return []

        if not isinstance(data, list):
            logger.error(f"❌ Invalid messages data format for {app_slug}/{riff_slug}")
            return []

        logger.info(f"💬 Successfully loaded {len(data)} messages for riff: {app_slug}/{riff_slug}")
        return data

    def save_messages(self, app_slug: str, riff_slug: str, messages: List[Dict[str, Any]]) -> bool:
        """Save all messages for a specific riff"""
        logger.info(
            f"💾 Saving {len(messages)} messages for riff: {app_slug}/{riff_slug} for user {self.user_uuid[:8]}..."
        )

        messages_file = self.get_messages_file_path(app_slug, riff_slug)
        success = self.write_json_file(messages_file, messages)

        if success:
            logger.info(f"✅ Messages saved successfully for riff: {app_slug}/{riff_slug}")
        else:
            logger.error(f"❌ Failed to save messages for riff: {app_slug}/{riff_slug}")

        return success

    def add_message(self, app_slug: str, riff_slug: str, message: Dict[str, Any]) -> bool:
        """Add a single message to a riff"""
        logger.info(
            f"➕ Adding message to riff: {app_slug}/{riff_slug} for user {self.user_uuid[:8]}..."
        )

        # Load existing messages
        messages = self.load_messages(app_slug, riff_slug)

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add message ID if not present
        if "id" not in message:
            message["id"] = len(messages) + 1

        # Add the new message
        messages.append(message)

        # Save updated messages
        success = self.save_messages(app_slug, riff_slug, messages)

        if success:
            logger.info(f"✅ Message added successfully to riff: {app_slug}/{riff_slug}")
        else:
            logger.error(f"❌ Failed to add message to riff: {app_slug}/{riff_slug}")

        return success

    def get_message_count(self, app_slug: str, riff_slug: str) -> int:
        """Get the number of messages in a riff"""
        messages = self.load_messages(app_slug, riff_slug)
        return len(messages)

    def get_latest_message(self, app_slug: str, riff_slug: str) -> Optional[Dict[str, Any]]:
        """Get the most recent message from a riff"""
        messages = self.load_messages(app_slug, riff_slug)
        if not messages:
            return None
        
        # Messages are stored in chronological order, so the last one is the latest
        return messages[-1]

    def clear_messages(self, app_slug: str, riff_slug: str) -> bool:
        """Clear all messages from a riff"""
        logger.info(
            f"🗑️ Clearing messages for riff: {app_slug}/{riff_slug} for user {self.user_uuid[:8]}..."
        )

        return self.save_messages(app_slug, riff_slug, [])

    def messages_exist(self, app_slug: str, riff_slug: str) -> bool:
        """Check if messages file exists for a riff"""
        messages_file = self.get_messages_file_path(app_slug, riff_slug)
        return messages_file.exists()
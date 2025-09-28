"""
Conversation factory for creating remote and local conversations.
Handles the complexity of conversation creation with proper error handling and retry logic.
"""

import sys
import os
import uuid
import shutil
from typing import List, Callable, Optional
from utils.logging import get_logger
from .runtime_handler import RuntimeHandler, ensure_directory_exists

# Add the site-packages to the path for openhands imports
sys.path.insert(0, ".venv/lib/python3.12/site-packages")

from openhands.sdk import (
    Agent,
    Conversation,
    LocalFileStore,
)

# Import runtime service for checking runtime alive status
from services.runtime_service import runtime_service

logger = get_logger(__name__)


class ConversationFactory:
    """
    Factory for creating conversations with proper remote/local handling.
    Manages the complexity of conversation creation, error handling, and state migration.
    """

    def __init__(self, runtime_handler: RuntimeHandler):
        """
        Initialize conversation factory.

        Args:
            runtime_handler: RuntimeHandler instance with configuration
        """
        self.runtime_handler = runtime_handler

    def create_conversation(
        self,
        agent: Agent,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        callbacks: Optional[List[Callable]] = None,
    ) -> Conversation:
        """
        Create a conversation (remote or local based on runtime configuration).

        Args:
            agent: Agent instance
            user_uuid: User identifier
            app_slug: App identifier
            riff_slug: Riff identifier
            callbacks: Optional list of callback functions

        Returns:
            Configured Conversation instance

        Raises:
            RuntimeError: If remote runtime is not ready
            ValueError: If conversation creation fails due to tool migration
        """
        callbacks = callbacks or []

        if self.runtime_handler.is_remote:
            return self._create_remote_conversation(
                agent, user_uuid, app_slug, riff_slug, callbacks
            )
        else:
            return self._create_local_conversation(
                agent, user_uuid, app_slug, riff_slug, callbacks
            )

    def _create_remote_conversation(
        self,
        agent: Agent,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        callbacks: List[Callable],
    ) -> Conversation:
        """Create a remote conversation with runtime readiness checks."""
        key = f"{user_uuid}:{app_slug}:{riff_slug}"

        logger.info(
            f"🌐 Creating RemoteConversation for {key} using runtime: {self.runtime_handler.runtime_url}"
        )

        # Wait for the runtime to be ready and alive before creating the conversation
        logger.info(
            f"⏳ Waiting for runtime to be ready and alive before creating conversation: {self.runtime_handler.runtime_url}"
        )
        ready_success, ready_response = (
            runtime_service.wait_for_runtime_ready_and_alive(
                user_uuid,
                app_slug,
                riff_slug,
                self.runtime_handler.runtime_url,
                timeout=300,
                check_interval=5,
            )
        )

        if not ready_success:
            error_msg = f"Runtime is not ready and alive: {ready_response.get('error', 'Unknown error')}"
            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

        logger.info(
            f"✅ Runtime is ready and alive, creating conversation: {self.runtime_handler.runtime_url}"
        )

        return Conversation(
            agent=agent,
            host=self.runtime_handler.runtime_url,
            api_key=self.runtime_handler.session_api_key,
            callbacks=callbacks,
            visualize=False,
        )

    def _create_local_conversation(
        self,
        agent: Agent,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        callbacks: List[Callable],
    ) -> Conversation:
        """Create a local conversation with file store persistence."""
        key = f"{user_uuid}:{app_slug}:{riff_slug}"

        logger.info(f"🏠 Creating local Conversation for {key}")

        # Create LocalFileStore for persistence
        try:
            file_store = LocalFileStore(self.runtime_handler.state_path)
        except Exception as e:
            logger.error(f"❌ Failed to create file store for {key}: {e}")
            raise

        # Generate conversation ID as a proper UUID object
        # Use uuid5 to create a deterministic UUID from the user/app/riff combination
        conversation_key = f"{user_uuid}:{app_slug}:{riff_slug}"
        conversation_id = uuid.uuid5(uuid.NAMESPACE_DNS, conversation_key)

        try:
            return Conversation(
                agent=agent,
                callbacks=callbacks,
                persist_filestore=file_store,
                conversation_id=conversation_id,
                visualize=False,
            )
        except ValueError as e:
            # Handle tool name migration - clear persisted state if tool names have changed
            return self._handle_conversation_migration(
                agent, callbacks, file_store, conversation_id, key, str(e)
            )

    def _handle_conversation_migration(
        self,
        agent: Agent,
        callbacks: List[Callable],
        file_store: LocalFileStore,
        conversation_id: uuid.UUID,
        key: str,
        error_msg: str,
    ) -> Conversation:
        """Handle conversation creation errors due to tool migration or state issues."""
        if (
            ("Tool" in error_msg and "is not registered" in error_msg)
            or ("Agent provided is different" in error_msg and "tools:" in error_msg)
            or ("Conversation ID mismatch" in error_msg)
        ):
            logger.warning(f"⚠️ Detected tool migration issue for {key}: {error_msg}")
            logger.info(f"🔄 Clearing persisted state to handle tool name changes...")

            # Clear the persisted state directory
            if os.path.exists(self.runtime_handler.state_path):
                shutil.rmtree(self.runtime_handler.state_path)
                ensure_directory_exists(self.runtime_handler.state_path)

            # Recreate the file store
            file_store = LocalFileStore(self.runtime_handler.state_path)

            # Retry conversation creation
            logger.info(f"🏠 Retrying local Conversation creation for {key}")
            conversation = Conversation(
                agent=agent,
                callbacks=callbacks,
                persist_filestore=file_store,
                conversation_id=conversation_id,
                visualize=False,
            )
            logger.info(f"✅ Successfully recreated conversation after state migration")
            return conversation
        else:
            # Re-raise the original error if it's not a migration issue
            raise ValueError(error_msg)

    def create_conversation_with_retry(
        self,
        agent: Agent,
        user_uuid: str,
        app_slug: str,
        riff_slug: str,
        callbacks: Optional[List[Callable]] = None,
    ) -> Conversation:
        """
        Create a conversation with automatic retry for remote runtime issues.

        Args:
            agent: Agent instance
            user_uuid: User identifier
            app_slug: App identifier
            riff_slug: Riff identifier
            callbacks: Optional list of callback functions

        Returns:
            Configured Conversation instance
        """
        try:
            return self.create_conversation(
                agent, user_uuid, app_slug, riff_slug, callbacks
            )
        except (RuntimeError, ValueError) as e:
            # For remote conversations, we might want to retry once
            if self.runtime_handler.is_remote and "Runtime is not ready" in str(e):
                logger.warning(
                    f"⚠️ Retrying remote conversation creation after runtime error: {e}"
                )
                # Wait a bit and retry once
                import time

                time.sleep(5)
                return self.create_conversation(
                    agent, user_uuid, app_slug, riff_slug, callbacks
                )
            else:
                raise

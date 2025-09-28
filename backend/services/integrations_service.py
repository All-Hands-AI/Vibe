"""
Integrations Service - Business logic for API key management and validation.

This service handles:
- API key validation for different providers
- User API key storage and retrieval
- Provider validation and management
"""

import logging
from typing import Dict, Tuple, Any

from keys import (
    load_user_keys,
    save_user_keys,
    user_has_keys,
    validate_api_key,
    get_supported_providers,
    is_valid_provider,
)


logger = logging.getLogger(__name__)


class IntegrationsService:
    """Service for managing API key integrations."""

    def __init__(self):
        pass

    def get_supported_providers(self) -> list:
        """Get list of supported providers."""
        return get_supported_providers()

    def is_valid_provider(self, provider: str) -> bool:
        """Check if provider is valid."""
        return is_valid_provider(provider)

    def validate_api_key(self, provider: str, api_key: str) -> bool:
        """Validate API key for a provider."""
        return validate_api_key(provider, api_key)

    def user_has_keys(self, user_uuid: str) -> bool:
        """Check if user has any stored keys."""
        return user_has_keys(user_uuid)

    def load_user_keys(self, user_uuid: str) -> Dict[str, str]:
        """Load user's API keys."""
        return load_user_keys(user_uuid)

    def save_user_keys(self, user_uuid: str, keys: Dict[str, str]) -> bool:
        """Save user's API keys."""
        return save_user_keys(user_uuid, keys)

    def set_api_key(
        self, user_uuid: str, provider: str, api_key: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Set and validate API key for a provider.

        Args:
            user_uuid: User's UUID
            provider: Provider name (e.g., 'anthropic', 'github', 'fly')
            api_key: API key to set

        Returns:
            Tuple of (success: bool, response_data: Dict)
        """
        logger.info(f"🔑 Setting API key for provider: {provider}")
        logger.debug(f"🆔 User UUID: {user_uuid[:8]}...")

        # Validate provider
        if not self.is_valid_provider(provider):
            logger.warning(f"❌ Invalid provider requested: {provider}")
            logger.debug(f"📋 Valid providers: {self.get_supported_providers()}")
            return False, {
                "error": "Invalid provider",
                "valid_providers": self.get_supported_providers(),
            }

        # Validate inputs
        if not user_uuid or not user_uuid.strip():
            logger.warning("❌ Empty UUID provided")
            return False, {"error": "UUID cannot be empty"}

        if not api_key or not api_key.strip():
            logger.warning("❌ Empty API key provided")
            return False, {"error": "API key cannot be empty"}

        api_key = api_key.strip()
        logger.debug(f"🔍 Validating {provider} API key for user {user_uuid[:8]}...")

        # Validate the API key using the keys module
        is_valid = self.validate_api_key(provider, api_key)

        if is_valid:
            # Load existing keys for this user
            user_keys = self.load_user_keys(user_uuid)
            user_keys[provider] = api_key

            # Save to file
            if self.save_user_keys(user_uuid, user_keys):
                logger.info(
                    f"✅ {provider} API key validated and stored for user {user_uuid[:8]}"
                )
                return True, {
                    "valid": True,
                    "message": f"{provider.title()} API key is valid",
                }
            else:
                logger.error(
                    f"❌ Failed to save {provider} API key for user {user_uuid[:8]}"
                )
                return False, {"valid": False, "message": "Failed to save API key"}
        else:
            logger.warning(
                f"❌ {provider} API key validation failed for user {user_uuid[:8]}"
            )
            return False, {
                "valid": False,
                "message": f"{provider.title()} API key is invalid",
            }

    def check_api_key(
        self, user_uuid: str, provider: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if API key is set and valid for a provider.

        Args:
            user_uuid: User's UUID
            provider: Provider name (e.g., 'anthropic', 'github', 'fly')

        Returns:
            Tuple of (success: bool, response_data: Dict)
        """
        logger.info(f"🔍 Checking API key status for provider: {provider}")

        # Validate provider
        if not self.is_valid_provider(provider):
            logger.warning(f"❌ Invalid provider requested: {provider}")
            return False, {"error": "Invalid provider"}

        # Validate UUID
        if not user_uuid or not user_uuid.strip():
            logger.warning("❌ Empty UUID provided")
            return False, {"error": "UUID cannot be empty"}

        logger.debug(
            f"🔍 Checking {provider} API key status for user {user_uuid[:8]}..."
        )

        # Check if user has keys file
        if not self.user_has_keys(user_uuid):
            logger.debug(f"⚠️ No keys file found for user {user_uuid[:8]}")
            return True, {
                "valid": False,
                "message": f"{provider.title()} API key not set",
            }

        # Load user's keys
        user_keys = self.load_user_keys(user_uuid)
        api_key = user_keys.get(provider)

        if not api_key:
            logger.debug(f"⚠️ {provider} API key not set for user {user_uuid[:8]}")
            return True, {
                "valid": False,
                "message": f"{provider.title()} API key not set",
            }

        logger.debug(
            f"🔍 Re-validating stored {provider} API key for user {user_uuid[:8]}..."
        )

        # Re-validate the stored key using the keys module
        is_valid = self.validate_api_key(provider, api_key)

        result = {
            "valid": is_valid,
            "message": f'{provider.title()} API key is {"valid" if is_valid else "invalid"}',
        }

        logger.info(
            f"📊 {provider} API key check result for user {user_uuid[:8]}: {result}"
        )
        return True, result

    def get_user_key(self, user_uuid: str, provider: str) -> str:
        """
        Get a specific API key for a user.

        Args:
            user_uuid: User's UUID
            provider: Provider name

        Returns:
            API key string or empty string if not found
        """
        if not self.user_has_keys(user_uuid):
            return ""

        user_keys = self.load_user_keys(user_uuid)
        return user_keys.get(provider, "")

    def remove_api_key(
        self, user_uuid: str, provider: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Remove API key for a provider.

        Args:
            user_uuid: User's UUID
            provider: Provider name

        Returns:
            Tuple of (success: bool, response_data: Dict)
        """
        logger.info(f"🗑️ Removing API key for provider: {provider}")

        # Validate provider
        if not self.is_valid_provider(provider):
            logger.warning(f"❌ Invalid provider requested: {provider}")
            return False, {"error": "Invalid provider"}

        # Validate UUID
        if not user_uuid or not user_uuid.strip():
            logger.warning("❌ Empty UUID provided")
            return False, {"error": "UUID cannot be empty"}

        # Check if user has keys
        if not self.user_has_keys(user_uuid):
            logger.debug(f"⚠️ No keys file found for user {user_uuid[:8]}")
            return True, {"message": f"{provider.title()} API key was not set"}

        # Load user's keys
        user_keys = self.load_user_keys(user_uuid)

        if provider not in user_keys:
            logger.debug(f"⚠️ {provider} API key not set for user {user_uuid[:8]}")
            return True, {"message": f"{provider.title()} API key was not set"}

        # Remove the key
        del user_keys[provider]

        # Save updated keys
        if self.save_user_keys(user_uuid, user_keys):
            logger.info(f"✅ {provider} API key removed for user {user_uuid[:8]}")
            return True, {"message": f"{provider.title()} API key removed successfully"}
        else:
            logger.error(f"❌ Failed to save updated keys for user {user_uuid[:8]}")
            return False, {"error": "Failed to remove API key"}

    def list_user_integrations(self, user_uuid: str) -> Tuple[bool, Dict[str, Any]]:
        """
        List all integrations for a user with their status.

        Args:
            user_uuid: User's UUID

        Returns:
            Tuple of (success: bool, response_data: Dict)
        """
        logger.info(f"📋 Listing integrations for user {user_uuid[:8]}...")

        # Validate UUID
        if not user_uuid or not user_uuid.strip():
            logger.warning("❌ Empty UUID provided")
            return False, {"error": "UUID cannot be empty"}

        supported_providers = self.get_supported_providers()
        integrations = {}

        # Check if user has any keys
        if not self.user_has_keys(user_uuid):
            # User has no keys, all providers are not set
            for provider in supported_providers:
                integrations[provider] = {
                    "valid": False,
                    "message": f"{provider.title()} API key not set",
                }
        else:
            # Load user's keys and check each provider
            user_keys = self.load_user_keys(user_uuid)

            for provider in supported_providers:
                api_key = user_keys.get(provider)

                if not api_key:
                    integrations[provider] = {
                        "valid": False,
                        "message": f"{provider.title()} API key not set",
                    }
                else:
                    # Validate the stored key
                    is_valid = self.validate_api_key(provider, api_key)
                    integrations[provider] = {
                        "valid": is_valid,
                        "message": f'{provider.title()} API key is {"valid" if is_valid else "invalid"}',
                    }

        logger.info(
            f"📊 Listed {len(integrations)} integrations for user {user_uuid[:8]}"
        )
        return True, {
            "integrations": integrations,
            "supported_providers": supported_providers,
        }


# Create a singleton instance
integrations_service = IntegrationsService()

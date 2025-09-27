"""
Runtime Service for managing remote runtime environments via runtime-api.

This service handles:
- Starting new remote runtimes for each deployment
- Checking runtime status
- Pausing and resuming runtimes
- Managing runtime lifecycle for Riffs
"""

import os
import requests
from typing import Dict, Optional, Tuple
from utils.logging import get_logger

logger = get_logger(__name__)


class RuntimeService:
    """Service for managing remote runtime environments."""

    def __init__(self):
        # Get configuration from environment variables
        self.runtime_api_url = os.environ.get(
            "RUNTIME_API_URL", "https://runtime.staging.all-hands.dev/"
        )
        self.admin_api_key = os.environ.get("RUNTIME_API_STAGING_SECRET")
        self.default_image = "ghcr.io/all-hands-ai/agent-server:8daf576-python"

        if not self.admin_api_key:
            logger.warning(
                "⚠️ RUNTIME_API_STAGING_SECRET not set - runtime operations will fail"
            )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Tuple[bool, Dict]:
        """Make HTTP request to runtime-api."""
        if not self.admin_api_key:
            return False, {"error": "Runtime API key not configured"}

        url = f"{self.runtime_api_url.rstrip('/')}/{endpoint.lstrip('/')}"

        default_headers = {
            "X-API-Key": self.admin_api_key,
            "Content-Type": "application/json",
        }

        if headers:
            default_headers.update(headers)

        try:
            logger.info(f"🌐 Making {method} request to {url}")

            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(
                    url, json=data, headers=default_headers, timeout=30
                )
            else:
                return False, {"error": f"Unsupported HTTP method: {method}"}

            logger.info(f"📡 Runtime API response: {response.status_code}")

            if response.status_code in [200, 201, 202]:
                return True, response.json()
            else:
                error_msg = f"Runtime API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", error_msg)
                except Exception:
                    error_msg = f"{error_msg} - {response.text}"

                logger.error(f"❌ {error_msg}")
                return False, {"error": error_msg}

        except requests.exceptions.Timeout:
            logger.error("❌ Runtime API request timed out")
            return False, {"error": "Runtime API request timed out"}
        except requests.exceptions.ConnectionError:
            logger.error("❌ Failed to connect to Runtime API")
            return False, {"error": "Failed to connect to Runtime API"}
        except Exception as e:
            logger.error(f"❌ Runtime API request failed: {e}")
            return False, {"error": f"Runtime API request failed: {str(e)}"}

    def start_runtime(
        self, user_uuid: str, app_slug: str, riff_slug: str
    ) -> Tuple[bool, Dict]:
        """
        Start a new remote runtime for a Riff.

        Args:
            user_uuid: User's UUID
            app_slug: App slug identifier
            riff_slug: Riff slug identifier

        Returns:
            Tuple of (success: bool, response_data: Dict)
        """
        session_id = f"{user_uuid}.{app_slug}.{riff_slug}"

        runtime_config = {
            "session_id": session_id,
            "image": self.default_image,
            "command": "/usr/local/bin/openhands-agent-server --port 60000",
            "working_dir": "/",
        }

        logger.info(f"🚀 Starting runtime for session: {session_id}")
        success, response = self._make_request("POST", "/start", runtime_config)

        if success:
            logger.info(
                f"✅ Runtime started successfully: {response.get('runtime_id')}"
            )
        else:
            logger.error(f"❌ Failed to start runtime: {response.get('error')}")

        return success, response

    def get_runtime_status(
        self, user_uuid: str, app_slug: str, riff_slug: str
    ) -> Tuple[bool, Dict]:
        """
        Get the status of a runtime by session ID.

        Args:
            user_uuid: User's UUID
            app_slug: App slug identifier
            riff_slug: Riff slug identifier

        Returns:
            Tuple of (success: bool, response_data: Dict)
        """
        session_id = f"{user_uuid}.{app_slug}.{riff_slug}"

        logger.info(f"📊 Getting runtime status for session: {session_id}")
        success, response = self._make_request("GET", f"/sessions/{session_id}")

        if success:
            status = response.get("status", "unknown")
            logger.info(f"📈 Runtime status: {status}")
        else:
            logger.warning(f"⚠️ Failed to get runtime status: {response.get('error')}")

        return success, response

    def pause_runtime(self, runtime_id: str) -> Tuple[bool, Dict]:
        """
        Pause a runtime.

        Args:
            runtime_id: Runtime ID to pause

        Returns:
            Tuple of (success: bool, response_data: Dict)
        """
        logger.info(f"⏸️ Pausing runtime: {runtime_id}")

        pause_data = {"runtime_id": runtime_id}
        success, response = self._make_request("POST", "/pause", pause_data)

        if success:
            logger.info(f"✅ Runtime paused successfully: {runtime_id}")
        else:
            logger.error(f"❌ Failed to pause runtime: {response.get('error')}")

        return success, response

    def resume_runtime(self, runtime_id: str) -> Tuple[bool, Dict]:
        """
        Resume a paused runtime.

        Args:
            runtime_id: Runtime ID to resume

        Returns:
            Tuple of (success: bool, response_data: Dict)
        """
        logger.info(f"▶️ Resuming runtime: {runtime_id}")

        resume_data = {"runtime_id": runtime_id}
        success, response = self._make_request("POST", "/resume", resume_data)

        if success:
            logger.info(f"✅ Runtime resumed successfully: {runtime_id}")
        else:
            logger.error(f"❌ Failed to resume runtime: {response.get('error')}")

        return success, response

    def get_api_health(self) -> Tuple[bool, Dict]:
        """
        Check the health status of the runtime API.

        Returns:
            Tuple of (success: bool, response_data: Dict)
        """
        logger.info("🏥 Checking runtime API health")

        # Health endpoint typically doesn't require authentication
        try:
            url = f"{self.runtime_api_url.rstrip('/')}/health"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                logger.info("✅ Runtime API is healthy")
                return True, response.json()
            else:
                logger.warning(
                    f"⚠️ Runtime API health check failed: {response.status_code}"
                )
                return False, {"error": f"Health check failed: {response.status_code}"}

        except Exception as e:
            logger.error(f"❌ Runtime API health check failed: {e}")
            return False, {"error": f"Health check failed: {str(e)}"}

    def handle_agent_reset(
        self, user_uuid: str, app_slug: str, riff_slug: str
    ) -> Tuple[bool, Dict]:
        """
        Handle agent reset by checking runtime status and unpausing/restarting as needed.

        Args:
            user_uuid: User's UUID
            app_slug: App slug identifier
            riff_slug: Riff slug identifier

        Returns:
            Tuple of (success: bool, response_data: Dict)
        """
        logger.info(
            f"🔄 Handling agent reset for {user_uuid[:8]}.{app_slug}.{riff_slug}"
        )

        # First, check the current runtime status
        success, status_response = self.get_runtime_status(
            user_uuid, app_slug, riff_slug
        )

        if not success:
            # Runtime not found, start a new one
            logger.info("🆕 Runtime not found, starting new runtime")
            return self.start_runtime(user_uuid, app_slug, riff_slug)

        current_status = status_response.get("status", "").lower()
        runtime_id = status_response.get("runtime_id")

        if current_status == "paused" and runtime_id:
            # Runtime is paused, resume it
            logger.info(f"▶️ Runtime is paused, resuming: {runtime_id}")
            return self.resume_runtime(runtime_id)
        elif current_status in ["running", "starting"]:
            # Runtime is already running
            logger.info(f"✅ Runtime is already {current_status}")
            return True, status_response
        else:
            # Runtime is in an unexpected state, start a new one
            logger.info(
                f"🆕 Runtime status is '{current_status}', starting new runtime"
            )
            return self.start_runtime(user_uuid, app_slug, riff_slug)


# Global runtime service instance
runtime_service = RuntimeService()

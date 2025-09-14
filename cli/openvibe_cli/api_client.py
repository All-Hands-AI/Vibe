"""API client for communicating with OpenVibe backend."""

import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from openvibe_cli.config import Config

console = Console()


class APIError(Exception):
    """Exception raised for API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(message)


class OpenVibeAPI:
    """API client for OpenVibe backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000", user_uuid: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.user_uuid = user_uuid
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'OpenVibe-CLI/0.1.0'
        })
        
        if self.user_uuid:
            self.session.headers['X-User-UUID'] = self.user_uuid
    
    def set_user_uuid(self, user_uuid: str):
        """Set the user UUID for API requests."""
        self.user_uuid = user_uuid
        self.session.headers['X-User-UUID'] = user_uuid
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an HTTP request to the API."""
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error: {str(e)}")
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate errors."""
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"error": response.text or "Unknown error"}
        
        if not response.ok:
            error_msg = data.get('error', f'HTTP {response.status_code}')
            raise APIError(error_msg, response.status_code, data)
        
        return data
    
    # Apps API methods
    def list_apps(self) -> List[Dict[str, Any]]:
        """List all apps for the user."""
        response = self._make_request('GET', '/api/apps')
        data = self._handle_response(response)
        return data.get('apps', [])
    
    def get_app(self, app_slug: str) -> Dict[str, Any]:
        """Get details for a specific app."""
        response = self._make_request('GET', f'/api/apps/{app_slug}')
        return self._handle_response(response)
    
    def create_app(self, name: str) -> Dict[str, Any]:
        """Create a new app."""
        data = {"name": name}
        response = self._make_request('POST', '/api/apps', json=data)
        result = self._handle_response(response)
        return result.get('app', result)
    
    def delete_app(self, app_slug: str) -> Dict[str, Any]:
        """Delete an app."""
        response = self._make_request('DELETE', f'/api/apps/{app_slug}')
        return self._handle_response(response)
    
    # Riffs API methods
    def list_riffs(self, app_slug: str) -> List[Dict[str, Any]]:
        """List all riffs for an app."""
        response = self._make_request('GET', f'/api/apps/{app_slug}/riffs')
        data = self._handle_response(response)
        return data.get('riffs', [])
    
    def create_riff(self, app_slug: str, name: str, slug: Optional[str] = None) -> Dict[str, Any]:
        """Create a new riff."""
        if not slug:
            slug = self.create_slug(name)
        
        data = {"name": name, "slug": slug}
        response = self._make_request('POST', f'/api/apps/{app_slug}/riffs', json=data)
        result = self._handle_response(response)
        return result.get('riff', result)
    
    # Messages API methods
    def list_messages(self, app_slug: str, riff_slug: str) -> List[Dict[str, Any]]:
        """List all messages for a riff."""
        response = self._make_request('GET', f'/api/apps/{app_slug}/riffs/{riff_slug}/messages')
        data = self._handle_response(response)
        return data.get('messages', [])
    
    def send_message(self, app_slug: str, riff_slug: str, content: str, 
                    message_type: str = 'text', metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Send a message to a riff."""
        data = {
            "riff_slug": riff_slug,
            "content": content.strip(),
            "type": message_type,
            "metadata": metadata or {}
        }
        response = self._make_request('POST', f'/api/apps/{app_slug}/riffs/messages', json=data)
        return self._handle_response(response)
    
    # Utility methods
    @staticmethod
    def create_slug(name: str) -> str:
        """Create a slug from a name (matches frontend logic)."""
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')
    
    # Status and monitoring methods
    def check_llm_ready(self, app_slug: str, riff_slug: str) -> bool:
        """Check if LLM is ready for a riff."""
        try:
            response = self._make_request('GET', f'/api/apps/{app_slug}/riffs/{riff_slug}/llm/status')
            data = self._handle_response(response)
            return data.get('ready', False)
        except APIError:
            return False
    
    def get_agent_status(self, app_slug: str, riff_slug: str) -> Dict[str, Any]:
        """Get agent status for a riff."""
        try:
            response = self._make_request('GET', f'/api/apps/{app_slug}/riffs/{riff_slug}/agent/status')
            return self._handle_response(response)
        except APIError:
            return {"status": "unknown"}


def get_api_client() -> OpenVibeAPI:
    """Get configured API client instance."""
    config = Config.load()
    
    # Use configured backend URL or default to localhost
    base_url = getattr(config, 'backend_url', 'http://localhost:8000')
    user_uuid = getattr(config, 'user_uuid', None)
    
    return OpenVibeAPI(base_url=base_url, user_uuid=user_uuid)
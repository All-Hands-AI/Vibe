"""
Configuration for remote runtime support in OpenVibe.

This module provides configuration options and utilities for using
remote OpenHands Agent Server runtimes instead of local agents.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RemoteRuntimeConfig:
    """Configuration for remote runtime connections."""
    
    # Runtime API settings
    runtime_api_url: str = "https://runtime.staging.all-hands.dev"
    runtime_api_key: str = "ODu0HV9KL1wc1NUerIgZWqn1w8WctjWD"
    
    # Agent server settings
    agent_server_image: str = "ghcr.io/all-hands-ai/agent-server:85aab73-python"
    working_dir: str = "/workspace"
    environment: Optional[Dict[str, str]] = None
    resource_factor: int = 1
    
    # Feature flags
    use_remote_runtime: bool = False
    enable_websocket_events: bool = True
    
    def __post_init__(self):
        """Initialize default environment if not provided."""
        if self.environment is None:
            self.environment = {"DEBUG": "true"}


def get_remote_runtime_config() -> RemoteRuntimeConfig:
    """
    Get remote runtime configuration from environment variables.
    
    Environment variables:
    - OPENVIBE_USE_REMOTE_RUNTIME: Enable remote runtime (default: false)
    - OPENVIBE_RUNTIME_API_URL: Runtime API URL
    - OPENVIBE_RUNTIME_API_KEY: Runtime API key
    - OPENVIBE_AGENT_SERVER_IMAGE: Docker image for agent server
    - OPENVIBE_RUNTIME_WORKING_DIR: Working directory in runtime
    - OPENVIBE_RUNTIME_RESOURCE_FACTOR: Resource allocation factor
    - OPENVIBE_ENABLE_WEBSOCKET_EVENTS: Enable WebSocket events (default: true)
    
    Returns:
        RemoteRuntimeConfig instance
    """
    config = RemoteRuntimeConfig()
    
    # Feature flags
    config.use_remote_runtime = os.getenv("OPENVIBE_USE_REMOTE_RUNTIME", "false").lower() == "true"
    config.enable_websocket_events = os.getenv("OPENVIBE_ENABLE_WEBSOCKET_EVENTS", "true").lower() == "true"
    
    # Runtime API settings
    if runtime_api_url := os.getenv("OPENVIBE_RUNTIME_API_URL"):
        config.runtime_api_url = runtime_api_url
        
    if runtime_api_key := os.getenv("OPENVIBE_RUNTIME_API_KEY"):
        config.runtime_api_key = runtime_api_key
    
    # Agent server settings
    if agent_server_image := os.getenv("OPENVIBE_AGENT_SERVER_IMAGE"):
        config.agent_server_image = agent_server_image
        
    if working_dir := os.getenv("OPENVIBE_RUNTIME_WORKING_DIR"):
        config.working_dir = working_dir
        
    if resource_factor := os.getenv("OPENVIBE_RUNTIME_RESOURCE_FACTOR"):
        try:
            config.resource_factor = int(resource_factor)
        except ValueError:
            logger.warning(f"Invalid resource factor: {resource_factor}, using default: 1")
    
    # Environment variables for the runtime
    runtime_env = {}
    if debug := os.getenv("OPENVIBE_RUNTIME_DEBUG"):
        runtime_env["DEBUG"] = debug
    if runtime_env:
        config.environment.update(runtime_env)
    
    logger.info(f"🔧 Remote runtime config: use_remote={config.use_remote_runtime}")
    if config.use_remote_runtime:
        logger.info(f"   API URL: {config.runtime_api_url}")
        logger.info(f"   Image: {config.agent_server_image}")
        logger.info(f"   Working dir: {config.working_dir}")
        logger.info(f"   Resource factor: {config.resource_factor}")
        logger.info(f"   WebSocket events: {config.enable_websocket_events}")
    
    return config


def create_remote_runtime_client(config: RemoteRuntimeConfig, event_callback=None):
    """
    Create a RemoteRuntimeClient from configuration.
    
    Args:
        config: RemoteRuntimeConfig instance
        event_callback: Optional callback for handling events
        
    Returns:
        RemoteRuntimeClient instance or None if remote runtime is disabled
    """
    if not config.use_remote_runtime:
        return None
        
    from remote_runtime_client import RemoteRuntimeClient
    
    client = RemoteRuntimeClient(
        runtime_api_url=config.runtime_api_url,
        runtime_api_key=config.runtime_api_key,
        agent_server_image=config.agent_server_image,
        event_callback=event_callback if config.enable_websocket_events else None,
    )
    
    logger.info("✅ Created RemoteRuntimeClient")
    return client


# Example usage in Flask app
def example_flask_integration():
    """
    Example of how to integrate remote runtime support in the Flask app.
    
    This shows how to modify the existing Flask routes to support remote runtimes.
    """
    
    # This would go in your Flask app initialization
    config = get_remote_runtime_config()
    
    # Create a global remote runtime client if enabled
    remote_client = None
    if config.use_remote_runtime:
        def global_event_callback(event):
            # Handle events globally (e.g., broadcast to WebSocket clients)
            logger.info(f"Global event: {event}")
            
        remote_client = create_remote_runtime_client(config, global_event_callback)
    
    # Example route modification
    def create_agent_route_example():
        """Example of how to modify the create agent route."""
        from agent_loop import AgentLoopManager
        from openhands.sdk import LLM
        from pydantic import SecretStr
        
        # Get parameters from request (user_uuid, app_slug, riff_slug, etc.)
        user_uuid = "example-user"
        app_slug = "example-app"
        riff_slug = "example-riff"
        workspace_path = "/workspace/project"
        
        # Create LLM instance
        llm = LLM(
            model="anthropic/claude-3-5-sonnet-20241022",
            api_key=SecretStr("your-api-key"),
            base_url="https://api.anthropic.com",
        )
        
        # Message callback for this specific agent
        def message_callback(event):
            logger.info(f"Agent event for {user_uuid}: {event}")
        
        # Create agent loop with remote runtime support
        manager = AgentLoopManager()
        agent_loop = manager.create_agent_loop(
            user_uuid=user_uuid,
            app_slug=app_slug,
            riff_slug=riff_slug,
            llm=llm,
            workspace_path=workspace_path,
            message_callback=message_callback,
            use_remote_runtime=config.use_remote_runtime,
            remote_runtime_client=remote_client,
        )
        
        return {"status": "success", "runtime_type": "remote" if config.use_remote_runtime else "local"}


# Environment variable documentation
ENVIRONMENT_VARIABLES_DOC = """
Remote Runtime Environment Variables:

Required for remote runtime:
- OPENVIBE_USE_REMOTE_RUNTIME=true          # Enable remote runtime
- OPENVIBE_RUNTIME_API_KEY=<your-api-key>   # Runtime API key

Optional configuration:
- OPENVIBE_RUNTIME_API_URL=<api-url>                    # Default: https://runtime.staging.all-hands.dev
- OPENVIBE_AGENT_SERVER_IMAGE=<docker-image>           # Default: ghcr.io/all-hands-ai/agent-server:85aab73-python
- OPENVIBE_RUNTIME_WORKING_DIR=<working-dir>           # Default: /workspace
- OPENVIBE_RUNTIME_RESOURCE_FACTOR=<factor>            # Default: 1
- OPENVIBE_ENABLE_WEBSOCKET_EVENTS=<true|false>        # Default: true
- OPENVIBE_RUNTIME_DEBUG=<true|false>                  # Default: true

Example .env file:
OPENVIBE_USE_REMOTE_RUNTIME=true
OPENVIBE_RUNTIME_API_KEY=ODu0HV9KL1wc1NUerIgZWqn1w8WctjWD
OPENVIBE_RUNTIME_API_URL=https://runtime.staging.all-hands.dev
OPENVIBE_AGENT_SERVER_IMAGE=ghcr.io/all-hands-ai/agent-server:85aab73-python
OPENVIBE_RUNTIME_WORKING_DIR=/workspace
OPENVIBE_RUNTIME_RESOURCE_FACTOR=1
OPENVIBE_ENABLE_WEBSOCKET_EVENTS=true
OPENVIBE_RUNTIME_DEBUG=true
"""

if __name__ == "__main__":
    # Print configuration documentation
    print(ENVIRONMENT_VARIABLES_DOC)
    
    # Test configuration loading
    config = get_remote_runtime_config()
    print(f"\nLoaded configuration:")
    print(f"  Use remote runtime: {config.use_remote_runtime}")
    print(f"  Runtime API URL: {config.runtime_api_url}")
    print(f"  Agent server image: {config.agent_server_image}")
    print(f"  Working directory: {config.working_dir}")
    print(f"  Resource factor: {config.resource_factor}")
    print(f"  Enable WebSocket events: {config.enable_websocket_events}")
    print(f"  Environment: {config.environment}")
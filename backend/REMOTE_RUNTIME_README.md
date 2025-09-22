# Remote Runtime Support for OpenVibe

This document describes the remote runtime implementation that allows OpenVibe to use remote OpenHands Agent Server instances instead of running agents locally.

## Overview

The remote runtime implementation provides:

- **RemoteRuntimeClient**: Client for communicating with remote agent servers
- **Modified AgentLoop**: Support for both local and remote runtime execution
- **Configuration Management**: Environment-based configuration for remote runtimes
- **WebSocket Support**: Real-time event streaming from remote agents
- **Resource Management**: Proper cleanup and lifecycle management

## Architecture

```
OpenVibe Backend
├── RemoteRuntimeClient
│   ├── Runtime API Communication
│   ├── Agent Server REST API
│   └── WebSocket Event Streaming
├── AgentLoop (Modified)
│   ├── Local Runtime Support (existing)
│   └── Remote Runtime Support (new)
└── AgentLoopManager (Modified)
    └── Runtime Selection Logic
```

## Key Components

### 1. RemoteRuntimeClient

**File**: `remote_runtime_client.py`

The `RemoteRuntimeClient` class handles all communication with remote agent servers:

```python
from remote_runtime_client import RemoteRuntimeClient

# Create client
client = RemoteRuntimeClient(
    runtime_api_url="https://runtime.staging.all-hands.dev",
    runtime_api_key="your-api-key",
    agent_server_image="ghcr.io/all-hands-ai/agent-server:85aab73-python",
    event_callback=your_event_handler,
)

# Start remote runtime
runtime_info = client.start_remote_runtime()

# Create conversation
conversation_info = client.create_conversation(
    runtime_info=runtime_info,
    llm_config={"model": "claude-3-5-sonnet", "api_key": "..."},
    workspace_path="/workspace/project",
)

# Send messages
client.send_message(conversation_info, "Hello!", run=True)

# Get events
events = client.get_conversation_events(conversation_info)
```

### 2. Modified AgentLoop

**File**: `agent_loop.py`

The `AgentLoop` class now supports both local and remote runtimes:

```python
from agent_loop import AgentLoopManager
from remote_runtime_client import RemoteRuntimeClient

# Create remote client
remote_client = RemoteRuntimeClient(...)

# Create agent loop with remote runtime
manager = AgentLoopManager()
agent_loop = manager.create_agent_loop(
    user_uuid="user-123",
    app_slug="my-app",
    riff_slug="conversation-1",
    llm=llm_instance,
    workspace_path="/workspace/project",
    use_remote_runtime=True,  # Enable remote runtime
    remote_runtime_client=remote_client,
)

# Use normally - the API is the same
agent_loop.send_message("Hello!")
status = agent_loop.get_agent_status()
events = agent_loop.get_all_events()
```

### 3. Configuration Management

**File**: `remote_runtime_config.py`

Environment-based configuration for remote runtimes:

```python
from remote_runtime_config import get_remote_runtime_config, create_remote_runtime_client

# Load configuration from environment
config = get_remote_runtime_config()

# Create client from config
remote_client = create_remote_runtime_client(config, event_callback)
```

## Environment Variables

Configure remote runtime behavior using environment variables:

```bash
# Enable remote runtime
OPENVIBE_USE_REMOTE_RUNTIME=true

# Required: Runtime API key
OPENVIBE_RUNTIME_API_KEY=ODu0HV9KL1wc1NUerIgZWqn1w8WctjWD

# Optional: Runtime API URL (default: staging)
OPENVIBE_RUNTIME_API_URL=https://runtime.staging.all-hands.dev

# Optional: Agent server Docker image
OPENVIBE_AGENT_SERVER_IMAGE=ghcr.io/all-hands-ai/agent-server:85aab73-python

# Optional: Working directory in runtime
OPENVIBE_RUNTIME_WORKING_DIR=/workspace

# Optional: Resource allocation factor
OPENVIBE_RUNTIME_RESOURCE_FACTOR=1

# Optional: Enable WebSocket events
OPENVIBE_ENABLE_WEBSOCKET_EVENTS=true

# Optional: Debug mode
OPENVIBE_RUNTIME_DEBUG=true
```

## API Compatibility

The remote runtime implementation maintains full API compatibility with the existing local runtime:

| Method | Local Runtime | Remote Runtime | Notes |
|--------|---------------|----------------|-------|
| `send_message()` | ✅ | ✅ | Same interface |
| `get_all_events()` | ✅ | ✅ | Same interface |
| `get_agent_status()` | ✅ | ✅ | Additional `runtime_type` field |
| `pause_agent()` | ✅ | ✅ | Same interface |
| `resume_agent()` | ✅ | ✅ | Same interface |
| `cleanup()` | ✅ | ✅ | Handles remote cleanup |

## Remote Runtime Startup Process

1. **Runtime Creation**: POST to `/start` endpoint creates a new runtime container
2. **Agent Server Startup**: Container starts with OpenHands Agent Server
3. **Conversation Creation**: POST to `/conversations` creates a new conversation
4. **WebSocket Connection**: Establishes real-time event streaming
5. **Message Processing**: Messages sent via REST API, events received via WebSocket

## Example: Starting Remote Runtime

```bash
curl -X POST "https://runtime.staging.all-hands.dev/start" \
  -H "X-API-Key: ODu0HV9KL1wc1NUerIgZWqn1w8WctjWD" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "ghcr.io/all-hands-ai/agent-server:85aab73-python",
    "command": "/usr/local/bin/openhands-agent-server --port 60000 --no-reload",
    "working_dir": "/workspace",
    "environment": {"DEBUG": "true"},
    "resource_factor": 1
  }'
```

Response:
```json
{
  "runtime_id": "opvcsfecxutsbsbq",
  "session_api_key": "d83600c8-5d80-438d-b4be-43611ba94d4f",
  "session_id": "hpkjexgkksuuzveh",
  "url": "https://opvcsfecxutsbsbq.staging-runtime.all-hands.dev",
  "work_hosts": {
    "https://work-1-opvcsfecxutsbsbq.staging-runtime.all-hands.dev": 12000,
    "https://work-2-opvcsfecxutsbsbq.staging-runtime.all-hands.dev": 12001
  }
}
```

## Testing

### Unit Tests

Run the test script to verify remote runtime functionality:

```bash
cd backend
python test_remote_runtime.py
```

### Manual Testing

1. Set environment variables:
   ```bash
   export OPENVIBE_USE_REMOTE_RUNTIME=true
   export OPENVIBE_RUNTIME_API_KEY=ODu0HV9KL1wc1NUerIgZWqn1w8WctjWD
   ```

2. Start the Flask application:
   ```bash
   python app.py
   ```

3. Create an agent - it will use remote runtime automatically

## Integration with Flask App

To integrate remote runtime support into your Flask application:

```python
from remote_runtime_config import get_remote_runtime_config, create_remote_runtime_client
from agent_loop import AgentLoopManager

# Initialize at app startup
config = get_remote_runtime_config()
remote_client = create_remote_runtime_client(config) if config.use_remote_runtime else None

# In your route handlers
@app.route('/create_agent', methods=['POST'])
def create_agent():
    # ... get parameters from request ...
    
    manager = AgentLoopManager()
    agent_loop = manager.create_agent_loop(
        user_uuid=user_uuid,
        app_slug=app_slug,
        riff_slug=riff_slug,
        llm=llm,
        workspace_path=workspace_path,
        use_remote_runtime=config.use_remote_runtime,
        remote_runtime_client=remote_client,
    )
    
    return {"status": "success", "runtime_type": "remote" if config.use_remote_runtime else "local"}
```

## Error Handling

The implementation includes comprehensive error handling:

- **Runtime Startup Failures**: Automatic retry and fallback mechanisms
- **Network Issues**: Timeout handling and connection recovery
- **WebSocket Disconnections**: Automatic reconnection attempts
- **Resource Cleanup**: Proper cleanup on errors and shutdown

## Performance Considerations

- **Latency**: Remote runtimes have higher latency than local execution
- **Network**: Requires stable internet connection
- **Resources**: Remote runtimes consume cloud resources
- **Scaling**: Can handle multiple concurrent remote runtimes

## Security

- **API Keys**: Secure storage and transmission of runtime API keys
- **HTTPS**: All communication uses HTTPS/WSS
- **Session Keys**: Unique session keys for each runtime instance
- **Isolation**: Each runtime runs in isolated containers

## Troubleshooting

### Common Issues

1. **Runtime startup fails**:
   - Check API key validity
   - Verify network connectivity
   - Check runtime API status

2. **WebSocket connection issues**:
   - Verify firewall settings
   - Check WebSocket support
   - Review network proxy configuration

3. **Message sending fails**:
   - Check conversation status
   - Verify session API key
   - Review agent server logs

### Debug Mode

Enable debug logging:
```bash
export OPENVIBE_RUNTIME_DEBUG=true
```

### Logs

Monitor logs for remote runtime operations:
- Runtime startup: `🚀 Starting remote runtime...`
- Conversation creation: `💬 Creating conversation...`
- Message sending: `📤 Sending message...`
- Event reception: `📨 Received event...`
- Cleanup: `🧹 Cleaning up...`

## Migration Guide

### From Local to Remote Runtime

1. **Set Environment Variables**:
   ```bash
   export OPENVIBE_USE_REMOTE_RUNTIME=true
   export OPENVIBE_RUNTIME_API_KEY=your-api-key
   ```

2. **Update Dependencies**:
   ```bash
   pip install websockets
   ```

3. **No Code Changes Required**: The API remains the same

### Hybrid Deployment

You can run both local and remote runtimes simultaneously by configuring different agent loops with different runtime settings.

## Future Enhancements

- **Load Balancing**: Distribute agents across multiple runtime instances
- **Runtime Pooling**: Reuse runtime instances for better performance
- **Monitoring**: Enhanced monitoring and metrics collection
- **Auto-scaling**: Automatic scaling based on demand
- **Cost Optimization**: Smart resource allocation and cleanup

## Dependencies

New dependencies added for remote runtime support:

```toml
dependencies = [
    # ... existing dependencies ...
    "websockets>=12.0",
    "openhands-agent-server @ git+https://github.com/all-hands-ai/agent-sdk.git@f8e800a93a3726555a30d1c42a692f4c556187c5#subdirectory=openhands/agent_server",
]
```

## Files Modified/Added

### New Files
- `remote_runtime_client.py` - Remote runtime client implementation
- `remote_runtime_config.py` - Configuration management
- `test_remote_runtime.py` - Test script
- `REMOTE_RUNTIME_README.md` - This documentation

### Modified Files
- `agent_loop.py` - Added remote runtime support
- `pyproject.toml` - Added new dependencies

### Configuration Files
- `.env` - Environment variables for remote runtime configuration
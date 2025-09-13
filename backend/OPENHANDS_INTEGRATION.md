# OpenHands Agent SDK Integration

This document describes the OpenHands Agent SDK integration implemented for OpenVibe, including setup instructions, API endpoints, and architecture details.

## Overview

The integration provides REST API endpoints for managing AI agent conversations using the OpenHands Agent SDK. Key features include:

- **Conversation Management**: Create, list, and monitor AI agent conversations
- **GitHub Integration**: Automatic branch and PR creation for each conversation
- **File-based Storage**: Persistent conversation state and workspace management
- **Background Processing**: Conversations run in separate threads
- **Event Tracking**: Real-time event monitoring for conversation progress

## Architecture

### Components

1. **`agent_loop.py`** - Core agent loop manager
   - `AgentLoopManager` class handles conversation lifecycle
   - Thread management for background conversation execution
   - GitHub branch/PR operations
   - File-based state persistence

2. **`conversations.py`** - REST API endpoints
   - Flask blueprint with conversation management endpoints
   - Integration with AgentLoopManager
   - File-based conversation metadata storage

3. **File Storage Structure**
   ```
   /data/
   ├── {project_id}/
   │   └── conversations/
   │       └── {conversation_id}/
   │           ├── workspace/     # Agent working directory
   │           └── state/         # OpenHands conversation state
   └── conversations_{project_id}.json  # Conversation metadata
   ```

## API Endpoints

### Create Conversation
```http
POST /projects/{id}/conversations
X-User-UUID: {user_uuid}
Content-Type: application/json

{
  "message": "Initial message to the agent",
  "repo_url": "https://github.com/owner/repo",  // optional
  "conversation_id": "custom-id"                // optional
}
```

**Response:**
```json
{
  "id": "conversation-uuid",
  "project_id": "project-id",
  "status": "running",
  "message": "Started conversation with branch 'conversation-12345678'",
  "created_at": "2025-01-01T00:00:00",
  "branch_name": "conversation-12345678",
  "pr_number": 42
}
```

### List Conversations
```http
GET /projects/{id}/conversations
X-User-UUID: {user_uuid}
```

**Response:**
```json
{
  "conversations": [
    {
      "id": "conversation-uuid",
      "project_id": "project-id",
      "status": "running",
      "created_at": "2025-01-01T00:00:00",
      "live_status": {
        "status": "running",
        "is_alive": true,
        "event_count": 15
      }
    }
  ],
  "total": 1
}
```

### Get Conversation
```http
GET /projects/{id}/conversations/{conversation_id}
X-User-UUID: {user_uuid}
```

### Create Message
```http
POST /projects/{id}/conversations/{conversation_id}/messages
X-User-UUID: {user_uuid}
Content-Type: application/json

{
  "message": "Follow-up message to the agent"
}
```

### Get Events
```http
GET /projects/{id}/conversations/{conversation_id}/events
X-User-UUID: {user_uuid}
```

**Response:**
```json
{
  "conversation_id": "conversation-uuid",
  "events": [
    {
      "type": "MessageEvent",
      "timestamp": "2025-01-01T00:00:00",
      "content": "Event details..."
    }
  ],
  "total": 10
}
```

### Utility Endpoints

#### Cleanup Finished Conversations
```http
POST /conversations/cleanup
X-User-UUID: {user_uuid}
```

#### Get All Conversation Status
```http
GET /conversations/status
X-User-UUID: {user_uuid}
```

## Setup Instructions

### 1. Install OpenHands Agent SDK

The OpenHands Agent SDK is not yet available on PyPI. Install it manually:

```bash
# Clone the repository
git clone https://github.com/All-Hands-AI/agent-sdk.git
cd agent-sdk

# Install dependencies and setup
make build

# Install the SDK in your Python environment
pip install -e .
```

### 2. Update Requirements

The current `requirements.txt` includes placeholders for OpenHands dependencies. After installing the SDK manually, you can uncomment the litellm dependency if needed.

### 3. Configure API Keys

Users need to configure their API keys through the existing integrations endpoints:

- **Anthropic API Key**: Required for LLM operations
- **GitHub Token**: Optional, for automatic branch/PR creation

### 4. Environment Variables

Set up the following environment variables:

```bash
# For OpenHands LLM proxy (if using)
LITELLM_API_KEY=your-litellm-api-key

# Data directory (defaults to /data)
DATA_DIR=/path/to/data/directory
```

### 5. Start the Server

```bash
cd backend
python app.py
```

## GitHub Integration

When a conversation is created with a `repo_url`, the system automatically:

1. **Creates a Branch**: `conversation-{first-8-chars-of-uuid}`
2. **Creates a PR**: Draft PR from the conversation branch to main
3. **Adopts Existing**: If branch/PR already exists, adopts them

The agent's file operations will work within the conversation's workspace directory, which can be synchronized with the GitHub repository.

## Agent Configuration

The agent is configured with the following tools:

- **BashTool**: Execute shell commands in the workspace
- **FileEditorTool**: Create and edit files
- **TaskTrackerTool**: Track and manage tasks

The LLM is configured to use:
- Model: `litellm_proxy/anthropic/claude-sonnet-4-20250514`
- Base URL: `https://llm-proxy.eval.all-hands.dev`

## Error Handling

The system handles various error conditions:

- **Missing OpenHands SDK**: Returns HTTP 503 with setup instructions
- **Missing API Keys**: Returns 400 with clear error message
- **GitHub Failures**: Logs warnings but continues conversation
- **Agent Errors**: Captured in conversation thread status
- **File System Issues**: Proper error logging and recovery

### Graceful Degradation

When the OpenHands SDK is not installed:
- The Flask application starts successfully
- Conversation endpoints return HTTP 503 with helpful error messages
- File-based conversation listing still works
- Clear setup instructions are provided in error responses

## Monitoring and Debugging

### Conversation Status

Check conversation status through the API:
```bash
curl -H "X-User-UUID: your-uuid" \
     http://localhost:8000/conversations/status
```

### Event Tracking

Monitor conversation events in real-time:
```bash
curl -H "X-User-UUID: your-uuid" \
     http://localhost:8000/projects/project-id/conversations/conv-id/events
```

### Logs

The system provides detailed logging:
- Conversation creation and management
- GitHub operations
- Agent execution status
- File system operations

## Testing

Run the test suite:

```bash
cd backend
python test_conversations.py
```

The test suite includes:
- AgentLoopManager functionality
- File storage operations
- API endpoint validation

## Limitations and Future Improvements

### Current Limitations

1. **Message Sending**: Sending messages to running conversations is not yet implemented
2. **Conversation Modification**: Modifying running conversations is not supported
3. **SDK Dependency**: Requires manual installation of OpenHands SDK

### Future Improvements

1. **Real-time Communication**: WebSocket support for live conversation updates
2. **Conversation Persistence**: Resume conversations after server restart
3. **Multi-user Support**: Better isolation between user conversations
4. **Resource Management**: Automatic cleanup of old conversations and workspaces
5. **Advanced GitHub Integration**: Automatic commits and PR updates

## Security Considerations

- **API Key Storage**: User API keys are stored in file-based storage
- **Workspace Isolation**: Each conversation has its own workspace directory
- **GitHub Permissions**: Uses user's GitHub token for repository operations
- **Input Validation**: All API inputs are validated and sanitized

## File Structure

```
backend/
├── agent_loop.py              # Core agent loop manager
├── conversations.py           # REST API endpoints
├── test_conversations.py      # Test suite
├── OPENHANDS_INTEGRATION.md   # This documentation
├── app.py                     # Main Flask application
├── keys.py                    # API key management
├── projects.py                # Project management
└── requirements.txt           # Python dependencies
```

## Support

For issues related to:
- **OpenHands SDK**: Check the [official repository](https://github.com/All-Hands-AI/agent-sdk)
- **Integration Issues**: Review the logs and test suite output
- **API Usage**: Refer to the endpoint documentation above
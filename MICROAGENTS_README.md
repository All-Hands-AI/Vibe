# OpenHands Microagents Integration

This document describes the successful integration of OpenHands Agent SDK microagents in the OpenVibe repository.

## Overview

The OpenVibe repository contains microagents in the `.openhands/microagents/` directory that can be loaded and used with the OpenHands Agent SDK. These microagents provide repository-specific instructions and knowledge that can be utilized by AI agents working with the codebase.

## Discovered Microagents

### Repository Agent: `repo`
- **Type**: Repository agent
- **Source**: `.openhands/microagents/repo.md`
- **Content**: Contains development workflow instructions, testing commands, and critical project information
- **Size**: 1,449 characters

**Key Information Provided:**
- Project overview (React + Vite + Fly.io deployment)
- Critical dependency management instructions (use `uv` for Python virtual environments)
- File-based state management (NO SQL databases)
- Frontend and backend testing/linting commands

## Implementation

### Files Created

1. **`microagent_loader.py`** - Production-ready microagent loader
   - Loads microagents from `.openhands/microagents/` directory
   - Returns structured data for both repository and knowledge agents
   - Includes proper error handling and logging

2. **`example_usage.py`** - Demonstrates practical usage
   - Shows how to extract key information from loaded microagents
   - Parses important sections and commands
   - Provides examples of accessing agent metadata

### Usage Example

```python
from microagent_loader import load_microagents

# Load all microagents
repo_agents, knowledge_agents = load_microagents()

# Access repository instructions
if 'repo' in repo_agents:
    repo_agent = repo_agents['repo']
    print(f"Agent: {repo_agent.name}")
    print(f"Type: {repo_agent.type}")
    print(f"Content: {repo_agent.content}")
```

## Technical Details

### Dependencies
- **OpenHands SDK**: Installed via `openhands-sdk @ git+https://github.com/all-hands-ai/agent-sdk.git@main#subdirectory=openhands/sdk`
- **Python Environment**: Uses `uv` for virtual environment management (as specified in microagent instructions)

### Import Path Resolution
The implementation handles Python path conflicts by ensuring imports come from the installed package rather than system-level OpenHands installations.

### Agent Types Supported
- **Repository Agents**: Contain repository-specific instructions and workflows
- **Knowledge Agents**: Contain domain knowledge and documentation (none found in this repository)

## Running the Examples

1. **Setup virtual environment** (following microagent instructions):
   ```bash
   cd /workspace/project/OpenVibe
   uv venv
   source .venv/bin/activate
   uv pip install -e backend/
   ```

2. **Load microagents**:
   ```bash
   python microagent_loader.py
   ```

3. **See usage examples**:
   ```bash
   python example_usage.py
   ```

## Integration Benefits

1. **Automated Repository Knowledge**: AI agents can automatically access repository-specific instructions
2. **Consistent Development Practices**: Microagents ensure all developers and AI agents follow the same workflows
3. **Dynamic Configuration**: Instructions can be updated in markdown files without code changes
4. **Structured Access**: The SDK provides a clean API for accessing microagent content

## Future Enhancements

- Add more specialized microagents for different aspects of the project
- Implement knowledge agents for domain-specific information
- Add MCP (Model Context Protocol) tools integration
- Create task-specific microagents for common development workflows

---

*This integration demonstrates successful loading and utilization of OpenHands microagents using the official Agent SDK.*
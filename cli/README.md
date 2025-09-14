# OpenVibe CLI

🤙 A command-line interface for OpenVibe that provides 1:1 functionality parity with the web frontend.

## Features

- **🔧 Setup & Configuration**: Initial setup with API key management
- **📱 Apps Management**: Create, list, delete, and view apps with deployment status
- **🎵 Riffs Management**: Create, list, and view riffs within apps  
- **💬 Interactive Chat**: Real-time chat interface with message polling (both full-screen and simple modes)
- **🔑 Integration Management**: Set up and manage API keys for GitHub, Fly.io, and AI services
- **📊 Status Monitoring**: View system status, backend connectivity, and integration health
- **🎨 Rich UI**: Beautiful terminal interface with colors, progress bars, and tables

## Installation

### Option 1: Install from Source
```bash
# Clone the repository and navigate to the CLI directory
cd OpenVibe/cli

# Create virtual environment and install
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Option 2: Download Pre-built Binary
Pre-built binaries are automatically created for each PR and release:
- **Linux (x64)**: `openvibe-linux-x64`
- **macOS (x64)**: `openvibe-macos-x64`
- **Windows (x64)**: `openvibe-windows-x64.exe`

Download from GitHub Actions artifacts or releases, make executable, and add to your PATH.

### Option 3: Build Binary Locally
```bash
# Unix/macOS
cd OpenVibe/cli
./build.sh

# Windows
cd OpenVibe\cli
build.bat
```

## Quick Start

```bash
# 1. Welcome and help
openvibe welcome
openvibe --help

# 2. Initial setup
openvibe setup

# 3. Set up mock API keys for testing
openvibe integrations setup-mock

# 4. Check system status
openvibe status

# 5. Create your first app
openvibe apps create "My First App"

# 6. List your apps
openvibe apps list

# 7. View app details
openvibe apps show my-first-app

# 8. Create a riff
openvibe riffs create my-first-app "My First Riff"

# 9. Start chatting (simple mode)
openvibe chat my-first-app my-first-riff --simple
```

## Command Reference

### Setup & Configuration
```bash
openvibe setup                    # Configure CLI settings and API keys
openvibe setup --reset           # Reset configuration to defaults
openvibe status                   # Show system status and health
```

### Apps Management
```bash
openvibe apps list                # List all your apps
openvibe apps create "App Name"   # Create a new app
openvibe apps show <slug>         # Show detailed app information
openvibe apps delete <slug>       # Delete an app (with confirmation)
```

### Riffs Management
```bash
openvibe riffs list <app-slug>              # List riffs for an app
openvibe riffs create <app-slug> "Name"     # Create a new riff
openvibe riffs show <app-slug> <riff-slug>  # Show riff details
```

### Interactive Chat
```bash
openvibe chat <app-slug> <riff-slug>         # Full-screen chat interface
openvibe chat <app-slug> <riff-slug> --simple  # Simple line-by-line chat
```

**Chat Controls:**
- **Full-screen mode**: Ctrl+Enter to send, Ctrl+R to refresh, Ctrl+C to exit
- **Simple mode**: Type messages and press Enter, type 'exit' to quit

### Integration Management
```bash
openvibe integrations setup-mock             # Set up mock API keys for testing
openvibe integrations set-key <provider> <key>  # Set API key for a provider
openvibe integrations status                 # Check integration status
```

**Supported providers**: `github`, `fly`, `anthropic`

## Architecture

The CLI is built with:
- **Click**: Command-line interface framework
- **Rich**: Beautiful terminal output with colors and formatting
- **Prompt-toolkit**: Interactive chat interface
- **Requests**: HTTP client for API communication
- **Pydantic**: Configuration management

### Project Structure
```
openvibe_cli/
├── __init__.py
├── main.py              # Main CLI entry point
├── config.py            # Configuration management
├── api_client.py        # OpenVibe API client
└── commands/            # Command implementations
    ├── setup.py         # Setup and configuration
    ├── apps.py          # Apps management
    ├── riffs.py         # Riffs management
    ├── chat.py          # Interactive chat
    ├── integrations.py  # API key management
    └── status.py        # System status
```

## API Compatibility

This CLI provides 1:1 functionality parity with the OpenVibe React frontend:

- **Same API endpoints**: Uses identical REST API calls
- **Same data models**: Handles the same JSON structures
- **Same workflows**: Mirrors the frontend user experience
- **Same features**: Apps, riffs, chat, status monitoring

## Configuration

Configuration is stored in `~/.openvibe/config.json`:

```json
{
  "user_uuid": "generated-uuid",
  "backend_url": "http://localhost:8000",
  "github_token": "your-github-token",
  "fly_token": "your-fly-token",
  "anthropic_api_key": "your-anthropic-key"
}
```

## Binary Distribution

The CLI is automatically packaged as standalone binaries using PyInstaller:

### Automated Builds
- **GitHub Actions**: Binaries are built for Linux, macOS, and Windows on every PR
- **Artifacts**: Available as GitHub Actions artifacts (30-day retention)
- **Releases**: Tagged releases include permanent binary downloads
- **Cross-platform**: Native binaries for each platform with no dependencies

### Build Process
1. **PyInstaller**: Packages Python app and dependencies into single executable
2. **Testing**: Each binary is tested with `--version` and `--help` commands
3. **Artifacts**: Uploaded to GitHub Actions for easy download
4. **Comments**: PR comments include direct download links

### Local Building
```bash
# Install build dependencies
uv pip install -e .[build]

# Build using spec file
pyinstaller --clean --noconfirm openvibe.spec

# Or use convenience scripts
./build.sh        # Unix/macOS
build.bat         # Windows
```

## Development

### Running Tests
```bash
# Backend tests (with mock mode)
cd ../backend
MOCK_MODE=true python -m pytest

# CLI testing against mock backend
cd ../cli
MOCK_MODE=true python -m openvibe_cli.main status
```

### Adding New Commands

1. Create a new command file in `commands/`
2. Implement the command using Click decorators
3. Add rich formatting for beautiful output
4. Register the command in `main.py`
5. Update this README

### Mock Mode

For testing without real API keys, the backend supports mock mode:

```bash
# Start backend in mock mode
cd ../backend
MOCK_MODE=true python app.py

# Set up mock API keys
openvibe integrations setup-mock
```

## Troubleshooting

### Backend Connection Issues
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Check CLI configuration
openvibe setup
openvibe status
```

### API Key Issues
```bash
# Check integration status
openvibe integrations status

# Set up mock keys for testing
openvibe integrations setup-mock
```

### Chat Issues
```bash
# Use simple chat mode if full-screen has issues
openvibe chat <app> <riff> --simple

# Check riff exists
openvibe riffs list <app>
```

## Contributing

This CLI is designed to mirror the OpenVibe frontend exactly. When adding features:

1. Check the frontend implementation first
2. Maintain API compatibility
3. Use rich formatting for beautiful output
4. Add comprehensive error handling
5. Update documentation

## License

Same as OpenVibe project.
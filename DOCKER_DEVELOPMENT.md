# Docker Development Setup

This document explains the enhanced Dockerfile setup that supports both production and development modes with hot-reload capabilities and automatic git synchronization.

## Overview

The Dockerfile has been enhanced to support:
- **Full git repository presence** in the container
- **Automatic git branch watching** when `PULL_FROM_BRANCH` is set
- **Hot-reload for both React and Python** in development mode
- **Seamless switching** between production and development modes

## Environment Variables

### Required for Development Mode

- `PULL_FROM_BRANCH`: Set this to the branch name you want to watch and pull from
  - Example: `PULL_FROM_BRANCH=main`
  - When set, enables development mode with hot-reload

### Optional Configuration

- `GIT_POLL_INTERVAL`: How often to check for git updates (default: 30 seconds)
  - Example: `GIT_POLL_INTERVAL=60`
- `GIT_USER_NAME`: Git user name for commits (default: "openvibe-watcher")
- `GIT_USER_EMAIL`: Git user email (default: "watcher@openvibe.local")

## Usage

### Production Mode (Default)

```bash
# Build the image
docker build -t openvibe .

# Run in production mode (serves built React app via nginx)
docker run -p 80:80 openvibe
```

**Production mode features:**
- Serves pre-built React application via nginx
- Runs Python backend with gunicorn
- Optimized for performance and stability
- No git watching or hot-reload

### Development Mode

```bash
# Build the image
docker build -t openvibe .

# Run in development mode with git watching
docker run -p 3000:3000 -p 8000:8000 \
  -e PULL_FROM_BRANCH=main \
  openvibe
```

**Development mode features:**
- Installs Node.js at runtime for Vite dev server
- Runs React with hot-reload on port 3000
- Runs Python Flask in debug mode on port 8000
- Automatically pulls latest changes from specified branch
- Restarts services when code changes are detected
- Automatically updates dependencies when package files change

### Advanced Development Setup

```bash
# Run with custom git polling interval
docker run -p 3000:3000 -p 8000:8000 \
  -e PULL_FROM_BRANCH=develop \
  -e GIT_POLL_INTERVAL=60 \
  -e GIT_USER_NAME="MyName" \
  -e GIT_USER_EMAIL="my@email.com" \
  openvibe
```

## Port Mapping

| Port | Service | Mode |
|------|---------|------|
| 80 | Nginx (production) | Production only |
| 3000 | Vite dev server | Development only |
| 8000 | Python backend | Both modes |

## Services in Development Mode

When `PULL_FROM_BRANCH` is set, the following services run:

1. **git-watcher**: Monitors the specified branch and pulls changes
2. **service-restarter**: Restarts services when changes are detected
3. **vite-dev**: React development server with hot-reload
4. **flask-dev**: Python Flask in debug mode with auto-reload

## Services in Production Mode

When `PULL_FROM_BRANCH` is not set:

1. **nginx**: Serves the built React application
2. **backend**: Python backend via gunicorn

## File Structure

The container includes these additional files:

- `/usr/local/bin/git-watcher.sh`: Git monitoring script
- `/usr/local/bin/service-restarter.sh`: Service restart handler
- `/usr/local/bin/start-services.sh`: Dynamic service configuration
- `/app/`: Full git repository with source code
- `/data/`: Persistent data directory

## Automatic Dependency Management

The system automatically handles dependency updates:

- **npm dependencies**: Updated when `package.json` or `package-lock.json` changes
- **Python dependencies**: Updated when `backend/pyproject.toml` changes
- **Service restart**: Triggered after dependency updates

## Git Configuration

The git watcher automatically:
- Configures the repository as a safe directory
- Sets up git user credentials (configurable via env vars)
- Stashes local changes before pulling
- Handles branch switching and creation

## Troubleshooting

### Development Mode Not Starting

1. Ensure `PULL_FROM_BRANCH` is set
2. Check that the branch exists in the remote repository
3. Verify git credentials if using private repositories

### Services Not Restarting

1. Check supervisor logs: `docker exec <container> supervisorctl status`
2. Verify the restart trigger file: `docker exec <container> ls -la /tmp/restart-services`

### Port Conflicts

- Production mode uses port 80
- Development mode uses ports 3000 and 8000
- Ensure these ports are available and properly mapped

### Git Authentication

For private repositories, you may need to:
1. Mount SSH keys or git credentials
2. Set up git authentication in the container
3. Use HTTPS with tokens in the git remote URL

## Example Docker Compose

```yaml
version: '3.8'
services:
  openvibe-dev:
    build: .
    ports:
      - "3000:3000"
      - "8000:8000"
    environment:
      - PULL_FROM_BRANCH=main
      - GIT_POLL_INTERVAL=30
    volumes:
      - data:/data
    # Optional: Mount git credentials
    # volumes:
    #   - ~/.ssh:/root/.ssh:ro
    #   - ~/.gitconfig:/root/.gitconfig:ro

volumes:
  data:
```

## Security Considerations

- The development mode installs additional packages at runtime
- Git credentials should be handled securely
- Consider using read-only git access for production deployments
- The container runs with root privileges for service management

## Performance Notes

- Development mode has higher resource usage due to hot-reload
- Git polling frequency affects network usage
- Node.js installation adds startup time in development mode
- Consider using multi-stage builds for production optimization
# syntax = docker/dockerfile:1

# Adjust NODE_VERSION as desired
ARG NODE_VERSION=20.18.0
FROM node:${NODE_VERSION}-slim AS base

LABEL fly_launch_runtime="Vite"

# Vite app lives here
WORKDIR /app

# Set production environment
ENV NODE_ENV="production"


# Throw-away build stage to reduce size of final image
FROM base AS build

# Install packages needed to build node modules
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y build-essential node-gyp pkg-config python-is-python3

# Install node modules
COPY frontend/package-lock.json frontend/package.json ./
RUN npm ci --include=dev

# Copy frontend application code
COPY frontend/ .

# Build application
RUN npm run build

# Remove development dependencies
RUN npm prune --omit=dev


# Final stage for app image - using Ubuntu to support both nginx and python
FROM ubuntu:24.04

# Install Node.js, npm, nginx, python, development tools, Docker, and supervisor
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    # Core system tools
    nginx \
    supervisor \
    curl \
    wget \
    git \
    # Python and development tools
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    # Node.js (using NodeSource repository for latest LTS)
    ca-certificates \
    gnupg \
    lsb-release \
    # Build tools for native dependencies
    build-essential \
    gcc \
    g++ \
    make \
    # Additional development utilities
    vim \
    nano \
    htop \
    tree \
    jq \
    unzip \
    # Docker dependencies
    apt-transport-https \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install Docker
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update -qq && \
    apt-get install --no-install-recommends -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x LTS
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs

# Install Python package managers: uv and poetry
RUN pip3 install --break-system-packages uv poetry

# Verify installations and set up global npm packages for development
RUN npm install -g \
    # Development and build tools
    nodemon \
    concurrently \
    # Linting and formatting
    eslint \
    prettier \
    # Testing utilities
    jest \
    # Package management
    npm-check-updates

# Set up development environment variables
ENV POETRY_HOME="/opt/poetry" \
    POETRY_CACHE_DIR="/tmp/poetry_cache" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    PYTHONPATH="/app/backend" \
    NODE_ENV="development"

# Create development directories
RUN mkdir -p /app/frontend /app/backend /workspace

# Copy built React application
COPY --from=build /app/dist /usr/share/nginx/html

# Copy Python backend
COPY backend/ /app/backend/
WORKDIR /app/backend

# Install Python dependencies using uv from pyproject.toml
# First install the project itself which will handle git dependencies properly
RUN uv pip install --system --break-system-packages .

# Verify all development tools are installed and working
RUN echo "=== Verifying Development Tools ===" && \
    echo "Node.js version:" && node --version && \
    echo "npm version:" && npm --version && \
    echo "Python version:" && python3 --version && \
    echo "pip version:" && pip3 --version && \
    echo "uv version:" && uv --version && \
    echo "poetry version:" && poetry --version && \
    echo "git version:" && git --version && \
    echo "Docker version:" && docker --version && \
    echo "=== All tools verified successfully ==="

# Create data directory for persistent storage
RUN mkdir -p /data && chown -R www-data:www-data /data

# Pre-pull and save the agent server image during build to avoid runtime delays
ARG AGENT_SERVER_IMAGE=ghcr.io/all-hands-ai/agent-server:ea72d20@sha256:39c72c4796bb30f8d08d4cefbe3aa48b49f96c26eae6e7d79c4a8190fd10865f
RUN echo "📥 Pre-pulling and saving agent server image during build: ${AGENT_SERVER_IMAGE}" && \
    # Clean up any existing Docker state
    rm -f /var/run/docker.pid /var/run/docker.sock && \
    # Start Docker daemon in background
    dockerd --host=unix:///var/run/docker.sock --storage-driver=vfs --iptables=false --bridge=none > /tmp/dockerd-build.log 2>&1 & \
    DOCKER_PID=$! && \
    # Wait for Docker to be ready
    timeout=30; while [ $timeout -gt 0 ] && ! docker info >/dev/null 2>&1; do sleep 1; timeout=$((timeout-1)); done && \
    # Pull and save the image
    if docker info >/dev/null 2>&1; then \
        echo "✅ Docker daemon ready, pulling image..." && \
        docker pull ${AGENT_SERVER_IMAGE} && \
        echo "💾 Saving image to tar file..." && \
        docker save ${AGENT_SERVER_IMAGE} -o /data/agent-server-image.tar && \
        echo "✅ Successfully saved ${AGENT_SERVER_IMAGE} to /data/agent-server-image.tar" || \
        echo "⚠️ Failed to pull/save image, will pull at runtime"; \
    else \
        echo "⚠️ Docker daemon not ready, will pull at runtime"; \
    fi && \
    # Stop Docker daemon properly
    kill $DOCKER_PID 2>/dev/null || true && \
    wait $DOCKER_PID 2>/dev/null || true && \
    # Clean up all Docker state files
    rm -f /var/run/docker.pid /var/run/docker.sock /tmp/dockerd-build.log && \
    # Kill any remaining Docker processes
    pkill -f dockerd || true && \
    sleep 2

# Copy nginx configuration
COPY nginx.conf /etc/nginx/sites-available/default

# Copy htpasswd file for basic authentication
COPY .htpasswd /etc/nginx/.htpasswd

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy image loading script
COPY load-agent-image.sh /usr/local/bin/load-agent-image.sh
RUN chmod +x /usr/local/bin/load-agent-image.sh

# Create necessary directories
RUN mkdir -p /var/log/supervisor

# Expose port 80
EXPOSE 80

# Start supervisor to manage both nginx and python backend
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

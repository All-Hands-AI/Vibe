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

# Install Node.js, npm, nginx, python, development tools, and supervisor
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    # Core system tools
    nginx \
    supervisor \
    curl \
    wget \
    git \
    # Apache utilities for htpasswd
    apache2-utils \
    # Python and development tools
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    # Node.js (using NodeSource repository for latest LTS)
    ca-certificates \
    gnupg \
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
    && rm -rf /var/lib/apt/lists/*

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
    echo "=== All tools verified successfully ==="

# Create data directory for persistent storage
RUN mkdir -p /data && chown -R www-data:www-data /data

# Copy nginx configuration
COPY nginx.conf /etc/nginx/sites-available/default

# Copy entrypoint script for dynamic htpasswd generation
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create necessary directories
RUN mkdir -p /var/log/supervisor

# Expose port 80
EXPOSE 80

# Use entrypoint script to generate htpasswd and start services
CMD ["/entrypoint.sh"]

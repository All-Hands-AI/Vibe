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
COPY package-lock.json package.json ./
RUN npm ci --include=dev

# Copy application code including git repository
COPY . .

# Build application
RUN npm run build

# Remove development dependencies
RUN npm prune --omit=dev


# Final stage for app image - using Ubuntu to support both nginx and python
FROM ubuntu:22.04

# Install nginx, python, uv, supervisor, git, and development tools
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    nginx \
    python3 \
    python3-pip \
    supervisor \
    curl \
    git \
    inotify-tools \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install uv

# Copy built React application
COPY --from=build /app/dist /usr/share/nginx/html

# Copy entire repository including git for development mode
COPY --from=build /app /app
WORKDIR /app

# Install Python dependencies using uv from pyproject.toml
RUN cd backend && \
    uv pip compile pyproject.toml -o requirements.txt && \
    uv pip install --system -r requirements.txt && \
    rm requirements.txt

# Create data directory for persistent storage
RUN mkdir -p /data && chown -R www-data:www-data /data

# Copy nginx configuration
COPY nginx.conf /etc/nginx/sites-available/default

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy git watcher, service restarter, and startup scripts
COPY git-watcher.sh /usr/local/bin/git-watcher.sh
COPY service-restarter.sh /usr/local/bin/service-restarter.sh
COPY start-services.sh /usr/local/bin/start-services.sh
RUN chmod +x /usr/local/bin/git-watcher.sh /usr/local/bin/service-restarter.sh /usr/local/bin/start-services.sh

# Create necessary directories
RUN mkdir -p /var/log/supervisor

# Expose ports for both production and development
EXPOSE 80 3000 8000

# Start services using our dynamic startup script
CMD ["/usr/local/bin/start-services.sh"]

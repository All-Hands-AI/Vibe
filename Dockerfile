# syntax = docker/dockerfile:1

# Adjust NODE_VERSION as desired
ARG NODE_VERSION=20.18.0
FROM node:${NODE_VERSION}-slim AS base

LABEL fly_launch_runtime="Full-Stack"

# Set production environment
ENV NODE_ENV="production"

# Install packages needed for both frontend and backend
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y build-essential node-gyp pkg-config python-is-python3 nginx

# Build frontend
FROM base AS frontend-build
WORKDIR /app
COPY package-lock.json package.json ./
RUN npm ci --include=dev
COPY . .
RUN npm run build

# Build backend
FROM base AS backend-build
WORKDIR /app/backend
COPY backend/package.json backend/package-lock.json ./
RUN npm ci --omit=dev

# Final stage for app image
FROM node:${NODE_VERSION}-slim AS final

# Install nginx and curl
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y nginx curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set production environment
ENV NODE_ENV="production"

# Copy built frontend
COPY --from=frontend-build /app/dist /usr/share/nginx/html

# Copy backend
WORKDIR /app/backend
COPY --from=backend-build /app/backend/node_modules ./node_modules
COPY backend/package.json backend/server.js ./

# Create nginx configuration
RUN echo 'server { \
    listen 80; \
    server_name _; \
    \
    # Serve frontend \
    location / { \
        root /usr/share/nginx/html; \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # Proxy API requests to backend \
    location /api/ { \
        proxy_pass http://localhost:3001/; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        proxy_connect_timeout 5s; \
        proxy_send_timeout 60s; \
        proxy_read_timeout 60s; \
    } \
    \
    # Health check endpoint \
    location /health { \
        proxy_pass http://localhost:3001/health; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
        access_log off; \
    } \
}' > /etc/nginx/sites-available/default

# Create startup script
RUN echo '#!/bin/bash \
set -e \
\
echo "Starting OpenVibe application..." \
\
# Start backend server in background \
echo "Starting backend server..." \
cd /app/backend \
node server.js > /var/log/backend.log 2>&1 & \
BACKEND_PID=$! \
\
# Wait for backend to be ready \
echo "Waiting for backend to be ready..." \
for i in {1..30}; do \
    if curl -f http://localhost:3001/health >/dev/null 2>&1; then \
        echo "Backend is ready!" \
        break \
    fi \
    if ! kill -0 $BACKEND_PID 2>/dev/null; then \
        echo "Backend process died!" \
        cat /var/log/backend.log \
        exit 1 \
    fi \
    echo "Waiting for backend... ($i/30)" \
    sleep 1 \
done \
\
# Final check \
if ! curl -f http://localhost:3001/health >/dev/null 2>&1; then \
    echo "Backend failed to become ready!" \
    cat /var/log/backend.log \
    exit 1 \
fi \
\
echo "Backend started successfully (PID: $BACKEND_PID)" \
\
# Start nginx in foreground \
echo "Starting nginx..." \
nginx -g "daemon off;"' > /start.sh && chmod +x /start.sh

# Expose port
EXPOSE 80

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

# Start both services
CMD ["/start.sh"]

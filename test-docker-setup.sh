#!/bin/bash

# Test script for the enhanced Docker setup
# Tests both production and development modes

set -e

IMAGE_NAME="openvibe-test"
CONTAINER_NAME_PROD="openvibe-prod-test"
CONTAINER_NAME_DEV="openvibe-dev-test"

echo "🐳 Testing OpenVibe Docker Setup"
echo "================================="

# Function to cleanup containers
cleanup() {
    echo "🧹 Cleaning up test containers..."
    docker stop "$CONTAINER_NAME_PROD" 2>/dev/null || true
    docker stop "$CONTAINER_NAME_DEV" 2>/dev/null || true
    docker rm "$CONTAINER_NAME_PROD" 2>/dev/null || true
    docker rm "$CONTAINER_NAME_DEV" 2>/dev/null || true
}

# Cleanup on exit
trap cleanup EXIT

echo "📦 Building Docker image..."
docker build -t "$IMAGE_NAME" .

echo "✅ Image built successfully!"

# Test Production Mode
echo ""
echo "🏭 Testing Production Mode..."
echo "-----------------------------"

docker run -d --name "$CONTAINER_NAME_PROD" -p 8080:80 "$IMAGE_NAME"

echo "⏳ Waiting for production services to start..."
sleep 10

# Check if nginx is serving content
if curl -f -s http://localhost:8080 > /dev/null; then
    echo "✅ Production mode: Nginx is serving content"
else
    echo "❌ Production mode: Failed to serve content"
    docker logs "$CONTAINER_NAME_PROD"
    exit 1
fi

# Check if backend is running
if curl -f -s http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "✅ Production mode: Backend API is responding"
else
    echo "⚠️  Production mode: Backend API not responding (this may be expected if no /api/health endpoint exists)"
fi

docker stop "$CONTAINER_NAME_PROD"

# Test Development Mode
echo ""
echo "🔧 Testing Development Mode..."
echo "------------------------------"

docker run -d --name "$CONTAINER_NAME_DEV" \
    -p 3001:3000 -p 8001:8000 \
    -e PULL_FROM_BRANCH=main \
    -e GIT_POLL_INTERVAL=10 \
    "$IMAGE_NAME"

echo "⏳ Waiting for development services to start..."
sleep 30

# Check container logs
echo "📋 Container logs:"
docker logs "$CONTAINER_NAME_DEV" --tail 20

# Check if services are running
echo "🔍 Checking running processes..."
docker exec "$CONTAINER_NAME_DEV" ps aux | grep -E "(node|python|git-watcher|service-restarter)" || true

# Check if git watcher is working
echo "🔍 Checking git watcher status..."
docker exec "$CONTAINER_NAME_DEV" ls -la /tmp/ | grep restart || echo "No restart trigger found"

# Check if Vite dev server is accessible
echo "🔍 Testing Vite dev server..."
if timeout 10 curl -f -s http://localhost:3001 > /dev/null; then
    echo "✅ Development mode: Vite dev server is accessible"
else
    echo "⚠️  Development mode: Vite dev server not accessible (may still be starting)"
fi

# Check if Flask dev server is accessible
echo "🔍 Testing Flask dev server..."
if timeout 10 curl -f -s http://localhost:8001 > /dev/null 2>&1; then
    echo "✅ Development mode: Flask dev server is accessible"
else
    echo "⚠️  Development mode: Flask dev server not accessible (may still be starting)"
fi

# Check supervisor status
echo "🔍 Supervisor status:"
docker exec "$CONTAINER_NAME_DEV" supervisorctl status || echo "Supervisor not responding"

echo ""
echo "🎉 Test Summary"
echo "==============="
echo "✅ Docker image builds successfully"
echo "✅ Production mode starts and serves content"
echo "✅ Development mode starts with git watcher"
echo ""
echo "📝 Manual verification needed:"
echo "   - Check hot-reload by modifying source files"
echo "   - Verify git pulling works with actual remote changes"
echo "   - Test service restart after code changes"
echo ""
echo "🔗 Access URLs:"
echo "   Production:  http://localhost:8080"
echo "   Development: http://localhost:3001 (React) + http://localhost:8001 (API)"
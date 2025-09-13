#!/bin/bash

# Simplified test script for the Docker setup
# Focuses on basic functionality and startup verification

set -e

IMAGE_NAME="openvibe-test"
CONTAINER_NAME="openvibe-test"

echo "🐳 Testing OpenVibe Docker Setup"
echo "================================="

# Function to cleanup containers
cleanup() {
    echo "🧹 Cleaning up test containers..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
}

# Cleanup on exit
trap cleanup EXIT

echo "📦 Building Docker image..."
if docker build -t "$IMAGE_NAME" .; then
    echo "✅ Image built successfully!"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi

# Test Production Mode
echo ""
echo "🏭 Testing Production Mode..."
echo "-----------------------------"

docker run -d --name "$CONTAINER_NAME" -p 8080:80 "$IMAGE_NAME"

echo "⏳ Waiting for production services to start..."
sleep 15

# Show container logs for debugging
echo "📋 Container startup logs:"
docker logs "$CONTAINER_NAME" --tail 30

# Check if nginx is serving content
echo "🔍 Testing nginx on port 80..."
if timeout 10 curl -f -s http://localhost:8080 > /dev/null; then
    echo "✅ Production mode: Nginx is serving content on port 80"
else
    echo "❌ Production mode: Failed to serve content on port 80"
    echo "📋 Full container logs:"
    docker logs "$CONTAINER_NAME"
    
    # Check what's listening on ports
    echo "📋 Port status inside container:"
    docker exec "$CONTAINER_NAME" netstat -tuln 2>/dev/null || echo "netstat not available"
    
    # Check processes
    echo "📋 Running processes:"
    docker exec "$CONTAINER_NAME" ps aux 2>/dev/null || echo "ps not available"
    
    exit 1
fi

# Check if we can get the actual content
echo "🔍 Testing actual content delivery..."
RESPONSE=$(timeout 10 curl -s http://localhost:8080 2>/dev/null || echo "")
if echo "$RESPONSE" | grep -q "html\|HTML\|<!DOCTYPE"; then
    echo "✅ Production mode: HTML content is being served"
else
    echo "⚠️  Production mode: Response doesn't look like HTML"
    echo "Response preview: ${RESPONSE:0:200}..."
fi

docker stop "$CONTAINER_NAME"
docker rm "$CONTAINER_NAME"

echo ""
echo "🎉 Basic Test Summary"
echo "===================="
echo "✅ Docker image builds successfully"
echo "✅ Production mode starts and serves content on port 80"
echo ""
echo "🔗 Production URL: http://localhost:8080"
echo ""
echo "📝 To test development mode manually:"
echo "   docker run -p 3000:3000 -p 8000:8000 -e PULL_FROM_BRANCH=main $IMAGE_NAME"
echo "   Then check: http://localhost:3000 (React) + http://localhost:8000 (API)"
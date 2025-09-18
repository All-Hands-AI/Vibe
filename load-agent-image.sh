#!/bin/bash
# Script to load the pre-saved agent server image into the runtime Docker daemon

echo "🔄 Loading pre-saved agent server image..."

# Check if the saved image exists
if [ -f "/data/agent-server-image.tar" ]; then
    echo "📦 Found saved image at /data/agent-server-image.tar"
    
    # Wait for Docker daemon to be ready
    echo "⏳ Waiting for Docker daemon to be ready..."
    timeout=60
    while [ $timeout -gt 0 ] && ! docker info >/dev/null 2>&1; do
        sleep 1
        timeout=$((timeout-1))
    done
    
    if docker info >/dev/null 2>&1; then
        echo "✅ Docker daemon is ready, loading image..."
        
        # Load the image
        if docker load -i /data/agent-server-image.tar; then
            echo "✅ Successfully loaded agent server image from tar file"
            
            # Verify the image is available
            if docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "ghcr.io/all-hands-ai/agent-server"; then
                echo "✅ Agent server image is now available in Docker"
                docker images | grep "ghcr.io/all-hands-ai/agent-server"
            else
                echo "⚠️ Image loaded but not found in docker images list"
            fi
        else
            echo "❌ Failed to load image from tar file"
            exit 1
        fi
    else
        echo "❌ Docker daemon not ready after 60 seconds"
        exit 1
    fi
else
    echo "⚠️ No saved image found at /data/agent-server-image.tar"
    echo "🔄 Image will be pulled at runtime when needed"
fi

echo "🎉 Image loading process completed"
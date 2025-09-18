#!/usr/bin/env python3
"""
Test script to verify Docker image pulling works correctly.
"""

import os
import docker
from docker_agent_loop import AGENT_SERVER_IMAGE

def test_image_pull():
    """Test that we can pull the agent server image."""
    print(f"🧪 Testing Docker image pull for: {AGENT_SERVER_IMAGE}")
    
    try:
        client = docker.from_env()
        print("🐳 Docker client connected successfully")
        
        # Check if image exists locally
        try:
            image = client.images.get(AGENT_SERVER_IMAGE)
            print(f"✅ Image {AGENT_SERVER_IMAGE} found locally")
            print(f"📊 Image ID: {image.id}")
            print(f"📊 Image tags: {image.tags}")
            return True
        except docker.errors.ImageNotFound:
            print(f"📥 Image {AGENT_SERVER_IMAGE} not found locally, pulling...")
            
            # Pull the image
            image = client.images.pull(AGENT_SERVER_IMAGE)
            print(f"✅ Successfully pulled image {AGENT_SERVER_IMAGE}")
            print(f"📊 Image ID: {image.id}")
            print(f"📊 Image tags: {image.tags}")
            return True
            
    except Exception as e:
        print(f"❌ Error testing image pull: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_image_pull()
    if success:
        print("🎉 Image pull test completed successfully!")
    else:
        print("💥 Image pull test failed!")
        exit(1)
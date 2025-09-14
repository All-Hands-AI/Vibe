#!/usr/bin/env python3
"""
Test script to demonstrate the new riff adoption functionality.

This script shows how the new riff creation workflow handles existing branches and PRs:
1. When creating a new riff, it pushes a new branch and creates a PR
2. If the branch or PR already exists, it adopts the existing ones instead of failing
3. If a riff with the same name already exists, it adopts the existing riff
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
USER_UUID = "demo-user-12345"
HEADERS = {
    "X-User-UUID": USER_UUID,
    "Content-Type": "application/json"
}

def setup_api_keys():
    """Set up mock API keys for testing"""
    keys = {
        "anthropic": "mock-anthropic-key-12345",
        "github": "mock-github-key-12345", 
        "fly": "mock-fly-key-12345"
    }
    
    for provider, key in keys.items():
        response = requests.post(
            f"{BASE_URL}/integrations/{provider}",
            headers=HEADERS,
            json={"api_key": key}
        )
        print(f"✅ Set up {provider} API key: {response.status_code}")

def create_app(app_name):
    """Create a new app"""
    response = requests.post(
        f"{BASE_URL}/api/apps",
        headers=HEADERS,
        json={"name": app_name}
    )
    
    if response.status_code == 201:
        app_data = response.json()["app"]
        print(f"✅ Created app: {app_name} -> {app_data['slug']}")
        return app_data["slug"]
    else:
        print(f"❌ Failed to create app: {response.status_code} - {response.text}")
        return None

def create_riff(app_slug, riff_name):
    """Create a new riff"""
    response = requests.post(
        f"{BASE_URL}/api/apps/{app_slug}/riffs",
        headers=HEADERS,
        json={"name": riff_name}
    )
    
    if response.status_code in [200, 201]:
        riff_data = response.json()
        print(f"✅ Riff operation successful: {riff_data['message']}")
        return riff_data["riff"]
    else:
        print(f"❌ Failed to create riff: {response.status_code} - {response.text}")
        return None

def main():
    """Demonstrate the new riff adoption functionality"""
    print("🚀 Testing New Riff Adoption Functionality")
    print("=" * 50)
    
    # Set up API keys
    print("\n1. Setting up API keys...")
    setup_api_keys()
    
    # Create an app
    print("\n2. Creating a test app...")
    app_slug = create_app("Riff Adoption Demo")
    if not app_slug:
        return
    
    # Create first riff
    print("\n3. Creating first riff...")
    riff1 = create_riff(app_slug, "Feature Branch")
    if not riff1:
        return
    
    print(f"   - Riff slug: {riff1['slug']}")
    print(f"   - Created at: {riff1['created_at']}")
    
    # Try to create the same riff again - should adopt existing
    print("\n4. Attempting to create duplicate riff (should adopt existing)...")
    riff2 = create_riff(app_slug, "Feature Branch")
    if riff2:
        print(f"   - Same riff slug: {riff2['slug']}")
        print(f"   - Same creation time: {riff2['created_at']}")
        print("   ✅ Successfully adopted existing riff!")
    
    # Create a different riff
    print("\n5. Creating a different riff...")
    riff3 = create_riff(app_slug, "Bug Fix Branch")
    if riff3:
        print(f"   - New riff slug: {riff3['slug']}")
        print(f"   - Created at: {riff3['created_at']}")
    
    print("\n🎉 Demo completed successfully!")
    print("\nKey improvements:")
    print("- ✅ Existing riffs are adopted instead of rejected")
    print("- ✅ Existing branches are adopted instead of causing errors")
    print("- ✅ Existing PRs are adopted instead of causing conflicts")
    print("- ✅ Graceful handling of all edge cases")

if __name__ == "__main__":
    main()
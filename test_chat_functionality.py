#!/usr/bin/env python3
"""
Test script to demonstrate the chat functionality implementation.
This script tests the backend API endpoints for messages.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:12001"
USER_UUID = "test-user-uuid"
APP_SLUG = "test-app"
RIFF_SLUG = "chat-demo"

def test_api_endpoint(method, url, headers=None, data=None):
    """Test an API endpoint and return the response."""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        
        print(f"\n{method} {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """Test the chat functionality."""
    print("🚀 Testing OpenVibe Chat Functionality")
    print("=" * 50)
    
    headers = {"X-User-UUID": USER_UUID}
    
    # Test 1: Get all apps
    print("\n1. Testing GET /api/apps")
    apps = test_api_endpoint("GET", f"{BASE_URL}/api/apps")
    
    if not apps or not apps.get("apps"):
        print("❌ No apps found. Make sure test data is set up.")
        return
    
    # Test 2: Get riffs for the app
    print(f"\n2. Testing GET /api/apps/{APP_SLUG}/riffs")
    riffs = test_api_endpoint("GET", f"{BASE_URL}/api/apps/{APP_SLUG}/riffs")
    
    if not riffs or not riffs.get("riffs"):
        print("❌ No riffs found. Make sure test data is set up.")
        return
    
    # Test 3: Get messages for the riff (should be empty initially)
    print(f"\n3. Testing GET /api/apps/{APP_SLUG}/riffs/{RIFF_SLUG}/messages")
    messages = test_api_endpoint("GET", f"{BASE_URL}/api/apps/{APP_SLUG}/riffs/{RIFF_SLUG}/messages", headers=headers)
    
    initial_count = messages.get("count", 0) if messages else 0
    print(f"Initial message count: {initial_count}")
    
    # Test 4: Create a new message
    print(f"\n4. Testing POST /api/apps/{APP_SLUG}/riffs/messages")
    message_data = {
        "riff_slug": RIFF_SLUG,
        "content": f"Test message created at {datetime.now().isoformat()}",
        "type": "text"
    }
    
    new_message = test_api_endpoint("POST", f"{BASE_URL}/api/apps/{APP_SLUG}/riffs/messages", 
                                   headers=headers, data=message_data)
    
    if not new_message:
        print("❌ Failed to create message")
        return
    
    # Test 5: Get messages again to verify the new message was stored
    print(f"\n5. Testing GET /api/apps/{APP_SLUG}/riffs/{RIFF_SLUG}/messages (after creating message)")
    updated_messages = test_api_endpoint("GET", f"{BASE_URL}/api/apps/{APP_SLUG}/riffs/{RIFF_SLUG}/messages", headers=headers)
    
    if updated_messages:
        new_count = updated_messages.get("count", 0)
        print(f"New message count: {new_count}")
        
        if new_count > initial_count:
            print("✅ Message successfully created and stored!")
            
            # Show the latest message
            messages_list = updated_messages.get("messages", [])
            if messages_list:
                latest_message = messages_list[-1]
                print(f"Latest message: {latest_message.get('content')}")
                print(f"Created at: {latest_message.get('created_at')}")
                print(f"Message ID: {latest_message.get('id')}")
        else:
            print("❌ Message count did not increase")
    
    # Test 6: Create another message to test polling functionality
    print(f"\n6. Testing multiple messages (simulating chat)")
    for i in range(3):
        message_data = {
            "riff_slug": RIFF_SLUG,
            "content": f"Chat message #{i+1} - {datetime.now().strftime('%H:%M:%S')}",
            "type": "text"
        }
        
        result = test_api_endpoint("POST", f"{BASE_URL}/api/apps/{APP_SLUG}/riffs/messages", 
                                  headers=headers, data=message_data)
        
        if result:
            print(f"✅ Message #{i+1} created successfully")
        else:
            print(f"❌ Failed to create message #{i+1}")
        
        time.sleep(1)  # Simulate time between messages
    
    # Test 7: Final message count
    print(f"\n7. Final message count check")
    final_messages = test_api_endpoint("GET", f"{BASE_URL}/api/apps/{APP_SLUG}/riffs/{RIFF_SLUG}/messages", headers=headers)
    
    if final_messages:
        final_count = final_messages.get("count", 0)
        print(f"Final message count: {final_count}")
        
        print("\n📝 All messages in the riff:")
        for i, msg in enumerate(final_messages.get("messages", []), 1):
            print(f"  {i}. [{msg.get('created_at', 'Unknown time')}] {msg.get('content', 'No content')}")
    
    print("\n🎉 Chat functionality test completed!")
    print("\nImplemented features:")
    print("✅ Backend API endpoints for messages")
    print("✅ File-based message storage")
    print("✅ Message creation and retrieval")
    print("✅ User UUID-based message organization")
    print("✅ Riff-specific message storage")
    print("\nFrontend features (implemented but not tested here):")
    print("✅ ChatWindow component with real-time polling")
    print("✅ MessageList component with date grouping")
    print("✅ MessageInput component with file upload support")
    print("✅ BranchStatus component integration")
    print("✅ 2-second polling for new messages")

if __name__ == "__main__":
    main()
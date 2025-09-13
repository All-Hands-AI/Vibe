#!/usr/bin/env python3
"""
Demo script showing OpenHands Agent SDK integration usage

This script demonstrates how to use the conversation API endpoints
to create and manage AI agent conversations.
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:8000"
USER_UUID = "demo-user-12345"
PROJECT_ID = "demo-project"

def make_request(method, endpoint, data=None, timeout=30):
    """Make an API request with proper headers"""
    headers = {
        "X-User-UUID": USER_UUID,
        "Content-Type": "application/json"
    }
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def demo_conversation_flow():
    """Demonstrate a complete conversation flow"""
    print("🚀 OpenHands Agent SDK Integration Demo")
    print("=" * 50)
    
    # Step 1: Check server health
    print("\n1️⃣ Checking server health...")
    response = make_request("GET", "/api/health")
    if not response or response.status_code != 200:
        print("❌ Server is not running or unhealthy")
        print("   Please start the server with: python app.py")
        return False
    
    print("✅ Server is healthy")
    
    # Step 2: List existing conversations
    print("\n2️⃣ Listing existing conversations...")
    response = make_request("GET", f"/projects/{PROJECT_ID}/conversations")
    if response and response.status_code == 200:
        data = response.json()
        print(f"📋 Found {data.get('total', 0)} existing conversations")
        for conv in data.get('conversations', []):
            print(f"   - {conv['id']}: {conv['status']}")
    else:
        print("⚠️ Could not list conversations")
    
    # Step 3: Create a new conversation
    print("\n3️⃣ Creating a new conversation...")
    conversation_data = {
        "message": "Hello! Can you help me create a simple Python script that prints 'Hello, World!' and then explain what it does?",
        "repo_url": "https://github.com/example/demo-repo"  # Optional
    }
    
    response = make_request("POST", f"/projects/{PROJECT_ID}/conversations", conversation_data)
    if not response:
        print("❌ Failed to create conversation")
        return False
    
    if response.status_code == 201:
        conv_data = response.json()
        conversation_id = conv_data['id']
        print(f"✅ Created conversation: {conversation_id}")
        print(f"   Status: {conv_data['status']}")
        print(f"   Branch: {conv_data.get('branch_name', 'N/A')}")
        print(f"   PR: #{conv_data.get('pr_number', 'N/A')}")
    elif response.status_code == 400:
        error_data = response.json()
        print(f"❌ Failed to create conversation: {error_data.get('error', 'Unknown error')}")
        if "API key" in error_data.get('error', ''):
            print("   💡 Tip: Set up your Anthropic API key first:")
            print("   POST /integrations/anthropic with your API key")
        return False
    else:
        print(f"❌ Unexpected response: {response.status_code}")
        print(f"   {response.text}")
        return False
    
    # Step 4: Monitor conversation progress
    print(f"\n4️⃣ Monitoring conversation {conversation_id}...")
    for i in range(5):  # Check 5 times
        print(f"   Checking progress... ({i+1}/5)")
        
        # Get conversation status
        response = make_request("GET", f"/projects/{PROJECT_ID}/conversations/{conversation_id}")
        if response and response.status_code == 200:
            conv_data = response.json()
            live_status = conv_data.get('live_status', {})
            print(f"   Status: {live_status.get('status', 'unknown')}")
            print(f"   Events: {live_status.get('event_count', 0)}")
            print(f"   Alive: {live_status.get('is_alive', False)}")
            
            if live_status.get('status') in ['completed', 'error']:
                break
        
        time.sleep(2)  # Wait 2 seconds between checks
    
    # Step 5: Get conversation events
    print(f"\n5️⃣ Getting conversation events...")
    response = make_request("GET", f"/projects/{PROJECT_ID}/conversations/{conversation_id}/events")
    if response and response.status_code == 200:
        events_data = response.json()
        events = events_data.get('events', [])
        print(f"📊 Found {len(events)} events:")
        
        for i, event in enumerate(events[-5:]):  # Show last 5 events
            event_type = event.get('type', 'Unknown')
            timestamp = event.get('timestamp', 'N/A')
            print(f"   {i+1}. {event_type} at {timestamp}")
    else:
        print("⚠️ Could not retrieve events")
    
    # Step 6: Try to send a follow-up message (will likely fail as not implemented)
    print(f"\n6️⃣ Sending follow-up message...")
    message_data = {
        "message": "Great! Can you also add some comments to explain the code?"
    }
    
    response = make_request("POST", f"/projects/{PROJECT_ID}/conversations/{conversation_id}/messages", message_data)
    if response:
        if response.status_code == 201:
            print("✅ Follow-up message sent successfully")
        elif response.status_code == 501:
            print("⚠️ Follow-up messages not yet implemented (expected)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
    
    # Step 7: Get overall status
    print(f"\n7️⃣ Getting overall conversation status...")
    response = make_request("GET", "/conversations/status")
    if response and response.status_code == 200:
        status_data = response.json()
        conversations = status_data.get('conversations', [])
        print(f"📊 Total active conversations: {len(conversations)}")
        
        for conv in conversations:
            print(f"   - {conv['conversation_id']}: {conv['status']} ({conv['event_count']} events)")
    
    print("\n✅ Demo completed successfully!")
    return True

def demo_api_key_setup():
    """Demonstrate API key setup"""
    print("\n🔑 API Key Setup Demo")
    print("=" * 30)
    
    print("To use the OpenHands integration, you need to set up API keys:")
    print()
    print("1. Anthropic API Key (required):")
    print("   POST /integrations/anthropic")
    print("   Headers: X-User-UUID: your-uuid")
    print("   Body: {\"api_key\": \"your-anthropic-key\"}")
    print()
    print("2. GitHub Token (optional, for repo integration):")
    print("   POST /integrations/github")
    print("   Headers: X-User-UUID: your-uuid")
    print("   Body: {\"api_key\": \"your-github-token\"}")
    print()
    print("Example curl commands:")
    print(f"curl -X POST {BASE_URL}/integrations/anthropic \\")
    print(f"     -H 'X-User-UUID: {USER_UUID}' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"api_key\": \"your-anthropic-api-key\"}'")

def main():
    """Main demo function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        demo_api_key_setup()
        return
    
    print("OpenHands Agent SDK Integration Demo")
    print("This demo shows how to use the conversation API endpoints.")
    print()
    print("Prerequisites:")
    print("1. Server running on localhost:8000")
    print("2. OpenHands SDK installed")
    print("3. API keys configured (run with --setup for instructions)")
    print()
    
    input("Press Enter to continue or Ctrl+C to exit...")
    
    success = demo_conversation_flow()
    
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure the server is running: python app.py")
        print("2. Set up your API keys: python demo_conversation.py --setup")
        print("3. Install OpenHands SDK: see OPENHANDS_INTEGRATION.md")
        sys.exit(1)

if __name__ == "__main__":
    main()
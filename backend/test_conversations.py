#!/usr/bin/env python3
"""
Test script for OpenHands Agent SDK integration

This script tests the conversation endpoints and agent loop functionality.
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_agent_loop_manager():
    """Test the AgentLoopManager directly"""
    print("🧪 Testing AgentLoopManager...")
    
    try:
        from agent_loop import AgentLoopManager
        
        # Create manager
        manager = AgentLoopManager(data_dir="/tmp/test_data")
        print("✅ AgentLoopManager created successfully")
        
        # Test conversation creation (without actual API keys)
        success, message, conv_id = manager.start_conversation(
            project_id="test-project",
            initial_message="Hello, this is a test message",
            api_key="fake-key"  # This will fail but we can test the structure
        )
        
        print(f"📝 Conversation creation result: {success}, {message}")
        
        # Test listing conversations
        conversations = manager.list_conversations()
        print(f"📋 Found {len(conversations)} conversations")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing AgentLoopManager: {e}")
        return False

def test_file_storage():
    """Test file-based storage functionality"""
    print("🧪 Testing file storage...")
    
    try:
        from conversations import load_conversations, save_conversations
        
        test_project_id = "test-project-123"
        test_conversations = [
            {
                "id": "conv-1",
                "project_id": test_project_id,
                "user_uuid": "user-123",
                "initial_message": "Test message",
                "created_at": "2025-01-01T00:00:00",
                "status": "completed",
                "messages": []
            }
        ]
        
        # Test saving
        success = save_conversations(test_project_id, test_conversations)
        print(f"💾 Save result: {success}")
        
        # Test loading
        loaded_conversations = load_conversations(test_project_id)
        print(f"📁 Loaded {len(loaded_conversations)} conversations")
        
        # Verify data integrity
        if loaded_conversations and loaded_conversations[0]["id"] == "conv-1":
            print("✅ File storage test passed")
            return True
        else:
            print("❌ File storage test failed - data mismatch")
            return False
            
    except Exception as e:
        print(f"❌ Error testing file storage: {e}")
        return False

def test_api_endpoints():
    """Test the API endpoints (requires running server)"""
    print("🧪 Testing API endpoints...")
    
    base_url = "http://localhost:8000"
    headers = {
        "X-User-UUID": "test-user-123",
        "Content-Type": "application/json"
    }
    
    try:
        # Test health check first
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not running or health check failed: {response.status_code}")
            return False
        
        print("✅ Server is running")
        
        # Test listing conversations (should be empty initially)
        response = requests.get(
            f"{base_url}/projects/test-project/conversations",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Found {data.get('total', 0)} conversations")
            print("✅ List conversations endpoint working")
        else:
            print(f"❌ List conversations failed: {response.status_code}")
            return False
        
        # Test conversation creation (will fail without API keys, but should return proper error)
        create_data = {
            "message": "Hello, this is a test conversation",
            "repo_url": "https://github.com/test/repo"
        }
        
        response = requests.post(
            f"{base_url}/projects/test-project/conversations",
            headers=headers,
            json=create_data,
            timeout=10
        )
        
        if response.status_code in [400, 500]:  # Expected to fail without API keys
            print("✅ Create conversation endpoint working (expected failure without API keys)")
        else:
            print(f"❓ Unexpected response from create conversation: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server - make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting OpenHands Agent SDK integration tests...")
    print("=" * 60)
    
    tests = [
        ("AgentLoopManager", test_agent_loop_manager),
        ("File Storage", test_file_storage),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"💥 {test_name} test crashed: {e}")
            results[test_name] = False
        
        print(f"{'✅' if results[test_name] else '❌'} {test_name} test {'PASSED' if results[test_name] else 'FAILED'}")
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
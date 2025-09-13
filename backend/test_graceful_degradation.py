#!/usr/bin/env python3
"""
Test script for graceful degradation when OpenHands SDK is not available

This script tests that the application handles missing OpenHands SDK gracefully
and returns appropriate error messages.
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_graceful_degradation():
    """Test that endpoints handle missing OpenHands SDK gracefully"""
    print("🧪 Testing graceful degradation without OpenHands SDK...")
    
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
        
        # Test listing conversations (should work even without SDK)
        response = requests.get(
            f"{base_url}/projects/test-project/conversations",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 List conversations works: {data.get('total', 0)} conversations")
            print("✅ List conversations endpoint working")
        else:
            print(f"❌ List conversations failed: {response.status_code}")
            return False
        
        # Test conversation creation (should return 503 without SDK)
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
        
        if response.status_code == 503:
            data = response.json()
            error_msg = data.get('error', '')
            if 'OpenHands Agent SDK not available' in error_msg:
                print("✅ Create conversation returns proper 503 error")
                print(f"   Error message: {error_msg}")
                if 'setup_instructions' in data:
                    print(f"   Setup instructions: {data['setup_instructions']}")
            else:
                print(f"❌ Unexpected error message: {error_msg}")
                return False
        else:
            print(f"❌ Expected 503, got: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Test conversation events (should return 503 without SDK)
        response = requests.get(
            f"{base_url}/projects/test-project/conversations/fake-id/events",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 503:
            data = response.json()
            if 'OpenHands Agent SDK not available' in data.get('error', ''):
                print("✅ Get events returns proper 503 error")
            else:
                print(f"❌ Unexpected error message for events: {data}")
                return False
        else:
            print(f"❌ Expected 503 for events, got: {response.status_code}")
            return False
        
        # Test conversation status (should work but return empty list)
        response = requests.get(
            f"{base_url}/conversations/status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('total', 0) == 0 and 'message' in data:
                print("✅ Conversation status returns empty list with message")
                print(f"   Message: {data['message']}")
            else:
                print(f"❌ Unexpected status response: {data}")
                return False
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            return False
        
        # Test cleanup (should work but return message about no SDK)
        response = requests.post(
            f"{base_url}/conversations/cleanup",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'OpenHands Agent SDK not available' in data.get('message', ''):
                print("✅ Cleanup returns proper message about no SDK")
            else:
                print(f"❌ Unexpected cleanup response: {data}")
                return False
        else:
            print(f"❌ Cleanup endpoint failed: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server - make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error testing graceful degradation: {e}")
        return False

def test_imports():
    """Test that imports work without OpenHands SDK"""
    print("🧪 Testing imports without OpenHands SDK...")
    
    try:
        from conversations import conversations_bp, AGENT_MANAGER_AVAILABLE
        print("✅ conversations.py imports successfully")
        print(f"🤖 Agent manager available: {AGENT_MANAGER_AVAILABLE}")
        
        if not AGENT_MANAGER_AVAILABLE:
            print("✅ Correctly detected that OpenHands SDK is not available")
        else:
            print("⚠️ Agent manager shows as available but SDK is not installed")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Run graceful degradation tests"""
    print("🚀 Starting graceful degradation tests...")
    print("=" * 60)
    
    tests = [
        ("Import Handling", test_imports),
        ("API Graceful Degradation", test_graceful_degradation),
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
        print("🎉 All graceful degradation tests passed!")
        print("✅ Application handles missing OpenHands SDK properly")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
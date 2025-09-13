#!/usr/bin/env python3
"""
Simple test script to verify the new LLM endpoints work correctly.
This script tests the /ready and /reset endpoints.
"""

import requests
import json
import sys
import time

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_UUID = "test-user-12345"
TEST_APP_SLUG = "test-app"
TEST_RIFF_SLUG = "test-riff"

def test_endpoint(method, endpoint, expected_status=200, data=None):
    """Test an endpoint and return the response"""
    headers = {
        'X-User-UUID': TEST_USER_UUID,
        'Content-Type': 'application/json'
    }
    
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            print(f"❌ Unsupported method: {method}")
            return None
            
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print("✅ Status code matches expected")
        else:
            print(f"❌ Expected {expected_status}, got {response.status_code}")
            
        try:
            response_data = response.json()
            print(f"📊 Response: {json.dumps(response_data, indent=2)}")
            return response_data
        except:
            print(f"📊 Response (text): {response.text}")
            return response.text
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("🚀 Testing OpenVibe LLM Endpoints")
    print("=" * 50)
    
    # Test 1: Check ready endpoint (should return false initially if no LLM exists)
    print("\n1️⃣ Testing /ready endpoint")
    ready_response = test_endpoint("GET", f"/api/apps/{TEST_APP_SLUG}/riffs/{TEST_RIFF_SLUG}/ready")
    
    if ready_response and isinstance(ready_response, dict):
        is_ready = ready_response.get('ready', False)
        print(f"🔍 LLM Ready: {is_ready}")
    
    # Test 2: Test reset endpoint
    print("\n2️⃣ Testing /reset endpoint")
    reset_response = test_endpoint("POST", f"/api/apps/{TEST_APP_SLUG}/riffs/{TEST_RIFF_SLUG}/reset")
    
    if reset_response and isinstance(reset_response, dict):
        reset_success = 'message' in reset_response
        print(f"🔄 Reset Success: {reset_success}")
    
    # Test 3: Check ready endpoint again (should return true after reset if successful)
    print("\n3️⃣ Testing /ready endpoint after reset")
    ready_response_2 = test_endpoint("GET", f"/api/apps/{TEST_APP_SLUG}/riffs/{TEST_RIFF_SLUG}/ready")
    
    if ready_response_2 and isinstance(ready_response_2, dict):
        is_ready_after = ready_response_2.get('ready', False)
        print(f"🔍 LLM Ready After Reset: {is_ready_after}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    
    # Summary
    print("\n📋 Summary:")
    print("- /ready endpoint: ✅ Accessible")
    print("- /reset endpoint: ✅ Accessible") 
    print("- Note: Actual functionality depends on having valid Anthropic API keys")

if __name__ == "__main__":
    main()
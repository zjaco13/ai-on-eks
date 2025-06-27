#!/usr/bin/env python3
"""
Test script for the Weather Agent REST API

This script tests the REST API endpoints including session management functionality.
"""

import requests
import json
import time
import sys

def test_rest_api(base_url: str = "http://localhost:3000"):
    """Test the Weather Agent REST API endpoints"""

    print(f"Testing Weather Agent REST API at {base_url}")
    print("=" * 60)

    # Create a session to maintain cookies
    session = requests.Session()

    # Test 1: Health check
    print("1. Testing health check endpoint...")
    try:
        response = session.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            result = response.json()
            print(f"   Service: {result.get('service')}")
            print(f"   Version: {result.get('version')}")
            print(f"   Features: {result.get('features')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

    print()

    # Test 2: First chat request (creates session)
    print("2. Testing first chat request (session creation)...")
    try:
        payload = {"query": "What's the weather forecast for Seattle?"}
        response = session.post(
            f"{base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ First chat request successful")
            result = response.json()
            session_id = result.get('session_id')
            print(f"   Session ID: {session_id}")
            print(f"   Query: {result.get('query')}")
            print(f"   Response: {result.get('response')[:100]}...")
            print(f"   Conversation length: {result.get('conversation_length')}")
        else:
            print(f"❌ First chat request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ First chat request error: {str(e)}")
        return False

    print()

    # Test 3: Second chat request (same session)
    print("3. Testing second chat request (session continuity)...")
    try:
        payload = {"query": "Any weather alerts?"}
        response = session.post(
            f"{base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ Second chat request successful")
            result = response.json()
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   Query: {result.get('query')}")
            print(f"   Response: {result.get('response')[:100]}...")
            print(f"   Conversation length: {result.get('conversation_length')}")
            print("   Note: Agent should know to check alerts for Seattle from previous context")
        else:
            print(f"❌ Second chat request failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Second chat request error: {str(e)}")

    print()

    # Test 4: Get conversation history
    print("4. Testing conversation history endpoint...")
    try:
        response = session.get(f"{base_url}/chat/history")
        if response.status_code == 200:
            print("✅ Conversation history retrieved successfully")
            result = response.json()
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   Total exchanges: {result.get('total_exchanges')}")
            history = result.get('conversation_history', [])
            for i, exchange in enumerate(history, 1):
                print(f"   {i}. Q: {exchange.get('query')}")
                print(f"      A: {exchange.get('response')[:80]}...")
        else:
            print(f"❌ Conversation history failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Conversation history error: {str(e)}")

    print()

    # Test 5: Session info
    print("5. Testing session info endpoint...")
    try:
        response = session.get(f"{base_url}/session/info")
        if response.status_code == 200:
            print("✅ Session info retrieved successfully")
            result = response.json()
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   Conversation length: {result.get('conversation_length')}")
            print(f"   Has agent: {result.get('has_agent')}")
            print(f"   Session data keys: {result.get('session_data_keys')}")
        else:
            print(f"❌ Session info failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Session info error: {str(e)}")

    print()

    # Test 6: Clear conversation history
    print("6. Testing clear conversation history...")
    try:
        response = session.post(f"{base_url}/chat/clear")
        if response.status_code == 200:
            print("✅ Conversation history cleared successfully")
            result = response.json()
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"❌ Clear conversation failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Clear conversation error: {str(e)}")

    print()

    # Test 7: Verify history is cleared
    print("7. Testing that history was cleared...")
    try:
        response = session.get(f"{base_url}/chat/history")
        if response.status_code == 200:
            result = response.json()
            total_exchanges = result.get('total_exchanges', 0)
            if total_exchanges == 0:
                print("✅ History successfully cleared")
                print(f"   Total exchanges: {total_exchanges}")
            else:
                print(f"❌ History not cleared: {total_exchanges} exchanges remain")
        else:
            print(f"❌ History verification failed: {response.status_code}")
    except Exception as e:
        print(f"❌ History verification error: {str(e)}")

    print()

    # Test 8: Invalid endpoint (404 test)
    print("8. Testing invalid endpoint (404)...")
    try:
        response = session.get(f"{base_url}/invalid/endpoint")
        if response.status_code == 404:
            print("✅ 404 handling works correctly")
            result = response.json()
            print(f"   Available endpoints: {result.get('available_endpoints')}")
        else:
            print(f"❌ 404 handling unexpected: {response.status_code}")
    except Exception as e:
        print(f"❌ 404 test error: {str(e)}")

    print()

    # Test 9: Invalid request body (400 test)
    print("9. Testing invalid request body (400)...")
    try:
        response = session.post(
            f"{base_url}/chat",
            json={"invalid": "data"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 400:
            print("✅ 400 handling works correctly")
            result = response.json()
            print(f"   Error: {result.get('error')}")
        else:
            print(f"❌ 400 handling unexpected: {response.status_code}")
    except Exception as e:
        print(f"❌ 400 test error: {str(e)}")

    print()
    print("=" * 60)
    print("REST API testing completed!")


def wait_for_server(base_url: str = "http://localhost:3000", timeout: int = 30):
    """Wait for the server to be ready"""
    print(f"Waiting for server at {base_url} to be ready...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        time.sleep(1)

    print(f"❌ Server not ready after {timeout} seconds")
    return False


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"

    if wait_for_server(base_url):
        test_rest_api(base_url)
    else:
        print("Server is not responding. Please start the REST API server first:")
        print("uv run rest-api")
        sys.exit(1)

#!/usr/bin/env python3
"""
Test script for the Weather Agent REST API

This script tests the REST API endpoints to ensure they work correctly.
"""

import requests
import json
import time
import sys

def test_rest_api(base_url: str = "http://localhost:3000"):
    """Test the Weather Agent REST API endpoints"""

    print(f"Testing Weather Agent REST API at {base_url}")
    print("=" * 50)

    # Test 1: Health check
    print("1. Testing health check endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

    print()

    # Test 2: Chat endpoint
    print("2. Testing chat endpoint...")
    try:
        payload = {"query": "What's the weather forecast for Seattle?"}
        response = requests.post(
            f"{base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ Chat request successful")
            result = response.json()
            print(f"   Query: {result.get('query')}")
            print(f"   Response: {result.get('response')[:100]}...")
        else:
            print(f"❌ Chat request failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Chat request error: {str(e)}")

    print()

    # Test 3: Invalid endpoint (404 test)
    print("3. Testing invalid endpoint (404)...")
    try:
        response = requests.get(f"{base_url}/invalid/endpoint")
        if response.status_code == 404:
            print("✅ 404 handling works correctly")
            result = response.json()
            print(f"   Available endpoints: {result.get('available_endpoints')}")
        else:
            print(f"❌ 404 handling unexpected: {response.status_code}")
    except Exception as e:
        print(f"❌ 404 test error: {str(e)}")

    print()

    # Test 4: Invalid request body (400 test)
    print("4. Testing invalid request body (400)...")
    try:
        response = requests.post(
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
    print("=" * 50)
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

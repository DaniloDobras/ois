#!/usr/bin/env python3
"""
Test script for authentication endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_authentication_flow():
    """Test the complete authentication flow"""
    
    print("🔐 Testing Authentication Flow")
    print("=" * 50)
    
    # Test 1: Access protected route without token
    print("\n1. Testing protected route without authentication...")
    try:
        response = requests.get(f"{BASE_URL}/auth/protected")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Get login URL
    print("\n2. Getting Keycloak login URL...")
    try:
        response = requests.get(f"{BASE_URL}/auth/login", allow_redirects=False)
        print(f"   Status: {response.status_code}")
        print(f"   Redirect URL: {response.headers.get('Location', 'No redirect')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Test business endpoints without auth
    print("\n3. Testing business endpoints without authentication...")
    endpoints = [
        "/order",
        "/bucket-actions", 
        "/admin-only",
        "/operator-tasks"
    ]
    
    for endpoint in endpoints:
        try:
            if endpoint == "/order":
                # POST request for order creation
                response = requests.post(f"{BASE_URL}{endpoint}", json={
                    "priority": "high",
                    "order_type": "loading",
                    "actions": []
                })
            else:
                # GET request for other endpoints
                response = requests.get(f"{BASE_URL}{endpoint}")
            
            print(f"   {endpoint}: {response.status_code}")
            if response.status_code != 200:
                print(f"      Response: {response.json()}")
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")
    
    print("\n" + "=" * 50)
    print("✅ Authentication flow test completed!")
    print("\nTo test with actual authentication:")
    print("1. Start Keycloak: docker run -p 8080:8080 -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:latest start-dev")
    print("2. Configure the client in Keycloak admin console")
    print("3. Visit: http://localhost:8000/auth/login")
    print("4. Use the returned token in Authorization header for API calls")

if __name__ == "__main__":
    test_authentication_flow()

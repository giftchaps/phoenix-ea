#!/usr/bin/env python3
"""
Simple test for the Phoenix EA server
"""

import requests
import time

def test_server():
    """Test the simple server"""
    print("Testing Phoenix EA Server...")
    
    # Wait a moment for server to start
    time.sleep(2)
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Health check - {data}")
            return True
        else:
            print(f"ERROR: Health check returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_server()
    if success:
        print("Server is working!")
    else:
        print("Server test failed")

#!/usr/bin/env python3
"""
Phoenix EA Test Client
Tests the test server endpoints
"""

import requests
import json
import time

def test_server():
    """Test the Phoenix EA test server"""
    base_url = "http://localhost:8000"
    
    print("Phoenix EA Test Client")
    print("=" * 30)
    
    # Test endpoints
    endpoints = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/api/v1/test", "Test endpoint"),
        ("/docs", "API documentation")
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        try:
            print(f"Testing {description}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                print(f"  SUCCESS: {response.status_code}")
                if endpoint != "/docs":  # Don't print HTML content
                    try:
                        data = response.json()
                        print(f"  Response: {json.dumps(data, indent=2)}")
                    except:
                        print(f"  Response: {response.text[:100]}...")
                results[endpoint] = True
            else:
                print(f"  WARNING: {response.status_code}")
                results[endpoint] = False
                
        except requests.exceptions.ConnectionError:
            print(f"  ERROR: Connection failed - server not running")
            results[endpoint] = False
        except Exception as e:
            print(f"  ERROR: {e}")
            results[endpoint] = False
    
    # Summary
    print("\n" + "=" * 30)
    print("TEST SUMMARY")
    print("=" * 30)
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for endpoint, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"{endpoint}: {status}")
    
    print(f"\nOverall: {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        print("SUCCESS: All tests passed! Server is working correctly.")
        return True
    else:
        print("WARNING: Some tests failed. Check server status.")
        return False

def main():
    """Main test function"""
    print("Make sure the test server is running:")
    print("python test_server.py")
    print("\nWaiting 2 seconds before testing...")
    time.sleep(2)
    
    return test_server()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

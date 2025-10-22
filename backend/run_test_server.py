#!/usr/bin/env python3
"""
Run Phoenix EA Test Server and Test It
Starts the test server and runs basic tests
"""

import subprocess
import time
import requests
import sys
import threading
import os

def start_server():
    """Start the test server in a separate process"""
    print("Starting Phoenix EA Test Server...")
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, "test_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        return process
    except Exception as e:
        print(f"Error starting server: {e}")
        return None

def test_endpoints():
    """Test the server endpoints"""
    print("Testing server endpoints...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        ("/", "Root"),
        ("/health", "Health"),
        ("/api/v1/test", "Test"),
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        try:
            print(f"Testing {name} endpoint...")
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                print(f"  SUCCESS: {response.status_code}")
                try:
                    data = response.json()
                    print(f"  Response: {data}")
                except (ValueError, Exception) as e:
                    print(f"  Response: {response.text[:100]}")
                results[endpoint] = True
            else:
                print(f"  WARNING: {response.status_code}")
                results[endpoint] = False
                
        except requests.exceptions.ConnectionError:
            print(f"  ERROR: Connection failed")
            results[endpoint] = False
        except Exception as e:
            print(f"  ERROR: {e}")
            results[endpoint] = False
    
    return results

def main():
    """Main function"""
    print("Phoenix EA Test Server Runner")
    print("=" * 40)
    
    # Start server
    server_process = start_server()
    if not server_process:
        print("Failed to start server")
        return False
    
    try:
        # Test endpoints
        results = test_endpoints()
        
        # Summary
        print("\n" + "=" * 40)
        print("TEST SUMMARY")
        print("=" * 40)
        
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
            print("WARNING: Some tests failed.")
            return False
            
    finally:
        # Clean up - stop server
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Phoenix EA Test Runner
Runs all tests and provides a comprehensive report
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_test_script(script_name, description):
    """Run a test script and return results"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    script_path = Path(__file__).parent / "tests" / script_name
    
    if not script_path.exists():
        print(f"❌ Test script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, timeout=60)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⏰ Test timed out: {script_name}")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def check_services():
    """Check if required services are running"""
    print("🔍 Checking required services...")
    
    services = {
        "PostgreSQL": ("localhost", 5432),
        "Backend API": ("localhost", 8000),
        "Frontend": ("localhost", 3000)
    }
    
    results = {}
    
    for service_name, (host, port) in services.items():
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ {service_name} is running on {host}:{port}")
                results[service_name] = True
            else:
                print(f"❌ {service_name} is not running on {host}:{port}")
                results[service_name] = False
        except Exception as e:
            print(f"❌ Error checking {service_name}: {e}")
            results[service_name] = False
    
    return results

def main():
    """Main test runner"""
    print("🚀 Phoenix EA Test Runner")
    print("=" * 60)
    
    # Check services first
    service_results = check_services()
    
    # Run tests
    test_results = {}
    
    # Basic startup test
    test_results["startup"] = run_test_script(
        "test_backend_startup.py",
        "Backend Startup Test"
    )
    
    # Full system test (only if backend is running)
    if service_results.get("Backend API", False):
        test_results["full_system"] = run_test_script(
            "test_full_system.py",
            "Full System Integration Test"
        )
    else:
        print("\n⚠️  Skipping full system test - Backend API not running")
        test_results["full_system"] = False
    
    # Print final summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)
    
    # Service status
    print("\n🔧 Service Status:")
    for service, status in service_results.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service}")
    
    # Test results
    print("\n🧪 Test Results:")
    for test_name, passed in test_results.items():
        status_icon = "✅" if passed else "❌"
        print(f"  {status_icon} {test_name.replace('_', ' ').title()}")
    
    # Overall status
    all_services_running = all(service_results.values())
    all_tests_passed = all(test_results.values())
    
    if all_services_running and all_tests_passed:
        print("\n🎉 All tests passed! System is fully operational.")
        return True
    elif all_services_running:
        print("\n⚠️  Services are running but some tests failed.")
        return False
    else:
        print("\n❌ Some services are not running. Please start them first:")
        print("   1. PostgreSQL: docker start phoenix-postgres")
        print("   2. Backend: python start_backend.py")
        print("   3. Frontend: cd frontend && npm run dev")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

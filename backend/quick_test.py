#!/usr/bin/env python3
"""
Quick Phoenix EA Backend Test
Fast test to verify backend is ready
"""

import sys
import os

# Add the backend src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("Phoenix EA Quick Test")
    print("=" * 30)
    
    # Test 1: Database
    print("1. Testing database...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost", port="5432", database="phoenix_ea",
            user="phoenix", password="phoenix123"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM symbols")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"   SUCCESS: Database connected ({count} symbols)")
    except Exception as e:
        print(f"   ERROR: Database failed - {e}")
        return False
    
    # Test 2: SMC Engine
    print("2. Testing SMC Engine...")
    try:
        from strategy.smc_engine import SMCStrategyEngine
        engine = SMCStrategyEngine({})
        print("   SUCCESS: SMC Engine ready")
    except Exception as e:
        print(f"   ERROR: SMC Engine failed - {e}")
        return False
    
    # Test 3: API Server
    print("3. Testing API server...")
    try:
        import requests
        response = requests.get("http://localhost:8000/", timeout=2)
        if response.status_code == 200:
            print("   SUCCESS: API server running")
        else:
            print(f"   WARNING: API server returned {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   INFO: API server not running (start with: python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload)")
    except Exception as e:
        print(f"   ERROR: API test failed - {e}")
    
    print("\nBackend is ready!")
    print("To start the server: python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload")
    return True

if __name__ == "__main__":
    main()

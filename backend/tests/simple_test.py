#!/usr/bin/env python3
"""
Simple Phoenix EA Backend Test
Basic functionality test without emojis for Windows compatibility
"""

import sys
import os
import requests
import json

# Add the backend src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_database():
    """Test database connection"""
    print("Testing database connection...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="phoenix_ea",
            user="phoenix",
            password="phoenix123"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM symbols")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"SUCCESS: Database connected - {count} symbols found")
        return True
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        return False

def test_imports():
    """Test required imports"""
    print("Testing required imports...")
    modules = [
        "fastapi", "uvicorn", "pandas", "numpy", 
        "sqlalchemy", "psycopg2", "redis", "aiohttp"
    ]
    
    success_count = 0
    for module in modules:
        try:
            __import__(module)
            print(f"SUCCESS: {module} imported")
            success_count += 1
        except ImportError as e:
            print(f"ERROR: {module} import failed: {e}")
    
    print(f"Import test: {success_count}/{len(modules)} modules available")
    return success_count > 0

def test_api():
    """Test API endpoints"""
    print("Testing API endpoints...")
    base_url = "http://localhost:8000"
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("SUCCESS: Root endpoint working")
            return True
        else:
            print(f"WARNING: Root endpoint returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("ERROR: API server not running")
        return False
    except Exception as e:
        print(f"ERROR: API test failed: {e}")
        return False

def test_smc_engine():
    """Test SMC engine"""
    print("Testing SMC Strategy Engine...")
    try:
        from strategy.smc_engine import SMCStrategyEngine
        
        config = {
            "swing_lookback": 2,
            "sweep_min_pts": 5,
            "reentry_max_candles": 3,
            "ob_lookback": 15,
            "ob_volume_pctl": 60,
            "zone_lookback": 50,
            "min_impulse_atr": 2.0,
            "eqh_eql_tolerance_pts": 5,
            "ob_required": True,
            "premium_discount_filter": True,
            "min_confidence": 0.65,
            "atr_mult": 2.0,
            "sl_buffer_pts": 2,
            "tick_value": 1.0,
            "pip_size": 0.0001,
            "min_lot": 0.01,
            "max_lot": 10.0
        }
        
        engine = SMCStrategyEngine(config)
        print("SUCCESS: SMC Strategy Engine initialized")
        return True
    except Exception as e:
        print(f"ERROR: SMC Engine test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Phoenix EA Backend Test")
    print("=" * 40)
    
    results = {
        "database": test_database(),
        "imports": test_imports(),
        "api": test_api(),
        "smc_engine": test_smc_engine()
    }
    
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name.upper()}: {status}")
    
    # Overall result
    critical_tests = [results["database"], results["imports"], results["smc_engine"]]
    overall_success = all(critical_tests)
    
    if overall_success:
        print("\nRESULT: Backend is ready!")
        if not results["api"]:
            print("NOTE: API server not running - start with: python start_backend.py")
    else:
        print("\nRESULT: Some critical tests failed")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

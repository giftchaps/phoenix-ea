#!/usr/bin/env python3
"""
Phoenix EA Backend Startup Test
Tests basic backend functionality and API endpoints
"""

import asyncio
import sys
import os
import requests
import json
from datetime import datetime

# Add the backend src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_database_connection():
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
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        print("SUCCESS: Database connection successful")
        return True
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("🔍 Testing API endpoints...")
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/",
        "/docs",
        "/api/v1/status",
        "/api/v1/signals",
        "/api/v1/backtests",
        "/api/v1/risk"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            results[endpoint] = {
                "status_code": response.status_code,
                "success": response.status_code < 400
            }
            if response.status_code < 400:
                print(f"✅ {endpoint} - Status: {response.status_code}")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Connection failed (server not running)")
            results[endpoint] = {"success": False, "error": "Connection failed"}
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            results[endpoint] = {"success": False, "error": str(e)}
    
    return results

def test_websocket_connection():
    """Test WebSocket connection"""
    print("🔍 Testing WebSocket connection...")
    try:
        import websockets
        import asyncio
        
        async def test_ws():
            try:
                async with websockets.connect("ws://localhost:8000/ws") as websocket:
                    await websocket.send(json.dumps({"type": "ping"}))
                    response = await websocket.recv()
                    print("✅ WebSocket connection successful")
                    return True
            except Exception as e:
                print(f"❌ WebSocket connection failed: {e}")
                return False
        
        return asyncio.run(test_ws())
    except ImportError:
        print("⚠️  websockets library not available, skipping WebSocket test")
        return None
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

def test_smc_engine():
    """Test SMC Strategy Engine"""
    print("🔍 Testing SMC Strategy Engine...")
    try:
        from strategy.smc_engine import SMCStrategyEngine
        
        # Test configuration
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
        print("✅ SMC Strategy Engine initialized successfully")
        return True
    except Exception as e:
        print(f"❌ SMC Strategy Engine test failed: {e}")
        return False

def test_imports():
    """Test all module imports"""
    print("🔍 Testing module imports...")
    
    modules_to_test = [
        "fastapi",
        "uvicorn",
        "pandas",
        "numpy",
        "sqlalchemy",
        "psycopg2",
        "redis",
        "aiohttp",
        "websockets"
    ]
    
    results = {}
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module} - Import successful")
            results[module] = True
        except ImportError as e:
            print(f"❌ {module} - Import failed: {e}")
            results[module] = False
    
    return results

def main():
    """Run all tests"""
    print("Phoenix EA Backend Startup Test")
    print("=" * 50)
    
    # Test results
    results = {
        "database": False,
        "api": {},
        "websocket": None,
        "smc_engine": False,
        "imports": {}
    }
    
    # Run tests
    results["imports"] = test_imports()
    results["database"] = test_database_connection()
    results["smc_engine"] = test_smc_engine()
    results["api"] = test_api_endpoints()
    results["websocket"] = test_websocket_connection()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    # Database
    if results["database"]:
        print("✅ Database: Connected")
    else:
        print("❌ Database: Failed")
    
    # Imports
    import_success = sum(results["imports"].values())
    import_total = len(results["imports"])
    print(f"📦 Imports: {import_success}/{import_total} successful")
    
    # SMC Engine
    if results["smc_engine"]:
        print("✅ SMC Engine: Working")
    else:
        print("❌ SMC Engine: Failed")
    
    # API Endpoints
    api_success = sum(1 for r in results["api"].values() if r.get("success", False))
    api_total = len(results["api"])
    print(f"🌐 API Endpoints: {api_success}/{api_total} working")
    
    # WebSocket
    if results["websocket"] is True:
        print("✅ WebSocket: Connected")
    elif results["websocket"] is False:
        print("❌ WebSocket: Failed")
    else:
        print("⚠️  WebSocket: Skipped")
    
    # Overall status
    critical_tests = [
        results["database"],
        results["smc_engine"],
        import_success > 0
    ]
    
    if all(critical_tests):
        print("\n🎉 Backend is ready for startup!")
        return True
    else:
        print("\n⚠️  Some critical components failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

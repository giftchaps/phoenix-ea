#!/usr/bin/env python3
"""
Phoenix EA Full System Test
Tests the complete system integration including frontend-backend communication
"""

import asyncio
import sys
import os
import requests
import json
import time
import websockets
from datetime import datetime

# Add the backend src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

class SystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        self.frontend_url = "http://localhost:3000"
        self.results = {}
    
    def test_database_connection(self):
        """Test database connection and basic queries"""
        print("🔍 Testing database connection...")
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
            
            # Test basic queries
            cursor.execute("SELECT COUNT(*) FROM symbols")
            symbol_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM signals")
            signal_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"✅ Database connected - Symbols: {symbol_count}, Signals: {signal_count}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def test_api_health(self):
        """Test API health endpoints"""
        print("🔍 Testing API health...")
        try:
            # Test root endpoint
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print("✅ Root endpoint working")
            else:
                print(f"⚠️  Root endpoint returned {response.status_code}")
            
            # Test status endpoint
            response = requests.get(f"{self.base_url}/api/v1/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status endpoint working - {data}")
            else:
                print(f"⚠️  Status endpoint returned {response.status_code}")
            
            return True
        except requests.exceptions.ConnectionError:
            print("❌ API server not running")
            return False
        except Exception as e:
            print(f"❌ API health test failed: {e}")
            return False
    
    def test_smc_engine_integration(self):
        """Test SMC engine integration"""
        print("🔍 Testing SMC engine integration...")
        try:
            from strategy.smc_engine import SMCStrategyEngine
            import pandas as pd
            import numpy as np
            
            # Create sample data
            dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
            sample_data = pd.DataFrame({
                'time': dates,
                'open': np.random.uniform(2000, 2100, 100),
                'high': np.random.uniform(2000, 2100, 100),
                'low': np.random.uniform(2000, 2100, 100),
                'close': np.random.uniform(2000, 2100, 100),
                'volume': np.random.uniform(1000, 10000, 100),
                'atr': np.random.uniform(5, 15, 100)
            })
            
            # Initialize engine
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
            
            # Test signal generation
            signal = engine.generate_signal(
                symbol="XAUUSD",
                timeframe="M15",
                bars=sample_data,
                h4_bias="bullish",
                h1_bias="bullish",
                account_balance=10000,
                risk_pct=1.0
            )
            
            if signal:
                print(f"✅ SMC engine generated signal: {signal.side} @ {signal.entry}")
            else:
                print("⚠️  SMC engine did not generate signal (expected with random data)")
            
            return True
        except Exception as e:
            print(f"❌ SMC engine integration failed: {e}")
            return False
    
    def test_websocket_connection(self):
        """Test WebSocket connection"""
        print("🔍 Testing WebSocket connection...")
        try:
            async def test_ws():
                try:
                    async with websockets.connect(self.ws_url) as websocket:
                        # Send test message
                        test_message = {
                            "type": "test",
                            "data": "Hello WebSocket",
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(test_message))
                        
                        # Wait for response
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        data = json.loads(response)
                        print(f"✅ WebSocket connection successful - Response: {data}")
                        return True
                except Exception as e:
                    print(f"❌ WebSocket connection failed: {e}")
                    return False
            
            return asyncio.run(test_ws())
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            return False
    
    def test_frontend_connection(self):
        """Test frontend connection"""
        print("🔍 Testing frontend connection...")
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                print("✅ Frontend is accessible")
                return True
            else:
                print(f"⚠️  Frontend returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Frontend not running")
            return False
        except Exception as e:
            print(f"❌ Frontend connection test failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test all API endpoints"""
        print("🔍 Testing API endpoints...")
        endpoints = [
            ("/", "Root"),
            ("/docs", "API Documentation"),
            ("/api/v1/status", "System Status"),
            ("/api/v1/signals", "Signals"),
            ("/api/v1/backtests", "Backtests"),
            ("/api/v1/risk", "Risk Metrics"),
            ("/api/v1/symbols", "Symbols")
        ]
        
        results = {}
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                success = response.status_code < 400
                results[endpoint] = {
                    "success": success,
                    "status_code": response.status_code,
                    "name": name
                }
                
                if success:
                    print(f"✅ {name} ({endpoint}) - Status: {response.status_code}")
                else:
                    print(f"⚠️  {name} ({endpoint}) - Status: {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                print(f"❌ {name} ({endpoint}) - Connection failed")
                results[endpoint] = {"success": False, "error": "Connection failed"}
            except Exception as e:
                print(f"❌ {name} ({endpoint}) - Error: {e}")
                results[endpoint] = {"success": False, "error": str(e)}
        
        return results
    
    def test_cors_headers(self):
        """Test CORS headers for frontend integration"""
        print("🔍 Testing CORS headers...")
        try:
            response = requests.options(f"{self.base_url}/api/v1/status", 
                                      headers={"Origin": "http://localhost:3000"})
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            if cors_headers["Access-Control-Allow-Origin"]:
                print("✅ CORS headers configured")
                return True
            else:
                print("⚠️  CORS headers not found")
                return False
        except Exception as e:
            print(f"❌ CORS test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all system tests"""
        print("🚀 Phoenix EA Full System Test")
        print("=" * 60)
        
        # Run tests
        self.results["database"] = self.test_database_connection()
        self.results["api_health"] = self.test_api_health()
        self.results["smc_engine"] = self.test_smc_engine_integration()
        self.results["websocket"] = self.test_websocket_connection()
        self.results["frontend"] = self.test_frontend_connection()
        self.results["api_endpoints"] = self.test_api_endpoints()
        self.results["cors"] = self.test_cors_headers()
        
        # Print summary
        self.print_summary()
        
        return self.results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        # Database
        if self.results.get("database"):
            print("✅ Database: Connected and working")
        else:
            print("❌ Database: Failed")
        
        # API Health
        if self.results.get("api_health"):
            print("✅ API Health: Server responding")
        else:
            print("❌ API Health: Server not responding")
        
        # SMC Engine
        if self.results.get("smc_engine"):
            print("✅ SMC Engine: Working")
        else:
            print("❌ SMC Engine: Failed")
        
        # WebSocket
        if self.results.get("websocket"):
            print("✅ WebSocket: Connected")
        else:
            print("❌ WebSocket: Failed")
        
        # Frontend
        if self.results.get("frontend"):
            print("✅ Frontend: Accessible")
        else:
            print("❌ Frontend: Not accessible")
        
        # API Endpoints
        if "api_endpoints" in self.results:
            api_success = sum(1 for r in self.results["api_endpoints"].values() if r.get("success", False))
            api_total = len(self.results["api_endpoints"])
            print(f"🌐 API Endpoints: {api_success}/{api_total} working")
        
        # CORS
        if self.results.get("cors"):
            print("✅ CORS: Configured")
        else:
            print("⚠️  CORS: Not configured")
        
        # Overall status
        critical_tests = [
            self.results.get("database", False),
            self.results.get("api_health", False),
            self.results.get("smc_engine", False)
        ]
        
        if all(critical_tests):
            print("\n🎉 System is fully operational!")
            print("🌐 Backend: http://localhost:8000")
            print("📚 API Docs: http://localhost:8000/docs")
            print("🔌 WebSocket: ws://localhost:8000/ws")
            print("🎨 Frontend: http://localhost:3000")
        else:
            print("\n⚠️  Some critical components failed. Check the errors above.")
            print("💡 Make sure to:")
            print("   1. Start PostgreSQL: docker start phoenix-postgres")
            print("   2. Start Backend: python start_backend.py")
            print("   3. Start Frontend: cd frontend && npm run dev")

def main():
    """Main test function"""
    tester = SystemTester()
    results = tester.run_all_tests()
    
    # Return success if critical components are working
    critical_success = all([
        results.get("database", False),
        results.get("api_health", False),
        results.get("smc_engine", False)
    ])
    
    return critical_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

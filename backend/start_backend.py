#!/usr/bin/env python3
"""
Phoenix EA Backend Startup Script
Starts the FastAPI server with proper configuration
"""

import os
import sys
import subprocess
import time
import signal
import psutil
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_port_available(port):
    """Check if a port is available"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return False
    return True

def kill_process_on_port(port):
    """Kill any process running on the specified port"""
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.info['connections'] or []:
                if conn.laddr.port == port:
                    print(f"🔪 Killing process {proc.info['pid']} on port {port}")
                    proc.kill()
                    time.sleep(1)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def check_database():
    """Check if PostgreSQL is running"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "phoenix_ea"),
            user=os.getenv("DB_USER", "phoenix"),
            password=os.getenv("DB_PASSWORD", "phoenix123")
        )
        conn.close()
        return True
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        return False

def start_database():
    """Start PostgreSQL database if not running"""
    print("🔍 Checking database connection...")
    if check_database():
        print("✅ Database is already running")
        return True
    
    print("🚀 Starting PostgreSQL database...")
    try:
        # Try to start the Docker container
        result = subprocess.run([
            "docker", "start", "phoenix-postgres"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PostgreSQL container started")
            time.sleep(3)  # Wait for database to be ready
            return check_database()
        else:
            print("❌ Failed to start PostgreSQL container")
            print("Please ensure Docker is running and the phoenix-postgres container exists")
            return False
    except FileNotFoundError:
        print("❌ Docker not found. Please start PostgreSQL manually")
        return False

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting Phoenix EA Backend...")
    
    # Check if port 8000 is available
    if not check_port_available(8000):
        print("⚠️  Port 8000 is already in use")
        response = input("Do you want to kill the process on port 8000? (y/n): ")
        if response.lower() == 'y':
            kill_process_on_port(8000)
        else:
            print("❌ Cannot start backend on port 8000")
            return False
    
    # Set environment variables
    os.environ["PYTHONPATH"] = str(Path(__file__).parent / "src")
    
    # Start the server
    try:
        print("🌐 Starting FastAPI server on http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔌 WebSocket: ws://localhost:8000/ws")
        print("⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Run uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🚀 Phoenix EA Backend Startup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src/api/main.py").exists():
        print("❌ Please run this script from the backend directory")
        return False
    
    # Start database
    if not start_database():
        print("❌ Database startup failed")
        return False
    
    # Start backend
    if not start_backend():
        print("❌ Backend startup failed")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

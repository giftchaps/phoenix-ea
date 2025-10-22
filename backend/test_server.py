#!/usr/bin/env python3
"""
Phoenix EA Test Server
Simple FastAPI server to test basic functionality
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Phoenix EA Test")

@app.get("/health")
def health_check():
    return {"status": "healthy", "app": "Phoenix EA"}

@app.get("/api/v1/test")
def test_endpoint():
    return {"message": "Backend is working!"}

@app.get("/")
def root():
    return {
        "message": "Phoenix EA Test Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "test": "/api/v1/test",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Phoenix EA Test Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🧪 Test Endpoint: http://localhost:8000/api/v1/test")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

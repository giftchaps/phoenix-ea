#!/usr/bin/env python3
"""
Simple Phoenix EA Test Server
Minimal FastAPI server for testing
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Phoenix EA Test")

@app.get("/")
def root():
    return {"message": "Phoenix EA Test Server", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy", "app": "Phoenix EA"}

@app.get("/test")
def test():
    return {"message": "Backend is working!"}

if __name__ == "__main__":
    print("Starting Phoenix EA Test Server...")
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

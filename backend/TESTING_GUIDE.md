# Phoenix EA Backend Testing Guide

## Overview
This guide explains how to test the Phoenix EA backend system and verify all components are working correctly.

## Prerequisites
- PostgreSQL database running (Docker container: `phoenix-postgres`)
- Python virtual environment activated
- All dependencies installed

## Test Scripts Created

### 1. Simple Test (`tests/simple_test.py`)
**Purpose**: Basic functionality test without emojis for Windows compatibility
**Tests**:
- Database connection
- Required imports
- API endpoints (if server running)
- SMC Strategy Engine

**Usage**:
```bash
cd backend
.\venv\Scripts\activate
python tests\simple_test.py
```

### 2. Backend Startup Test (`tests/test_backend_startup.py`)
**Purpose**: Comprehensive startup test with detailed reporting
**Tests**:
- Database connection and queries
- All API endpoints
- WebSocket connection
- SMC engine integration
- Module imports

**Usage**:
```bash
cd backend
.\venv\Scripts\activate
python tests\test_backend_startup.py
```

### 3. Full System Test (`tests/test_full_system.py`)
**Purpose**: Complete system integration test
**Tests**:
- Database operations
- API health and endpoints
- SMC engine with sample data
- WebSocket communication
- Frontend connectivity
- CORS configuration

**Usage**:
```bash
cd backend
.\venv\Scripts\activate
python tests\test_full_system.py
```

### 4. Test Runner (`run_tests.py`)
**Purpose**: Runs all tests and provides comprehensive report
**Features**:
- Checks if services are running
- Runs startup and system tests
- Provides detailed summary

**Usage**:
```bash
cd backend
.\venv\Scripts\activate
python run_tests.py
```

### 5. Windows Batch Script (`test_backend.bat`)
**Purpose**: Easy testing on Windows
**Usage**: Double-click the file or run from command prompt

## Manual Testing Steps

### 1. Test Database Connection
```bash
cd backend
.\venv\Scripts\activate
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', port='5432', database='phoenix_ea', user='phoenix', password='phoenix123'); print('Database connected successfully')"
```

### 2. Test SMC Engine
```bash
cd backend
.\venv\Scripts\activate
python -c "from src.strategy.smc_engine import SMCStrategyEngine; engine = SMCStrategyEngine({}); print('SMC Engine initialized successfully')"
```

### 3. Start Backend Server
```bash
cd backend
.\venv\Scripts\activate
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test API Endpoints
Once server is running, test these URLs in browser:
- http://localhost:8000/ (Root endpoint)
- http://localhost:8000/docs (API documentation)
- http://localhost:8000/api/v1/status (System status)

### 5. Test WebSocket
```bash
# Use a WebSocket client or browser console:
# ws://localhost:8000/ws
```

## Expected Test Results

### ✅ Successful Tests Should Show:
- Database: Connected with 4 symbols found
- Imports: All 8 modules imported successfully
- SMC Engine: Initialized successfully
- API: Server responding (when running)

### ❌ Common Issues and Solutions:

1. **Database Connection Failed**
   - Ensure PostgreSQL container is running: `docker start phoenix-postgres`
   - Check database credentials in connection string

2. **Import Errors**
   - Activate virtual environment: `.\venv\Scripts\activate`
   - Install missing packages: `pip install <package_name>`

3. **API Server Not Running**
   - Start server: `python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload`
   - Check if port 8000 is available

4. **WebSocket Connection Failed**
   - Ensure server is running
   - Check WebSocket endpoint: `ws://localhost:8000/ws`

## Test Results Interpretation

### Critical Tests (Must Pass):
- Database connection
- Required imports
- SMC Strategy Engine

### Optional Tests:
- API endpoints (requires server running)
- WebSocket connection (requires server running)
- Frontend connectivity (requires frontend running)

## Troubleshooting

### Windows-Specific Issues:
- Use `.\venv\Scripts\activate` instead of `source venv/bin/activate`
- PowerShell doesn't support `&&` operator - run commands separately
- Unicode emojis may not display correctly in Windows console

### Common Commands:
```bash
# Check if port is in use
netstat -an | findstr :8000

# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Check Docker containers
docker ps
docker start phoenix-postgres
```

## Next Steps

1. **Run Simple Test**: `python tests\simple_test.py`
2. **Start Backend**: `python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload`
3. **Test API**: Visit http://localhost:8000/docs
4. **Run Full Test**: `python tests\test_full_system.py`

## Success Criteria

The backend is ready when:
- ✅ Database connection successful
- ✅ All imports working
- ✅ SMC Engine initialized
- ✅ API server running on port 8000
- ✅ API documentation accessible at /docs
- ✅ WebSocket endpoint responding

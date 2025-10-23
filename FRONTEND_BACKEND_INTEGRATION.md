# Phoenix EA - Frontend-Backend Integration Guide

Complete guide for integrating and running the Phoenix EA frontend and backend together.

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Quick Start](#quick-start)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [API Endpoints](#api-endpoints)
6. [Real-Time Updates](#real-time-updates)
7. [Authentication](#authentication)
8. [Error Handling](#error-handling)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## 🏗️ System Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│                 │         │                  │         │                 │
│  Next.js        │◄────────┤  FastAPI         │◄────────┤  PostgreSQL     │
│  Frontend       │  HTTP   │  Backend         │         │  Database       │
│  (Port 3000)    │  REST   │  (Port 8000)     │         │                 │
│                 │◄────────┤                  │         │                 │
│                 │  WS     │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                    │
                                    │
                            ┌───────┴────────┐
                            │                │
                      ┌─────▼─────┐    ┌────▼─────┐
                      │  Deriv    │    │   MT5    │
                      │  API      │    │  Broker  │
                      └───────────┘    └──────────┘
```

### Technology Stack

**Frontend:**
- Next.js 14 (React 19)
- TypeScript
- Tailwind CSS 4
- WebSocket client

**Backend:**
- Python 3.10+
- FastAPI
- SQLAlchemy
- PostgreSQL
- WebSocket server

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (optional, can use SQLite)
- Git

### Step 1: Clone and Setup Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start backend server
python -m uvicorn src.api.main:app --reload --port 8000
```

### Step 2: Setup Frontend

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Ensure NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Start frontend
npm run dev
```

### Step 3: Access Dashboard

Open browser: **http://localhost:3000**

---

## 🔧 Backend Setup

### Environment Variables

Create `/backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/phoenix_ea
# Or for SQLite: sqlite:///./phoenix_ea.db

# API Security
API_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Trading Platforms
DERIV_APP_ID=your-deriv-app-id
DERIV_API_TOKEN=your-deriv-token
MT5_LOGIN=your-mt5-login
MT5_PASSWORD=your-mt5-password
MT5_SERVER=your-mt5-server

# Notifications
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

# Risk Management
MAX_RISK_PER_TRADE=1.0
MAX_DAILY_RISK=3.0
DAILY_STOP_R=-10.0
MAX_CONCURRENT_R=2.0
```

### Start Backend

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Run with uvicorn
python -m uvicorn src.api.main:app --reload --port 8000 --host 0.0.0.0

# Or with gunicorn for production
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Verify Backend

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2025-10-23T..."}
```

---

## 🎨 Frontend Setup

### Environment Variables

Create `/frontend/.env.local`:

```bash
# Backend API URL (required)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# WebSocket URL (required)
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Environment (optional)
NEXT_PUBLIC_ENV=development
```

### Important Notes

1. **CORS Configuration**: Backend must allow frontend origin
   - Default allows: `http://localhost:3000`
   - Configure in `backend/src/api/main.py`

2. **API URL Format**: Must include `/api/v1` prefix
   - Correct: `http://localhost:8000/api/v1`
   - Incorrect: `http://localhost:8000`

3. **WebSocket URL**: No `/api/v1` prefix
   - Correct: `ws://localhost:8000/ws`
   - Incorrect: `ws://localhost:8000/api/v1/ws`

### Start Frontend

```bash
cd frontend

# Development mode
npm run dev

# Production build
npm run build
npm run start
```

### Verify Frontend

1. Open http://localhost:3000
2. Check connection status in top-right (should show "Connected")
3. Verify no errors in browser console

---

## 📡 API Endpoints

### Public Endpoints

#### Health Check
```http
GET /health
```
Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T12:00:00"
}
```

### Protected Endpoints

All require `Authorization: Bearer <token>` header.

#### Get Active Signals
```http
GET /api/v1/signals/active
```
Response:
```json
[
  {
    "id": "uuid",
    "symbol": "XAUUSD",
    "timeframe": "M15",
    "side": "LONG",
    "entry": 2650.50,
    "stop_loss": 2645.00,
    "take_profit_1": 2660.00,
    "take_profit_2": 2670.00,
    "risk_reward": 2.0,
    "confidence": 0.85,
    "status": "active",
    ...
  }
]
```

#### Get Signal History
```http
GET /api/v1/signals/history
```

#### Get Statistics
```http
GET /api/v1/stats
```
Response:
```json
{
  "today_signals": 5,
  "active_positions": 2,
  "total_pnl_r": 12.5,
  "win_rate": 0.64,
  "profit_factor": 1.85,
  "total_trades": 150,
  "winning_trades": 96,
  "losing_trades": 54
}
```

#### Get Risk Metrics
```http
GET /api/v1/risk/metrics
```
Response:
```json
{
  "daily_pnl": 250.50,
  "daily_pnl_r": 2.5,
  "trade_count": 3,
  "active_trades_count": 2,
  "active_risk_r": 1.5,
  "max_risk_per_trade": 1.0,
  "max_daily_risk": 3.0,
  "daily_stop_r": -10.0,
  "max_concurrent_r": 2.0,
  "drawdown_threshold_r": -6.0,
  "risk_utilization": 0.75,
  "risk_reduction_active": false,
  "can_trade": true
}
```

#### Generate Signal
```http
POST /api/v1/signals/generate
Content-Type: application/json

{
  "symbol": "XAUUSD",
  "timeframe": "M15",
  "force": false
}
```

#### Execute Signal
```http
POST /api/v1/signals/{signal_id}/execute
Content-Type: application/json

{
  "signal_id": "uuid",
  "auto_manage": true
}
```

#### Close Position
```http
POST /api/v1/signals/{signal_id}/close
Content-Type: application/json

{
  "signal_id": "uuid",
  "partial_pct": 1.0
}
```

---

## 🔄 Real-Time Updates

### WebSocket Connection

Frontend automatically connects to WebSocket server for real-time updates.

**Connection URL**: `ws://localhost:8000/ws`

### Message Types

**1. Signal Update**
```json
{
  "type": "signal_update",
  "data": {
    "signal_id": "uuid",
    "status": "active",
    "action": "created"
  }
}
```

**2. Risk Update**
```json
{
  "type": "risk_update",
  "data": {
    "can_trade": true,
    "daily_pnl_r": 2.5,
    "active_risk_r": 1.5
  }
}
```

**3. Stats Update**
```json
{
  "type": "stats_update",
  "data": {
    "total_pnl_r": 12.5,
    "win_rate": 0.64
  }
}
```

### Frontend Implementation

```typescript
import { wsClient } from './lib/api';

// Connect to WebSocket
wsClient.connect(
  (data) => {
    console.log('Message received:', data);

    if (data.type === 'signal_update') {
      // Refresh signals
      loadActiveSignals();
    }
  },
  (error) => {
    console.error('WebSocket error:', error);
  }
);

// Disconnect on cleanup
wsClient.disconnect();
```

---

## 🔐 Authentication

### Token-Based Authentication

The API uses JWT tokens for authentication.

#### Get Token (Not implemented yet - placeholder)

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

#### Use Token in Frontend

```typescript
import { apiClient } from './lib/api';

// Set token
apiClient.setAuthToken('your-jwt-token');

// All subsequent requests include token
const signals = await apiClient.getActiveSignals();
```

### Development Mode

Currently, authentication can be bypassed in development by modifying `verify_token` function in `backend/src/api/main.py`.

---

## ⚠️ Error Handling

### Frontend Error Handling

The API client automatically handles:
- Network errors (retry up to 3 times)
- 5xx server errors (retry with exponential backoff)
- 4xx client errors (throw immediately)

```typescript
import { apiClient, ApiError } from './lib/api';

try {
  const signals = await apiClient.getActiveSignals();
} catch (error) {
  if (error instanceof ApiError) {
    console.error(`API Error ${error.status}: ${error.detail}`);
  } else {
    console.error('Network error:', error);
  }
}
```

### Backend Error Responses

**400 Bad Request**
```json
{
  "detail": "Invalid request parameters"
}
```

**403 Forbidden**
```json
{
  "detail": "Market filters blocked signal: Outside session windows"
}
```

**404 Not Found**
```json
{
  "detail": "Signal not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

---

## 🚀 Deployment

### Production Backend Deployment

1. **Set production environment variables**
2. **Use PostgreSQL** (not SQLite)
3. **Use gunicorn** with multiple workers
4. **Enable HTTPS** with SSL certificate
5. **Configure CORS** for production frontend URL

```bash
# Start with gunicorn
gunicorn src.api.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/phoenix-ea/access.log \
  --error-logfile /var/log/phoenix-ea/error.log
```

### Production Frontend Deployment

1. **Build frontend**
   ```bash
   npm run build
   ```

2. **Update environment variables**
   ```bash
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
   NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com/ws
   NEXT_PUBLIC_ENV=production
   ```

3. **Deploy to Vercel** (recommended)
   ```bash
   vercel --prod
   ```

   Or deploy to custom server:
   ```bash
   npm run start
   ```

### CORS Configuration

Update `backend/src/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",              # Development
        "https://yourdomain.com",             # Production
        "https://www.yourdomain.com"          # Production www
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔧 Troubleshooting

### Problem: "Backend Connection Failed"

**Symptoms**: Red "Disconnected" status in dashboard header

**Solutions**:
1. Verify backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check frontend `.env.local`:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

3. Check CORS configuration allows `http://localhost:3000`

4. Check backend logs for errors

### Problem: "No data displayed"

**Solutions**:
1. Check browser console for API errors
2. Verify authentication token is set (if required)
3. Check backend database has data:
   ```bash
   python backend/test_priority1_fixes.py
   ```

### Problem: "WebSocket not connecting"

**Solutions**:
1. Verify WebSocket URL in `.env.local`:
   ```bash
   NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
   ```

2. Check backend supports WebSocket connections
3. Check firewall allows WebSocket

### Problem: "CORS errors in console"

**Solutions**:
1. Verify CORS configuration in `backend/src/api/main.py`
2. Ensure frontend origin is in `allow_origins` list
3. Restart backend after CORS changes

### Problem: "Build errors"

**Solutions**:
```bash
# Frontend
cd frontend
rm -rf .next node_modules
npm install
npm run build

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

---

## 📊 Testing Integration

### Test Backend Health

```bash
curl http://localhost:8000/health
```

### Test Frontend API Connection

Open browser console on http://localhost:3000 and check for:
- ✅ No CORS errors
- ✅ "Connected" status in header
- ✅ Data loading in dashboard

### Test WebSocket Connection

In browser console:
```javascript
// Should see WebSocket messages
console.log('Check Network tab for WS connection')
```

---

## 📈 Performance Optimization

### Backend
- Use connection pooling for database
- Enable Redis caching for frequently accessed data
- Use async database queries
- Enable gzip compression

### Frontend
- Enable Next.js caching
- Use React.memo for expensive components
- Implement virtual scrolling for long lists
- Optimize images with Next.js Image component

---

## 🆘 Support

### Logs

**Backend logs**:
```bash
tail -f backend/logs/app.log
```

**Frontend logs**:
- Browser console (F12)
- Terminal running `npm run dev`

### Common Issues

1. **Port already in use**: Change port in startup command
2. **Database connection failed**: Check DATABASE_URL
3. **Module not found**: Run `pip install -r requirements.txt`
4. **TypeScript errors**: Run `npm install` in frontend

---

**Last Updated**: October 23, 2025
**Version**: 2.0.0

# Phoenix EA Frontend

Modern, responsive, and elegant web dashboard for the Phoenix EA trading system built with Next.js 14, React 19, and TypeScript.

## 🚀 Features

### Real-Time Trading Dashboard
- **Live Signals**: Real-time display of active trading signals with WebSocket updates
- **Signal History**: Complete history of past signals with performance metrics
- **Risk Management**: Live risk metrics dashboard with visual indicators
- **Statistics**: Comprehensive performance statistics and analytics

### Robust Architecture
- **Type-Safe**: Full TypeScript implementation with strict type checking
- **Error Handling**: Comprehensive error handling with automatic retry logic
- **Loading States**: Elegant loading animations and skeleton screens
- **Responsive Design**: Mobile-first design that works on all devices

### Elegant UI/UX
- **Modern Design**: Clean, professional interface with smooth animations
- **Dark Mode Support**: Automatic dark mode based on system preferences
- **Custom Components**: Reusable UI component library
- **Accessibility**: WCAG compliant with keyboard navigation support

## 📦 Installation

### Prerequisites
- Node.js 18+ and npm
- Backend API server running (see `/backend` directory)

### Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env.local
   ```

4. **Edit `.env.local`** with your configuration:
   ```bash
   # Backend API URL
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

   # WebSocket URL for real-time updates
   NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

   # Environment
   NEXT_PUBLIC_ENV=development
   ```

5. **Start development server**
   ```bash
   npm run dev
   ```

6. **Open browser**
   Navigate to `http://localhost:3000`

## 🏗️ Project Structure

```
frontend/
├── app/
│   ├── components/           # React components
│   │   ├── EnhancedDashboard.tsx  # Main dashboard component
│   │   ├── SignalCard.tsx         # Signal display card
│   │   ├── RiskMetrics.tsx        # Risk metrics dashboard
│   │   └── UIComponents.tsx       # Reusable UI components
│   ├── lib/                  # Utility libraries
│   │   ├── api.ts            # API client with error handling
│   │   └── types.ts          # TypeScript type definitions
│   ├── globals.css           # Global styles and animations
│   ├── layout.tsx            # Root layout component
│   └── page.tsx              # Home page
├── .env.local                # Environment variables (create from .env.example)
├── .env.example              # Environment variables template
├── package.json              # Dependencies and scripts
└── README.md                 # This file
```

## 🎨 Components

### EnhancedDashboard
The main dashboard component that orchestrates the entire UI.

**Features:**
- Real-time data fetching with auto-refresh (30s)
- WebSocket integration for live updates
- Tab navigation (Live Signals / History)
- Symbol filtering
- Connection status monitoring

### SignalCard
Displays individual trading signal information with complete trade details.

### RiskMetrics
Real-time risk management dashboard with visual indicators and alerts.

## 🔌 API Integration

### Available Endpoints

- `GET /api/v1/signals/active` - Get active signals
- `GET /api/v1/signals/history` - Get signal history
- `GET /api/v1/stats` - Get performance statistics
- `GET /api/v1/risk/metrics` - Get risk metrics
- `POST /api/v1/signals/generate` - Generate new signal
- `POST /api/v1/signals/{id}/execute` - Execute signal
- `POST /api/v1/signals/{id}/close` - Close position

## 🧪 Development

### Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linter
npm run lint
```

## 🔧 Troubleshooting

### Backend Connection Failed

Ensure backend server is running:
```bash
cd ../backend
python -m uvicorn src.api.main:app --reload --port 8000
```

### WebSocket Issues

Check `NEXT_PUBLIC_WS_URL` in `.env.local` matches backend WebSocket endpoint.

---

**Built with Next.js 14, React 19, and TypeScript**

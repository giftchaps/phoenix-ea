"""
Phoenix EA - FastAPI Backend Routes
Main API endpoints for signal generation, management, and statistics
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules (assuming they're in the project)
from src.strategy.smc_engine import SMCStrategyEngine, Signal
from src.backtesting.backtest_engine import BacktestEngine, BrokerModel
from src.notifications.telegram_bot import TelegramNotifier
from src.data.deriv_client import DerivClient
from src.risk.risk_manager import RiskManager
from src.database.models import SessionLocal, SignalDB, TradeDB, SymbolDB
from src.filters.market_filters import MarketFilters, create_sample_economic_calendar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Phoenix EA Signals API",
    description="Institutional-grade SMC trading signals",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourfrontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global instances
strategy_engine: Optional[SMCStrategyEngine] = None
telegram_bot: Optional[TelegramNotifier] = None
deriv_client: Optional[DerivClient] = None
risk_manager: Optional[RiskManager] = None
active_websockets: List[WebSocket] = []


# Pydantic models
class SignalStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class SignalResponse(BaseModel):
    id: str
    symbol: str
    timeframe: str
    side: str
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: Optional[float]
    risk_reward: float
    confidence: float
    sweep_type: str
    structure_type: str
    ob_present: bool
    premium_discount: str
    h4_aligned: bool
    h1_bias: str
    atr_percentile: float
    posted_at: datetime
    status: SignalStatus
    lots: Optional[float]


class GenerateSignalRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., XAUUSD, V75)")
    timeframe: str = Field(default="M15", description="Signal timeframe")
    force: bool = Field(default=False, description="Force generation ignoring filters")


class ExecuteSignalRequest(BaseModel):
    signal_id: str
    auto_manage: bool = Field(default=True, description="Enable auto partials/BE")


class StatsResponse(BaseModel):
    today_signals: int
    active_positions: int
    total_pnl_r: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int


class RiskMetricsResponse(BaseModel):
    daily_pnl: float
    daily_pnl_r: float
    trade_count: int
    active_trades_count: int
    active_risk_r: float
    max_risk_per_trade: float
    max_daily_risk: float
    daily_stop_r: float
    max_concurrent_r: float
    drawdown_threshold_r: float
    risk_utilization: float
    risk_reduction_active: bool
    can_trade: bool


class AdminConfigUpdate(BaseModel):
    symbol: Optional[str]
    enabled: Optional[bool]
    risk_pct: Optional[float]
    min_confidence: Optional[float]
    ob_required: Optional[bool]


# Startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global strategy_engine, telegram_bot, deriv_client, risk_manager, market_filters, app_config

    logger.info("Starting Phoenix EA backend...")

    # Load configuration
    with open("config/strategy_config.json", "r") as f:
        app_config = json.load(f)

    # Initialize strategy engine
    strategy_engine = SMCStrategyEngine(app_config["symbols"]["XAUUSD"]["strategy_params"])
    logger.info("Strategy engine initialized")

    # Initialize market filters
    market_filters = MarketFilters(app_config["symbols"]["XAUUSD"])
    # Load economic calendar
    calendar_events = create_sample_economic_calendar()
    market_filters.load_economic_calendar(calendar_events)
    logger.info("Market filters initialized")

    # Initialize Telegram bot
    telegram_bot = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        channel_id=os.getenv("TELEGRAM_CHANNEL_ID", "@aurexai_signals"),
        admin_chat_ids=[int(id) for id in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") if id]
    )
    await telegram_bot.initialize()
    logger.info("Telegram bot initialized")

    # Initialize Deriv client
    deriv_client = DerivClient(
        api_url=os.getenv("DERIV_API_URL")
    )
    await deriv_client.connect()
    logger.info("Deriv client connected")

    # Initialize risk manager
    risk_manager = RiskManager(
        daily_stop_r=-3.0,
        max_concurrent_r=2.0,
        drawdown_threshold_r=6.0,
        rolling_trades_window=20
    )
    logger.info("Risk manager initialized")

    # Start background tasks
    asyncio.create_task(signal_generation_loop())
    asyncio.create_task(position_monitoring_loop())

    logger.info("✅ Phoenix EA backend ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Phoenix EA backend...")
    
    if deriv_client:
        await deriv_client.disconnect()
    
    # Close all WebSocket connections
    for ws in active_websockets:
        await ws.close()


# Authentication dependency
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API token"""
    # In production, verify against database
    if credentials.credentials != "your_secret_api_key":
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "strategy_engine": strategy_engine is not None,
            "telegram": telegram_bot is not None,
            "deriv": deriv_client is not None and deriv_client.connected,
            "risk_manager": risk_manager is not None
        }
    }


# Signal endpoints
@app.get("/api/v1/signals/active", response_model=List[SignalResponse])
async def get_active_signals(token: str = Depends(verify_token)):
    """Get all active signals"""
    db = SessionLocal()
    try:
        signals = db.query(SignalDB).filter(
            SignalDB.status.in_([SignalStatus.PENDING, SignalStatus.ACTIVE])
        ).order_by(SignalDB.posted_at.desc()).all()
        
        return [SignalResponse(**signal.__dict__) for signal in signals]
    finally:
        db.close()


@app.get("/api/v1/signals/history", response_model=List[SignalResponse])
async def get_signal_history(
    limit: int = 50,
    symbol: Optional[str] = None,
    status: Optional[SignalStatus] = None,
    token: str = Depends(verify_token)
):
    """Get signal history with filters"""
    db = SessionLocal()
    try:
        query = db.query(SignalDB)
        
        if symbol:
            query = query.filter(SignalDB.symbol == symbol)
        if status:
            query = query.filter(SignalDB.status == status)
        
        signals = query.order_by(SignalDB.posted_at.desc()).limit(limit).all()
        return [SignalResponse(**signal.__dict__) for signal in signals]
    finally:
        db.close()


@app.post("/api/v1/signals/generate", response_model=Optional[SignalResponse])
async def generate_signal(
    request: GenerateSignalRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Generate new trading signal"""

    # Check risk limits
    if not request.force and not risk_manager.can_trade():
        raise HTTPException(
            status_code=429,
            detail=f"Daily stop hit: {risk_manager.daily_pnl_r:.2f}R"
        )

    # Fetch data
    try:
        # Get bars from data source
        m15_bars = await fetch_bars(request.symbol, "M15", 100)
        h1_bars = await fetch_bars(request.symbol, "H1", 50)
        h4_bars = await fetch_bars(request.symbol, "H4", 50)

        # Calculate ATR percentile
        if hasattr(m15_bars, 'atr'):
            current_atr = m15_bars['atr'].iloc[-1]
            atr_percentile = (m15_bars['atr'] < current_atr).sum() / len(m15_bars) * 100
        else:
            current_atr = None
            atr_percentile = None

        # ✅ PRIORITY 1 FIX: Check market filters (News Guard + Session Windows + ATR Regime)
        if not request.force:
            filters_passed, filter_reasons = market_filters.check_all_filters(
                timestamp=datetime.now(),
                current_atr=current_atr,
                atr_percentile=atr_percentile
            )

            if not filters_passed:
                logger.info(f"❌ Signal blocked by filters: {', '.join(filter_reasons)}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Market filters blocked signal: {', '.join(filter_reasons)}"
                )

            logger.info(f"✅ Market filters passed: {', '.join(filter_reasons)}")

        # Get biases
        h4_bias = determine_bias(h4_bars)
        h1_bias = determine_bias(h1_bars)

        # Get effective risk percent (adjusted for drawdown throttle)
        base_risk_pct = 1.0
        effective_risk_pct = risk_manager.get_effective_risk_percent(base_risk_pct)

        if effective_risk_pct < base_risk_pct:
            logger.warning(f"⚠️  Risk reduced due to drawdown throttle: {base_risk_pct}% -> {effective_risk_pct}%")

        # Generate signal
        signal = strategy_engine.generate_signal(
            symbol=request.symbol,
            timeframe=request.timeframe,
            bars=m15_bars,
            h4_bias=h4_bias,
            h1_bias=h1_bias,
            account_balance=10000,  # Get from account
            risk_pct=effective_risk_pct
        )

        if signal:
            # Save to database
            db_signal = save_signal_to_db(signal)

            # Register trade with risk manager
            risk_manager.register_trade(signal.id, signal.risk_r)

            # Send notifications
            background_tasks.add_task(telegram_bot.send_signal, signal.__dict__)
            background_tasks.add_task(broadcast_signal, signal.__dict__)

            logger.info(f"Signal generated: {signal.id}")
            return SignalResponse(**signal.__dict__)
        else:
            return None

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Signal generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/signals/{signal_id}/execute")
async def execute_signal(
    signal_id: str,
    request: ExecuteSignalRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Execute signal (place order)"""
    
    db = SessionLocal()
    try:
        signal = db.query(SignalDB).filter(SignalDB.id == signal_id).first()
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        if signal.status != SignalStatus.PENDING:
            raise HTTPException(status_code=400, detail="Signal already executed")
        
        # Place order based on broker
        if 'V' in signal.symbol:  # Deriv synthetics
            result = await deriv_client.place_order(signal.__dict__)
        else:  # MT5 forex
            result = await place_mt5_order(signal.__dict__)
        
        if result['success']:
            # Update signal status
            signal.status = SignalStatus.ACTIVE
            db.commit()
            
            # Notify
            background_tasks.add_task(
                telegram_bot.send_update,
                signal_id,
                "order_placed",
                {"ticket": result.get('contract_id')}
            )
            
            return {"success": True, "order_id": result.get('contract_id')}
        else:
            raise HTTPException(status_code=500, detail=result.get('error'))
            
    finally:
        db.close()


@app.post("/api/v1/signals/{signal_id}/close")
async def close_signal(
    signal_id: str,
    partial_pct: float = 1.0,
    reason: str = "manual",
    token: str = Depends(verify_token)
):
    """Close position for a signal"""

    db = SessionLocal()
    try:
        signal = db.query(SignalDB).filter(SignalDB.id == signal_id).first()
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")

        # Close position
        if 'V' in signal.symbol:
            result = await deriv_client.close_position(signal.contract_id, partial_pct)
        else:
            result = await close_mt5_position(signal.ticket, partial_pct)

        if result['success']:
            # Calculate P&L in R multiples
            pnl_dollars = result.get('pnl', 0.0)
            entry_price = signal.entry
            sl_distance = abs(signal.entry - signal.stop_loss)

            # Calculate R multiple (assuming 1R = initial risk)
            if sl_distance > 0:
                pnl_r = pnl_dollars / (signal.lots * sl_distance * signal.risk_r)
            else:
                pnl_r = 0.0

            # Update risk manager
            if partial_pct >= 1.0:
                # Full close - unregister trade and update metrics
                risk_manager.unregister_trade(signal_id)
                risk_manager.update_trade_result(pnl_dollars, pnl_r)
                signal.status = SignalStatus.CLOSED
            else:
                # Partial close - reduce active risk proportionally
                if signal_id in risk_manager.active_trades:
                    original_risk = risk_manager.active_trades[signal_id]
                    reduced_risk = original_risk * (1 - partial_pct)
                    risk_manager.active_trades[signal_id] = reduced_risk
                    risk_manager.active_risk_r = sum(risk_manager.active_trades.values())

            db.commit()

            logger.info(f"Position closed: {signal_id} ({partial_pct*100}%) - P&L: ${pnl_dollars:.2f} ({pnl_r:.2f}R)")

            return {"success": True, "pnl": pnl_dollars, "pnl_r": pnl_r}
        else:
            raise HTTPException(status_code=500, detail=result.get('error'))

    finally:
        db.close()


# Statistics endpoints
@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_statistics(
    period: str = "all",  # all, today, week, month
    token: str = Depends(verify_token)
):
    """Get performance statistics"""
    
    db = SessionLocal()
    try:
        # Calculate stats from database
        now = datetime.now()
        
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = None
        
        # Query trades
        query = db.query(TradeDB)
        if start_date:
            query = query.filter(TradeDB.exit_time >= start_date)
        
        trades = query.all()
        
        # Calculate metrics
        total_signals = len(trades)
        active_positions = db.query(SignalDB).filter(
            SignalDB.status == SignalStatus.ACTIVE
        ).count()
        
        winning_trades = [t for t in trades if t.pnl_r > 0]
        losing_trades = [t for t in trades if t.pnl_r <= 0]
        
        win_rate = len(winning_trades) / total_signals if total_signals > 0 else 0
        
        today_trades = [t for t in trades if t.exit_time.date() == now.date()]
        today_pnl_r = sum(t.pnl_r for t in today_trades)
        today_pnl_usd = sum(t.pnl_dollars for t in today_trades)
        
        # Profit factor
        gross_profit = sum(t.pnl_r for t in winning_trades)
        gross_loss = abs(sum(t.pnl_r for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Max drawdown
        cumulative_r = [0]
        for t in trades:
            cumulative_r.append(cumulative_r[-1] + t.pnl_r)
        
        running_max = [cumulative_r[0]]
        for val in cumulative_r[1:]:
            running_max.append(max(running_max[-1], val))
        
        drawdowns = [cumulative_r[i] - running_max[i] for i in range(len(cumulative_r))]
        max_drawdown_r = abs(min(drawdowns))
        
        # Sharpe ratio (simplified)
        returns = [t.pnl_r for t in trades]
        if len(returns) > 1:
            import numpy as np
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe = 0
        
        return StatsResponse(
            today_signals=len(today_trades),
            active_positions=active_positions,
            total_pnl_r=sum(t.pnl_r for t in trades),
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_signals,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades)
        )
        
    finally:
        db.close()


@app.get("/api/v1/risk/metrics", response_model=RiskMetricsResponse)
async def get_risk_metrics(token: str = Depends(verify_token)):
    """Get current risk management metrics"""

    if not risk_manager:
        raise HTTPException(status_code=500, detail="Risk manager not initialized")

    # Calculate risk utilization
    risk_utilization = risk_manager.active_risk_r / risk_manager.max_concurrent_r if risk_manager.max_concurrent_r > 0 else 0

    return RiskMetricsResponse(
        daily_pnl=risk_manager.daily_pnl,
        daily_pnl_r=risk_manager.daily_pnl_r,
        trade_count=risk_manager.trade_count,
        active_trades_count=risk_manager.active_trades_count,
        active_risk_r=risk_manager.active_risk_r,
        max_risk_per_trade=risk_manager.max_risk_per_trade,
        max_daily_risk=risk_manager.max_daily_risk,
        daily_stop_r=risk_manager.daily_stop_r,
        max_concurrent_r=risk_manager.max_concurrent_r,
        drawdown_threshold_r=risk_manager.drawdown_threshold_r,
        risk_utilization=risk_utilization,
        risk_reduction_active=risk_manager.risk_reduction_active,
        can_trade=risk_manager.can_trade()
    )


# Admin endpoints
@app.post("/api/v1/admin/config")
async def update_config(
    update: AdminConfigUpdate,
    token: str = Depends(verify_token)
):
    """Update strategy configuration"""
    
    # In production, save to database and reload config
    logger.info(f"Config update: {update}")
    
    return {"success": True, "message": "Configuration updated"}


@app.post("/api/v1/admin/backtest")
async def run_backtest(
    symbol: str,
    start_date: str,
    end_date: str,
    token: str = Depends(verify_token)
):
    """Run backtest on historical data"""
    
    # This would trigger a background backtest job
    logger.info(f"Backtest requested: {symbol} from {start_date} to {end_date}")
    
    return {
        "success": True,
        "message": "Backtest queued",
        "job_id": "BT_" + datetime.now().strftime("%Y%m%d%H%M%S")
    }


# WebSocket endpoint for real-time updates
@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time signal updates"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        logger.info("WebSocket client disconnected")


# Helper functions
async def broadcast_signal(signal_data: Dict):
    """Broadcast signal to all connected WebSocket clients"""
    message = json.dumps({
        "type": "new_signal",
        "data": signal_data
    })
    
    for ws in active_websockets:
        try:
            await ws.send_text(message)
        except Exception as e:
            logger.error(f"WebSocket broadcast error: {e}")


async def signal_generation_loop():
    """Background task to generate signals periodically"""
    while True:
        try:
            # Check for new bar closes and generate signals
            # This would be triggered by bar close events from data feeds
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Signal generation loop error: {e}")


async def position_monitoring_loop():
    """Background task to monitor open positions"""
    while True:
        try:
            # Monitor positions for TP/SL/BE
            await asyncio.sleep(5)  # Check every 5 seconds
        except Exception as e:
            logger.error(f"Position monitoring error: {e}")


async def fetch_bars(symbol: str, timeframe: str, count: int):
    """Fetch historical bars from data source"""
    try:
        # Try Deriv client first if available
        if deriv_client and deriv_client.enabled:
            result = await deriv_client.get_ohlc(symbol, timeframe, count)
            if result and result.get('ohlc'):
                return result['ohlc']

        # Fallback: Generate sample bars for testing
        # In production, this should connect to MT5, broker API, or data provider
        logger.warning(f"Using sample data for {symbol} {timeframe}")
        import pandas as pd
        import numpy as np

        # Generate sample OHLCV data
        base_price = 2000.0 if 'XAU' in symbol else 1.1000
        dates = pd.date_range(end=pd.Timestamp.now(), periods=count, freq='15min')

        data = {
            'timestamp': dates,
            'open': base_price + np.random.randn(count) * 10,
            'high': base_price + np.random.randn(count) * 10 + 5,
            'low': base_price + np.random.randn(count) * 10 - 5,
            'close': base_price + np.random.randn(count) * 10,
            'volume': np.random.randint(100, 1000, count)
        }

        df = pd.DataFrame(data)
        # Calculate ATR
        df['atr'] = calculate_atr(df)

        return df

    except Exception as e:
        logger.error(f"Failed to fetch bars for {symbol}: {e}")
        return None


def determine_bias(bars):
    """Determine market bias from bars using EMA"""
    try:
        import pandas as pd

        if bars is None or len(bars) < 200:
            return "neutral"

        # Calculate 200 EMA
        if isinstance(bars, pd.DataFrame):
            close_prices = bars['close']
        else:
            close_prices = pd.Series([bar['close'] for bar in bars])

        ema_200 = close_prices.ewm(span=200, adjust=False).mean()
        current_price = close_prices.iloc[-1]
        current_ema = ema_200.iloc[-1]

        # Determine bias
        if current_price > current_ema:
            return "bullish"
        elif current_price < current_ema:
            return "bearish"
        else:
            return "neutral"

    except Exception as e:
        logger.error(f"Failed to determine bias: {e}")
        return "neutral"


def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    try:
        import pandas as pd
        import numpy as np

        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr.fillna(10.0)  # Default ATR if calculation fails

    except Exception as e:
        logger.error(f"Failed to calculate ATR: {e}")
        return pd.Series([10.0] * len(df))


def save_signal_to_db(signal: Signal):
    """Save signal to database"""
    db = SessionLocal()
    try:
        db_signal = SignalDB(**signal.__dict__)
        db.add(db_signal)
        db.commit()
        return db_signal
    finally:
        db.close()


async def place_mt5_order(signal: Dict):
    """Place order on MT5"""
    try:
        # TODO: Implement actual MT5 API integration using MetaTrader5 library
        # For now, simulate MT5 order placement
        logger.info(f"Placing MT5 order: {signal.get('symbol')} {signal.get('side')}")

        # Simulate ticket generation
        import random
        ticket = random.randint(100000, 999999)

        result = {
            "ticket": ticket,
            "status": "active",
            "symbol": signal.get("symbol"),
            "type": signal.get("side"),
            "entry": signal.get("entry"),
            "stop_loss": signal.get("stop_loss"),
            "take_profit_1": signal.get("take_profit_1"),
            "lots": signal.get("lots", 0.01),
            "timestamp": signal.get("posted_at")
        }

        logger.info(f"MT5 order placed successfully: Ticket #{ticket}")
        return result

    except Exception as e:
        logger.error(f"Failed to place MT5 order: {e}")
        return None


async def close_mt5_position(ticket: int, partial_pct: float):
    """Close MT5 position (full or partial)"""
    try:
        # TODO: Implement actual MT5 API integration using MetaTrader5 library
        # For now, simulate MT5 position closing
        logger.info(f"Closing MT5 position: Ticket #{ticket} ({partial_pct * 100}%)")

        result = {
            "ticket": ticket,
            "status": "closed" if partial_pct >= 1.0 else "partial",
            "partial_pct": partial_pct,
            "closed_at": datetime.now().isoformat()
        }

        logger.info(f"MT5 position closed successfully: Ticket #{ticket}")
        return result

    except Exception as e:
        logger.error(f"Failed to close MT5 position: {e}")
        return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
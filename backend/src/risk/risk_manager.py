"""
Risk Manager
Handles risk management for the Phoenix EA system
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

class RiskManager:
    """Risk management system"""

    def __init__(self, max_risk_per_trade: float = 0.02, max_daily_risk: float = 0.05,
                 daily_stop_r: float = -3.0, max_concurrent_r: float = 2.0,
                 drawdown_threshold_r: float = 6.0, rolling_trades_window: int = 20):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_risk = max_daily_risk
        self.daily_pnl = 0.0
        self.daily_pnl_r = 0.0  # Daily PnL in R multiples
        self.trade_count = 0
        self.daily_stop_r = daily_stop_r  # Daily stop loss in R (e.g., -3.0R)
        self.max_concurrent_r = max_concurrent_r  # Max concurrent risk in R
        self.drawdown_threshold_r = drawdown_threshold_r  # Drawdown threshold in R

        # Track active trades and their risk
        self.active_trades_count = 0
        self.active_risk_r = 0.0  # Total R risk of active trades
        self.active_trades: Dict[str, float] = {}  # signal_id -> risk_r

        # Drawdown throttle tracking
        self.rolling_trades_window = rolling_trades_window
        self.rolling_pnl_r: deque = deque(maxlen=rolling_trades_window)
        self.risk_reduction_active = False
        self.risk_reduction_factor = 0.5  # Reduce risk by 50% when throttle active

        logger.info(f"Risk Manager initialized - Max trade risk: {max_risk_per_trade}, "
                   f"Max daily risk: {max_daily_risk}, Daily stop: {daily_stop_r}R")
    
    def calculate_position_size(self, account_balance: float, stop_loss_distance: float, 
                              risk_percent: float = None) -> float:
        """Calculate position size based on risk parameters"""
        if risk_percent is None:
            risk_percent = self.max_risk_per_trade
        
        risk_amount = account_balance * risk_percent
        position_size = risk_amount / stop_loss_distance if stop_loss_distance > 0 else 0
        
        logger.debug(f"Position size calculated: {position_size} (risk: {risk_percent}, balance: {account_balance})")
        return position_size
    
    def check_risk_limits(self, trade_risk: float) -> bool:
        """Check if trade is within risk limits"""
        if trade_risk > self.max_risk_per_trade:
            logger.warning(f"Trade risk {trade_risk} exceeds max per trade {self.max_risk_per_trade}")
            return False

        if abs(self.daily_pnl) > self.max_daily_risk:
            logger.warning(f"Daily PnL {self.daily_pnl} exceeds max daily risk {self.max_daily_risk}")
            return False

        return True

    def can_trade(self) -> bool:
        """Check if trading is allowed based on current risk status"""
        # Check if daily stop loss has been hit
        if self.daily_pnl_r <= self.daily_stop_r:
            logger.warning(f"Daily stop loss hit: {self.daily_pnl_r:.2f}R (limit: {self.daily_stop_r}R)")
            return False

        # Check if drawdown threshold exceeded
        if abs(self.daily_pnl_r) >= abs(self.drawdown_threshold_r):
            logger.warning(f"Drawdown threshold exceeded: {self.daily_pnl_r:.2f}R (threshold: {self.drawdown_threshold_r}R)")
            return False

        # FIXED: Check if max concurrent RISK (not count) exceeded
        if self.active_risk_r >= self.max_concurrent_r:
            logger.warning(f"Max concurrent risk reached: {self.active_risk_r:.2f}R (max: {self.max_concurrent_r}R)")
            return False

        return True

    def register_trade(self, signal_id: str, risk_r: float = 1.0) -> None:
        """Register a new active trade and its risk"""
        self.active_trades[signal_id] = risk_r
        self.active_trades_count = len(self.active_trades)
        self.active_risk_r = sum(self.active_trades.values())
        logger.info(f"Trade registered: {signal_id} ({risk_r}R). Active: {self.active_trades_count} trades, {self.active_risk_r:.2f}R total")

    def unregister_trade(self, signal_id: str) -> None:
        """Remove a trade from active tracking"""
        if signal_id in self.active_trades:
            risk_r = self.active_trades.pop(signal_id)
            self.active_trades_count = len(self.active_trades)
            self.active_risk_r = sum(self.active_trades.values())
            logger.info(f"Trade unregistered: {signal_id} ({risk_r}R). Active: {self.active_trades_count} trades, {self.active_risk_r:.2f}R total")

    def update_drawdown_throttle(self, pnl_r: float) -> None:
        """Update rolling drawdown and check if throttle should activate"""
        self.rolling_pnl_r.append(pnl_r)

        # Calculate rolling drawdown
        if len(self.rolling_pnl_r) >= self.rolling_trades_window:
            rolling_dd_r = sum(self.rolling_pnl_r)

            # Check if throttle should activate
            if rolling_dd_r <= -abs(self.drawdown_threshold_r):
                if not self.risk_reduction_active:
                    self.risk_reduction_active = True
                    logger.warning(f"⚠️  DRAWDOWN THROTTLE ACTIVATED: Rolling DD = {rolling_dd_r:.2f}R "
                                 f"(threshold: {-abs(self.drawdown_threshold_r)}R). "
                                 f"Risk reduced by {int((1-self.risk_reduction_factor)*100)}%")
            else:
                if self.risk_reduction_active:
                    self.risk_reduction_active = False
                    logger.info(f"✅ DRAWDOWN THROTTLE DEACTIVATED: Rolling DD = {rolling_dd_r:.2f}R. "
                              f"Risk restored to normal.")

    def get_effective_risk_percent(self, base_risk: float) -> float:
        """Get risk percent adjusted for drawdown throttle"""
        if self.risk_reduction_active:
            return base_risk * self.risk_reduction_factor
        return base_risk
    
    def update_trade_result(self, pnl: float, pnl_r: float = 0.0):
        """Update risk metrics with trade result"""
        self.daily_pnl += pnl
        self.daily_pnl_r += pnl_r
        self.trade_count += 1

        # Update drawdown throttle
        self.update_drawdown_throttle(pnl_r)

        logger.info(f"Trade result: ${pnl:.2f} ({pnl_r:.2f}R), Daily PnL: ${self.daily_pnl:.2f} ({self.daily_pnl_r:.2f}R), "
                   f"Trade count: {self.trade_count}")

    def reset_daily_metrics(self):
        """Reset daily metrics (call at end of day)"""
        logger.info(f"Resetting daily metrics. Final: ${self.daily_pnl:.2f} ({self.daily_pnl_r:.2f}R), {self.trade_count} trades")
        self.daily_pnl = 0.0
        self.daily_pnl_r = 0.0
        self.trade_count = 0

    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        rolling_dd_r = sum(self.rolling_pnl_r) if self.rolling_pnl_r else 0.0

        return {
            "daily_pnl": self.daily_pnl,
            "daily_pnl_r": self.daily_pnl_r,
            "trade_count": self.trade_count,
            "active_trades_count": self.active_trades_count,
            "active_risk_r": self.active_risk_r,
            "max_risk_per_trade": self.max_risk_per_trade,
            "max_daily_risk": self.max_daily_risk,
            "daily_stop_r": self.daily_stop_r,
            "max_concurrent_r": self.max_concurrent_r,
            "drawdown_threshold_r": self.drawdown_threshold_r,
            "rolling_dd_r": rolling_dd_r,
            "risk_reduction_active": self.risk_reduction_active,
            "effective_risk_factor": self.risk_reduction_factor if self.risk_reduction_active else 1.0,
            "risk_utilization": abs(self.daily_pnl) / self.max_daily_risk if self.max_daily_risk > 0 else 0,
            "can_trade": self.can_trade()
        }

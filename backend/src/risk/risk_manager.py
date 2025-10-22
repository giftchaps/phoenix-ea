"""
Risk Manager
Handles risk management for the Phoenix EA system
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskManager:
    """Risk management system"""
    
    def __init__(self, max_risk_per_trade: float = 0.02, max_daily_risk: float = 0.05):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_risk = max_daily_risk
        self.daily_pnl = 0.0
        self.trade_count = 0
        
        logger.info(f"Risk Manager initialized - Max trade risk: {max_risk_per_trade}, Max daily risk: {max_daily_risk}")
    
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
    
    def update_trade_result(self, pnl: float):
        """Update risk metrics with trade result"""
        self.daily_pnl += pnl
        self.trade_count += 1
        
        logger.info(f"Trade result: {pnl}, Daily PnL: {self.daily_pnl}, Trade count: {self.trade_count}")
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        return {
            "daily_pnl": self.daily_pnl,
            "trade_count": self.trade_count,
            "max_risk_per_trade": self.max_risk_per_trade,
            "max_daily_risk": self.max_daily_risk,
            "risk_utilization": abs(self.daily_pnl) / self.max_daily_risk if self.max_daily_risk > 0 else 0
        }

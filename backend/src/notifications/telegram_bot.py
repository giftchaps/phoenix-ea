"""
Telegram Bot Notifier
Handles Telegram notifications for the Phoenix EA system
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Telegram notification handler"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None, channel_id: Optional[str] = None, admin_chat_ids: Optional[list] = None):
        self.bot_token = bot_token
        self.chat_id = chat_id or channel_id
        self.admin_chat_ids = admin_chat_ids or []
        self.enabled = bool(bot_token and self.chat_id)
        
        if self.enabled:
            logger.info("Telegram notifications enabled")
        else:
            logger.warning("Telegram notifications disabled - missing bot_token or chat_id")
    
    async def initialize(self):
        """Initialize the Telegram bot"""
        if self.enabled:
            logger.info("Telegram bot initialized successfully")
        else:
            logger.warning("Telegram bot initialization skipped - not enabled")
    
    async def send_message(self, message: str) -> bool:
        """Send a message via Telegram"""
        if not self.enabled:
            logger.debug(f"Telegram notification (disabled): {message}")
            return False
        
        try:
            # TODO: Implement actual Telegram API call
            logger.info(f"Telegram notification: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def send_signal(self, signal_data: dict) -> bool:
        """Send trading signal notification"""
        message = f"📊 New Signal: {signal_data.get('symbol', 'N/A')} {signal_data.get('side', 'N/A')}"
        return await self.send_message(message)
    
    async def send_alert(self, alert_type: str, message: str) -> bool:
        """Send system alert"""
        formatted_message = f"🚨 {alert_type}: {message}"
        return await self.send_message(formatted_message)

    async def send_update(self, update_type: str, data: dict) -> bool:
        """Send general update notification"""
        if not self.enabled:
            logger.debug(f"Telegram update (disabled): {update_type}")
            return False

        try:
            # Format the update message based on type
            if update_type == "order_executed":
                message = (
                    f"✅ Order Executed\n"
                    f"Symbol: {data.get('symbol', 'N/A')}\n"
                    f"Side: {data.get('side', 'N/A')}\n"
                    f"Entry: {data.get('entry', 'N/A')}\n"
                    f"SL: {data.get('stop_loss', 'N/A')}\n"
                    f"TP: {data.get('take_profit_1', 'N/A')}"
                )
            elif update_type == "position_closed":
                message = (
                    f"🔒 Position Closed\n"
                    f"Symbol: {data.get('symbol', 'N/A')}\n"
                    f"PnL: {data.get('pnl', 'N/A')}\n"
                    f"R: {data.get('r_multiple', 'N/A')}"
                )
            elif update_type == "risk_warning":
                message = (
                    f"⚠️ Risk Warning\n"
                    f"{data.get('message', 'Risk limit reached')}"
                )
            else:
                message = f"📢 Update: {update_type}\n{str(data)}"

            return await self.send_message(message)

        except Exception as e:
            logger.error(f"Failed to send Telegram update: {e}")
            return False

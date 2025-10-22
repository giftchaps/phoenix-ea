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

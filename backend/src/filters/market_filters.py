"""
Market Filters
Handles session windows, news guard, and ATR regime filtering
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz

logger = logging.getLogger(__name__)


class MarketFilters:
    """Market condition filters for trading"""

    def __init__(self, config: Dict):
        """
        Initialize market filters

        Args:
            config: Symbol configuration with filters, session_windows, etc.
        """
        self.config = config
        self.symbol = config.get("name", "Unknown")

        # Session windows
        self.session_windows = config.get("session_windows", [])

        # News guard configuration
        filters = config.get("filters", {})
        self.news_guard_config = filters.get("news_guard", {})
        self.news_guard_enabled = self.news_guard_config.get("enabled", False)
        self.block_minutes_before = self.news_guard_config.get("block_minutes_before", 15)
        self.block_minutes_after = self.news_guard_config.get("block_minutes_after", 15)
        self.watched_events = self.news_guard_config.get("events", [])

        # ATR regime filter
        self.atr_regime_config = filters.get("atr_regime", {})
        self.atr_regime_enabled = self.atr_regime_config.get("enabled", False)
        self.atr_min_pctl = self.atr_regime_config.get("min_percentile", 40)
        self.atr_max_pctl = self.atr_regime_config.get("max_percentile", 85)

        # Economic calendar cache (in production, fetch from API)
        self.economic_calendar: List[Dict] = []

        logger.info(f"Market Filters initialized for {self.symbol} - "
                   f"News Guard: {self.news_guard_enabled}, "
                   f"Session Windows: {len(self.session_windows)}, "
                   f"ATR Regime: {self.atr_regime_enabled}")

    def check_session_window(self, timestamp: Optional[datetime] = None) -> Tuple[bool, str]:
        """
        Check if current time is within allowed trading session windows

        Args:
            timestamp: Time to check (defaults to now)

        Returns:
            (is_allowed, reason)
        """
        if not self.session_windows:
            return True, "No session restrictions"

        check_time = timestamp or datetime.now(pytz.UTC)

        for window in self.session_windows:
            try:
                # Parse session times
                start_str = window.get("start", "00:00")
                end_str = window.get("end", "23:59")
                tz_str = window.get("timezone", "UTC")

                # Convert to timezone
                tz = pytz.timezone(tz_str)
                check_time_local = check_time.astimezone(tz)

                # Parse start and end times
                start_hour, start_min = map(int, start_str.split(":"))
                end_hour, end_min = map(int, end_str.split(":"))

                # Create time objects for today
                start_time = check_time_local.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
                end_time = check_time_local.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)

                # Check if within window
                if start_time <= check_time_local <= end_time:
                    return True, f"Within session window {start_str}-{end_str} {tz_str}"

            except Exception as e:
                logger.error(f"Error parsing session window {window}: {e}")
                continue

        return False, "Outside all session windows"

    def check_news_guard(self, timestamp: Optional[datetime] = None) -> Tuple[bool, str]:
        """
        Check if current time is within news blackout period

        Args:
            timestamp: Time to check (defaults to now)

        Returns:
            (is_allowed, reason)
        """
        if not self.news_guard_enabled:
            return True, "News guard disabled"

        check_time = timestamp or datetime.now(pytz.UTC)

        # Check against economic calendar
        for event in self.economic_calendar:
            event_time = event.get("time")
            event_name = event.get("name", "Unknown")
            event_currency = event.get("currency", "")

            if not event_time:
                continue

            # Check if event affects this symbol
            if not self._event_affects_symbol(event_currency):
                continue

            # Calculate blackout window
            blackout_start = event_time - timedelta(minutes=self.block_minutes_before)
            blackout_end = event_time + timedelta(minutes=self.block_minutes_after)

            # Check if within blackout
            if blackout_start <= check_time <= blackout_end:
                return False, f"News blackout: {event_name} at {event_time.strftime('%H:%M %Z')}"

        return True, "No news conflicts"

    def check_atr_regime(self, current_atr: float, atr_percentile: float) -> Tuple[bool, str]:
        """
        Check if ATR is within acceptable regime

        Args:
            current_atr: Current ATR value
            atr_percentile: ATR percentile (0-100)

        Returns:
            (is_allowed, reason)
        """
        if not self.atr_regime_enabled:
            return True, "ATR regime filter disabled"

        if atr_percentile < self.atr_min_pctl:
            return False, f"ATR too low: {atr_percentile:.1f}th percentile (min: {self.atr_min_pctl})"

        if atr_percentile > self.atr_max_pctl:
            return False, f"ATR too high: {atr_percentile:.1f}th percentile (max: {self.atr_max_pctl})"

        return True, f"ATR regime OK: {atr_percentile:.1f}th percentile"

    def check_all_filters(self, timestamp: Optional[datetime] = None,
                          current_atr: Optional[float] = None,
                          atr_percentile: Optional[float] = None) -> Tuple[bool, List[str]]:
        """
        Check all market filters

        Args:
            timestamp: Time to check (defaults to now)
            current_atr: Current ATR value
            atr_percentile: ATR percentile

        Returns:
            (all_passed, reasons_list)
        """
        reasons = []
        all_passed = True

        # Session window check
        session_ok, session_reason = self.check_session_window(timestamp)
        reasons.append(f"Session: {session_reason}")
        if not session_ok:
            all_passed = False

        # News guard check
        news_ok, news_reason = self.check_news_guard(timestamp)
        reasons.append(f"News: {news_reason}")
        if not news_ok:
            all_passed = False

        # ATR regime check
        if current_atr is not None and atr_percentile is not None:
            atr_ok, atr_reason = self.check_atr_regime(current_atr, atr_percentile)
            reasons.append(f"ATR: {atr_reason}")
            if not atr_ok:
                all_passed = False

        return all_passed, reasons

    def load_economic_calendar(self, events: List[Dict]) -> None:
        """
        Load economic calendar events

        Args:
            events: List of event dicts with keys: time, name, currency, impact
        """
        self.economic_calendar = []

        for event in events:
            # Only add high-impact events that match watched event types
            if event.get("impact", "").lower() == "high":
                event_name = event.get("name", "")
                if any(watched in event_name for watched in self.watched_events):
                    self.economic_calendar.append(event)

        logger.info(f"Loaded {len(self.economic_calendar)} high-impact events for {self.symbol}")

    def _event_affects_symbol(self, currency: str) -> bool:
        """
        Check if an economic event affects this trading symbol

        Args:
            currency: Event currency code (e.g., "USD", "EUR")

        Returns:
            True if event affects symbol
        """
        symbol_upper = self.symbol.upper()

        # Gold is affected by USD events
        if "XAU" in symbol_upper or "GOLD" in symbol_upper:
            return currency == "USD"

        # Forex pairs affected by either currency
        if len(symbol_upper) >= 6:
            base = symbol_upper[:3]
            quote = symbol_upper[3:6]
            return currency in [base, quote]

        return False


def create_sample_economic_calendar() -> List[Dict]:
    """
    Create sample economic calendar for testing
    In production, fetch from API like forexfactory.com or investing.com
    """
    now = datetime.now(pytz.UTC)

    return [
        {
            "time": now + timedelta(hours=2),
            "name": "NFP - Non-Farm Payrolls",
            "currency": "USD",
            "impact": "high"
        },
        {
            "time": now + timedelta(days=1, hours=10),
            "name": "CPI - Consumer Price Index",
            "currency": "USD",
            "impact": "high"
        },
        {
            "time": now + timedelta(days=2, hours=14),
            "name": "FOMC Interest Rate Decision",
            "currency": "USD",
            "impact": "high"
        }
    ]

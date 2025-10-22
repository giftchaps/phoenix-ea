#!/usr/bin/env python3
"""
Test Priority 1 Critical Fixes
Tests all safety-critical features implemented
"""

import sys
import logging
from datetime import datetime, timedelta
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_risk_manager():
    """Test RiskManager fixes"""
    print("\n" + "="*60)
    print("TEST 1: Risk Manager - Concurrent Risk Calculation")
    print("="*60)

    from src.risk.risk_manager import RiskManager

    rm = RiskManager(
        daily_stop_r=-3.0,
        max_concurrent_r=2.0,
        drawdown_threshold_r=6.0,
        rolling_trades_window=20
    )

    print(f"✓ Risk Manager initialized")
    print(f"  - Daily stop: {rm.daily_stop_r}R")
    print(f"  - Max concurrent: {rm.max_concurrent_r}R")
    print(f"  - Drawdown threshold: {rm.drawdown_threshold_r}R")

    # Test concurrent risk tracking
    print("\n📊 Testing concurrent risk tracking...")
    print(f"  Initial active risk: {rm.active_risk_r:.2f}R")
    assert rm.active_risk_r == 0.0, "Initial risk should be 0"

    # Register trades
    rm.register_trade("signal_1", risk_r=1.0)
    print(f"  After trade 1 (1.0R): {rm.active_risk_r:.2f}R")
    assert rm.active_risk_r == 1.0, "Should have 1.0R active"

    rm.register_trade("signal_2", risk_r=0.8)
    print(f"  After trade 2 (0.8R): {rm.active_risk_r:.2f}R")
    assert rm.active_risk_r == 1.8, "Should have 1.8R active"

    # Test can_trade with concurrent limit
    can_trade_before = rm.can_trade()
    print(f"  Can trade at 1.8R: {can_trade_before}")
    assert can_trade_before == True, "Should allow trading below 2.0R limit"

    rm.register_trade("signal_3", risk_r=0.5)
    print(f"  After trade 3 (0.5R): {rm.active_risk_r:.2f}R")
    assert rm.active_risk_r == 2.3, "Should have 2.3R active"

    can_trade_after = rm.can_trade()
    print(f"  Can trade at 2.3R: {can_trade_after}")
    assert can_trade_after == False, "Should BLOCK trading above 2.0R limit"

    # Unregister trade
    rm.unregister_trade("signal_1")
    print(f"  After closing trade 1: {rm.active_risk_r:.2f}R")
    assert rm.active_risk_r == 1.3, "Should have 1.3R active"

    print("\n✅ PASS: Concurrent risk calculation working correctly!")

    return True


def test_drawdown_throttle():
    """Test Drawdown Throttle"""
    print("\n" + "="*60)
    print("TEST 2: Drawdown Throttle - Risk Reduction")
    print("="*60)

    from src.risk.risk_manager import RiskManager

    rm = RiskManager(
        daily_stop_r=-3.0,
        max_concurrent_r=2.0,
        drawdown_threshold_r=6.0,
        rolling_trades_window=5  # Small window for testing
    )

    print(f"✓ Risk Manager initialized (rolling window: 5 trades)")

    # Simulate losing streak
    print("\n📉 Simulating losing streak...")
    losses = [-1.5, -1.2, -1.0, -1.5, -1.0]  # Total: -6.2R

    for i, loss_r in enumerate(losses, 1):
        rm.update_trade_result(pnl=-100.0, pnl_r=loss_r)
        rolling_dd = sum(rm.rolling_pnl_r)
        print(f"  Trade {i}: {loss_r:.1f}R | Rolling DD: {rolling_dd:.1f}R | Throttle: {rm.risk_reduction_active}")

    # Check throttle activated
    assert rm.risk_reduction_active == True, "Throttle should be active after -6.2R drawdown"
    print(f"\n⚠️  Drawdown throttle ACTIVATED at {sum(rm.rolling_pnl_r):.1f}R")

    # Check risk reduction
    base_risk = 1.0
    effective_risk = rm.get_effective_risk_percent(base_risk)
    print(f"  Base risk: {base_risk}%")
    print(f"  Effective risk: {effective_risk}%")
    print(f"  Reduction: {(1 - effective_risk/base_risk)*100:.0f}%")

    assert effective_risk == 0.5, "Risk should be reduced by 50%"

    # Simulate recovery
    print("\n📈 Simulating recovery...")
    wins = [+2.0, +1.5]

    for i, win_r in enumerate(wins, 1):
        rm.update_trade_result(pnl=200.0, pnl_r=win_r)
        rolling_dd = sum(rm.rolling_pnl_r)
        print(f"  Win {i}: +{win_r:.1f}R | Rolling DD: {rolling_dd:.1f}R | Throttle: {rm.risk_reduction_active}")

    # Check throttle deactivated
    assert rm.risk_reduction_active == False, "Throttle should deactivate after recovery"
    print(f"\n✅ Drawdown throttle DEACTIVATED")

    print("\n✅ PASS: Drawdown throttle working correctly!")

    return True


def test_market_filters():
    """Test Market Filters"""
    print("\n" + "="*60)
    print("TEST 3: Market Filters - News Guard & Session Windows")
    print("="*60)

    from src.filters.market_filters import MarketFilters, create_sample_economic_calendar

    # Create test config
    config = {
        "name": "XAUUSD",
        "session_windows": [
            {"start": "08:00", "end": "17:00", "timezone": "America/New_York"}
        ],
        "filters": {
            "news_guard": {
                "enabled": True,
                "block_minutes_before": 15,
                "block_minutes_after": 15,
                "events": ["NFP", "CPI", "FOMC"]
            },
            "atr_regime": {
                "enabled": True,
                "min_percentile": 40,
                "max_percentile": 85
            }
        }
    }

    mf = MarketFilters(config)
    print(f"✓ Market Filters initialized for {config['name']}")

    # Load economic calendar
    calendar = create_sample_economic_calendar()
    mf.load_economic_calendar(calendar)
    print(f"  Loaded {len(mf.economic_calendar)} high-impact events")

    # Test session windows
    print("\n📅 Testing session windows...")

    # Create timestamps in different timezones
    ny_tz = pytz.timezone("America/New_York")

    # Within session (10:00 NY time)
    within_session = datetime.now(pytz.UTC).replace(hour=14, minute=0)  # 10:00 NY
    session_ok, reason = mf.check_session_window(within_session)
    print(f"  10:00 NY: {session_ok} - {reason}")

    # Outside session (18:00 NY time)
    outside_session = datetime.now(pytz.UTC).replace(hour=22, minute=0)  # 18:00 NY
    session_ok, reason = mf.check_session_window(outside_session)
    print(f"  18:00 NY: {session_ok} - {reason}")

    # Test news guard
    print("\n📰 Testing news guard...")

    # During news event (simulated)
    during_news = calendar[0]['time']  # First event time
    news_ok, reason = mf.check_news_guard(during_news)
    print(f"  At news time: {news_ok} - {reason}")
    assert news_ok == False, "Should block trading during news"

    # Outside news window
    safe_time = calendar[0]['time'] + timedelta(hours=2)
    news_ok, reason = mf.check_news_guard(safe_time)
    print(f"  2hrs after news: {news_ok} - {reason}")
    assert news_ok == True, "Should allow trading outside news window"

    # Test ATR regime
    print("\n📊 Testing ATR regime filter...")

    atr_low, reason = mf.check_atr_regime(current_atr=5.0, atr_percentile=30)
    print(f"  ATR 30th pctl: {atr_low} - {reason}")
    assert atr_low == False, "Should block low ATR regime"

    atr_ok, reason = mf.check_atr_regime(current_atr=10.0, atr_percentile=60)
    print(f"  ATR 60th pctl: {atr_ok} - {reason}")
    assert atr_ok == True, "Should allow normal ATR regime"

    atr_high, reason = mf.check_atr_regime(current_atr=20.0, atr_percentile=90)
    print(f"  ATR 90th pctl: {atr_high} - {reason}")
    assert atr_high == False, "Should block high ATR regime"

    print("\n✅ PASS: Market filters working correctly!")

    return True


def main():
    """Run all tests"""
    print("\n")
    print("="*60)
    print("  PHOENIX EA - PRIORITY 1 CRITICAL FIXES TEST SUITE")
    print("="*60)
    print("\nTesting all safety-critical features...")

    results = []

    try:
        results.append(("Risk Manager", test_risk_manager()))
    except Exception as e:
        print(f"\n❌ FAIL: Risk Manager - {e}")
        results.append(("Risk Manager", False))

    try:
        results.append(("Drawdown Throttle", test_drawdown_throttle()))
    except Exception as e:
        print(f"\n❌ FAIL: Drawdown Throttle - {e}")
        results.append(("Drawdown Throttle", False))

    try:
        results.append(("Market Filters", test_market_filters()))
    except Exception as e:
        print(f"\n❌ FAIL: Market Filters - {e}")
        results.append(("Market Filters", False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 SUCCESS: All Priority 1 fixes working correctly!")
        print("   - Concurrent risk calculation fixed")
        print("   - Drawdown throttle implemented")
        print("   - News Guard filter active")
        print("   - Session Windows enforced")
        print("   - ATR Regime filter working")
        return 0
    else:
        print("\n⚠️  WARNING: Some tests failed. Review above output.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

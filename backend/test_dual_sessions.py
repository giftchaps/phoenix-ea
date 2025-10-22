#!/usr/bin/env python3
"""
Test Dual Session Windows (London + New York)
Verifies system can trade during both sessions
"""

import sys
import json
from datetime import datetime, timedelta
import pytz

def test_dual_sessions():
    """Test London and New York session windows"""
    print("\n" + "="*70)
    print("TEST: Dual Session Windows - London + New York")
    print("="*70)

    from src.filters.market_filters import MarketFilters

    # Load actual config
    with open("config/strategy_config.json", "r") as f:
        config = json.load(f)

    xauusd_config = config["symbols"]["XAUUSD"]

    print(f"\n📋 Configuration for {xauusd_config['name']}:")
    print(f"  Session Windows: {len(xauusd_config['session_windows'])}")
    for i, window in enumerate(xauusd_config['session_windows'], 1):
        print(f"    {i}. {window.get('name', 'Unnamed')}: "
              f"{window['start']}-{window['end']} {window['timezone']}")

    # Initialize market filters
    mf = MarketFilters(xauusd_config)

    print(f"\n✓ Market Filters initialized")
    print(f"  - News Guard: {mf.news_guard_enabled}")
    print(f"  - Session Windows: {len(mf.session_windows)}")
    print(f"  - ATR Regime: {mf.atr_regime_enabled}")

    # Test various times across the day
    print("\n📅 Testing trading hours across 24-hour period...")
    print("-" * 70)

    # Create test timestamps in UTC
    test_times = [
        ("Asian Session", "02:00"),      # 02:00 UTC = 10:00 SGT (Asian)
        ("London Open", "08:00"),        # 08:00 UTC = 08:00 London (GMT in winter)
        ("London Mid", "12:00"),         # 12:00 UTC = 12:00 London
        ("London/NY Overlap", "13:00"),  # 13:00 UTC = 13:00 London, 08:00 NY (EST)
        ("NY Mid", "15:00"),             # 15:00 UTC = 15:00 London, 10:00 NY
        ("London Close", "16:00"),       # 16:00 UTC = 16:00 London, 11:00 NY
        ("NY Afternoon", "19:00"),       # 19:00 UTC = closed London, 14:00 NY
        ("NY Close", "22:00"),           # 22:00 UTC = 17:00 NY
        ("After Hours", "23:00"),        # 23:00 UTC = 18:00 NY (closed)
    ]

    today = datetime.now(pytz.UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    results = []

    for period_name, time_str in test_times:
        hour, minute = map(int, time_str.split(":"))
        test_time = today.replace(hour=hour, minute=minute)

        # Check session window
        is_allowed, reason = mf.check_session_window(test_time)

        # Get local times for display
        london_tz = pytz.timezone("Europe/London")
        ny_tz = pytz.timezone("America/New_York")

        london_time = test_time.astimezone(london_tz).strftime("%H:%M")
        ny_time = test_time.astimezone(ny_tz).strftime("%H:%M")

        status = "✅ ALLOWED" if is_allowed else "❌ BLOCKED"

        print(f"{period_name:20} | UTC {time_str} | London {london_time} | NY {ny_time} | {status}")
        print(f"{'':20} | {reason}")
        print("-" * 70)

        results.append((period_name, is_allowed))

    # Verify expected results
    print("\n📊 Verification:")

    expected_allowed = [
        "London Open",
        "London Mid",
        "London/NY Overlap",
        "NY Mid",
        "London Close",
        "NY Afternoon"
    ]

    expected_blocked = [
        "Asian Session",
        "NY Close",
        "After Hours"
    ]

    all_pass = True

    for period_name, is_allowed in results:
        if period_name in expected_allowed:
            if not is_allowed:
                print(f"  ❌ FAIL: {period_name} should be ALLOWED but was BLOCKED")
                all_pass = False
            else:
                print(f"  ✅ PASS: {period_name} correctly ALLOWED")
        elif period_name in expected_blocked:
            if is_allowed:
                print(f"  ❌ FAIL: {period_name} should be BLOCKED but was ALLOWED")
                all_pass = False
            else:
                print(f"  ✅ PASS: {period_name} correctly BLOCKED")

    print("\n" + "="*70)

    if all_pass:
        print("✅ SUCCESS: Dual session windows working correctly!")
        print("\nTrading Hours Summary:")
        print("  - London Session: 08:00-16:00 GMT (8 hours)")
        print("  - New York Session: 08:00-17:00 EST (9 hours)")
        print("  - Overlap Period: 13:00-16:00 GMT / 08:00-11:00 EST (3 hours)")
        print("  - Total Trading Window: ~13 hours per day")
        print("  - Blocked: Asian session, after NY close")
        return True
    else:
        print("❌ FAIL: Some session checks did not work as expected")
        return False


def main():
    """Run the test"""
    print("\n" + "="*70)
    print("  PHOENIX EA - DUAL SESSION WINDOWS TEST")
    print("="*70)
    print("\nVerifying London + New York session configuration...")

    try:
        success = test_dual_sessions()

        if success:
            print("\n🎉 All tests passed! System ready to trade both sessions.")
            return 0
        else:
            print("\n⚠️  Some tests failed. Review output above.")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

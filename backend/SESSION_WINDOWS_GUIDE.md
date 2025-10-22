# Session Windows Configuration Guide

## Overview

Phoenix EA uses **dual session windows** to trade during the most liquid market hours:
- **London Session**: 08:00-16:00 Europe/London (GMT/BST)
- **New York Session**: 08:00-17:00 America/New_York (EST/EDT)

## Why Dual Sessions?

### Benefits
1. **Maximum Liquidity**: Trade during both major forex/gold sessions
2. **Optimal Spreads**: Best pricing during London and NY hours
3. **Multiple Opportunities**: ~13 hours of trading time per day
4. **Overlap Trading**: Catch the 13:00-16:00 GMT overlap (highest volume)

### Avoided Periods
- **Asian Session** (00:00-08:00 GMT): Lower liquidity, wider spreads
- **After Hours** (22:00+ GMT): Thin markets, high slippage

## Trading Hours Breakdown

### London Session (08:00-16:00 GMT)
- **Early Morning** (08:00-12:00): European market opens, good volatility
- **Midday** (12:00-13:00): Pre-overlap period
- **Overlap** (13:00-16:00): NY opens, HIGHEST liquidity

### New York Session (08:00-17:00 EST)
- **Overlap** (08:00-11:00): London still open, HIGHEST liquidity
- **Afternoon** (11:00-16:00): London closed, US market focus
- **Late** (16:00-17:00): Final hour, good for trend continuation

## Time Zone Examples

| UTC Time | London Time | NY Time | Status | Notes |
|----------|-------------|---------|--------|-------|
| 02:00 | 03:00 | 22:00 | ❌ BLOCKED | Asian session |
| 08:00 | 09:00 | 04:00 | ✅ ALLOWED | London open |
| 13:00 | 14:00 | 09:00 | ✅ ALLOWED | **Overlap - Best liquidity** |
| 16:00 | 17:00 | 12:00 | ✅ ALLOWED | London close, NY continues |
| 19:00 | 20:00 | 15:00 | ✅ ALLOWED | NY afternoon |
| 22:00 | 23:00 | 18:00 | ❌ BLOCKED | After hours |

## Configuration

### File: `config/strategy_config.json`

```json
{
  "symbols": {
    "XAUUSD": {
      "session_windows": [
        {
          "start": "08:00",
          "end": "16:00",
          "timezone": "Europe/London",
          "name": "London Session"
        },
        {
          "start": "08:00",
          "end": "17:00",
          "timezone": "America/New_York",
          "name": "New York Session"
        }
      ]
    }
  }
}
```

## Daylight Saving Time (DST)

The system **automatically handles DST** using `pytz`:
- London uses GMT (winter) / BST (summer)
- New York uses EST (winter) / EDT (summer)
- No manual adjustment needed!

### DST Schedule
- **London**: Last Sunday in March → Last Sunday in October (BST)
- **New York**: 2nd Sunday in March → 1st Sunday in November (EDT)

## Customization

### To Add a Session
Add a new window object to the `session_windows` array:

```json
{
  "start": "00:00",
  "end": "08:00",
  "timezone": "Asia/Tokyo",
  "name": "Tokyo Session"
}
```

### To Remove a Session
Delete the unwanted window from the `session_windows` array.

### To Disable Session Filtering
Set `session_windows` to an empty array:

```json
"session_windows": []
```

## Testing

Run the dual session test:

```bash
cd backend
python test_dual_sessions.py
```

Expected output:
```
✅ SUCCESS: Dual session windows working correctly!

Trading Hours Summary:
  - London Session: 08:00-16:00 GMT (8 hours)
  - New York Session: 08:00-17:00 EST (9 hours)
  - Overlap Period: 13:00-16:00 GMT (3 hours)
  - Total Trading Window: ~13 hours per day
```

## Best Practices

### For Gold (XAUUSD)
- ✅ Use both London + NY sessions (configured)
- ✅ Focus on overlap period for highest volume
- ❌ Avoid Asian session (low liquidity)

### For Forex Pairs (EURUSD, GBPUSD)
- ✅ Use both London + NY sessions (configured)
- ✅ Best signals during overlap
- ✅ Good continuation trades in NY afternoon

### For Synthetic Indices
- May trade 24/7 if desired
- Configure `session_windows: []` to disable

## Troubleshooting

### Signal Blocked by Session Filter

**Error Message:**
```
Market filters blocked signal: Session: Outside all session windows
```

**Solution:**
1. Check current time vs configured windows
2. Verify timezone configuration
3. Ensure DST is handled correctly
4. Run `python test_dual_sessions.py` to verify

### Wrong Session Detected

**Issue:** System thinks it's in session when it's not

**Solution:**
1. Verify server timezone is UTC
2. Check `pytz` is installed: `pip install pytz`
3. Verify config timezone strings are valid

## Performance Impact

- **Minimal**: Session check is O(n) where n = number of windows
- **Typical**: 2 windows, <1ms check time
- **Negligible**: No performance degradation

## Summary

✅ **Dual session configuration enables:**
- Trading during peak liquidity hours
- Both European and US market sessions
- Maximum signal opportunities
- Protection from low-liquidity periods

✅ **System automatically:**
- Handles daylight saving time
- Converts timezones correctly
- Blocks off-hours trading
- Logs session status

The system is now configured for **optimal trading hours** across both major sessions!

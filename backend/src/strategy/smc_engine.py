"""
Aurex AI - Enhanced SMC Strategy Engine v2
Liquidity Sweep → BOS/MSS → Order Block → FVG → Demand/Supply Zones
"""

from dataclasses import dataclass
from typing import List, Optional, Literal, Tuple
from datetime import datetime
import numpy as np
import pandas as pd


@dataclass
class SwingPoint:
    """Represents a swing high or low"""
    index: int
    price: float
    swing_type: Literal["high", "low"]
    is_cluster: bool = False  # EQH/EQL
    cluster_count: int = 1


@dataclass
class LiquiditySweep:
    """Detected liquidity sweep event"""
    direction: Literal["bullish", "bearish"]  # Direction of expected reaction
    swept_price: float
    sweep_candle_idx: int
    reentry_idx: int
    is_cluster: bool  # EQH/EQL sweep
    cluster_count: int = 1
    sweep_size_pts: float = 0.0


@dataclass
class Structure:
    """Market structure break"""
    structure_type: Literal["BOS", "MSS"]  # Break of Structure or Market Structure Shift
    direction: Literal["bullish", "bearish"]
    break_candle_idx: int
    broken_level: float
    strength: float  # 0-1 based on close distance past level


@dataclass
class OrderBlock:
    """Order Block zone"""
    direction: Literal["bullish", "bearish"]
    high: float
    low: float
    candle_idx: int
    volume_percentile: float
    has_rejection_wick: bool
    quality_score: float  # 0-1


@dataclass
class FairValueGap:
    """Fair Value Gap (imbalance)"""
    direction: Literal["bullish", "bearish"]
    high: float
    low: float
    midpoint: float
    candle_idx: int
    gap_size_pts: float


@dataclass
class Zone:
    """Demand or Supply zone"""
    zone_type: Literal["demand", "supply"]
    high: float
    low: float
    created_idx: int
    impulse_atr_mult: float
    tested_count: int
    is_fresh: bool
    quality_score: float  # 0-1


@dataclass
class Signal:
    """Trading signal output"""
    symbol: str
    timeframe: str
    side: Literal["LONG", "SHORT"]
    entry: float
    stop_loss: float
    take_profit_1: float  # +1R
    take_profit_2: float  # +2R or liquidity
    take_profit_3: Optional[float]  # Runner to far liquidity
    risk_reward: float
    confidence: float
    posted_at: datetime
    
    # Metadata for explainability
    sweep_type: str  # "single" | "EQH" | "EQL"
    structure_type: str  # "BOS" | "MSS"
    ob_present: bool
    zone_id: Optional[int]
    premium_discount: str  # "premium" | "discount" | "neutral"
    h4_aligned: bool
    h1_bias: str
    atr_percentile: float
    
    # Risk management
    lots: float
    risk_r: float
    partial_plan: dict


class SMCStrategyEngine:
    """
    Enhanced Smart Money Concepts Strategy Engine
    Implements institutional trade identification with multi-layer confluence
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.swing_lookback = config.get("swing_lookback", 2)
        self.sweep_min_pts = config.get("sweep_min_pts", 5)
        self.reentry_max_candles = config.get("reentry_max_candles", 3)
        self.ob_lookback = config.get("ob_lookback", 15)
        self.ob_volume_pctl = config.get("ob_volume_pctl", 60)
        self.zone_lookback = config.get("zone_lookback", 50)
        self.min_impulse_atr = config.get("min_impulse_atr", 2.0)
        self.eqh_eql_tolerance = config.get("eqh_eql_tolerance_pts", 5)
        self.ob_required = config.get("ob_required", True)
        self.premium_discount_filter = config.get("premium_discount_filter", True)
        
    
    def detect_swings(self, bars: pd.DataFrame, lookback: int = None) -> List[SwingPoint]:
        """
        Identify swing highs and lows using pivot detection
        
        Args:
            bars: OHLCV dataframe
            lookback: Number of bars left/right for pivot validation
            
        Returns:
            List of SwingPoint objects
        """
        if lookback is None:
            lookback = self.swing_lookback
            
        swings = []
        highs = bars['high'].values
        lows = bars['low'].values
        
        for i in range(lookback, len(bars) - lookback):
            # Swing High
            if all(highs[i] >= highs[i-j] for j in range(1, lookback+1)) and \
               all(highs[i] > highs[i+j] for j in range(1, lookback+1)):
                swings.append(SwingPoint(
                    index=i,
                    price=highs[i],
                    swing_type="high"
                ))
            
            # Swing Low
            if all(lows[i] <= lows[i-j] for j in range(1, lookback+1)) and \
               all(lows[i] < lows[i+j] for j in range(1, lookback+1)):
                swings.append(SwingPoint(
                    index=i,
                    price=lows[i],
                    swing_type="low"
                ))
        
        return swings
    
    
    def detect_liquidity_clusters(self, swings: List[SwingPoint], 
                                   tolerance_pts: float) -> List[SwingPoint]:
        """
        Identify Equal Highs (EQH) and Equal Lows (EQL)
        
        Args:
            swings: List of swing points
            tolerance_pts: Max price difference to consider "equal"
            
        Returns:
            Updated swings with cluster flags
        """
        highs = [s for s in swings if s.swing_type == "high"]
        lows = [s for s in swings if s.swing_type == "low"]
        
        def mark_clusters(swing_list):
            for i in range(len(swing_list)):
                cluster_count = 1
                for j in range(i+1, min(i+5, len(swing_list))):  # Look ahead 5 swings
                    if abs(swing_list[i].price - swing_list[j].price) <= tolerance_pts:
                        cluster_count += 1
                
                if cluster_count >= 2:
                    swing_list[i].is_cluster = True
                    swing_list[i].cluster_count = cluster_count
        
        mark_clusters(highs)
        mark_clusters(lows)
        
        return swings
    
    
    def detect_sweep(self, bars: pd.DataFrame, swings: List[SwingPoint], 
                     current_idx: int) -> Optional[LiquiditySweep]:
        """
        Detect liquidity sweep: price takes out swing high/low then closes back inside
        
        Args:
            bars: OHLCV dataframe
            swings: Detected swing points
            current_idx: Current bar index
            
        Returns:
            LiquiditySweep object or None
        """
        if current_idx < self.reentry_max_candles:
            return None
        
        current_bar = bars.iloc[current_idx]
        lookback_swings = [s for s in swings if current_idx - 20 <= s.index < current_idx]
        
        # Check for sweep of swing high (bearish sweep)
        swing_highs = [s for s in lookback_swings if s.swing_type == "high"]
        if swing_highs:
            last_swing_high = max(swing_highs, key=lambda x: x.price)
            if current_bar['high'] > last_swing_high.price + self.sweep_min_pts:
                # Check if closed back inside
                prior_range_low = bars.iloc[last_swing_high.index]['low']
                if current_bar['close'] < last_swing_high.price:
                    return LiquiditySweep(
                        direction="bearish",
                        swept_price=last_swing_high.price,
                        sweep_candle_idx=current_idx,
                        reentry_idx=current_idx,
                        is_cluster=last_swing_high.is_cluster,
                        cluster_count=last_swing_high.cluster_count,
                        sweep_size_pts=current_bar['high'] - last_swing_high.price
                    )
        
        # Check for sweep of swing low (bullish sweep)
        swing_lows = [s for s in lookback_swings if s.swing_type == "low"]
        if swing_lows:
            last_swing_low = min(swing_lows, key=lambda x: x.price)
            if current_bar['low'] < last_swing_low.price - self.sweep_min_pts:
                # Check if closed back inside
                prior_range_high = bars.iloc[last_swing_low.index]['high']
                if current_bar['close'] > last_swing_low.price:
                    return LiquiditySweep(
                        direction="bullish",
                        swept_price=last_swing_low.price,
                        sweep_candle_idx=current_idx,
                        reentry_idx=current_idx,
                        is_cluster=last_swing_low.is_cluster,
                        cluster_count=last_swing_low.cluster_count,
                        sweep_size_pts=last_swing_low.price - current_bar['low']
                    )
        
        return None
    
    
    def confirm_structure(self, bars: pd.DataFrame, swings: List[SwingPoint],
                          sweep: LiquiditySweep, current_idx: int) -> Optional[Structure]:
        """
        Confirm BOS (Break of Structure) or MSS (Market Structure Shift)
        
        Args:
            bars: OHLCV dataframe
            swings: Swing points
            sweep: Detected sweep
            current_idx: Current bar index
            
        Returns:
            Structure object or None
        """
        if current_idx <= sweep.sweep_candle_idx:
            return None
        
        recent_swings = [s for s in swings if sweep.sweep_candle_idx - 30 <= s.index < current_idx]
        
        if sweep.direction == "bearish":
            # After bearish sweep, look for break below recent higher-low
            swing_lows = [s for s in recent_swings if s.swing_type == "low"]
            if not swing_lows:
                return None
            
            # Determine if this is BOS or MSS
            # MSS = break against trend (e.g., downward break in uptrend)
            # BOS = break with trend
            last_low = max(swing_lows, key=lambda x: x.index)
            
            for i in range(sweep.sweep_candle_idx + 1, current_idx + 1):
                if bars.iloc[i]['close'] < last_low.price:
                    # Check if this is MSS (reversal) or BOS (continuation)
                    # Simple heuristic: if we're breaking a higher-low, it's likely MSS
                    prior_lows = [s for s in swing_lows if s.index < last_low.index]
                    is_mss = len(prior_lows) > 0 and last_low.price > min(prior_lows, key=lambda x: x.price).price
                    
                    close_distance = abs(bars.iloc[i]['close'] - last_low.price)
                    atr = bars['atr'].iloc[i] if 'atr' in bars else 10
                    strength = min(close_distance / atr, 1.0)
                    
                    return Structure(
                        structure_type="MSS" if is_mss else "BOS",
                        direction="bearish",
                        break_candle_idx=i,
                        broken_level=last_low.price,
                        strength=strength
                    )
        
        else:  # bullish sweep
            # After bullish sweep, look for break above recent lower-high
            swing_highs = [s for s in recent_swings if s.swing_type == "high"]
            if not swing_highs:
                return None
            
            last_high = max(swing_highs, key=lambda x: x.index)
            
            for i in range(sweep.sweep_candle_idx + 1, current_idx + 1):
                if bars.iloc[i]['close'] > last_high.price:
                    prior_highs = [s for s in swing_highs if s.index < last_high.index]
                    is_mss = len(prior_highs) > 0 and last_high.price < max(prior_highs, key=lambda x: x.price).price
                    
                    close_distance = abs(bars.iloc[i]['close'] - last_high.price)
                    atr = bars['atr'].iloc[i] if 'atr' in bars else 10
                    strength = min(close_distance / atr, 1.0)
                    
                    return Structure(
                        structure_type="MSS" if is_mss else "BOS",
                        direction="bullish",
                        break_candle_idx=i,
                        broken_level=last_high.price,
                        strength=strength
                    )
        
        return None
    
    
    def find_order_block(self, bars: pd.DataFrame, direction: str, 
                         current_idx: int) -> Optional[OrderBlock]:
        """
        Identify the last opposing candle before structure break (Order Block)
        
        Args:
            bars: OHLCV dataframe
            direction: "bullish" or "bearish"
            current_idx: Current bar index
            
        Returns:
            OrderBlock object or None
        """
        start_idx = max(0, current_idx - self.ob_lookback)
        
        # Calculate volume percentiles
        volumes = bars['volume'].iloc[start_idx:current_idx+1]
        volume_pctl = lambda v: (volumes < v).sum() / len(volumes) * 100
        
        if direction == "bullish":
            # Find last bearish candle (down-close) before bullish break
            for i in range(current_idx, start_idx, -1):
                bar = bars.iloc[i]
                if bar['close'] < bar['open']:  # Bearish candle
                    v_pctl = volume_pctl(bar['volume'])
                    if v_pctl >= self.ob_volume_pctl:
                        # Check for rejection wick
                        body_size = abs(bar['close'] - bar['open'])
                        lower_wick = bar['open'] - bar['low']
                        has_wick = lower_wick >= body_size * 0.6
                        
                        quality = (v_pctl / 100) * 0.6 + (0.4 if has_wick else 0)
                        
                        return OrderBlock(
                            direction="bullish",
                            high=bar['high'],
                            low=bar['low'],
                            candle_idx=i,
                            volume_percentile=v_pctl,
                            has_rejection_wick=has_wick,
                            quality_score=quality
                        )
        
        else:  # bearish
            # Find last bullish candle before bearish break
            for i in range(current_idx, start_idx, -1):
                bar = bars.iloc[i]
                if bar['close'] > bar['open']:  # Bullish candle
                    v_pctl = volume_pctl(bar['volume'])
                    if v_pctl >= self.ob_volume_pctl:
                        body_size = abs(bar['close'] - bar['open'])
                        upper_wick = bar['high'] - bar['close']
                        has_wick = upper_wick >= body_size * 0.6
                        
                        quality = (v_pctl / 100) * 0.6 + (0.4 if has_wick else 0)
                        
                        return OrderBlock(
                            direction="bearish",
                            high=bar['high'],
                            low=bar['low'],
                            candle_idx=i,
                            volume_percentile=v_pctl,
                            has_rejection_wick=has_wick,
                            quality_score=quality
                        )
        
        return None
    
    
    def find_fvg(self, bars: pd.DataFrame, direction: str, 
                 current_idx: int) -> Optional[FairValueGap]:
        """
        Detect 3-candle Fair Value Gap (imbalance)
        
        Args:
            bars: OHLCV dataframe
            direction: "bullish" or "bearish"
            current_idx: Current bar index
            
        Returns:
            FairValueGap object or None
        """
        if current_idx < 2:
            return None
        
        c1 = bars.iloc[current_idx - 2]
        c2 = bars.iloc[current_idx - 1]
        c3 = bars.iloc[current_idx]
        
        if direction == "bullish":
            # Gap between candle 1 high and candle 3 low
            if c1['high'] < c3['low']:
                gap_size = c3['low'] - c1['high']
                return FairValueGap(
                    direction="bullish",
                    high=c3['low'],
                    low=c1['high'],
                    midpoint=(c3['low'] + c1['high']) / 2,
                    candle_idx=current_idx,
                    gap_size_pts=gap_size
                )
        
        else:  # bearish
            # Gap between candle 1 low and candle 3 high
            if c1['low'] > c3['high']:
                gap_size = c1['low'] - c3['high']
                return FairValueGap(
                    direction="bearish",
                    high=c1['low'],
                    low=c3['high'],
                    midpoint=(c1['low'] + c3['high']) / 2,
                    candle_idx=current_idx,
                    gap_size_pts=gap_size
                )
        
        return None
    
    
    def detect_zones(self, bars: pd.DataFrame, current_idx: int) -> List[Zone]:
        """
        Identify institutional demand/supply zones
        Zones = consolidation before strong impulse
        
        Args:
            bars: OHLCV dataframe
            current_idx: Current bar index
            
        Returns:
            List of Zone objects
        """
        zones = []
        start_idx = max(0, current_idx - self.zone_lookback)
        
        # Calculate ATR for impulse detection
        atr_values = bars['atr'].values if 'atr' in bars else np.ones(len(bars)) * 10
        
        for i in range(start_idx, current_idx - 5):
            # Look for impulse move (strong directional move)
            impulse_bars = bars.iloc[i:i+5]
            price_move = impulse_bars['close'].iloc[-1] - impulse_bars['close'].iloc[0]
            atr_at_start = atr_values[i]
            
            if abs(price_move) >= self.min_impulse_atr * atr_at_start:
                # Found impulse, now identify the consolidation zone before it
                zone_start = max(0, i - 8)
                zone_bars = bars.iloc[zone_start:i]
                
                zone_high = zone_bars['high'].max()
                zone_low = zone_bars['low'].min()
                
                # Check if zone has been tested since creation
                tested_count = 0
                is_fresh = True
                for j in range(i+5, current_idx):
                    if bars.iloc[j]['low'] <= zone_high and bars.iloc[j]['high'] >= zone_low:
                        tested_count += 1
                        is_fresh = False
                
                zone_type = "demand" if price_move > 0 else "supply"
                impulse_mult = abs(price_move) / atr_at_start
                quality = min(impulse_mult / 3.0, 1.0) * (1.0 if is_fresh else 0.6)
                
                zones.append(Zone(
                    zone_type=zone_type,
                    high=zone_high,
                    low=zone_low,
                    created_idx=i,
                    impulse_atr_mult=impulse_mult,
                    tested_count=tested_count,
                    is_fresh=is_fresh,
                    quality_score=quality
                ))
        
        return zones
    
    
    def calculate_premium_discount(self, bars: pd.DataFrame, swings: List[SwingPoint],
                                    entry_price: float, direction: str) -> str:
        """
        Determine if entry is at premium (upper 50%) or discount (lower 50%)
        
        Args:
            bars: OHLCV dataframe
            swings: Swing points
            entry_price: Proposed entry price
            direction: "bullish" or "bearish"
            
        Returns:
            "premium", "discount", or "neutral"
        """
        if not swings or len(swings) < 2:
            return "neutral"
        
        # Get last major swing range
        recent_swings = sorted(swings[-10:], key=lambda x: x.index)
        highs = [s.price for s in recent_swings if s.swing_type == "high"]
        lows = [s.price for s in recent_swings if s.swing_type == "low"]
        
        if not highs or not lows:
            return "neutral"
        
        range_high = max(highs)
        range_low = min(lows)
        midpoint = (range_high + range_low) / 2
        
        if direction == "bullish":
            # Want to buy at discount (lower 50%)
            if entry_price <= midpoint:
                return "discount"
            else:
                return "premium"
        else:  # bearish
            # Want to sell at premium (upper 50%)
            if entry_price >= midpoint:
                return "premium"
            else:
                return "discount"
    
    
    def calculate_confidence(self, sweep: LiquiditySweep, structure: Structure,
                            ob: Optional[OrderBlock], fvg: FairValueGap,
                            zones: List[Zone], premium_discount: str,
                            h4_aligned: bool, h1_aligned: bool) -> float:
        """
        Calculate overall signal confidence score (0-1)
        
        Confidence formula:
        Base: 0.50
        + Structure type (MSS: +0.12, BOS: +0.05)
        + OB present & overlaps FVG: +0.10
        + Fresh zone aligned: +0.15
        + EQH/EQL sweep: +0.20 (else +0.08)
        + H4 aligned: +0.20
        + H1 aligned: +0.10
        - Wrong premium/discount: -0.15
        - Multi-tested zone: -0.10
        """
        confidence = 0.50
        
        # Structure bonus
        if structure.structure_type == "MSS":
            confidence += 0.12
        else:
            confidence += 0.05
        
        # Order Block confluence
        if ob:
            if fvg.low <= ob.high and fvg.high >= ob.low:  # Overlap check
                confidence += 0.10 * ob.quality_score
        
        # Zone alignment
        aligned_zones = [z for z in zones if z.is_fresh and 
                        fvg.low <= z.high and fvg.high >= z.low]
        if aligned_zones:
            best_zone = max(aligned_zones, key=lambda x: x.quality_score)
            confidence += 0.15 * best_zone.quality_score
        
        # Liquidity cluster bonus
        if sweep.is_cluster:
            confidence += 0.20
        else:
            confidence += 0.08
        
        # Multi-timeframe alignment
        if h4_aligned:
            confidence += 0.20
        if h1_aligned:
            confidence += 0.10
        
        # Premium/discount penalty
        correct_position = (structure.direction == "bullish" and premium_discount == "discount") or \
                          (structure.direction == "bearish" and premium_discount == "premium")
        if not correct_position and premium_discount != "neutral":
            confidence -= 0.15
        
        # Multi-tested zone penalty
        tested_zones = [z for z in zones if not z.is_fresh and z.tested_count > 1]
        if tested_zones:
            confidence -= 0.10
        
        return max(0.0, min(1.0, confidence))
    
    
    def generate_signal(self, symbol: str, timeframe: str, bars: pd.DataFrame,
                       h4_bias: str, h1_bias: str, account_balance: float,
                       risk_pct: float) -> Optional[Signal]:
        """
        Main signal generation logic - orchestrates all detection steps
        
        Args:
            symbol: Trading symbol
            timeframe: Signal timeframe (e.g., "M15")
            bars: OHLCV dataframe with 'atr' column
            h4_bias: H4 structure bias ("bullish"/"bearish"/"neutral")
            h1_bias: H1 structure bias
            account_balance: Account size for position sizing
            risk_pct: Risk percentage per trade
            
        Returns:
            Signal object or None
        """
        current_idx = len(bars) - 1
        
        # Step 1: Detect swings
        swings = self.detect_swings(bars)
        swings = self.detect_liquidity_clusters(swings, self.eqh_eql_tolerance)
        
        # Step 2: Detect sweep
        sweep = self.detect_sweep(bars, swings, current_idx)
        if not sweep:
            return None
        
        # Step 3: Confirm structure (BOS/MSS)
        structure = self.confirm_structure(bars, swings, sweep, current_idx)
        if not structure:
            return None
        
        # Check H1 alignment
        if structure.direction != h1_bias.lower():
            return None
        
        # Step 4: Find Order Block
        ob = self.find_order_block(bars, structure.direction, structure.break_candle_idx)
        if self.ob_required and not ob:
            return None
        
        # Step 5: Find FVG
        fvg = self.find_fvg(bars, structure.direction, current_idx)
        if not fvg:
            return None
        
        # Check OB-FVG overlap if OB required
        if self.ob_required and ob:
            if not (fvg.low <= ob.high and fvg.high >= ob.low):
                return None
        
        # Step 6: Detect zones
        zones = self.detect_zones(bars, current_idx)
        
        # Step 7: Premium/discount check
        premium_discount = self.calculate_premium_discount(bars, swings, fvg.midpoint, structure.direction)
        if self.premium_discount_filter:
            correct_position = (structure.direction == "bullish" and premium_discount == "discount") or \
                              (structure.direction == "bearish" and premium_discount == "premium")
            if not correct_position and premium_discount != "neutral":
                return None
        
        # Step 8: Calculate confidence
        h4_aligned = h4_bias.lower() == structure.direction
        h1_aligned = h1_bias.lower() == structure.direction
        
        confidence = self.calculate_confidence(
            sweep, structure, ob, fvg, zones, premium_discount,
            h4_aligned, h1_aligned
        )
        
        min_confidence = self.config.get("min_confidence", 0.65)
        if confidence < min_confidence:
            return None
        
        # Step 9: Calculate entry, SL, TP
        entry = fvg.midpoint
        atr = bars['atr'].iloc[-1]
        atr_mult = self.config.get("atr_mult", 2.0)
        sl_buffer = self.config.get("sl_buffer_pts", 2)
        
        if structure.direction == "bullish":
            sl_distance = entry - (sweep.swept_price - sl_buffer)
            sl_atr = atr * atr_mult
            stop_loss = entry - max(sl_distance, sl_atr)
        else:
            sl_distance = (sweep.swept_price + sl_buffer) - entry
            sl_atr = atr * atr_mult
            stop_loss = entry + max(sl_distance, sl_atr)
        
        # TP levels
        r_distance = abs(entry - stop_loss)
        sign = 1 if structure.direction == "bullish" else -1
        
        tp1 = entry + sign * r_distance  # +1R
        tp2 = entry + sign * 2 * r_distance  # +2R
        
        # TP3: Opposing liquidity (optional runner)
        opposing_swings = [s for s in swings if s.swing_type == ("low" if structure.direction == "bearish" else "high")]
        if opposing_swings:
            nearest_liquidity = min(opposing_swings, key=lambda s: abs(s.price - entry))
            if abs(nearest_liquidity.price - entry) > 2.5 * r_distance:
                tp3 = nearest_liquidity.price
            else:
                tp3 = None
        else:
            tp3 = None
        
        # Position sizing
        risk_dollars = account_balance * (risk_pct / 100)
        tick_value = self.config.get("tick_value", 1.0)
        pip_size = self.config.get("pip_size", 0.0001)
        sl_pips = abs(entry - stop_loss) / pip_size
        
        lots = risk_dollars / (sl_pips * tick_value)
        lots = max(self.config.get("min_lot", 0.01), 
                  min(lots, self.config.get("max_lot", 100.0)))
        
        # Partial plan
        partial_plan = {
            "tp1": {"level": tp1, "close_pct": 0.5, "move_sl_to_be": True},
            "tp2": {"level": tp2, "close_pct": 0.3, "trail": True},
        }
        if tp3:
            partial_plan["tp3"] = {"level": tp3, "close_pct": 0.2, "trail": True}
        
        # Get ATR percentile
        atr_values = bars['atr'].iloc[-50:]
        atr_pctl = (atr_values < atr).sum() / len(atr_values) * 100
        
        # Find aligned zone ID
        aligned_zones = [z for z in zones if fvg.low <= z.high and fvg.high >= z.low]
        zone_id = aligned_zones[0].created_idx if aligned_zones else None
        
        return Signal(
            symbol=symbol,
            timeframe=timeframe,
            side="LONG" if structure.direction == "bullish" else "SHORT",
            entry=entry,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            risk_reward=2.0,
            confidence=confidence,
            posted_at=datetime.now(),
            sweep_type="EQH" if sweep.is_cluster and structure.direction == "bearish" else 
                       "EQL" if sweep.is_cluster else "single",
            structure_type=structure.structure_type,
            ob_present=ob is not None,
            zone_id=zone_id,
            premium_discount=premium_discount,
            h4_aligned=h4_aligned,
            h1_bias=h1_bias,
            atr_percentile=atr_pctl,
            lots=lots,
            risk_r=1.0,
            partial_plan=partial_plan
        )


# Example usage
if __name__ == "__main__":
    # Configuration
    config = {
        "swing_lookback": 2,
        "sweep_min_pts": 5,
        "reentry_max_candles": 3,
        "ob_lookback": 15,
        "ob_volume_pctl": 60,
        "zone_lookback": 50,
        "min_impulse_atr": 2.0,
        "eqh_eql_tolerance_pts": 5,
        "ob_required": True,
        "premium_discount_filter": True,
        "min_confidence": 0.65,
        "atr_mult": 2.0,
        "sl_buffer_pts": 2,
        "tick_value": 1.0,
        "pip_size": 0.0001,
        "min_lot": 0.01,
        "max_lot": 10.0
    }
    
    # Initialize engine
    engine = SMCStrategyEngine(config)
    
    # Example: Generate signal
    # bars_df = load_bars("XAUUSD", "M15")  # Your data loading function
    # signal = engine.generate_signal(
    #     symbol="XAUUSD",
    #     timeframe="M15",
    #     bars=bars_df,
    #     h4_bias="bullish",
    #     h1_bias="bullish",
    #     account_balance=10000,
    #     risk_pct=1.0
    # )
    # 
    # if signal:
    #     print(f"Signal generated: {signal.side} @ {signal.entry}")
    #     print(f"Confidence: {signal.confidence:.2f}")
    #     print(f"Structure: {signal.structure_type}")
    
    print("SMC Strategy Engine v2 initialized successfully")


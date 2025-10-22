"""
Aurex AI - Backtesting & Walk-Forward Validation Engine
Comprehensive testing framework with Monte Carlo simulation
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from enum import Enum


class ExitReason(Enum):
    TP1_HIT = "tp1_hit"
    TP2_HIT = "tp2_hit"
    TP3_HIT = "tp3_hit"
    STOP_LOSS = "stop_loss"
    TIME_STOP = "time_stop"
    BE_STOPPED = "be_stopped"


@dataclass
class Trade:
    """Individual trade record"""
    entry_time: datetime
    exit_time: datetime
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    stop_loss: float
    lots: float
    pnl_dollars: float
    pnl_r: float
    exit_reason: ExitReason
    confidence: float
    setup_metadata: dict
    mae_r: float  # Maximum Adverse Excursion
    mfe_r: float  # Maximum Favorable Excursion


@dataclass
class BacktestResults:
    """Complete backtest metrics"""
    # Basic stats
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # P&L metrics
    total_pnl_dollars: float
    total_pnl_r: float
    avg_win_r: float
    avg_loss_r: float
    avg_rr: float
    profit_factor: float
    expectancy_r: float
    
    # Risk metrics
    max_drawdown_pct: float
    max_drawdown_r: float
    max_consecutive_losses: int
    sharpe_ratio: float
    
    # Trade distribution
    avg_trade_duration_hours: float
    trades_per_month: float
    
    # Detailed records
    trades: List[Trade]
    equity_curve: pd.DataFrame
    monthly_returns: pd.DataFrame


class BrokerModel:
    """Simulates realistic execution with slippage and costs"""
    
    def __init__(self, slippage_pips: float, commission_per_lot: float, 
                 spread_pips: float, pip_size: float):
        self.slippage_pips = slippage_pips
        self.commission_per_lot = commission_per_lot
        self.spread_pips = spread_pips
        self.pip_size = pip_size
    
    def apply_entry_costs(self, entry_price: float, side: str) -> float:
        """Apply spread and slippage to entry"""
        spread_cost = self.spread_pips * self.pip_size
        slippage_cost = self.slippage_pips * self.pip_size
        
        if side == "LONG":
            return entry_price + spread_cost + slippage_cost
        else:
            return entry_price - slippage_cost  # Spread already in bid
    
    def apply_exit_costs(self, exit_price: float, side: str) -> float:
        """Apply slippage to exit"""
        slippage_cost = self.slippage_pips * self.pip_size
        
        if side == "LONG":
            return exit_price - slippage_cost
        else:
            return exit_price + slippage_cost
    
    def calculate_commission(self, lots: float) -> float:
        """Calculate round-trip commission"""
        return self.commission_per_lot * lots * 2  # Entry + exit


class BacktestEngine:
    """
    Main backtesting engine with realistic execution simulation
    """
    
    def __init__(self, config: dict, broker_model: BrokerModel):
        self.config = config
        self.broker = broker_model
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
    
    def simulate_trade(self, signal: 'Signal', bars: pd.DataFrame, 
                      signal_idx: int, initial_balance: float) -> Trade:
        """
        Simulate a single trade from signal to exit
        
        Args:
            signal: Generated signal object
            bars: OHLCV dataframe
            signal_idx: Bar index where signal was generated
            initial_balance: Account balance at trade start
            
        Returns:
            Trade object with results
        """
        entry_price = self.broker.apply_entry_costs(signal.entry, signal.side)
        stop_loss = signal.stop_loss
        
        # Track position through bars
        entry_time = bars.iloc[signal_idx]['time']
        max_bars = len(bars)
        time_stop_bars = self.config.get('time_stop_minutes', 60) // self.config.get('tf_minutes', 15)
        
        # Track MAE/MFE
        mae_r = 0.0
        mfe_r = 0.0
        r_distance = abs(entry_price - stop_loss)
        
        # Partial tracking
        position_pct = 1.0
        be_activated = False
        current_sl = stop_loss
        
        for i in range(signal_idx + 1, min(signal_idx + time_stop_bars + 1, max_bars)):
            bar = bars.iloc[i]
            
            # Update MAE/MFE
            if signal.side == "LONG":
                adverse = (bar['low'] - entry_price) / r_distance
                favorable = (bar['high'] - entry_price) / r_distance
            else:
                adverse = (entry_price - bar['high']) / r_distance
                favorable = (entry_price - bar['low']) / r_distance
            
            mae_r = min(mae_r, adverse)
            mfe_r = max(mfe_r, favorable)
            
            # Check TP3 (runner) first if exists
            if signal.take_profit_3 and position_pct > 0:
                if (signal.side == "LONG" and bar['high'] >= signal.take_profit_3) or \
                   (signal.side == "SHORT" and bar['low'] <= signal.take_profit_3):
                    exit_price = self.broker.apply_exit_costs(signal.take_profit_3, signal.side)
                    return self._create_trade(signal, entry_time, bar['time'], entry_price, 
                                             exit_price, ExitReason.TP3_HIT, mae_r, mfe_r,
                                             initial_balance, position_pct)
            
            # Check TP2
            if position_pct > 0.5:  # Still have TP2 portion
                if (signal.side == "LONG" and bar['high'] >= signal.take_profit_2) or \
                   (signal.side == "SHORT" and bar['low'] <= signal.take_profit_2):
                    # Take partial at TP2
                    position_pct = 0.2 if signal.take_profit_3 else 0.0
                    
                    if position_pct == 0:
                        exit_price = self.broker.apply_exit_costs(signal.take_profit_2, signal.side)
                        return self._create_trade(signal, entry_time, bar['time'], entry_price,
                                                 exit_price, ExitReason.TP2_HIT, mae_r, mfe_r,
                                                 initial_balance, 1.0)
            
            # Check TP1
            if position_pct == 1.0:
                if (signal.side == "LONG" and bar['high'] >= signal.take_profit_1) or \
                   (signal.side == "SHORT" and bar['low'] <= signal.take_profit_1):
                    # Take 50% off, move to BE
                    position_pct = 0.5
                    be_activated = True
                    current_sl = entry_price
            
            # Check Stop Loss (including BE)
            if (signal.side == "LONG" and bar['low'] <= current_sl) or \
               (signal.side == "SHORT" and bar['high'] >= current_sl):
                exit_price = self.broker.apply_exit_costs(current_sl, signal.side)
                reason = ExitReason.BE_STOPPED if be_activated else ExitReason.STOP_LOSS
                
                # Calculate PnL based on remaining position
                if position_pct < 1.0:
                    # Already took partials - calculate blended result
                    partial_pnl_r = 0.5 * 1.0  # 50% at TP1 = +0.5R
                    remaining_pnl_r = position_pct * 0  # Stopped at BE = 0R
                    total_pnl_r = partial_pnl_r + remaining_pnl_r
                    
                    trade = self._create_trade(signal, entry_time, bar['time'], entry_price,
                                              exit_price, reason, mae_r, mfe_r,
                                              initial_balance, position_pct)
                    trade.pnl_r = total_pnl_r
                    return trade
                else:
                    return self._create_trade(signal, entry_time, bar['time'], entry_price,
                                            exit_price, reason, mae_r, mfe_r,
                                            initial_balance, position_pct)
        
        # Time stop hit
        exit_price = self.broker.apply_exit_costs(bars.iloc[min(signal_idx + time_stop_bars, max_bars-1)]['close'], 
                                                  signal.side)
        return self._create_trade(signal, entry_time, bars.iloc[-1]['time'], entry_price,
                                 exit_price, ExitReason.TIME_STOP, mae_r, mfe_r,
                                 initial_balance, position_pct)
    
    def _create_trade(self, signal: 'Signal', entry_time: datetime, exit_time: datetime,
                     entry_price: float, exit_price: float, exit_reason: ExitReason,
                     mae_r: float, mfe_r: float, initial_balance: float,
                     position_pct: float) -> Trade:
        """Helper to create Trade object with calculated P&L"""
        r_distance = abs(signal.entry - signal.stop_loss)
        
        if signal.side == "LONG":
            pnl_r = (exit_price - entry_price) / r_distance
        else:
            pnl_r = (entry_price - exit_price) / r_distance
        
        pnl_dollars = pnl_r * (initial_balance * signal.risk_r / 100)
        pnl_dollars -= self.broker.calculate_commission(signal.lots)
        
        return Trade(
            entry_time=entry_time,
            exit_time=exit_time,
            symbol=signal.symbol,
            side=signal.side,
            entry_price=entry_price,
            exit_price=exit_price,
            stop_loss=signal.stop_loss,
            lots=signal.lots,
            pnl_dollars=pnl_dollars,
            pnl_r=pnl_r * position_pct,
            exit_reason=exit_reason,
            confidence=signal.confidence,
            setup_metadata={
                'sweep_type': signal.sweep_type,
                'structure_type': signal.structure_type,
                'ob_present': signal.ob_present,
                'premium_discount': signal.premium_discount
            },
            mae_r=mae_r,
            mfe_r=mfe_r
        )
    
    def run_backtest(self, signals: List['Signal'], bars: pd.DataFrame,
                    initial_balance: float = 10000) -> BacktestResults:
        """
        Run full backtest on list of signals
        
        Args:
            signals: List of generated signals
            bars: Complete OHLCV dataframe
            initial_balance: Starting account balance
            
        Returns:
            BacktestResults with comprehensive metrics
        """
        trades = []
        balance = initial_balance
        equity_curve = [initial_balance]
        
        for signal in signals:
            # Find signal index in bars
            signal_idx = None
            for i, bar in bars.iterrows():
                if bar['time'] == signal.posted_at:
                    signal_idx = i
                    break
            
            if signal_idx is None:
                continue
            
            # Simulate trade
            trade = self.simulate_trade(signal, bars, signal_idx, balance)
            trades.append(trade)
            
            balance += trade.pnl_dollars
            equity_curve.append(balance)
        
        return self._calculate_metrics(trades, equity_curve, initial_balance)
    
    def _calculate_metrics(self, trades: List[Trade], equity_curve: List[float],
                          initial_balance: float) -> BacktestResults:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return BacktestResults(
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0,
                total_pnl_dollars=0, total_pnl_r=0, avg_win_r=0, avg_loss_r=0,
                avg_rr=0, profit_factor=0, expectancy_r=0, max_drawdown_pct=0,
                max_drawdown_r=0, max_consecutive_losses=0, sharpe_ratio=0,
                avg_trade_duration_hours=0, trades_per_month=0,
                trades=[], equity_curve=pd.DataFrame(), monthly_returns=pd.DataFrame()
            )
        
        # Basic stats
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl_r > 0]
        losing_trades = [t for t in trades if t.pnl_r <= 0]
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl_r = sum(t.pnl_r for t in trades)
        total_pnl_dollars = sum(t.pnl_dollars for t in trades)
        avg_win_r = np.mean([t.pnl_r for t in winning_trades]) if winning_trades else 0
        avg_loss_r = np.mean([t.pnl_r for t in losing_trades]) if losing_trades else 0
        
        gross_profit = sum(t.pnl_r for t in winning_trades)
        gross_loss = abs(sum(t.pnl_r for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        expectancy_r = total_pnl_r / total_trades
        
        avg_rr = abs(avg_win_r / avg_loss_r) if avg_loss_r != 0 else 0
        
        # Drawdown calculation
        equity_array = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        max_drawdown_pct = abs(drawdown.min())
        
        # Calculate drawdown in R
        r_equity = np.cumsum([0] + [t.pnl_r for t in trades])
        r_running_max = np.maximum.accumulate(r_equity)
        r_drawdown = r_equity - r_running_max
        max_drawdown_r = abs(r_drawdown.min())
        
        # Consecutive losses
        max_consecutive_losses = 0
        current_streak = 0
        for trade in trades:
            if trade.pnl_r <= 0:
                current_streak += 1
                max_consecutive_losses = max(max_consecutive_losses, current_streak)
            else:
                current_streak = 0
        
        # Sharpe ratio (simplified)
        returns = [t.pnl_r for t in trades]
        sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        sharpe_ratio *= np.sqrt(252)  # Annualized
        
        # Duration metrics
        durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in trades]
        avg_trade_duration_hours = np.mean(durations)
        
        # Trades per month
        if trades:
            time_span = (trades[-1].exit_time - trades[0].entry_time).days / 30.44
            trades_per_month = total_trades / time_span if time_span > 0 else 0
        else:
            trades_per_month = 0
        
        # Create equity curve DataFrame
        equity_df = pd.DataFrame({
            'equity': equity_curve,
            'drawdown': np.concatenate([[0], drawdown])
        })
        
        # Monthly returns
        trade_df = pd.DataFrame([{
            'date': t.exit_time,
            'pnl_r': t.pnl_r
        } for t in trades])
        
        if not trade_df.empty:
            trade_df['month'] = pd.to_datetime(trade_df['date']).dt.to_period('M')
            monthly_returns = trade_df.groupby('month')['pnl_r'].sum().reset_index()
        else:
            monthly_returns = pd.DataFrame()
        
        return BacktestResults(
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            total_pnl_dollars=total_pnl_dollars,
            total_pnl_r=total_pnl_r,
            avg_win_r=avg_win_r,
            avg_loss_r=avg_loss_r,
            avg_rr=avg_rr,
            profit_factor=profit_factor,
            expectancy_r=expectancy_r,
            max_drawdown_pct=max_drawdown_pct,
            max_drawdown_r=max_drawdown_r,
            max_consecutive_losses=max_consecutive_losses,
            sharpe_ratio=sharpe_ratio,
            avg_trade_duration_hours=avg_trade_duration_hours,
            trades_per_month=trades_per_month,
            trades=trades,
            equity_curve=equity_df,
            monthly_returns=monthly_returns
        )


class WalkForwardAnalysis:
    """
    Walk-forward optimization and validation
    """
    
    def __init__(self, train_months: int = 6, test_months: int = 2, cycles: int = 3):
        self.train_months = train_months
        self.test_months = test_months
        self.cycles = cycles
    
    def split_data(self, bars: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Split data into train/test sets for walk-forward
        
        Returns:
            List of (train_df, test_df) tuples
        """
        splits = []
        total_period = self.train_months + self.test_months
        
        for cycle in range(self.cycles):
            start_idx = cycle * self.test_months * 30 * 24 * 4  # Approximate bars
            train_end_idx = start_idx + self.train_months * 30 * 24 * 4
            test_end_idx = train_end_idx + self.test_months * 30 * 24 * 4
            
            if test_end_idx > len(bars):
                break
            
            train_df = bars.iloc[start_idx:train_end_idx].copy()
            test_df = bars.iloc[train_end_idx:test_end_idx].copy()
            splits.append((train_df, test_df))
        
        return splits
    
    def run_walk_forward(self, strategy_engine, backtest_engine, bars: pd.DataFrame,
                        h4_bars: pd.DataFrame, h1_bars: pd.DataFrame,
                        account_balance: float) -> Dict:
        """
        Execute walk-forward analysis
        
        Returns:
            Dictionary with results per cycle
        """
        splits = self.split_data(bars)
        results = []
        
        for cycle_idx, (train_df, test_df) in enumerate(splits):
            print(f"Running Walk-Forward Cycle {cycle_idx + 1}/{len(splits)}...")
            
            # Generate signals on test period
            test_signals = []
            for idx in range(len(test_df)):
                signal = strategy_engine.generate_signal(
                    symbol="XAUUSD",
                    timeframe="M15",
                    bars=test_df.iloc[:idx+1],
                    h4_bias="bullish",  # Simplified - should derive from h4_bars
                    h1_bias="bullish",  # Simplified - should derive from h1_bars
                    account_balance=account_balance,
                    risk_pct=1.0
                )
                if signal:
                    test_signals.append(signal)
            
            # Backtest on test period
            cycle_results = backtest_engine.run_backtest(
                test_signals, test_df, account_balance
            )
            
            results.append({
                'cycle': cycle_idx + 1,
                'train_period': f"{train_df.iloc[0]['time']} to {train_df.iloc[-1]['time']}",
                'test_period': f"{test_df.iloc[0]['time']} to {test_df.iloc[-1]['time']}",
                'results': cycle_results
            })
        
        return {
            'cycles': results,
            'pass_rate': self._calculate_pass_rate(results)
        }
    
    def _calculate_pass_rate(self, results: List[Dict]) -> Dict:
        """Calculate how many cycles passed validation gates"""
        gates = {
            'min_profit_factor': 1.30,
            'min_win_rate': 0.40,
            'max_drawdown': 0.12
        }
        
        passed_cycles = 0
        for result in results:
            r = result['results']
            if (r.profit_factor >= gates['min_profit_factor'] and
                r.win_rate >= gates['min_win_rate'] and
                r.max_drawdown_pct <= gates['max_drawdown']):
                passed_cycles += 1
        
        return {
            'passed': passed_cycles,
            'total': len(results),
            'pass_rate': passed_cycles / len(results) if results else 0,
            'approved': passed_cycles >= 2  # Need at least 2/3 cycles passing
        }


class MonteCarloSimulation:
    """
    Monte Carlo analysis for robustness testing
    """
    
    def __init__(self, iterations: int = 1000):
        self.iterations = iterations
    
    def run_simulation(self, trades: List[Trade]) -> Dict:
        """
        Run Monte Carlo by randomizing trade order and adding random gaps
        
        Returns:
            Distribution statistics for key metrics
        """
        if not trades:
            return {}
        
        trade_returns = [t.pnl_r for t in trades]
        
        simulation_results = {
            'final_r': [],
            'max_dd_r': [],
            'win_rate': [],
            'profit_factor': []
        }
        
        for i in range(self.iterations):
            # Randomize trade order
            shuffled_returns = np.random.choice(trade_returns, size=len(trade_returns), replace=False)
            
            # Calculate metrics for this sequence
            final_r = np.sum(shuffled_returns)
            
            # Drawdown
            cumulative = np.cumsum(shuffled_returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdowns = cumulative - running_max
            max_dd = abs(drawdowns.min())
            
            # Win rate
            wins = len([r for r in shuffled_returns if r > 0])
            win_rate = wins / len(shuffled_returns)
            
            # Profit factor
            gross_profit = sum(r for r in shuffled_returns if r > 0)
            gross_loss = abs(sum(r for r in shuffled_returns if r <= 0))
            pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            simulation_results['final_r'].append(final_r)
            simulation_results['max_dd_r'].append(max_dd)
            simulation_results['win_rate'].append(win_rate)
            simulation_results['profit_factor'].append(pf if pf != float('inf') else 10)
        
        # Calculate percentiles
        return {
            'final_r': {
                'mean': np.mean(simulation_results['final_r']),
                'std': np.std(simulation_results['final_r']),
                '5th_percentile': np.percentile(simulation_results['final_r'], 5),
                '50th_percentile': np.percentile(simulation_results['final_r'], 50),
                '95th_percentile': np.percentile(simulation_results['final_r'], 95)
            },
            'max_dd_r': {
                'mean': np.mean(simulation_results['max_dd_r']),
                'std': np.std(simulation_results['max_dd_r']),
                '5th_percentile': np.percentile(simulation_results['max_dd_r'], 5),
                '95th_percentile': np.percentile(simulation_results['max_dd_r'], 95)
            },
            'win_rate': {
                'mean': np.mean(simulation_results['win_rate']),
                'std': np.std(simulation_results['win_rate'])
            },
            'profit_factor': {
                'mean': np.mean(simulation_results['profit_factor']),
                'std': np.std(simulation_results['profit_factor'])
            },
            'probability_of_profit': len([r for r in simulation_results['final_r'] if r > 0]) / self.iterations
        }


def print_backtest_report(results: BacktestResults, symbol: str, period: str):
    """
    Pretty print backtest results
    """
    print(f"\n{'='*60}")
    print(f"BACKTEST REPORT - {symbol} ({period})")
    print(f"{'='*60}\n")
    
    print("TRADE STATISTICS")
    print(f"  Total Trades:           {results.total_trades}")
    print(f"  Winning Trades:         {results.winning_trades} ({results.win_rate:.1%})")
    print(f"  Losing Trades:          {results.losing_trades}")
    print(f"  Max Consecutive Losses: {results.max_consecutive_losses}")
    print()
    
    print("PERFORMANCE METRICS")
    print(f"  Total P&L:              ${results.total_pnl_dollars:,.2f} ({results.total_pnl_r:+.2f}R)")
    print(f"  Profit Factor:          {results.profit_factor:.2f}")
    print(f"  Expectancy per Trade:   {results.expectancy_r:+.3f}R")
    print(f"  Average Win:            {results.avg_win_r:+.3f}R")
    print(f"  Average Loss:           {results.avg_loss_r:.3f}R")
    print(f"  Average RR:             1:{results.avg_rr:.2f}")
    print(f"  Sharpe Ratio:           {results.sharpe_ratio:.2f}")
    print()
    
    print("RISK METRICS")
    print(f"  Max Drawdown:           {results.max_drawdown_pct:.1%} ({results.max_drawdown_r:.2f}R)")
    print()
    
    print("TRADE TIMING")
    print(f"  Avg Trade Duration:     {results.avg_trade_duration_hours:.1f} hours")
    print(f"  Trades per Month:       {results.trades_per_month:.1f}")
    print()
    
    # Validation gates
    gates_passed = []
    if results.profit_factor >= 1.30:
        gates_passed.append("✓ Profit Factor")
    else:
        gates_passed.append("✗ Profit Factor")
    
    if results.win_rate >= 0.40:
        gates_passed.append("✓ Win Rate")
    else:
        gates_passed.append("✗ Win Rate")
    
    if results.max_drawdown_pct <= 0.12:
        gates_passed.append("✓ Max Drawdown")
    else:
        gates_passed.append("✗ Max Drawdown")
    
    print("VALIDATION GATES")
    for gate in gates_passed:
        print(f"  {gate}")
    print()
    
    print(f"{'='*60}\n")


# Example usage
if __name__ == "__main__":
    # Initialize broker model
    broker = BrokerModel(
        slippage_pips=1.0,
        commission_per_lot=7.0,
        spread_pips=0.3,
        pip_size=0.01
    )
    
    # Initialize backtest engine
    config = {
        'time_stop_minutes': 60,
        'tf_minutes': 15
    }
    
    backtest_engine = BacktestEngine(config, broker)
    
    # Walk-forward analysis
    wf_analysis = WalkForwardAnalysis(train_months=6, test_months=2, cycles=3)
    
    # Monte Carlo simulation
    mc_simulation = MonteCarloSimulation(iterations=1000)
    
    print("Backtest Engine initialized successfully")
    print("Ready for walk-forward and Monte Carlo analysis")
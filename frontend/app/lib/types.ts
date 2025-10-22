// TypeScript type definitions for Phoenix EA

export interface Signal {
  id: string;
  contract_id?: string;
  ticket?: number;
  symbol: string;
  timeframe: string;
  side: 'LONG' | 'SHORT';
  entry: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  take_profit_3?: number;
  risk_reward: number;
  confidence: number;
  posted_at: string;
  sweep_type: string;
  structure_type: string;
  ob_present: boolean;
  zone_id?: number;
  premium_discount: string;
  h4_aligned: boolean;
  h1_bias: string;
  atr_percentile: number;
  lots: number;
  risk_r: number;
  partial_plan?: Record<string, any>;
  status?: string;
}

export interface BacktestResult {
  id: number;
  strategy_name: string;
  symbol: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  total_pnl: number;
  max_drawdown: number;
  sharpe_ratio: number;
  created_at: string;
}

export interface SystemStatus {
  status: string;
  database: boolean;
  redis: boolean;
  deriv: boolean;
  strategy_engine: string;
  uptime: number;
}

export interface RiskMetrics {
  daily_pnl: number;
  daily_pnl_r: number;
  trade_count: number;
  active_trades_count: number;
  max_risk_per_trade: number;
  max_daily_risk: number;
  daily_stop_r: number;
  max_concurrent_r: number;
  drawdown_threshold_r: number;
  risk_utilization: number;
  can_trade: boolean;
}

export interface Trade {
  id: number;
  signal_id: string;
  entry_time: string;
  exit_time?: string;
  entry_price: number;
  exit_price?: number;
  lots: number;
  pnl_dollars?: number;
  pnl_r?: number;
  exit_reason?: string;
  mae_r?: number;
  mfe_r?: number;
}

export interface GenerateSignalRequest {
  symbol: string;
  timeframe: string;
  force?: boolean;
}

export interface ExecuteSignalRequest {
  signal_id: string;
  platform: 'deriv' | 'mt5';
  lot_size?: number;
}

export interface ClosePositionRequest {
  signal_id: string;
  partial_pct?: number;
}

export interface BacktestRequest {
  symbol: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  strategy_params?: Record<string, any>;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

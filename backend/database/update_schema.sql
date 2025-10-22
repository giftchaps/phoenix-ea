-- Update Phoenix EA Database Schema to match specification
-- This script updates the existing schema to match the required structure

-- Drop existing tables if they exist (in correct order due to foreign keys)
DROP TABLE IF EXISTS trade_executions CASCADE;
DROP TABLE IF EXISTS signals CASCADE;
DROP TABLE IF EXISTS backtest_results CASCADE;
DROP TABLE IF EXISTS risk_metrics CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS system_config CASCADE;

-- Create Symbols table
CREATE TABLE symbols (
    id SERIAL PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL,
    pip_size DECIMAL(10, 6),
    tick_value DECIMAL(10, 2),
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create Bars table
CREATE TABLE bars (
    id SERIAL PRIMARY KEY,
    symbol_id INT REFERENCES symbols(id),
    timeframe VARCHAR(5),
    time TIMESTAMP NOT NULL,
    open DECIMAL(12, 6),
    high DECIMAL(12, 6),
    low DECIMAL(12, 6),
    close DECIMAL(12, 6),
    volume BIGINT,
    atr DECIMAL(12, 6),
    UNIQUE(symbol_id, timeframe, time)
);

-- Create Signals table (updated to match specification)
CREATE TABLE signals (
    id VARCHAR(50) PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(5),
    side VARCHAR(10),
    entry DECIMAL(12, 6),
    stop_loss DECIMAL(12, 6),
    take_profit_1 DECIMAL(12, 6),
    take_profit_2 DECIMAL(12, 6),
    take_profit_3 DECIMAL(12, 6),
    confidence DECIMAL(4, 3),
    sweep_type VARCHAR(10),
    structure_type VARCHAR(10),
    ob_present BOOLEAN,
    premium_discount VARCHAR(10),
    h4_aligned BOOLEAN,
    h1_bias VARCHAR(10),
    atr_percentile DECIMAL(5, 2),
    posted_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending'
);

-- Create Trades table
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    signal_id VARCHAR(50) REFERENCES signals(id),
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    entry_price DECIMAL(12, 6),
    exit_price DECIMAL(12, 6),
    lots DECIMAL(8, 2),
    pnl_dollars DECIMAL(12, 2),
    pnl_r DECIMAL(8, 3),
    exit_reason VARCHAR(20),
    mae_r DECIMAL(8, 3),
    mfe_r DECIMAL(8, 3)
);

-- Create Backtest Results table (keeping for backtesting functionality)
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    win_rate DECIMAL(5, 2) NOT NULL,
    total_return DECIMAL(10, 2) NOT NULL,
    max_drawdown DECIMAL(10, 2) NOT NULL,
    sharpe_ratio DECIMAL(8, 4),
    profit_factor DECIMAL(8, 4),
    avg_win DECIMAL(10, 2),
    avg_loss DECIMAL(10, 2),
    largest_win DECIMAL(10, 2),
    largest_loss DECIMAL(10, 2),
    config JSONB NOT NULL,
    results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create System Configuration table
CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Risk Metrics table
CREATE TABLE risk_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    current_exposure DECIMAL(10, 2) NOT NULL DEFAULT 0,
    max_exposure DECIMAL(10, 2) NOT NULL,
    daily_pnl DECIMAL(10, 2) NOT NULL DEFAULT 0,
    weekly_pnl DECIMAL(10, 2) NOT NULL DEFAULT 0,
    monthly_pnl DECIMAL(10, 2) NOT NULL DEFAULT 0,
    drawdown DECIMAL(10, 2) NOT NULL DEFAULT 0,
    max_drawdown DECIMAL(10, 2) NOT NULL DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Notifications table
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM' CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'SENT', 'FAILED')),
    channel VARCHAR(50) NOT NULL,
    recipient VARCHAR(200),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for better performance
CREATE INDEX idx_bars_symbol_timeframe ON bars(symbol_id, timeframe);
CREATE INDEX idx_bars_time ON bars(time);
CREATE INDEX idx_signals_symbol_timeframe ON signals(symbol, timeframe);
CREATE INDEX idx_signals_posted_at ON signals(posted_at);
CREATE INDEX idx_signals_confidence ON signals(confidence);
CREATE INDEX idx_trades_signal_id ON trades(signal_id);
CREATE INDEX idx_trades_entry_time ON trades(entry_time);
CREATE INDEX idx_backtest_results_strategy ON backtest_results(strategy_name);
CREATE INDEX idx_backtest_results_symbol ON backtest_results(symbol);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- Insert default symbols
INSERT INTO symbols (name, pip_size, tick_value, enabled) VALUES
('XAUUSD', 0.01, 1.0, true),
('EURUSD', 0.0001, 1.0, true),
('V75', 0.01, 0.1, true),
('V50', 0.01, 0.1, true);

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, description) VALUES
('strategy_config', '{
    "swing_lookback": 2,
    "sweep_min_pts": 5,
    "reentry_max_candles": 3,
    "ob_lookback": 15,
    "ob_volume_pctl": 60,
    "zone_lookback": 50,
    "min_impulse_atr": 2.0,
    "eqh_eql_tolerance_pts": 5,
    "ob_required": true,
    "premium_discount_filter": true,
    "min_confidence": 0.65,
    "atr_mult": 2.0,
    "sl_buffer_pts": 2,
    "tick_value": 1.0,
    "pip_size": 0.0001,
    "min_lot": 0.01,
    "max_lot": 10.0
}', 'Default SMC strategy configuration'),
('risk_config', '{
    "max_risk_per_trade": 1.0,
    "max_daily_risk": 5.0,
    "max_weekly_risk": 20.0,
    "max_drawdown": 10.0,
    "position_sizing": "fixed_percentage"
}', 'Risk management configuration'),
('notification_config', '{
    "telegram_enabled": false,
    "email_enabled": false,
    "webhook_enabled": false,
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "email_smtp_server": "",
    "email_username": "",
    "email_password": ""
}', 'Notification system configuration')
ON CONFLICT (config_key) DO NOTHING;

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE symbols IS 'Trading symbols and their specifications';
COMMENT ON TABLE bars IS 'OHLCV price data for different timeframes';
COMMENT ON TABLE signals IS 'Trading signals generated by the SMC strategy engine';
COMMENT ON TABLE trades IS 'Actual trade executions and P&L tracking';
COMMENT ON TABLE backtest_results IS 'Results from strategy backtesting';
COMMENT ON TABLE system_config IS 'System configuration and parameters';
COMMENT ON TABLE risk_metrics IS 'Real-time risk management metrics';
COMMENT ON TABLE notifications IS 'System notifications and alerts';

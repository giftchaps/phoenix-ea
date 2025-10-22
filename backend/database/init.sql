-- Phoenix EA Database Initialization
-- Creates tables for trading signals, backtests, and system configuration

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Trading Signals Table
CREATE TABLE IF NOT EXISTS signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    entry_price DECIMAL(10, 5) NOT NULL,
    stop_loss DECIMAL(10, 5) NOT NULL,
    take_profit_1 DECIMAL(10, 5) NOT NULL,
    take_profit_2 DECIMAL(10, 5) NOT NULL,
    take_profit_3 DECIMAL(10, 5),
    risk_reward DECIMAL(5, 2) NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    lots DECIMAL(10, 2) NOT NULL,
    risk_r DECIMAL(5, 2) NOT NULL,
    sweep_type VARCHAR(20) NOT NULL,
    structure_type VARCHAR(10) NOT NULL,
    ob_present BOOLEAN NOT NULL,
    zone_id INTEGER,
    premium_discount VARCHAR(20) NOT NULL,
    h4_aligned BOOLEAN NOT NULL,
    h1_bias VARCHAR(20) NOT NULL,
    atr_percentile DECIMAL(5, 2) NOT NULL,
    partial_plan JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Backtest Results Table
CREATE TABLE IF NOT EXISTS backtest_results (
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

-- Trade Executions Table
CREATE TABLE IF NOT EXISTS trade_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID REFERENCES signals(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price DECIMAL(10, 5) NOT NULL,
    exit_price DECIMAL(10, 5),
    lots DECIMAL(10, 2) NOT NULL,
    pnl DECIMAL(10, 2),
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED', 'CANCELLED')),
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System Configuration Table
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Risk Management Table
CREATE TABLE IF NOT EXISTS risk_metrics (
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

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
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
CREATE INDEX IF NOT EXISTS idx_signals_symbol_timeframe ON signals(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at);
CREATE INDEX IF NOT EXISTS idx_signals_confidence ON signals(confidence);
CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy ON backtest_results(strategy_name);
CREATE INDEX IF NOT EXISTS idx_backtest_results_symbol ON backtest_results(symbol);
CREATE INDEX IF NOT EXISTS idx_trade_executions_signal_id ON trade_executions(signal_id);
CREATE INDEX IF NOT EXISTS idx_trade_executions_status ON trade_executions(status);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

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
CREATE TRIGGER update_signals_updated_at BEFORE UPDATE ON signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (if needed for specific users)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO phoenix;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO phoenix;

COMMENT ON TABLE signals IS 'Trading signals generated by the SMC strategy engine';
COMMENT ON TABLE backtest_results IS 'Results from strategy backtesting';
COMMENT ON TABLE trade_executions IS 'Actual trade executions and P&L tracking';
COMMENT ON TABLE system_config IS 'System configuration and parameters';
COMMENT ON TABLE risk_metrics IS 'Real-time risk management metrics';
COMMENT ON TABLE notifications IS 'System notifications and alerts';

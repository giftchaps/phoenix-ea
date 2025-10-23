"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Activity, TrendingUp, BarChart3, Shield, Wifi, WifiOff, RefreshCw, AlertCircle } from 'lucide-react';
import { apiClient, wsClient, config, ApiError } from '../lib/api';
import type { Signal, RiskMetrics as RiskMetricsType } from '../lib/types';
import SignalCard from './SignalCard';
import RiskMetrics from './RiskMetrics';
import { StatCard, LoadingSpinner, ErrorAlert, EmptyState, Button } from './UIComponents';

export default function EnhancedDashboard() {
  // State
  const [activeTab, setActiveTab] = useState<'live' | 'history'>('live');
  const [filterSymbol, setFilterSymbol] = useState('all');
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');

  // Data state
  const [activeSignals, setActiveSignals] = useState<Signal[]>([]);
  const [historySignals, setHistorySignals] = useState<Signal[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetricsType | null>(null);

  // Loading states
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [riskLoading, setRiskLoading] = useState(true);

  // Error states
  const [error, setError] = useState<string | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [riskError, setRiskError] = useState<string | null>(null);

  // Last update timestamp
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Test API connection
  const checkConnection = useCallback(async () => {
    try {
      await apiClient.getSystemStatus();
      setIsConnected(true);
      setConnectionStatus('Connected');
      return true;
    } catch (err) {
      setIsConnected(false);
      setConnectionStatus('Disconnected');
      console.error('Backend connection failed:', err);
      return false;
    }
  }, []);

  // Load active signals
  const loadActiveSignals = useCallback(async () => {
    try {
      setError(null);
      const signals = await apiClient.getActiveSignals();
      setActiveSignals(signals);
      setLastUpdate(new Date());
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.detail || err.message : 'Failed to load active signals';
      setError(errorMsg);
      console.error('Error loading active signals:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load signal history
  const loadHistorySignals = useCallback(async () => {
    try {
      setError(null);
      const signals = await apiClient.getSignalHistory();
      setHistorySignals(signals);
      setLastUpdate(new Date());
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.detail || err.message : 'Failed to load signal history';
      setError(errorMsg);
      console.error('Error loading signal history:', err);
    }
  }, []);

  // Load statistics
  const loadStats = useCallback(async () => {
    try {
      setStatsError(null);
      const data = await apiClient.getStats();
      setStats(data);
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.detail || err.message : 'Failed to load statistics';
      setStatsError(errorMsg);
      console.error('Error loading stats:', err);
    } finally {
      setStatsLoading(false);
    }
  }, []);

  // Load risk metrics
  const loadRiskMetrics = useCallback(async () => {
    try {
      setRiskError(null);
      const data = await apiClient.getRiskMetrics();
      setRiskMetrics(data);
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.detail || err.message : 'Failed to load risk metrics';
      setRiskError(errorMsg);
      console.error('Error loading risk metrics:', err);
    } finally {
      setRiskLoading(false);
    }
  }, []);

  // Refresh all data
  const refreshAll = useCallback(async () => {
    setLoading(true);
    setStatsLoading(true);
    setRiskLoading(true);

    await Promise.all([
      loadActiveSignals(),
      loadHistorySignals(),
      loadStats(),
      loadRiskMetrics(),
    ]);
  }, [loadActiveSignals, loadHistorySignals, loadStats, loadRiskMetrics]);

  // Initial load
  useEffect(() => {
    const init = async () => {
      const connected = await checkConnection();
      if (connected) {
        await refreshAll();
      } else {
        setLoading(false);
        setStatsLoading(false);
        setRiskLoading(false);
      }
    };

    init();
  }, [checkConnection, refreshAll]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (isConnected) {
        refreshAll();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [isConnected, refreshAll]);

  // WebSocket for real-time updates
  useEffect(() => {
    const handleWebSocketMessage = (data: any) => {
      console.log('WebSocket message:', data);

      // Handle different message types
      if (data.type === 'signal_update') {
        // Refresh signals when we get an update
        loadActiveSignals();
      } else if (data.type === 'risk_update') {
        // Refresh risk metrics
        loadRiskMetrics();
      } else if (data.type === 'stats_update') {
        // Refresh stats
        loadStats();
      }
    };

    const handleWebSocketError = (error: Event) => {
      console.error('WebSocket error:', error);
    };

    if (isConnected) {
      wsClient.connect(handleWebSocketMessage, handleWebSocketError);
    }

    return () => {
      wsClient.disconnect();
    };
  }, [isConnected, loadActiveSignals, loadRiskMetrics, loadStats]);

  // Filter signals by symbol
  const filteredActiveSignals = filterSymbol === 'all'
    ? activeSignals
    : activeSignals.filter(s => s.symbol === filterSymbol);

  const filteredHistorySignals = filterSymbol === 'all'
    ? historySignals
    : historySignals.filter(s => s.symbol === filterSymbol);

  // Calculate unique symbols for filter
  const availableSymbols = Array.from(
    new Set([...activeSignals, ...historySignals].map(s => s.symbol))
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-800 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
                <Activity className="w-8 h-8" />
                Phoenix EA Dashboard
              </h1>
              <p className="text-blue-100">Smart Money Concepts Trading System</p>
            </div>
            <div className="flex items-center gap-4">
              {/* Connection Status */}
              <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-lg backdrop-blur-sm">
                {isConnected ? (
                  <Wifi className="w-5 h-5 text-green-300" />
                ) : (
                  <WifiOff className="w-5 h-5 text-red-300" />
                )}
                <div className="text-left">
                  <p className={`text-sm font-medium ${isConnected ? 'text-green-300' : 'text-red-300'}`}>
                    {connectionStatus}
                  </p>
                  <p className="text-xs text-blue-200">
                    {new Date(lastUpdate).toLocaleTimeString()}
                  </p>
                </div>
              </div>

              {/* Refresh Button */}
              <Button
                variant="secondary"
                size="sm"
                onClick={refreshAll}
                disabled={!isConnected}
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Connection Error */}
        {!isConnected && (
          <div className="mb-6">
            <ErrorAlert
              title="Backend Connection Failed"
              message={`Unable to connect to the backend API at ${config.apiUrl}. Please ensure the backend server is running.`}
              onRetry={checkConnection}
            />
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <StatCard
            icon={Activity}
            label="Today's Signals"
            value={stats?.today_signals || 0}
            loading={statsLoading}
          />
          <StatCard
            icon={TrendingUp}
            label="Active Positions"
            value={stats?.active_positions || 0}
            loading={statsLoading}
          />
          <StatCard
            icon={BarChart3}
            label="Total P&L"
            value={stats ? `${stats.total_pnl_r >= 0 ? '+' : ''}${stats.total_pnl_r.toFixed(2)}R` : '0.00R'}
            trend={stats && stats.total_pnl_r !== 0 ? {
              value: `${Math.abs(stats.total_pnl_r).toFixed(1)}`,
              isPositive: stats.total_pnl_r > 0
            } : undefined}
            loading={statsLoading}
          />
          <StatCard
            icon={Shield}
            label="Win Rate"
            value={stats ? `${(stats.win_rate * 100).toFixed(1)}%` : '0%'}
            loading={statsLoading}
          />
        </div>

        {/* Risk Metrics */}
        <div className="mb-6">
          {riskError ? (
            <ErrorAlert
              title="Risk Metrics Error"
              message={riskError}
              onRetry={loadRiskMetrics}
            />
          ) : (
            <RiskMetrics metrics={riskMetrics} loading={riskLoading} />
          )}
        </div>

        {/* Tabs and Filters */}
        <div className="flex items-center gap-4 mb-6 flex-wrap">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('live')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'live'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/50'
                  : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              Live Signals
              {activeSignals.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-white/20 rounded-full text-xs">
                  {activeSignals.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'history'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/50'
                  : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              History
              {historySignals.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-white/20 rounded-full text-xs">
                  {historySignals.length}
                </span>
              )}
            </button>
          </div>

          {/* Symbol Filter */}
          <div className="ml-auto">
            <select
              value={filterSymbol}
              onChange={(e) => setFilterSymbol(e.target.value)}
              className="px-4 py-3 rounded-lg border border-gray-200 bg-white text-gray-700 font-medium shadow-sm hover:border-gray-300 transition-colors"
            >
              <option value="all">All Symbols</option>
              {availableSymbols.map(symbol => (
                <option key={symbol} value={symbol}>{symbol}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Signals Grid */}
        {activeTab === 'live' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-6 h-6" />
              Active Signals ({filteredActiveSignals.length})
            </h2>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner size="lg" text="Loading signals..." />
              </div>
            ) : error ? (
              <ErrorAlert
                title="Error Loading Signals"
                message={error}
                onRetry={loadActiveSignals}
              />
            ) : filteredActiveSignals.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {filteredActiveSignals.map(signal => (
                  <SignalCard key={signal.id} signal={signal} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={Activity}
                message="No active signals at the moment. The system is monitoring the market for high-quality setups."
              />
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="w-6 h-6" />
              Signal History ({filteredHistorySignals.length})
            </h2>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner size="lg" text="Loading history..." />
              </div>
            ) : error ? (
              <ErrorAlert
                title="Error Loading History"
                message={error}
                onRetry={loadHistorySignals}
              />
            ) : filteredHistorySignals.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {filteredHistorySignals.map(signal => (
                  <SignalCard key={signal.id} signal={signal} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={BarChart3}
                message="No signal history available yet."
              />
            )}
          </div>
        )}

        {/* Risk Warning Footer */}
        <div className="mt-8 p-4 bg-gradient-to-r from-yellow-50 to-orange-50 border-l-4 border-yellow-400 rounded-lg shadow-sm">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-yellow-900 mb-1">Risk Warning</p>
              <p className="text-sm text-yellow-800">
                Trading signals are for educational purposes only. Past performance does not guarantee future results.
                Always manage your risk appropriately and never risk more than you can afford to lose.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

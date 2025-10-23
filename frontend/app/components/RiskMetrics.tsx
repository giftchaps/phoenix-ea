"use client";

import React from 'react';
import { Shield, AlertTriangle, TrendingDown, TrendingUp, Activity, Lock } from 'lucide-react';
import type { RiskMetrics as RiskMetricsType } from '../lib/types';
import { Card, Badge, LoadingSpinner } from './UIComponents';

interface RiskMetricsProps {
  metrics: RiskMetricsType | null;
  loading?: boolean;
}

export default function RiskMetrics({ metrics, loading }: RiskMetricsProps) {
  if (loading) {
    return (
      <Card>
        <h2 className="text-lg font-bold text-gray-900 mb-4">Risk Management</h2>
        <LoadingSpinner size="md" text="Loading risk metrics..." />
      </Card>
    );
  }

  if (!metrics) {
    return null;
  }

  const riskUtilizationPercent = (metrics.risk_utilization * 100).toFixed(1);
  const dailyPnlColor = metrics.daily_pnl_r >= 0 ? 'text-green-600' : 'text-red-600';
  const canTradeColor = metrics.can_trade ? 'text-green-600' : 'text-red-600';

  return (
    <Card className="hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <Shield className="w-5 h-5" />
          Risk Management
        </h2>
        {metrics.can_trade ? (
          <Badge variant="success">Trading Enabled</Badge>
        ) : (
          <Badge variant="danger">Trading Disabled</Badge>
        )}
      </div>

      {/* Daily P&L */}
      <div className="mb-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 mb-1">Daily P&L</p>
            <p className={`text-2xl font-bold ${dailyPnlColor}`}>
              {metrics.daily_pnl_r >= 0 ? '+' : ''}
              {metrics.daily_pnl_r.toFixed(2)}R
            </p>
            <p className="text-xs text-gray-500 mt-1">
              ${metrics.daily_pnl.toFixed(2)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600 mb-1">Daily Stop</p>
            <p className="text-xl font-bold text-gray-900">
              {metrics.daily_stop_r.toFixed(1)}R
            </p>
          </div>
        </div>
      </div>

      {/* Active Risk */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4 text-blue-600" />
            <p className="text-xs text-blue-700 font-medium">Active Trades</p>
          </div>
          <p className="text-2xl font-bold text-blue-900">{metrics.active_trades_count}</p>
        </div>

        <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-purple-600" />
            <p className="text-xs text-purple-700 font-medium">Active Risk</p>
          </div>
          <p className="text-2xl font-bold text-purple-900">
            {metrics.active_risk_r?.toFixed(2) || '0.00'}R
          </p>
        </div>
      </div>

      {/* Risk Limits */}
      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm text-gray-600">Risk Utilization</p>
            <p className="text-sm font-medium text-gray-900">{riskUtilizationPercent}%</p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                metrics.risk_utilization > 0.8
                  ? 'bg-red-500'
                  : metrics.risk_utilization > 0.6
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(metrics.risk_utilization * 100, 100)}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-gray-600 mb-1">Max Per Trade</p>
            <p className="font-bold text-gray-900">{metrics.max_risk_per_trade.toFixed(1)}%</p>
          </div>
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-gray-600 mb-1">Max Concurrent</p>
            <p className="font-bold text-gray-900">{metrics.max_concurrent_r.toFixed(1)}R</p>
          </div>
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-gray-600 mb-1">Max Daily Risk</p>
            <p className="font-bold text-gray-900">{metrics.max_daily_risk.toFixed(1)}%</p>
          </div>
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-gray-600 mb-1">DD Threshold</p>
            <p className="font-bold text-gray-900">{metrics.drawdown_threshold_r.toFixed(1)}R</p>
          </div>
        </div>
      </div>

      {/* Risk Reduction Alert */}
      {metrics.risk_reduction_active && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-yellow-900">Drawdown Throttle Active</p>
              <p className="text-xs text-yellow-700 mt-1">
                Risk automatically reduced by 50% due to rolling drawdown
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Trading Disabled Alert */}
      {!metrics.can_trade && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-2">
            <Lock className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-red-900">Trading Disabled</p>
              <p className="text-xs text-red-700 mt-1">
                Daily stop loss hit or maximum concurrent risk reached
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Trade Count */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Total Trades Today</span>
          <span className="font-bold text-gray-900">{metrics.trade_count}</span>
        </div>
      </div>
    </Card>
  );
}

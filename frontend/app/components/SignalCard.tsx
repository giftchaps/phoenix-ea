"use client";

import React from 'react';
import { TrendingUp, TrendingDown, Activity, Target, Clock, CheckCircle, XCircle } from 'lucide-react';
import type { Signal } from '../lib/types';
import { Badge } from './UIComponents';

interface SignalCardProps {
  signal: Signal;
  onExecute?: (signalId: string) => void;
  onClose?: (signalId: string) => void;
}

export default function SignalCard({ signal, onExecute, onClose }: SignalCardProps) {
  const isBuy = signal.side === 'LONG';
  const isActive = signal.status === 'active';
  const isClosed = signal.status === 'closed';

  // Format price based on symbol
  const formatPrice = (price: number) => {
    if (signal.symbol.includes('XAU')) return price.toFixed(2);
    if (signal.symbol.includes('USD')) return price.toFixed(4);
    return price.toFixed(2);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-bold text-gray-900">{signal.symbol}</h3>
            <Badge variant={isBuy ? 'success' : 'danger'}>
              {signal.side}
            </Badge>
            {isActive && <Badge variant="info">ACTIVE</Badge>}
            {isClosed && <Badge variant="default">CLOSED</Badge>}
          </div>
          <p className="text-sm text-gray-500">{signal.timeframe}</p>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1 text-sm text-gray-600 mb-1">
            <Clock className="w-4 h-4" />
            <span className="text-xs">
              {new Date(signal.posted_at).toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Activity
              className={`w-4 h-4 ${
                signal.confidence >= 0.75
                  ? 'text-green-500'
                  : signal.confidence >= 0.65
                  ? 'text-yellow-500'
                  : 'text-gray-400'
              }`}
            />
            <span className="text-sm font-medium">
              {(signal.confidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Price Levels */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-500 mb-1">Entry</p>
          <p className="text-lg font-bold text-gray-900">{formatPrice(signal.entry)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Stop Loss</p>
          <p className="text-lg font-bold text-red-600">{formatPrice(signal.stop_loss)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">TP1</p>
          <p className="text-md font-semibold text-green-600">{formatPrice(signal.take_profit_1)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">TP2</p>
          <p className="text-md font-semibold text-green-600">{formatPrice(signal.take_profit_2)}</p>
        </div>
      </div>

      {/* Risk/Reward */}
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-4">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">Risk:Reward</span>
        </div>
        <span className="text-lg font-bold text-gray-900">1:{signal.risk_reward.toFixed(1)}</span>
      </div>

      {/* Setup Details */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Structure</span>
          <Badge variant={signal.structure_type === 'MSS' ? 'warning' : 'info'}>
            {signal.structure_type}
          </Badge>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Sweep</span>
          <Badge variant="default">{signal.sweep_type}</Badge>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Order Block</span>
          <span className="font-medium flex items-center gap-1">
            {signal.ob_present ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-green-600">Present</span>
              </>
            ) : (
              <>
                <XCircle className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">None</span>
              </>
            )}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Position</span>
          <Badge
            variant={
              (signal.premium_discount === 'premium' && signal.side === 'SHORT') ||
              (signal.premium_discount === 'discount' && signal.side === 'LONG')
                ? 'success'
                : 'default'
            }
          >
            {signal.premium_discount}
          </Badge>
        </div>
      </div>

      {/* Bias & ATR */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-200 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-gray-500">H1 Bias:</span>
          <span className="font-medium text-gray-700">{signal.h1_bias}</span>
          {signal.h4_aligned && (
            <Badge variant="success">H4 Aligned</Badge>
          )}
        </div>
        <div>
          <span className="text-gray-500">ATR: </span>
          <span className="font-medium text-gray-700">{signal.atr_percentile}th</span>
        </div>
      </div>

      {/* Risk Information */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Position Size</span>
          <span className="font-medium text-gray-900">{signal.lots.toFixed(2)} lots</span>
        </div>
        <div className="flex items-center justify-between text-sm mt-1">
          <span className="text-gray-600">Risk</span>
          <span className="font-medium text-gray-900">{signal.risk_r.toFixed(2)}R</span>
        </div>
      </div>

      {/* Action Buttons */}
      {isActive && (onExecute || onClose) && (
        <div className="mt-4 flex gap-2">
          {onExecute && (
            <button
              onClick={() => onExecute(signal.id)}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Execute Trade
            </button>
          )}
          {onClose && (
            <button
              onClick={() => onClose(signal.id)}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-900 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors"
            >
              Close Position
            </button>
          )}
        </div>
      )}
    </div>
  );
}

"use client";

import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, Target, Shield, Clock, BarChart3, Wifi, WifiOff } from 'lucide-react';
import { apiClient, wsClient, config } from '../lib/api';

// Type definitions
interface Signal {
  id: number;
  symbol: string;
  side: 'BUY' | 'SELL';
  entry: number;
  stopLoss: number;
  takeProfit1: number;
  takeProfit2: number;
  rr: number;
  confidence: number;
  strategy: string;
  sweepType: string;
  structureType: string;
  obPresent: boolean;
  premiumDiscount: string;
  h4Aligned: boolean;
  h1Bias: string;
  atrPercentile: number;
  postedAt: string;
  status: 'active' | 'closed' | 'pending';
  exitPrice?: number;
  exitReason?: string;
  pnlR?: number;
}

interface Stats {
  todaySignals: number;
  activePositions: number;
  totalPnL: string;
  winRate: string;
  profitFactor: number;
  weeklyEquity: number[];
}

// Sample signal data
const sampleSignals: Signal[] = [
  {
    id: 1,
    symbol: 'XAUUSD',
    side: 'SELL',
    entry: 2045.30,
    stopLoss: 2052.80,
    takeProfit1: 2037.80,
    takeProfit2: 2030.30,
    rr: 2.0,
    confidence: 0.82,
    strategy: 'SMC – Sweep→MSS→FVG',
    sweepType: 'EQH',
    structureType: 'MSS',
    obPresent: true,
    premiumDiscount: 'premium',
    h4Aligned: true,
    h1Bias: 'Bearish',
    atrPercentile: 67,
    postedAt: '2025-10-22 09:15 ET',
    status: 'active'
  },
  {
    id: 2,
    symbol: 'V75',
    side: 'BUY',
    entry: 135.42,
    stopLoss: 133.81,
    takeProfit1: 137.03,
    takeProfit2: 138.64,
    rr: 2.0,
    confidence: 0.74,
    strategy: 'SMC – Sweep→BOS→FVG',
    sweepType: 'EQL',
    structureType: 'BOS',
    obPresent: true,
    premiumDiscount: 'discount',
    h4Aligned: true,
    h1Bias: 'Bullish',
    atrPercentile: 58,
    postedAt: '2025-10-22 08:42 ET',
    status: 'active'
  },
  {
    id: 3,
    symbol: 'EURUSD',
    side: 'SELL',
    entry: 1.0850,
    stopLoss: 1.0875,
    takeProfit1: 1.0825,
    takeProfit2: 1.0800,
    rr: 2.0,
    confidence: 0.68,
    strategy: 'SMC – Sweep→BOS→FVG',
    sweepType: 'single',
    structureType: 'BOS',
    obPresent: false,
    premiumDiscount: 'premium',
    h4Aligned: false,
    h1Bias: 'Bearish',
    atrPercentile: 52,
    postedAt: '2025-10-22 07:30 ET',
    status: 'closed',
    exitPrice: 1.0825,
    exitReason: 'TP1',
    pnlR: 1.0
  }
];

const stats: Stats = {
  todaySignals: 5,
  activePositions: 2,
  totalPnL: '+12.5R',
  winRate: '64%',
  profitFactor: 1.85,
  weeklyEquity: [100, 102, 101.5, 104, 105.5, 107, 112.5]
};

const SignalCard = ({ signal }: { signal: Signal }) => {
  const isBuy = signal.side === 'BUY';
  const isActive = signal.status === 'active';
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-bold text-gray-900">{signal.symbol}</h3>
            <span className={`px-2 py-1 rounded text-xs font-bold ${
              isBuy ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {signal.side}
            </span>
            {isActive && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700">
                ACTIVE
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500">{signal.strategy}</p>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1 text-sm text-gray-600 mb-1">
            <Clock className="w-4 h-4" />
            {signal.postedAt}
          </div>
          <div className="flex items-center gap-1">
            <Activity className={`w-4 h-4 ${signal.confidence >= 0.75 ? 'text-green-500' : signal.confidence >= 0.65 ? 'text-yellow-500' : 'text-gray-400'}`} />
            <span className="text-sm font-medium">{(signal.confidence * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      {/* Price Levels */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-500 mb-1">Entry</p>
          <p className="text-lg font-bold text-gray-900">{signal.entry.toFixed(signal.symbol.includes('USD') && !signal.symbol.includes('XAU') ? 4 : 2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Stop Loss</p>
          <p className="text-lg font-bold text-red-600">{signal.stopLoss.toFixed(signal.symbol.includes('USD') && !signal.symbol.includes('XAU') ? 4 : 2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">TP1 (50%)</p>
          <p className="text-md font-semibold text-green-600">{signal.takeProfit1.toFixed(signal.symbol.includes('USD') && !signal.symbol.includes('XAU') ? 4 : 2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">TP2 (30%)</p>
          <p className="text-md font-semibold text-green-600">{signal.takeProfit2.toFixed(signal.symbol.includes('USD') && !signal.symbol.includes('XAU') ? 4 : 2)}</p>
        </div>
      </div>

      {/* Risk/Reward */}
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-4">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">Risk:Reward</span>
        </div>
        <span className="text-lg font-bold text-gray-900">1:{signal.rr.toFixed(1)}</span>
      </div>

      {/* Setup Details */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Structure</span>
          <span className={`font-medium px-2 py-0.5 rounded ${
            signal.structureType === 'MSS' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
          }`}>
            {signal.structureType}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Sweep</span>
          <span className={`font-medium px-2 py-0.5 rounded ${
            signal.sweepType === 'EQH' || signal.sweepType === 'EQL' ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-700'
          }`}>
            {signal.sweepType}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Order Block</span>
          <span className="font-medium">{signal.obPresent ? '✓ Present' : '✗ None'}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Position</span>
          <span className={`font-medium ${
            signal.premiumDiscount === 'premium' && signal.side === 'SELL' ? 'text-green-600' :
            signal.premiumDiscount === 'discount' && signal.side === 'BUY' ? 'text-green-600' :
            'text-gray-600'
          }`}>
            {signal.premiumDiscount}
          </span>
        </div>
      </div>

      {/* Bias & ATR */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-200 text-xs">
        <div>
          <span className="text-gray-500">H1 Bias: </span>
          <span className="font-medium text-gray-700">{signal.h1Bias}</span>
          {signal.h4Aligned && <span className="ml-2 text-green-600">✓ H4 Aligned</span>}
        </div>
        <div>
          <span className="text-gray-500">ATR: </span>
          <span className="font-medium text-gray-700">{signal.atrPercentile}th</span>
        </div>
      </div>

      {/* Exit Info (if closed) */}
      {!isActive && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Exit: {signal.exitPrice?.toFixed(signal.symbol.includes('USD') && !signal.symbol.includes('XAU') ? 4 : 2)} ({signal.exitReason})</span>
            <span className={`text-sm font-bold ${(signal.pnlR ?? 0) > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {(signal.pnlR ?? 0) > 0 ? '+' : ''}{(signal.pnlR ?? 0).toFixed(2)}R
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

const StatCard = ({ icon: Icon, label, value, trend }: { 
  icon: React.ComponentType<{ className?: string }>, 
  label: string, 
  value: string, 
  trend?: { value: string, isPositive: boolean } 
}) => (
  <div className="bg-white rounded-lg border border-gray-200 p-4">
    <div className="flex items-center justify-between mb-2">
      <Icon className="w-5 h-5 text-gray-500" />
      {trend && (
        <span className={`text-xs font-medium ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {trend.isPositive ? '+' : ''}{trend.value}%
        </span>
      )}
    </div>
    <p className="text-2xl font-bold text-gray-900 mb-1">{value}</p>
    <p className="text-sm text-gray-600">{label}</p>
  </div>
);

export default function PhoenixDashboard() {
  const [activeTab, setActiveTab] = useState('live');
  const [filterSymbol, setFilterSymbol] = useState('all');
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [apiStatus, setApiStatus] = useState('Unknown');

  const filteredSignals = filterSymbol === 'all' 
    ? sampleSignals 
    : sampleSignals.filter(s => s.symbol === filterSymbol);

  // Test API connection on component mount
  useEffect(() => {
    const testApiConnection = async () => {
      try {
        await apiClient.getSystemStatus();
        setApiStatus('Connected');
        setIsConnected(true);
        setConnectionStatus('Backend Connected');
      } catch (error) {
        setApiStatus('Disconnected');
        setIsConnected(false);
        setConnectionStatus('Backend Disconnected');
        console.log('Backend API not available:', error);
      }
    };

    testApiConnection();
  }, []);

  // WebSocket connection
  useEffect(() => {
    const handleWebSocketMessage = (data: any) => {
      console.log('WebSocket message received:', data);
      // Handle real-time updates here
    };

    const handleWebSocketError = (error: Event) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('WebSocket Error');
    };

    wsClient.connect(handleWebSocketMessage, handleWebSocketError);

    return () => {
      wsClient.disconnect();
    };
  }, []);

  const activeSignals = filteredSignals.filter(s => s.status === 'active');
  const closedSignals = filteredSignals.filter(s => s.status === 'closed');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Phoenix EA Signals</h1>
              <p className="text-blue-100">Institutional-Grade SMC Trading Signals</p>
            </div>
            <div className="flex items-center gap-4">
              {/* Connection Status */}
              <div className="flex items-center gap-2">
                {isConnected ? (
                  <Wifi className="w-5 h-5 text-green-300" />
                ) : (
                  <WifiOff className="w-5 h-5 text-red-300" />
                )}
                <span className={`text-sm font-medium ${
                  isConnected ? 'text-green-300' : 'text-red-300'
                }`}>
                  {connectionStatus}
                </span>
              </div>
              {/* API URL Display */}
              <div className="text-xs text-blue-200">
                API: {config.apiUrl}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <StatCard icon={Activity} label="Today's Signals" value={stats.todaySignals.toString()} />
          <StatCard icon={TrendingUp} label="Active Positions" value={stats.activePositions.toString()} />
          <StatCard icon={BarChart3} label="Total P&L" value={stats.totalPnL} trend={{ value: "12.5", isPositive: true }} />
          <StatCard icon={Shield} label="Win Rate" value={stats.winRate} />
        </div>

        {/* Performance Overview */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-900">Performance Overview</h2>
            <div className="flex items-center gap-4 text-sm">
              <div>
                <span className="text-gray-500">Profit Factor: </span>
                <span className="font-bold text-gray-900">{stats.profitFactor}</span>
              </div>
              <div>
                <span className="text-gray-500">Weekly: </span>
                <span className="font-bold text-green-600">+{(stats.weeklyEquity[stats.weeklyEquity.length - 1] - stats.weeklyEquity[0]).toFixed(1)}%</span>
              </div>
            </div>
          </div>
          
          {/* Simple equity curve */}
          <div className="flex items-end gap-1 h-32">
            {stats.weeklyEquity.map((value, idx) => (
              <div key={idx} className="flex-1 bg-blue-200 rounded-t hover:bg-blue-300 transition-colors" 
                   style={{ height: `${(value - 95) * 8}%` }}
                   title={`Day ${idx + 1}: ${value}%`}>
              </div>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={() => setActiveTab('live')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'live' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            Live Signals
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'history' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            History
          </button>
          
          <div className="ml-auto">
            <select 
              value={filterSymbol}
              onChange={(e) => setFilterSymbol(e.target.value)}
              className="px-4 py-2 rounded-lg border border-gray-200 bg-white text-gray-700 font-medium"
            >
              <option value="all">All Symbols</option>
              <option value="XAUUSD">XAUUSD</option>
              <option value="EURUSD">EURUSD</option>
              <option value="V75">V75</option>
              <option value="V50">V50</option>
            </select>
          </div>
        </div>

        {/* Signals Grid */}
        {activeTab === 'live' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Active Signals ({activeSignals.length})
            </h2>
            {activeSignals.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {activeSignals.map(signal => (
                  <SignalCard key={signal.id} signal={signal} />
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
                <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No active signals at the moment</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Signal History ({closedSignals.length})
            </h2>
            {closedSignals.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {closedSignals.map(signal => (
                  <SignalCard key={signal.id} signal={signal} />
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
                <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No closed signals yet</p>
              </div>
            )}
          </div>
        )}

        {/* Footer Note */}
        <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>Risk Warning:</strong> Trading signals are for educational purposes only. Past performance does not guarantee future results. Always manage your risk appropriately.
          </p>
        </div>
      </div>
    </div>
  );
}
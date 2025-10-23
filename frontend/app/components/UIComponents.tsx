import React from 'react';
import { AlertCircle, Loader2, TrendingUp, TrendingDown, Activity, Target, Shield, Clock, BarChart3 } from 'lucide-react';

// Loading Spinner Component
export const LoadingSpinner = ({ size = 'md', text }: { size?: 'sm' | 'md' | 'lg'; text?: string }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <Loader2 className={`${sizeClasses[size]} animate-spin text-blue-600`} />
      {text && <p className="text-sm text-gray-600">{text}</p>}
    </div>
  );
};

// Error Alert Component
export const ErrorAlert = ({
  title = 'Error',
  message,
  onRetry
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
    <div className="flex items-start gap-3">
      <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <h3 className="font-semibold text-red-900 mb-1">{title}</h3>
        <p className="text-sm text-red-700">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  </div>
);

// Info Alert Component
export const InfoAlert = ({ message }: { message: string }) => (
  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
    <div className="flex items-start gap-3">
      <Activity className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
      <p className="text-sm text-blue-700">{message}</p>
    </div>
  </div>
);

// Empty State Component
export const EmptyState = ({
  icon: Icon = Activity,
  message
}: {
  icon?: React.ComponentType<{ className?: string }>;
  message: string;
}) => (
  <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
    <Icon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
    <p className="text-gray-500">{message}</p>
  </div>
);

// Stat Card Component
export const StatCard = ({
  icon: Icon,
  label,
  value,
  trend,
  loading = false
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  trend?: { value: string; isPositive: boolean };
  loading?: boolean;
}) => (
  <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
    <div className="flex items-center justify-between mb-2">
      <Icon className="w-5 h-5 text-gray-500" />
      {trend && !loading && (
        <span className={`text-xs font-medium flex items-center gap-1 ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {trend.isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {trend.value}
        </span>
      )}
    </div>
    {loading ? (
      <div className="h-8 bg-gray-200 rounded animate-pulse mb-1" />
    ) : (
      <p className="text-2xl font-bold text-gray-900 mb-1">{value}</p>
    )}
    <p className="text-sm text-gray-600">{label}</p>
  </div>
);

// Badge Component
export const Badge = ({
  children,
  variant = 'default'
}: {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'danger' | 'warning' | 'info';
}) => {
  const variants = {
    default: 'bg-gray-100 text-gray-700',
    success: 'bg-green-100 text-green-700',
    danger: 'bg-red-100 text-red-700',
    warning: 'bg-yellow-100 text-yellow-700',
    info: 'bg-blue-100 text-blue-700',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${variants[variant]}`}>
      {children}
    </span>
  );
};

// Card Container Component
export const Card = ({
  children,
  className = ''
}: {
  children: React.ReactNode;
  className?: string;
}) => (
  <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
    {children}
  </div>
);

// Button Component
export const Button = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
}) => {
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
    success: 'bg-green-600 hover:bg-green-700 text-white',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        ${variants[variant]}
        ${sizes[size]}
        ${fullWidth ? 'w-full' : ''}
        font-medium rounded-lg transition-colors
        disabled:opacity-50 disabled:cursor-not-allowed
        flex items-center justify-center gap-2
      `}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  );
};

// Skeleton Loader Component
export const Skeleton = ({ className = '' }: { className?: string }) => (
  <div className={`bg-gray-200 rounded animate-pulse ${className}`} />
);

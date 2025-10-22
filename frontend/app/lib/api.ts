// API utility functions for Phoenix EA frontend
import type {
  Signal,
  BacktestResult,
  SystemStatus,
  RiskMetrics,
  GenerateSignalRequest,
  ExecuteSignalRequest,
  ClosePositionRequest,
  BacktestRequest,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

// API client class
export class ApiClient {
  private baseUrl: string;
  private authToken: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // Set authorization token
  setAuthToken(token: string): void {
    this.authToken = token;
  }

  // Generic request method
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add authorization header if token is set
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Get all active signals
  async getActiveSignals(): Promise<Signal[]> {
    return this.request<Signal[]>('/signals/active');
  }

  // Get signal history
  async getSignalHistory(): Promise<Signal[]> {
    return this.request<Signal[]>('/signals/history');
  }

  // Get signal by ID
  async getSignal(id: string): Promise<Signal> {
    return this.request<Signal>(`/signals/${id}`);
  }

  // Generate new signal
  async generateSignal(request: GenerateSignalRequest): Promise<Signal> {
    return this.request<Signal>('/signals/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Execute signal
  async executeSignal(signalId: string, request: ExecuteSignalRequest): Promise<any> {
    return this.request(`/signals/${signalId}/execute`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Close position
  async closePosition(signalId: string, request: ClosePositionRequest): Promise<any> {
    return this.request(`/signals/${signalId}/close`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Get backtest results
  async getBacktestResults(): Promise<BacktestResult[]> {
    return this.request<BacktestResult[]>('/backtests');
  }

  // Run backtest
  async runBacktest(request: BacktestRequest): Promise<BacktestResult> {
    return this.request<BacktestResult>('/admin/backtest', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Get system status
  async getSystemStatus(): Promise<SystemStatus> {
    return this.request<SystemStatus>('/status');
  }

  // Get risk metrics
  async getRiskMetrics(): Promise<RiskMetrics> {
    return this.request<RiskMetrics>('/risk');
  }

  // Get statistics
  async getStats(): Promise<any> {
    return this.request('/stats');
  }

  // Get system configuration
  async getConfig(): Promise<any> {
    return this.request('/admin/config');
  }

  // Update system configuration
  async updateConfig(config: Record<string, any>): Promise<any> {
    return this.request('/admin/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }
}

// WebSocket client class
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(url: string = WS_URL) {
    this.url = url;
  }

  connect(onMessage: (data: any) => void, onError?: (error: Event) => void): void {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect(onMessage, onError);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (onError) onError(error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }

  private attemptReconnect(onMessage: (data: any) => void, onError?: (error: Event) => void): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect(onMessage, onError);
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Create default instances
export const apiClient = new ApiClient();
export const wsClient = new WebSocketClient();

// Environment variables
export const config = {
  apiUrl: API_BASE_URL,
  wsUrl: WS_URL,
};

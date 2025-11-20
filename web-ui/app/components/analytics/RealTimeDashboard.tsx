import React, { useState, useEffect, useRef } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { WebSocketHook } from './hooks/useWebSocket';

interface Widget {
  id: string;
  title: string;
  metric: string;
  threshold?: {
    warning: number;
    critical: number;
  };
  size: 'small' | 'medium' | 'large';
}

interface MetricData {
  timestamp: number;
  [key: string]: number | string;
}

interface RealTimeDashboardProps {
  widgets: Widget[];
  refreshInterval?: number;
  enableAlerts?: boolean;
  onThresholdBreach?: (widgetId: string, value: number) => void;
}

export const RealTimeDashboard: React.FC<RealTimeDashboardProps> = ({
  widgets,
  refreshInterval = 1000,
  enableAlerts = true,
  onThresholdBreach,
}) => {
  const [data, setData] = useState<Record<string, MetricData[]>>({});
  const [currentValues, setCurrentValues] = useState<Record<string, number>>({});
  const [alerts, setAlerts] = useState<Array<{ id: string; widgetId: string; message: string; severity: 'warning' | 'critical'; timestamp: number }>>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const ws = WebSocketHook('ws://localhost:8080/metrics', {
    onMessage: (message) => {
      const metricData: MetricData = {
        timestamp: Date.now(),
        ...message.data,
      };

      setData((prev) => {
        const updated = { ...prev };
        Object.keys(message.data).forEach((key) => {
          const metricKey = `${message.source}_${key}`;
          if (!updated[metricKey]) {
            updated[metricKey] = [];
          }
          updated[metricKey] = [...updated[metricKey], metricData].slice(-3600);

          if (enableAlerts) {
            const widget = widgets.find((w) => w.id === metricKey || w.metric === metricKey);
            if (widget?.threshold) {
              const currentValue = metricData[key] as number;
              const previousValue = currentValues[metricKey];

              if (previousValue !== undefined) {
                if (currentValue >= widget.threshold.critical && previousValue < widget.threshold.critical) {
                  const alert = {
                    id: `alert-${Date.now()}`,
                    widgetId: metricKey,
                    message: `${widget.title}: CRITICAL - ${currentValue.toFixed(2)} exceeded threshold`,
                    severity: 'critical' as const,
                    timestamp: Date.now(),
                  };
                  setAlerts((prev) => [alert, ...prev].slice(0, 100));
                  onThresholdBreach?.(metricKey, currentValue);
                } else if (currentValue >= widget.threshold.warning && previousValue < widget.threshold.warning) {
                  const alert = {
                    id: `alert-${Date.now()}`,
                    widgetId: metricKey,
                    message: `${widget.title}: WARNING - ${currentValue.toFixed(2)} approaching threshold`,
                    severity: 'warning' as const,
                    timestamp: Date.now(),
                  };
                  setAlerts((prev) => [alert, ...prev].slice(0, 100));
                  onThresholdBreach?.(metricKey, currentValue);
                }
              }
            }
          }
        });
        setCurrentValues((prev) => ({ ...prev, ...message.data }));
        return updated;
      });
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const getWidgetSize = (size: string) => {
    switch (size) {
      case 'small':
        return 'col-span-1 row-span-1';
      case 'medium':
        return 'col-span-2 row-span-1';
      case 'large':
        return 'col-span-2 row-span-2';
      default:
        return 'col-span-1 row-span-1';
    }
  };

  const getThresholdColor = (value: number, threshold?: { warning: number; critical: number }) => {
    if (!threshold) return '#8884d8';
    if (value >= threshold.critical) return '#ff4444';
    if (value >= threshold.warning) return '#ffaa00';
    return '#00C49F';
  };

  const formatValue = (value: number, metric: string) => {
    if (metric.includes('cpu') || metric.includes('memory') || metric.includes('gpu')) {
      return `${value.toFixed(1)}%`;
    }
    if (metric.includes('temperature')) {
      return `${value.toFixed(1)}°C`;
    }
    if (metric.includes('speed') || metric.includes('throughput')) {
      return `${(value / 1024 / 1024).toFixed(2)} MB/s`;
    }
    return value.toFixed(2);
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Real-Time Performance Dashboard</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${ws.isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm font-medium">
              {ws.isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div className="text-sm text-gray-600">
            Last update: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>

      {alerts.length > 0 && (
        <div className="mb-6 space-y-2">
          {alerts.slice(0, 3).map((alert) => (
            <div
              key={alert.id}
              className={`p-3 rounded-lg border-l-4 ${
                alert.severity === 'critical'
                  ? 'bg-red-50 border-red-500 text-red-700'
                  : 'bg-yellow-50 border-yellow-500 text-yellow-700'
              }`}
            >
              <div className="flex justify-between items-center">
                <div className="font-semibold">{alert.message}</div>
                <div className="text-xs">
                  {new Date(alert.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-4 grid-rows-3 gap-4 auto-rows-fr">
        {widgets.map((widget) => {
          const metricKey = widget.metric;
          const widgetData = data[metricKey] || [];
          const currentValue = currentValues[metricKey];
          const latestData = widgetData.slice(-60);

          return (
            <div
              key={widget.id}
              className={`bg-white rounded-lg shadow-lg p-4 ${getWidgetSize(widget.size)} ${
                widget.threshold && currentValue !== undefined
                  ? currentValue >= widget.threshold.critical
                    ? 'border-2 border-red-500'
                    : currentValue >= widget.threshold.warning
                    ? 'border-2 border-yellow-500'
                    : ''
                  : ''
              }`}
            >
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-sm font-semibold text-gray-600">{widget.title}</h3>
                {widget.threshold && (
                  <div className="text-xs text-gray-500">
                    {widget.threshold.warning}/{widget.threshold.critical}
                  </div>
                )}
              </div>

              <div className="mb-2">
                <div className="text-3xl font-bold" style={{ color: getThresholdColor(currentValue || 0, widget.threshold) }}>
                  {currentValue !== undefined ? formatValue(currentValue, metricKey) : '--'}
                </div>
              </div>

              {latestData.length > 1 && (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={latestData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" hide />
                    <YAxis hide />
                    <Tooltip
                      formatter={(value: number) => [formatValue(value, metricKey), widget.title]}
                      labelFormatter={(label) => new Date(label).toLocaleTimeString()}
                    />
                    <Area
                      type="monotone"
                      dataKey={metricKey}
                      stroke={getThresholdColor(currentValue || 0, widget.threshold)}
                      fill={getThresholdColor(currentValue || 0, widget.threshold)}
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}

              {widget.threshold && currentValue !== undefined && (
                <div className="mt-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Warning</span>
                    <span className="text-yellow-600">{widget.threshold.warning}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Critical</span>
                    <span className="text-red-600">{widget.threshold.critical}%</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-6 bg-white rounded-lg shadow-lg p-4">
        <h2 className="text-lg font-semibold mb-4">Alert History</h2>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="text-gray-500 text-sm">No alerts</div>
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-2 rounded border-l-4 ${
                  alert.severity === 'critical'
                    ? 'bg-red-50 border-red-500'
                    : 'bg-yellow-50 border-yellow-500'
                }`}
              >
                <div className="flex justify-between items-center">
                  <div className="text-sm">{alert.message}</div>
                  <div className="text-xs text-gray-500">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default RealTimeDashboard;

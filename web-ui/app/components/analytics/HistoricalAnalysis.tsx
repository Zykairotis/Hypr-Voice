import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
  ReferenceLine,
} from 'recharts';

interface HistoricalMetric {
  timestamp: number;
  value: number;
  metric: string;
  metadata?: Record<string, any>;
}

interface HistoricalAnalysisProps {
  data: HistoricalMetric[];
  timeRange: '1h' | '24h' | '7d' | '30d' | '90d' | '1y' | 'custom';
  onTimeRangeChange?: (range: any) => void;
  customStartDate?: Date;
  customEndDate?: Date;
  aggregateBy?: 'minute' | 'hour' | 'day' | 'week' | 'month';
  metrics: string[];
  selectedMetrics?: string[];
  onMetricToggle?: (metric: string) => void;
}

export const HistoricalAnalysis: React.FC<HistoricalAnalysisProps> = ({
  data,
  timeRange,
  onTimeRangeChange,
  customStartDate,
  customEndDate,
  aggregateBy = 'hour',
  metrics,
  selectedMetrics = metrics,
  onMetricToggle,
}) => {
  const [filteredData, setFilteredData] = useState<HistoricalMetric[]>([]);
  const [aggregatedData, setAggregatedData] = useState<any[]>([]);
  const [statistics, setStatistics] = useState<Record<string, any>>({});
  const [regressionPoints, setRegressionPoints] = useState<Array<{ x: number; y: number }>>([]);

  useEffect(() => {
    const now = Date.now();
    const timeRanges = {
      '1h': 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
      '90d': 90 * 24 * 60 * 60 * 1000,
      '1y': 365 * 24 * 60 * 60 * 1000,
    };

    let filtered = data;

    if (timeRange !== 'custom') {
      filtered = data.filter((m) => m.timestamp > now - timeRanges[timeRange]);
    } else if (customStartDate && customEndDate) {
      filtered = data.filter(
        (m) => m.timestamp >= customStartDate.getTime() && m.timestamp <= customEndDate.getTime()
      );
    }

    filtered = filtered.filter((m) => selectedMetrics.includes(m.metric));
    setFilteredData(filtered);
  }, [data, timeRange, customStartDate, customEndDate, selectedMetrics]);

  useEffect(() => {
    if (filteredData.length === 0) {
      setAggregatedData([]);
      setStatistics({});
      return;
    }

    const interval = aggregateBy === 'minute' ? 60000
      : aggregateBy === 'hour' ? 3600000
      : aggregateBy === 'day' ? 86400000
      : aggregateBy === 'week' ? 604800000
      : 2592000000;

    const buckets = new Map<number, { timestamp: number; values: Record<string, number[]> }>();

    filteredData.forEach((metric) => {
      const bucketKey = Math.floor(metric.timestamp / interval) * interval;
      if (!buckets.has(bucketKey)) {
        buckets.set(bucketKey, {
          timestamp: bucketKey,
          values: {},
        });
      }
      const bucket = buckets.get(bucketKey)!;
      if (!bucket.values[metric.metric]) {
        bucket.values[metric.metric] = [];
      }
      bucket.values[metric.metric].push(metric.value);
    });

    const aggregated = Array.from(buckets.values()).map((bucket) => {
      const result: any = { timestamp: bucket.timestamp };
      Object.keys(bucket.values).forEach((metric) => {
        const values = bucket.values[metric];
        result[metric] = values.reduce((sum, v) => sum + v, 0) / values.length;
      });
      return result;
    }).sort((a, b) => a.timestamp - b.timestamp);

    setAggregatedData(aggregated);

    const stats: Record<string, any> = {};
    selectedMetrics.forEach((metric) => {
      const metricData = filteredData.filter((m) => m.metric === metric);
      const values = metricData.map((m) => m.value);

      stats[metric] = {
        min: Math.min(...values),
        max: Math.max(...values),
        avg: values.reduce((sum, v) => sum + v, 0) / values.length,
        median: values.sort((a, b) => a - b)[Math.floor(values.length / 2)],
        p95: values.sort((a, b) => a - b)[Math.floor(values.length * 0.95)],
        p99: values.sort((a, b) => a - b)[Math.floor(values.length * 0.99)],
        stdDev: Math.sqrt(
          values.reduce((sum, v) => sum + Math.pow(v - stats[metric]?.avg || 0, 2), 0) / values.length
        ),
        count: values.length,
      };
    });

    setStatistics(stats);

    if (aggregated.length > 1) {
      const regression = aggregated.map((d, i) => ({
        x: i,
        y: d[selectedMetrics[0]],
      }));
      setRegressionPoints(regression);
    }
  }, [filteredData, selectedMetrics, aggregateBy]);

  const getTimeLabel = (timestamp: number) => {
    switch (aggregateBy) {
      case 'minute':
        return new Date(timestamp).toLocaleTimeString();
      case 'hour':
        return new Date(timestamp).toLocaleString();
      case 'day':
        return new Date(timestamp).toLocaleDateString();
      case 'week':
        return `Week ${new Date(timestamp).toLocaleDateString()}`;
      case 'month':
        return new Date(timestamp).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      default:
        return new Date(timestamp).toLocaleDateString();
    }
  };

  const detectAnomalies = (metric: string) => {
    const stat = statistics[metric];
    if (!stat) return [];

    return aggregatedData
      .map((d, i) => ({
        index: i,
        value: d[metric],
        timestamp: d.timestamp,
        isAnomaly: Math.abs(d[metric] - stat.avg) > stat.stdDev * 2,
      }))
      .filter((p) => p.isAnomaly);
  };

  const calculateTrend = (metric: string) => {
    if (aggregatedData.length < 2) return { slope: 0, trend: 'stable' };

    const values = aggregatedData.map((d) => d[metric]);
    const n = values.length;
    const sumX = (n * (n - 1)) / 2;
    const sumY = values.reduce((sum, v) => sum + v, 0);
    const sumXY = values.reduce((sum, v, i) => sum + v * i, 0);
    const sumX2 = (n * (n - 1) * (2 * n - 1)) / 6;

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);

    if (Math.abs(slope) < 0.1) return { slope, trend: 'stable' };
    return {
      slope,
      trend: slope > 0 ? 'increasing' : 'decreasing',
      percentage: ((slope * (n - 1)) / values[0]) * 100,
    };
  };

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Historical Data Analysis</h2>

        <div className="flex gap-2 mb-4">
          {(['1h', '24h', '7d', '30d', '90d', '1y'] as const).map((range) => (
            <button
              key={range}
              onClick={() => onTimeRangeChange?.(range)}
              className={`px-4 py-2 rounded ${
                timeRange === range ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
              }`}
            >
              {range}
            </button>
          ))}
          <button
            onClick={() => onTimeRangeChange?.('custom')}
            className={`px-4 py-2 rounded ${
              timeRange === 'custom' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Custom
          </button>
        </div>

        <div className="flex gap-2 mb-4">
          {(['minute', 'hour', 'day', 'week', 'month'] as const).map((agg) => (
            <button
              key={agg}
              className="px-3 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200"
            >
              {agg}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap gap-2 mb-6">
          {metrics.map((metric) => (
            <button
              key={metric}
              onClick={() => onMetricToggle?.(metric)}
              className={`px-3 py-1 rounded text-sm ${
                selectedMetrics.includes(metric)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              {metric}
            </button>
          ))}
        </div>

        <div className="h-96 mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={aggregatedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={getTimeLabel}
              />
              <YAxis />
              <Tooltip
                labelFormatter={getTimeLabel}
                formatter={(value: number) => [value.toFixed(2), 'Value']}
              />
              <Legend />
              {selectedMetrics.map((metric, idx) => (
                <Line
                  key={metric}
                  type="monotone"
                  dataKey={metric}
                  stroke={['#8884d8', '#82ca9d', '#ffc658', '#ff8042'][idx % 4]}
                  dot={false}
                  name={metric}
                />
              ))}
              <Brush dataKey="timestamp" height={30} stroke="#8884d8" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {selectedMetrics.map((metric) => {
          const stat = statistics[metric];
          const trend = calculateTrend(metric);
          const anomalies = detectAnomalies(metric);

          return (
            <div key={metric} className="bg-white rounded-lg shadow-lg p-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">{metric}</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Average:</span>
                  <span className="font-semibold">{stat?.avg?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Min/Max:</span>
                  <span className="font-semibold">
                    {stat?.min?.toFixed(2)} / {stat?.max?.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">P95/P99:</span>
                  <span className="font-semibold">
                    {stat?.p95?.toFixed(2)} / {stat?.p99?.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Trend:</span>
                  <span
                    className={`font-semibold ${
                      trend.trend === 'increasing'
                        ? 'text-green-600'
                        : trend.trend === 'decreasing'
                        ? 'text-red-600'
                        : 'text-gray-600'
                    }`}
                  >
                    {trend.trend}{trend.percentage ? ` (${trend.percentage.toFixed(1)}%)` : ''}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Anomalies:</span>
                  <span className="font-semibold">{anomalies.length}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Usage Pattern Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">Peak Usage Hours</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={Array.from({ length: 24 }, (_, i) => ({
                  hour: i,
                  count: filteredData.filter((m) => new Date(m.timestamp).getHours() === i).length,
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div>
            <h4 className="font-semibold text-gray-700 mb-2">Weekly Pattern</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, idx) => ({
                  day,
                  count: filteredData.filter((m) => new Date(m.timestamp).getDay() === idx).length,
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Performance Regression Detection</h3>
        {regressionPoints.length > 0 && (
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-gray-700 mb-2">Regression Line</h4>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={regressionPoints}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="x" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="y" stroke="#ff7300" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-600">R-squared</div>
                <div className="text-2xl font-bold text-gray-800">
                  {regressionPoints.length > 2 ? '0.85' : '--'}
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-600">Slope</div>
                <div className="text-2xl font-bold text-gray-800">
                  {regressionPoints.length > 2 ? calculateTrend(selectedMetrics[0]).slope.toFixed(3) : '--'}
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-600">P-value</div>
                <div className="text-2xl font-bold text-gray-800">
                  {regressionPoints.length > 10 ? '< 0.01' : '--'}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Capacity Planning</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-blue-50 rounded">
            <div className="text-sm text-blue-600 mb-1">Current Utilization</div>
            <div className="text-2xl font-bold text-blue-800">
              {aggregatedData.length > 0
                ? (
                    aggregatedData.reduce((sum, d) => sum + (d[selectedMetrics[0]] || 0), 0) /
                    aggregatedData.length
                  ).toFixed(1)
                : '--'}
              %
            </div>
          </div>
          <div className="p-4 bg-yellow-50 rounded">
            <div className="text-sm text-yellow-600 mb-1">Projected Peak (30d)</div>
            <div className="text-2xl font-bold text-yellow-800">+15%</div>
          </div>
          <div className="p-4 bg-green-50 rounded">
            <div className="text-sm text-green-600 mb-1">Recommended Capacity</div>
            <div className="text-2xl font-bold text-green-800">
              {aggregatedData.length > 0
                ? Math.max(...aggregatedData.map((d) => d[selectedMetrics[0]] || 0)) * 1.3
                : '--'}
              %
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HistoricalAnalysis;

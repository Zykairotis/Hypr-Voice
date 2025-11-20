import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';

interface TTSMetrics {
  id: string;
  timestamp: number;
  provider: string;
  voice: string;
  textLength: number;
  synthesisTime: number;
  audioGenerationTime: number;
  totalTime: number;
  success: boolean;
  errorMessage?: string;
  quality?: number;
  cost: number;
}

interface TTSPerformanceProps {
  data: TTSMetrics[];
  providerFilter?: string;
  voiceFilter?: string;
  realTime?: boolean;
  refreshInterval?: number;
}

export const TTSPerformance: React.FC<TTSPerformanceProps> = ({
  data,
  providerFilter,
  voiceFilter,
  realTime = false,
  refreshInterval = 3000,
}) => {
  const [metrics, setMetrics] = useState<TTSMetrics[]>(data);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('1h');

  useEffect(() => {
    if (realTime) {
      const interval = setInterval(() => {
        setMetrics((prev) => {
          const newMetric: TTSMetrics = {
            id: `tts-${Date.now()}`,
            timestamp: Date.now(),
            provider: ['OpenAI', 'Azure', 'Google', 'AWS'].sort(() => Math.random() - 0.5)[0],
            voice: ['voice-1', 'voice-2', 'voice-3'].sort(() => Math.random() - 0.5)[0],
            textLength: Math.floor(Math.random() * 500) + 50,
            synthesisTime: Math.random() * 2000 + 500,
            audioGenerationTime: Math.random() * 1000 + 200,
            totalTime: 0,
            success: Math.random() > 0.1,
            quality: Math.random() * 40 + 60,
            cost: Math.random() * 0.5 + 0.1,
          };
          newMetric.totalTime = newMetric.synthesisTime + newMetric.audioGenerationTime;
          return [...prev, newMetric].slice(-1000);
        });
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [realTime, refreshInterval]);

  const filteredData = metrics.filter((m) => {
    if (providerFilter && m.provider !== providerFilter) return false;
    if (voiceFilter && m.voice !== voiceFilter) return false;

    const now = Date.now();
    const timeRanges = {
      '1h': 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
    };
    return m.timestamp > now - timeRanges[timeRange];
  });

  const providers = Array.from(new Set(filteredData.map((m) => m.provider)));

  const providerMetrics = providers.map((provider) => {
    const providerData = filteredData.filter((m) => m.provider === provider);
    const total = providerData.length;
    const successful = providerData.filter((m) => m.success).length;
    const avgSynthesisTime =
      providerData.reduce((sum, m) => sum + m.synthesisTime, 0) / Math.max(1, total);
    const avgQuality =
      providerData.reduce((sum, m) => sum + (m.quality || 0), 0) / Math.max(1, total);
    const totalCost = providerData.reduce((sum, m) => sum + m.cost, 0);
    const avgCharsPerSec =
      providerData.reduce((sum, m) => sum + m.textLength, 0) /
      Math.max(1, providerData.reduce((sum, m) => sum + m.totalTime, 0) / 1000);

    return {
      provider,
      total,
      successRate: (successful / Math.max(1, total)) * 100,
      avgSynthesisTime,
      avgQuality,
      totalCost,
      avgCharsPerSec,
      avgCost: totalCost / Math.max(1, total),
    };
  });

  const timeSeriesData = filteredData
    .sort((a, b) => a.timestamp - b.timestamp)
    .map((m) => ({
      time: new Date(m.timestamp).toLocaleTimeString(),
      synthesisTime: m.synthesisTime,
      audioTime: m.audioGenerationTime,
      charsPerSec: (m.textLength / m.totalTime) * 1000,
      quality: m.quality || 0,
      cost: m.cost,
    }));

  const providerComparison = providerMetrics.map((pm) => ({
    provider: pm.provider,
    'Success Rate': pm.successRate,
    'Avg Quality': pm.avgQuality,
    'Synthesis Speed': (pm.avgSynthesisTime / 1000).toFixed(2),
    'Cost per Request': pm.avgCost.toFixed(4),
  }));

  const qualityDistribution = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100].map(
    (range) => {
      const nextRange = range + 10;
      const count = filteredData.filter((m) => {
        const q = m.quality || 0;
        return q >= range && q < nextRange;
      }).length;
      return {
        range: `${range}-${nextRange}%`,
        count,
      };
    }
  );

  const costEfficiencyData = filteredData.map((m) => ({
    cost: m.cost,
    quality: m.quality || 0,
    provider: m.provider,
    speed: m.totalTime,
  }));

  const getStatusColor = (success: boolean) => {
    return success ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100';
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">TTS Performance Analytics</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setTimeRange('1h')}
            className={`px-3 py-1 rounded ${
              timeRange === '1h' ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}
          >
            1H
          </button>
          <button
            onClick={() => setTimeRange('24h')}
            className={`px-3 py-1 rounded ${
              timeRange === '24h' ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}
          >
            24H
          </button>
          <button
            onClick={() => setTimeRange('7d')}
            className={`px-3 py-1 rounded ${
              timeRange === '7d' ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}
          >
            7D
          </button>
          <button
            onClick={() => setTimeRange('30d')}
            className={`px-3 py-1 rounded ${
              timeRange === '30d' ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}
          >
            30D
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {providerMetrics.map((pm) => (
          <div key={pm.provider} className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-sm font-semibold text-gray-600 mb-2">{pm.provider}</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Requests</span>
                <span className="font-semibold">{pm.total}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Success Rate</span>
                <span className="font-semibold">{pm.successRate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Avg Speed</span>
                <span className="font-semibold">
                  {(pm.avgSynthesisTime / 1000).toFixed(2)}s
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Avg Quality</span>
                <span className="font-semibold">{pm.avgQuality.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total Cost</span>
                <span className="font-semibold">${pm.totalCost.toFixed(4)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Synthesis Time Trends</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis />
              <Tooltip formatter={(value: number) => [`${(value / 1000).toFixed(2)}s`, '']} />
              <Legend />
              <Line
                type="monotone"
                dataKey="synthesisTime"
                stroke="#8884d8"
                name="Synthesis Time"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="audioTime"
                stroke="#82ca9d"
                name="Audio Generation"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Synthesis Speed (chars/sec)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis />
              <Tooltip formatter={(value) => [`${value.toFixed(1)}`, 'chars/sec']} />
              <Area
                type="monotone"
                dataKey="charsPerSec"
                stroke="#ffc658"
                fill="#ffc658"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Quality Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={qualityDistribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Cost vs Quality</h3>
          <ResponsiveContainer width="100%" height={250}>
            <ComposedChart data={costEfficiencyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="cost" />
              <YAxis dataKey="quality" />
              <Tooltip />
              <Bar dataKey="speed" fill="#82ca9d" opacity={0.5} />
              <Line type="monotone" dataKey="quality" stroke="#8884d8" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Provider Performance Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={providerComparison}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="provider" />
            <YAxis yAxisId="left" orientation="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="Success Rate" fill="#82ca9d" />
            <Bar yAxisId="left" dataKey="Avg Quality" fill="#8884d8" />
            <Bar yAxisId="right" dataKey="Synthesis Speed" fill="#ffc658" />
            <Bar yAxisId="right" dataKey="Cost per Request" fill="#ff8042" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Recent TTS Requests</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Time</th>
                <th className="text-left py-2">Provider</th>
                <th className="text-left py-2">Voice</th>
                <th className="text-right py-2">Text Length</th>
                <th className="text-right py-2">Synthesis Time</th>
                <th className="text-right py-2">Audio Time</th>
                <th className="text-right py-2">Total Time</th>
                <th className="text-right py-2">Quality</th>
                <th className="text-center py-2">Status</th>
                <th className="text-right py-2">Cost</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.slice(-20).map((m) => (
                <tr key={m.id} className="border-b hover:bg-gray-50">
                  <td className="py-2 text-sm">{new Date(m.timestamp).toLocaleTimeString()}</td>
                  <td className="py-2">{m.provider}</td>
                  <td className="py-2">{m.voice}</td>
                  <td className="py-2 text-right">{m.textLength} chars</td>
                  <td className="py-2 text-right">{(m.synthesisTime / 1000).toFixed(2)}s</td>
                  <td className="py-2 text-right">{(m.audioGenerationTime / 1000).toFixed(2)}s</td>
                  <td className="py-2 text-right">{(m.totalTime / 1000).toFixed(2)}s</td>
                  <td className="py-2 text-right">{m.quality?.toFixed(1)}%</td>
                  <td className="py-2 text-center">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                        m.success
                      )}`}
                    >
                      {m.success ? 'SUCCESS' : 'FAILED'}
                    </span>
                  </td>
                  <td className="py-2 text-right">${m.cost.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Overall Success Rate</h4>
          <div className="text-3xl font-bold text-green-600">
            {((filteredData.filter((m) => m.success).length / Math.max(1, filteredData.length)) * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500 mt-1">
            {filteredData.filter((m) => m.success).length} of {filteredData.length} requests
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Average Speed</h4>
          <div className="text-3xl font-bold text-blue-600">
            {(filteredData.reduce((sum, m) => sum + m.totalTime, 0) / Math.max(1, filteredData.length) / 1000).toFixed(2)}s
          </div>
          <div className="text-sm text-gray-500 mt-1">
            Average synthesis time
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Total Cost</h4>
          <div className="text-3xl font-bold text-purple-600">
            ${filteredData.reduce((sum, m) => sum + m.cost, 0).toFixed(4)}
          </div>
          <div className="text-sm text-gray-500 mt-1">
            ${(filteredData.reduce((sum, m) => sum + m.cost, 0) / Math.max(1, filteredData.length)).toFixed(4)} avg
          </div>
        </div>
      </div>
    </div>
  );
};

export default TTSPerformance;

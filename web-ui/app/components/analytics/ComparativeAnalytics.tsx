import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';

interface BenchmarkResult {
  id: string;
  name: string;
  timestamp: number;
  metrics: Record<string, number>;
  category: string;
  configuration?: Record<string, any>;
  environment?: string;
}

interface ABTestResult {
  id: string;
  name: string;
  startDate: number;
  endDate?: number;
  variantA: {
    name: string;
    metrics: Record<string, number>;
  };
  variantB: {
    name: string;
    metrics: Record<string, number>;
  };
  status: 'running' | 'completed' | 'paused';
  winner?: 'A' | 'B' | 'inconclusive';
}

interface ComparativeAnalyticsProps {
  benchmarks: BenchmarkResult[];
  abTests: ABTestResult[];
  timeRange: '24h' | '7d' | '30d' | '90d';
}

export const ComparativeAnalytics: React.FC<ComparativeAnalyticsProps> = ({
  benchmarks,
  abTests,
  timeRange,
}) => {
  const [selectedBenchmark, setSelectedBenchmark] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [comparisonMode, setComparisonMode] = useState<'beforeAfter' | 'abTest' | 'configuration'>('beforeAfter');

  const categories = Array.from(new Set(benchmarks.map((b) => b.category)));

  const filteredBenchmarks = benchmarks.filter((b) => {
    if (selectedCategory && b.category !== selectedCategory) return false;
    if (selectedBenchmark && b.id !== selectedBenchmark) return false;
    return true;
  });

  const latestBenchmark = selectedBenchmark
    ? benchmarks.find((b) => b.id === selectedBenchmark)
    : filteredBenchmarks.reduce((latest, b) =>
        !latest || b.timestamp > latest.timestamp ? b : latest
      );

  const comparisonData = filteredBenchmarks
    .sort((a, b) => a.timestamp - b.timestamp)
    .map((b) => ({
      name: b.name,
      timestamp: new Date(b.timestamp).toLocaleDateString(),
      ...b.metrics,
    }));

  const metrics = latestBenchmark ? Object.keys(latestBenchmark.metrics) : [];

  const getTopPerformers = (metric: string, count = 3) => {
    return filteredBenchmarks
      .sort((a, b) => (b.metrics[metric] || 0) - (a.metrics[metric] || 0))
      .slice(0, count)
      .map((b, idx) => ({
        rank: idx + 1,
        name: b.name,
        value: b.metrics[metric] || 0,
      }));
  };

  const renderBeforeAfterComparison = () => {
    if (!latestBenchmark || filteredBenchmarks.length < 2) {
      return <div className="text-gray-500">Not enough data for comparison</div>;
    }

    const sorted = filteredBenchmarks.sort((a, b) => b.timestamp - a.timestamp);
    const before = sorted[1];
    const after = sorted[0];

    const comparison = metrics.map((metric) => ({
      metric,
      before: before.metrics[metric] || 0,
      after: after.metrics[metric] || 0,
      improvement: before.metrics[metric]
        ? ((after.metrics[metric] - before.metrics[metric]) / before.metrics[metric]) * 100
        : 0,
    }));

    return (
      <div className="space-y-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-lg font-semibold mb-4">Performance Changes</h4>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={comparison}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="before" fill="#8884d8" name="Before" />
              <Bar dataKey="after" fill="#82ca9d" name="After" />
              <Line
                type="monotone"
                dataKey="improvement"
                stroke="#ff7300"
                name="Improvement %"
                yAxisId="right"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <h4 className="font-semibold mb-2">Before: {before.name}</h4>
            <div className="text-sm text-gray-600">
              {new Date(before.timestamp).toLocaleDateString()}
            </div>
            <div className="mt-2 space-y-1">
              {Object.entries(before.metrics).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-600">{key}:</span>
                  <span className="font-semibold">{value.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <h4 className="font-semibold mb-2">After: {after.name}</h4>
            <div className="text-sm text-gray-600">
              {new Date(after.timestamp).toLocaleDateString()}
            </div>
            <div className="mt-2 space-y-1">
              {Object.entries(after.metrics).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-600">{key}:</span>
                  <span className="font-semibold">{value.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderABTestComparison = () => {
    const runningTests = abTests.filter((t) => t.status === 'running' || t.status === 'completed');

    return (
      <div className="space-y-6">
        {runningTests.map((test) => {
          const comparison = Object.keys(test.variantA.metrics).map((metric) => ({
            metric,
            variantA: test.variantA.metrics[metric] || 0,
            variantB: test.variantB.metrics[metric] || 0,
            difference: (test.variantB.metrics[metric] || 0) - (test.variantA.metrics[metric] || 0),
          }));

          const winner = test.winner === 'A' ? test.variantA.name : test.winner === 'B' ? test.variantB.name : 'Inconclusive';

          return (
            <div key={test.id} className="bg-white p-4 rounded-lg shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-lg font-semibold">{test.name}</h4>
                  <div className="text-sm text-gray-600">
                    {new Date(test.startDate).toLocaleDateString()} -{' '}
                    {test.endDate ? new Date(test.endDate).toLocaleDateString() : 'Ongoing'}
                  </div>
                </div>
                <div className="text-right">
                  <span className={`px-3 py-1 rounded-full text-sm ${
                    test.status === 'completed' ? 'bg-green-100 text-green-800' :
                    test.status === 'running' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {test.status.toUpperCase()}
                  </span>
                  {test.winner && (
                    <div className="mt-2 text-sm font-semibold">
                      Winner: {winner}
                    </div>
                  )}
                </div>
              </div>

              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={comparison}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="variantA" fill="#8884d8" name={test.variantA.name} />
                  <Bar dataKey="variantB" fill="#82ca9d" name={test.variantB.name} />
                </BarChart>
              </ResponsiveContainer>

              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <h5 className="font-semibold text-sm mb-2">{test.variantA.name}</h5>
                  <div className="space-y-1">
                    {Object.entries(test.variantA.metrics).map(([key, value]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-gray-600">{key}:</span>
                        <span className="font-semibold">{value.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h5 className="font-semibold text-sm mb-2">{test.variantB.name}</h5>
                  <div className="space-y-1">
                    {Object.entries(test.variantB.metrics).map(([key, value]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-gray-600">{key}:</span>
                        <span className="font-semibold">{value.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderConfigurationComparison = () => {
    return (
      <div className="space-y-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-lg font-semibold mb-4">Performance by Configuration</h4>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              {metrics.map((metric, idx) => (
                <Bar
                  key={metric}
                  dataKey={metric}
                  fill={['#8884d8', '#82ca9d', '#ffc658', '#ff8042'][idx % 4]}
                  name={metric}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {metrics.slice(0, 3).map((metric) => (
            <div key={metric} className="bg-white p-4 rounded-lg shadow">
              <h5 className="font-semibold mb-2">Top Performers - {metric}</h5>
              <div className="space-y-2">
                {getTopPerformers(metric).map((performer) => (
                  <div key={performer.name} className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-gray-600">
                        #{performer.rank}
                      </span>
                      <span className="text-sm">{performer.name}</span>
                    </div>
                    <span className="font-bold text-blue-600">
                      {performer.value.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-lg font-semibold mb-4">Configuration Details</h4>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Name</th>
                  <th className="text-left py-2">Configuration</th>
                  <th className="text-left py-2">Environment</th>
                  <th className="text-right py-2">Date</th>
                </tr>
              </thead>
              <tbody>
                {filteredBenchmarks.slice(0, 10).map((benchmark) => (
                  <tr key={benchmark.id} className="border-b">
                    <td className="py-2 font-semibold">{benchmark.name}</td>
                    <td className="py-2 text-sm">
                      {benchmark.configuration
                        ? Object.entries(benchmark.configuration)
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(', ')
                        : 'Default'}
                    </td>
                    <td className="py-2">{benchmark.environment || 'Production'}</td>
                    <td className="py-2 text-right text-sm">
                      {new Date(benchmark.timestamp).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold text-gray-800">Comparative Analytics</h2>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex gap-4 mb-6">
          <div className="flex gap-2">
            <button
              onClick={() => setComparisonMode('beforeAfter')}
              className={`px-4 py-2 rounded ${
                comparisonMode === 'beforeAfter'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Before/After
            </button>
            <button
              onClick={() => setComparisonMode('abTest')}
              className={`px-4 py-2 rounded ${
                comparisonMode === 'abTest'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              A/B Tests
            </button>
            <button
              onClick={() => setComparisonMode('configuration')}
              className={`px-4 py-2 rounded ${
                comparisonMode === 'configuration'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Configuration
            </button>
          </div>

          <select
            value={selectedCategory || ''}
            onChange={(e) => setSelectedCategory(e.target.value || null)}
            className="px-3 py-2 border rounded"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {comparisonMode === 'beforeAfter' && renderBeforeAfterComparison()}
        {comparisonMode === 'abTest' && renderABTestComparison()}
        {comparisonMode === 'configuration' && renderConfigurationComparison()}
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Performance Trends Over Time</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={comparisonData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Legend />
            {metrics.map((metric, idx) => (
              <Line
                key={metric}
                type="monotone"
                dataKey={metric}
                stroke={['#8884d8', '#82ca9d', '#ffc658', '#ff8042'][idx % 4]}
                dot={false}
                name={metric}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {latestBenchmark && metrics.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">
            Benchmark Details: {latestBenchmark.name}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(latestBenchmark.metrics).map(([key, value]) => (
              <div key={key} className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600 mb-1">{key}</div>
                <div className="text-2xl font-bold text-gray-800">{value.toFixed(2)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ComparativeAnalytics;

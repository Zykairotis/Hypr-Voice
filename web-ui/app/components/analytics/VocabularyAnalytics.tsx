import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

interface VocabularyMetrics {
  id: string;
  timestamp: number;
  application: string;
  category: string;
  keywordsMatched: number;
  keywordsTotal: number;
  matchAccuracy: number;
  contextExtracted: number;
  contextTotal: number;
  switchingFrequency: number;
  customizationImpact: number;
  processingTime: number;
  success: boolean;
}

interface VocabularyAnalyticsProps {
  data: VocabularyMetrics[];
  appFilter?: string;
  categoryFilter?: string;
  realTime?: boolean;
  refreshInterval?: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

export const VocabularyAnalytics: React.FC<VocabularyAnalyticsProps> = ({
  data,
  appFilter,
  categoryFilter,
  realTime = false,
  refreshInterval = 5000,
}) => {
  const [metrics, setMetrics] = useState<VocabularyMetrics[]>(data);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [selectedApp, setSelectedApp] = useState<string | null>(null);

  useEffect(() => {
    if (realTime) {
      const interval = setInterval(() => {
        setMetrics((prev) => {
          const newMetric: VocabularyMetrics = {
            id: `vocab-${Date.now()}`,
            timestamp: Date.now(),
            application: ['Code Editor', 'Browser', 'Terminal', 'IDE'].sort(() => Math.random() - 0.5)[0],
            category: ['Development', 'Web', 'System', 'Productivity'].sort(() => Math.random() - 0.5)[0],
            keywordsMatched: Math.floor(Math.random() * 50) + 10,
            keywordsTotal: Math.floor(Math.random() * 20) + 50,
            matchAccuracy: Math.random() * 20 + 80,
            contextExtracted: Math.floor(Math.random() * 10) + 5,
            contextTotal: 15,
            switchingFrequency: Math.random() * 5,
            customizationImpact: Math.random() * 30 + 10,
            processingTime: Math.random() * 100 + 20,
            success: Math.random() > 0.05,
          };
          return [...prev, newMetric].slice(-2000);
        });
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [realTime, refreshInterval]);

  const filteredData = metrics.filter((m) => {
    if (appFilter && m.application !== appFilter) return false;
    if (categoryFilter && m.category !== categoryFilter) return false;

    const now = Date.now();
    const timeRanges = {
      '1h': 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
    };
    return m.timestamp > now - timeRanges[timeRange];
  });

  const applications = Array.from(new Set(filteredData.map((m) => m.application)));
  const categories = Array.from(new Set(filteredData.map((m) => m.category)));

  const appMetrics = applications.map((app) => {
    const appData = filteredData.filter((m) => m.application === app);
    const total = appData.length;
    const avgAccuracy =
      appData.reduce((sum, m) => sum + m.matchAccuracy, 0) / Math.max(1, total);
    const avgContext = appData.reduce((sum, m) => sum + m.contextExtracted, 0) / Math.max(1, total);
    const avgSwitching = appData.reduce((sum, m) => sum + m.switchingFrequency, 0) / Math.max(1, total);
    const avgCustomization = appData.reduce((sum, m) => sum + m.customizationImpact, 0) / Math.max(1, total);
    const totalSwitching = appData.reduce((sum, m) => sum + m.switchingFrequency, 0);
    const avgProcessingTime = appData.reduce((sum, m) => sum + m.processingTime, 0) / Math.max(1, total);

    return {
      application: app,
      totalRequests: total,
      avgAccuracy,
      avgContextExtraction: (avgContext / 15) * 100,
      avgSwitchingFrequency: avgSwitching,
      totalSwitching,
      avgCustomizationImpact: avgCustomization,
      avgProcessingTime,
    };
  });

  const categoryMetrics = categories.map((category) => {
    const catData = filteredData.filter((m) => m.category === category);
    const total = catData.length;
    const avgAccuracy =
      catData.reduce((sum, m) => sum + m.matchAccuracy, 0) / Math.max(1, total);
    const keywordEffectiveness = catData.reduce((sum, m) => sum + (m.keywordsMatched / m.keywordsTotal), 0) / Math.max(1, total) * 100;
    const avgProcessingTime = catData.reduce((sum, m) => sum + m.processingTime, 0) / Math.max(1, total);

    return {
      category,
      totalRequests: total,
      avgAccuracy,
      keywordEffectiveness,
      avgProcessingTime,
    };
  });

  const timeSeriesData = filteredData
    .sort((a, b) => a.timestamp - b.timestamp)
    .map((m) => ({
      time: new Date(m.timestamp).toLocaleTimeString(),
      accuracy: m.matchAccuracy,
      keywords: (m.keywordsMatched / m.keywordsTotal) * 100,
      context: (m.contextExtracted / m.contextTotal) * 100,
      switching: m.switchingFrequency,
      customization: m.customizationImpact,
    }));

  const switchingDistribution = Array.from(new Set(filteredData.map((m) => m.switchingFrequency))).map(
    (freq) => ({
      range: `${(freq * 2).toFixed(1)}-${(freq * 2 + 1).toFixed(1)}/sec`,
      count: filteredData.filter((m) => Math.abs(m.switchingFrequency - freq) < 0.1).length,
    })
  ).slice(0, 10);

  const appDistribution = appMetrics.map((am) => ({
    name: am.application,
    value: am.totalRequests,
  }));

  const radarData = selectedApp
    ? [
        {
          metric: 'Match Accuracy',
          value: appMetrics.find((am) => am.application === selectedApp)?.avgAccuracy || 0,
          fullMark: 100,
        },
        {
          metric: 'Context Extraction',
          value: appMetrics.find((am) => am.application === selectedApp)?.avgContextExtraction || 0,
          fullMark: 100,
        },
        {
          metric: 'Keyword Effectiveness',
          value: (appMetrics.find((am) => am.application === selectedApp)?.avgAccuracy || 0) * 0.9,
          fullMark: 100,
        },
        {
          metric: 'Customization Impact',
          value: appMetrics.find((am) => am.application === selectedApp)?.avgCustomizationImpact || 0,
          fullMark: 100,
        },
        {
          metric: 'Processing Speed',
          value: 100 - Math.min(100, (appMetrics.find((am) => am.application === selectedApp)?.avgProcessingTime || 0)),
          fullMark: 100,
        },
      ]
    : [];

  const keywordEffectiveness = filteredData.map((m) => ({
    time: new Date(m.timestamp).toLocaleTimeString(),
    effectiveness: (m.keywordsMatched / m.keywordsTotal) * 100,
    accuracy: m.matchAccuracy,
  }));

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Vocabulary Analytics</h2>
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
        {appMetrics.map((am) => (
          <div
            key={am.application}
            className={`bg-white p-4 rounded-lg shadow cursor-pointer hover:shadow-lg transition ${
              selectedApp === am.application ? 'ring-2 ring-blue-500' : ''
            }`}
            onClick={() => setSelectedApp(selectedApp === am.application ? null : am.application)}
          >
            <h3 className="text-sm font-semibold text-gray-600 mb-2">{am.application}</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Requests</span>
                <span className="font-semibold">{am.totalRequests}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Accuracy</span>
                <span className="font-semibold">{am.avgAccuracy.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Context Extract</span>
                <span className="font-semibold">{am.avgContextExtraction.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Switching Freq</span>
                <span className="font-semibold">{am.avgSwitchingFrequency.toFixed(2)}/sec</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Customization</span>
                <span className="font-semibold">{am.avgCustomizationImpact.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Match Accuracy Trends</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="accuracy"
                stroke="#8884d8"
                name="Match Accuracy (%)"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="keywords"
                stroke="#82ca9d"
                name="Keyword Effectiveness (%)"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="context"
                stroke="#ffc658"
                name="Context Extraction (%)"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Vocabulary Switching Frequency</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="switching"
                stroke="#ff8042"
                fill="#ff8042"
                fillOpacity={0.6}
                name="Switches/sec"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Application Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={appDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => entry.name}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {appDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Category Performance</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={categoryMetrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="avgAccuracy" fill="#8884d8" name="Avg Accuracy" />
              <Bar dataKey="keywordEffectiveness" fill="#82ca9d" name="Keyword Effectiveness" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Keyword Effectiveness Over Time</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={keywordEffectiveness}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="effectiveness"
                stroke="#82ca9d"
                name="Effectiveness (%)"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="accuracy"
                stroke="#8884d8"
                name="Accuracy (%)"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Switching Frequency Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={switchingDistribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#ff8042" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {selectedApp && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">
            Performance Radar - {selectedApp}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" />
              <PolarRadiusAxis domain={[0, 100]} />
              <Radar
                name="Performance"
                dataKey="value"
                stroke="#8884d8"
                fill="#8884d8"
                fillOpacity={0.6}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Vocabulary Performance Details</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Time</th>
                <th className="text-left py-2">Application</th>
                <th className="text-left py-2">Category</th>
                <th className="text-right py-2">Keywords Matched</th>
                <th className="text-right py-2">Match Accuracy</th>
                <th className="text-right py-2">Context Extract</th>
                <th className="text-right py-2">Switching Freq</th>
                <th className="text-right py-2">Customization</th>
                <th className="text-right py-2">Processing Time</th>
                <th className="text-center py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.slice(-20).map((m) => (
                <tr key={m.id} className="border-b hover:bg-gray-50">
                  <td className="py-2 text-sm">{new Date(m.timestamp).toLocaleTimeString()}</td>
                  <td className="py-2">{m.application}</td>
                  <td className="py-2">{m.category}</td>
                  <td className="py-2 text-right">
                    {m.keywordsMatched}/{m.keywordsTotal}
                  </td>
                  <td className="py-2 text-right">{m.matchAccuracy.toFixed(1)}%</td>
                  <td className="py-2 text-right">
                    {m.contextExtracted}/{m.contextTotal}
                  </td>
                  <td className="py-2 text-right">{m.switchingFrequency.toFixed(2)}/sec</td>
                  <td className="py-2 text-right">{m.customizationImpact.toFixed(1)}%</td>
                  <td className="py-2 text-right">{m.processingTime.toFixed(2)}ms</td>
                  <td className="py-2 text-center">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        m.success ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'
                      }`}
                    >
                      {m.success ? 'SUCCESS' : 'FAILED'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Avg Match Accuracy</h4>
          <div className="text-3xl font-bold text-blue-600">
            {(filteredData.reduce((sum, m) => sum + m.matchAccuracy, 0) / Math.max(1, filteredData.length)).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500 mt-1">Across all applications</div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Total Switches</h4>
          <div className="text-3xl font-bold text-purple-600">
            {filteredData.reduce((sum, m) => sum + m.switchingFrequency, 0).toFixed(1)}
          </div>
          <div className="text-sm text-gray-500 mt-1">Vocabulary transitions</div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Avg Customization</h4>
          <div className="text-3xl font-bold text-green-600">
            {(filteredData.reduce((sum, m) => sum + m.customizationImpact, 0) / Math.max(1, filteredData.length)).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500 mt-1">User impact</div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Total Requests</h4>
          <div className="text-3xl font-bold text-orange-600">
            {filteredData.length.toLocaleString()}
          </div>
          <div className="text-sm text-gray-500 mt-1">Processing events</div>
        </div>
      </div>
    </div>
  );
};

export default VocabularyAnalytics;

import React, { useState, useEffect } from 'react';
import SystemPerformance from './SystemPerformance';
import AgentPerformance from './AgentPerformance';
import TTSPerformance from './TTSPerformance';
import VocabularyAnalytics from './VocabularyAnalytics';
import RealTimeDashboard from './RealTimeDashboard';
import HistoricalAnalysis from './HistoricalAnalysis';
import ComparativeAnalytics from './ComparativeAnalytics';
import AlertsEngine from './AlertsEngine';
import PerformanceOptimization from './PerformanceOptimization';
import ExportReports from './ExportReports';
import { useAnalyticsData } from './hooks/useAnalyticsData';
import { useWebSocket } from './hooks/useWebSocket';

interface AnalyticsDashboardProps {
  className?: string;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ className = '' }) => {
  const [activeView, setActiveView] = useState<'overview' | 'system' | 'agents' | 'tts' | 'vocabulary' | 'realtime' | 'historical' | 'comparative' | 'alerts' | 'optimization' | 'export'>('overview');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);

  const { data, loading, error, refresh } = useAnalyticsData({
    autoRefresh,
    refreshInterval,
  });

  const { isConnected, lastMessage } = useWebSocket('ws://localhost:8080/analytics');

  const widgets = [
    { id: 'cpu', title: 'CPU Usage', metric: 'cpu_usage', threshold: { warning: 70, critical: 90 }, size: 'medium' as const },
    { id: 'memory', title: 'Memory Usage', metric: 'memory_usage', threshold: { warning: 75, critical: 85 }, size: 'medium' as const },
    { id: 'response', title: 'Response Time', metric: 'response_time', threshold: { warning: 500, critical: 1000 }, size: 'medium' as const },
    { id: 'throughput', title: 'Throughput', metric: 'throughput', size: 'medium' as const },
    { id: 'errors', title: 'Error Rate', metric: 'error_rate', threshold: { warning: 5, critical: 10 }, size: 'small' as const },
    { id: 'agents', title: 'Active Agents', metric: 'active_agents', size: 'small' as const },
  ];

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          Error loading analytics data: {error.message}
        </div>
      );
    }

    switch (activeView) {
      case 'overview':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="text-sm text-gray-600">System Health</div>
                <div className="text-3xl font-bold text-green-600 mt-2">Good</div>
                <div className="text-sm text-gray-500 mt-1">98.5% uptime</div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="text-sm text-gray-600">Active Agents</div>
                <div className="text-3xl font-bold text-blue-600 mt-2">{data?.agents?.length || 0}</div>
                <div className="text-sm text-gray-500 mt-1">Across {data?.agents?.length || 0} agents</div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="text-sm text-gray-600">Avg Response Time</div>
                <div className="text-3xl font-bold text-purple-600 mt-2">
                  {(data?.avgResponseTime || 0).toFixed(0)}ms
                </div>
                <div className="text-sm text-gray-500 mt-1">Last 24 hours</div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="text-sm text-gray-600">Active Alerts</div>
                <div className="text-3xl font-bold text-orange-600 mt-2">{data?.alerts?.length || 0}</div>
                <div className="text-sm text-gray-500 mt-1">{data?.criticalAlerts || 0} critical</div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <button
                  onClick={() => setActiveView('realtime')}
                  className="p-4 border rounded-lg hover:shadow-md transition text-left"
                >
                  <div className="text-2xl mb-2">📊</div>
                  <div className="font-semibold">Real-Time View</div>
                  <div className="text-sm text-gray-600">Live metrics dashboard</div>
                </button>
                <button
                  onClick={() => setActiveView('alerts')}
                  className="p-4 border rounded-lg hover:shadow-md transition text-left"
                >
                  <div className="text-2xl mb-2">🔔</div>
                  <div className="font-semibold">Manage Alerts</div>
                  <div className="text-sm text-gray-600">Configure notifications</div>
                </button>
                <button
                  onClick={() => setActiveView('optimization')}
                  className="p-4 border rounded-lg hover:shadow-md transition text-left"
                >
                  <div className="text-2xl mb-2">⚡</div>
                  <div className="font-semibold">Optimization</div>
                  <div className="text-sm text-gray-600">Performance tips</div>
                </button>
                <button
                  onClick={() => setActiveView('export')}
                  className="p-4 border rounded-lg hover:shadow-md transition text-left"
                >
                  <div className="text-2xl mb-2">📤</div>
                  <div className="font-semibold">Export Data</div>
                  <div className="text-sm text-gray-600">Generate reports</div>
                </button>
              </div>
            </div>

            <RealTimeDashboard
              widgets={widgets}
              refreshInterval={refreshInterval}
              enableAlerts={true}
              onThresholdBreach={(widgetId, value) => {
                console.warn(`Threshold breached for ${widgetId}: ${value}`);
              }}
            />
          </div>
        );

      case 'system':
        return <SystemPerformance data={data?.systemMetrics || []} realTime={autoRefresh} />;

      case 'agents':
        return <AgentPerformance data={data?.agentMetrics || []} realTime={autoRefresh} />;

      case 'tts':
        return <TTSPerformance data={data?.ttsMetrics || []} realTime={autoRefresh} />;

      case 'vocabulary':
        return <VocabularyAnalytics data={data?.vocabularyMetrics || []} realTime={autoRefresh} />;

      case 'realtime':
        return (
          <RealTimeDashboard
            widgets={widgets}
            refreshInterval={refreshInterval}
            enableAlerts={true}
            onThresholdBreach={(widgetId, value) => console.warn(`Alert: ${widgetId} = ${value}`)}
          />
        );

      case 'historical':
        return (
          <HistoricalAnalysis
            data={data?.historicalMetrics || []}
            timeRange="7d"
            metrics={data?.metricList || []}
            onTimeRangeChange={(range) => console.log('Time range changed:', range)}
            onMetricToggle={(metric) => console.log('Metric toggled:', metric)}
          />
        );

      case 'comparative':
        return (
          <ComparativeAnalytics
            benchmarks={data?.benchmarks || []}
            abTests={data?.abTests || []}
            timeRange="7d"
          />
        );

      case 'alerts':
        return (
          <AlertsEngine
            rules={data?.alertRules || []}
            alerts={data?.alerts || []}
            onRuleCreate={(rule) => console.log('Rule created:', rule)}
            onRuleUpdate={(id, updates) => console.log('Rule updated:', id, updates)}
            onRuleDelete={(id) => console.log('Rule deleted:', id)}
            onAlertAcknowledge={(id, user) => console.log('Alert acknowledged:', id, user)}
            onAlertResolve={(id) => console.log('Alert resolved:', id)}
          />
        );

      case 'optimization':
        return (
          <PerformanceOptimization
            bottlenecks={data?.bottlenecks || []}
            recommendations={data?.optimizationRecommendations || []}
          />
        );

      case 'export':
        return (
          <ExportReports
            onExport={(options) => {
              console.log('Export initiated:', options);
              refresh();
            }}
            availableMetrics={data?.metricList || []}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className={`bg-gray-50 min-h-screen ${className}`}>
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Analytics Dashboard</h1>
              <div className="ml-4 flex items-center">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="ml-2 text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm text-gray-600">Auto-refresh</span>
                <select
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
                  className="text-sm border rounded px-2 py-1"
                  disabled={!autoRefresh}
                >
                  <option value={1000}>1s</option>
                  <option value={5000}>5s</option>
                  <option value={10000}>10s</option>
                  <option value={30000}>30s</option>
                  <option value={60000}>1m</option>
                </select>
              </div>

              <button
                onClick={() => refresh()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-1 overflow-x-auto pb-2">
            {[
              { id: 'overview', label: 'Overview', icon: '📊' },
              { id: 'system', label: 'System', icon: '💻' },
              { id: 'agents', label: 'Agents', icon: '🤖' },
              { id: 'tts', label: 'TTS', icon: '🔊' },
              { id: 'vocabulary', label: 'Vocabulary', icon: '📚' },
              { id: 'realtime', label: 'Real-Time', icon: '⚡' },
              { id: 'historical', label: 'Historical', icon: '📈' },
              { id: 'comparative', label: 'Comparative', icon: '🔄' },
              { id: 'alerts', label: 'Alerts', icon: '🔔' },
              { id: 'optimization', label: 'Optimization', icon: '⚡' },
              { id: 'export', label: 'Export', icon: '📤' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveView(tab.id as any)}
                className={`px-4 py-3 whitespace-nowrap border-b-2 transition ${
                  activeView === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {renderContent()}
      </main>

      {lastMessage && (
        <div className="fixed bottom-4 right-4 bg-white p-4 rounded-lg shadow-lg border max-w-md">
          <div className="text-sm font-semibold mb-1">Real-Time Update</div>
          <div className="text-xs text-gray-600">{JSON.stringify(lastMessage.data).slice(0, 100)}...</div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;

import React, { useState } from 'react';

interface ExportOptions {
  format: 'pdf' | 'csv' | 'json' | 'html' | 'xlsx';
  dateRange: 'today' | 'yesterday' | '7d' | '30d' | '90d' | 'custom';
  startDate?: string;
  endDate?: string;
  metrics: string[];
  includeCharts: boolean;
  includeRawData: boolean;
  template: 'executive' | 'technical' | 'detailed' | 'summary';
}

interface ExportReportsProps {
  onExport: (options: ExportOptions) => void;
  availableMetrics: string[];
}

export const ExportReports: React.FC<ExportReportsProps> = ({
  onExport,
  availableMetrics,
}) => {
  const [options, setOptions] = useState<ExportOptions>({
    format: 'pdf',
    dateRange: '7d',
    metrics: [],
    includeCharts: true,
    includeRawData: false,
    template: 'detailed',
  });

  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);

  const handleMetricToggle = (metric: string) => {
    setOptions((prev) => ({
      ...prev,
      metrics: prev.metrics.includes(metric)
        ? prev.metrics.filter((m) => m !== metric)
        : [...prev.metrics, metric],
    }));
  };

  const handleExport = async () => {
    setIsExporting(true);
    setExportProgress(0);

    const progressInterval = setInterval(() => {
      setExportProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);

    try {
      await new Promise((resolve) => setTimeout(resolve, 2000));

      clearInterval(progressInterval);
      setExportProgress(100);

      setTimeout(() => {
        onExport(options);
        setIsExporting(false);
        setExportProgress(0);
      }, 500);
    } catch (error) {
      clearInterval(progressInterval);
      setIsExporting(false);
      setExportProgress(0);
      console.error('Export failed:', error);
    }
  };

  const exportHistory = [
    { id: '1', name: 'Weekly Performance Report', format: 'PDF', date: '2024-01-15', size: '2.4 MB' },
    { id: '2', name: 'Agent Metrics Summary', format: 'CSV', date: '2024-01-14', size: '856 KB' },
    { id: '3', name: 'TTS Analysis', format: 'XLSX', date: '2024-01-13', size: '1.8 MB' },
    { id: '4', name: 'System Health Dashboard', format: 'HTML', date: '2024-01-12', size: '3.2 MB' },
  ];

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold text-gray-800">Export & Reporting</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Generate New Report</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Export Format</label>
              <div className="grid grid-cols-3 gap-2">
                {['pdf', 'csv', 'json', 'html', 'xlsx'].map((format) => (
                  <button
                    key={format}
                    onClick={() => setOptions((prev) => ({ ...prev, format: format as any }))}
                    className={`px-3 py-2 rounded border text-sm font-semibold uppercase ${
                      options.format === format
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-700 border-gray-300 hover:border-blue-600'
                    }`}
                  >
                    {format}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Date Range</label>
              <select
                value={options.dateRange}
                onChange={(e) =>
                  setOptions((prev) => ({
                    ...prev,
                    dateRange: e.target.value as any,
                  }))
                }
                className="w-full px-3 py-2 border rounded"
              >
                <option value="today">Today</option>
                <option value="yesterday">Yesterday</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
                <option value="custom">Custom Range</option>
              </select>

              {options.dateRange === 'custom' && (
                <div className="grid grid-cols-2 gap-2 mt-2">
                  <input
                    type="date"
                    value={options.startDate}
                    onChange={(e) =>
                      setOptions((prev) => ({ ...prev, startDate: e.target.value }))
                    }
                    className="px-3 py-2 border rounded"
                  />
                  <input
                    type="date"
                    value={options.endDate}
                    onChange={(e) =>
                      setOptions((prev) => ({ ...prev, endDate: e.target.value }))
                    }
                    className="px-3 py-2 border rounded"
                  />
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Template</label>
              <select
                value={options.template}
                onChange={(e) =>
                  setOptions((prev) => ({ ...prev, template: e.target.value as any }))
                }
                className="w-full px-3 py-2 border rounded"
              >
                <option value="executive">Executive Summary</option>
                <option value="technical">Technical Report</option>
                <option value="detailed">Detailed Analysis</option>
                <option value="summary">Quick Summary</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Metrics to Include</label>
              <div className="border rounded p-3 max-h-40 overflow-y-auto space-y-2">
                <button
                  onClick={() => setOptions((prev) => ({ ...prev, metrics: availableMetrics }))}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Select All
                </button>
                {availableMetrics.map((metric) => (
                  <label key={metric} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={options.metrics.includes(metric)}
                      onChange={() => handleMetricToggle(metric)}
                    />
                    <span className="text-sm">{metric}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={options.includeCharts}
                  onChange={(e) =>
                    setOptions((prev) => ({ ...prev, includeCharts: e.target.checked }))
                  }
                />
                <span className="text-sm">Include Charts & Graphs</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={options.includeRawData}
                  onChange={(e) =>
                    setOptions((prev) => ({ ...prev, includeRawData: e.target.checked }))
                  }
                />
                <span className="text-sm">Include Raw Data Tables</span>
              </label>
            </div>

            {isExporting && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Exporting...</span>
                  <span>{exportProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${exportProgress}%` }}
                  />
                </div>
              </div>
            )}

            <button
              onClick={handleExport}
              disabled={isExporting || options.metrics.length === 0}
              className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold"
            >
              {isExporting ? 'Exporting...' : 'Generate Report'}
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Export History</h3>

          <div className="space-y-2">
            {exportHistory.map((exportItem) => (
              <div
                key={exportItem.id}
                className="p-3 border rounded hover:bg-gray-50 flex items-center justify-between"
              >
                <div>
                  <div className="font-medium text-gray-800">{exportItem.name}</div>
                  <div className="text-sm text-gray-600">
                    {exportItem.format} • {exportItem.date} • {exportItem.size}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                    Download
                  </button>
                  <button className="px-3 py-1 text-sm border rounded hover:bg-gray-50">
                    View
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-semibold text-blue-800 mb-2">API Access</h4>
            <p className="text-sm text-blue-700 mb-3">
              Access your analytics data programmatically via our REST API
            </p>
            <code className="block bg-blue-100 p-3 rounded text-sm text-blue-900 overflow-x-auto">
              GET /api/v1/analytics/export?format=csv&metrics=cpu,memory&range=7d
            </code>
            <button className="mt-3 px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              View API Documentation
            </button>
          </div>

          <div className="mt-4 p-4 bg-green-50 rounded-lg">
            <h4 className="font-semibold text-green-800 mb-2">Scheduled Reports</h4>
            <p className="text-sm text-green-700 mb-3">
              Set up automatic report generation and delivery
            </p>
            <button className="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700">
              Create Schedule
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Report Templates</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 border rounded hover:shadow-lg transition cursor-pointer">
            <div className="text-3xl mb-2">📊</div>
            <h4 className="font-semibold mb-1">Executive Summary</h4>
            <p className="text-sm text-gray-600">
              High-level KPIs and trends for leadership
            </p>
          </div>

          <div className="p-4 border rounded hover:shadow-lg transition cursor-pointer">
            <div className="text-3xl mb-2">⚙️</div>
            <h4 className="font-semibold mb-1">Technical Report</h4>
            <p className="text-sm text-gray-600">
              Detailed system metrics and performance data
            </p>
          </div>

          <div className="p-4 border rounded hover:shadow-lg transition cursor-pointer">
            <div className="text-3xl mb-2">🔍</div>
            <h4 className="font-semibold mb-1">Detailed Analysis</h4>
            <p className="text-sm text-gray-600">
              Comprehensive analysis with recommendations
            </p>
          </div>

          <div className="p-4 border rounded hover:shadow-lg transition cursor-pointer">
            <div className="text-3xl mb-2">📈</div>
            <h4 className="font-semibold mb-1">Quick Summary</h4>
            <p className="text-sm text-gray-600">
              Key metrics in a concise format
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Integration Options</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 border rounded">
            <h4 className="font-semibold mb-2">Slack Integration</h4>
            <p className="text-sm text-gray-600 mb-3">
              Receive reports directly in your Slack channels
            </p>
            <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              Connect
            </button>
          </div>

          <div className="p-4 border rounded">
            <h4 className="font-semibold mb-2">Email Reports</h4>
            <p className="text-sm text-gray-600 mb-3">
              Schedule automated email deliveries
            </p>
            <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              Configure
            </button>
          </div>

          <div className="p-4 border rounded">
            <h4 className="font-semibold mb-2">Webhook</h4>
            <p className="text-sm text-gray-600 mb-3">
              Trigger exports via webhook calls
            </p>
            <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              Setup
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportReports;

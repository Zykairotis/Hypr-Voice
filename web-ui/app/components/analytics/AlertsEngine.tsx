import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  metric: string;
  condition: 'greater_than' | 'less_than' | 'equals' | 'between' | 'changes';
  threshold: number;
  thresholdSecondary?: number;
  duration: number;
  severity: 'info' | 'warning' | 'critical';
  enabled: boolean;
  actions: AlertAction[];
  tags: string[];
}

export interface AlertAction {
  type: 'email' | 'webhook' | 'sms' | 'slack' | 'dashboard';
  target: string;
  template?: string;
  enabled: boolean;
}

export interface Alert {
  id: string;
  ruleId: string;
  ruleName: string;
  timestamp: number;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  value: number;
  acknowledged: boolean;
  acknowledgedBy?: string;
  acknowledgedAt?: number;
  resolved: boolean;
  resolvedAt?: number;
}

interface AlertsEngineProps {
  rules: AlertRule[];
  alerts: Alert[];
  currentMetricValue?: number;
  onRuleCreate?: (rule: AlertRule) => void;
  onRuleUpdate?: (ruleId: string, updates: Partial<AlertRule>) => void;
  onRuleDelete?: (ruleId: string) => void;
  onAlertAcknowledge?: (alertId: string, user: string) => void;
  onAlertResolve?: (alertId: string) => void;
}

export const AlertsEngine: React.FC<AlertsEngineProps> = ({
  rules,
  alerts,
  currentMetricValue,
  onRuleCreate,
  onRuleUpdate,
  onRuleDelete,
  onAlertAcknowledge,
  onAlertResolve,
}) => {
  const [activeTab, setActiveTab] = useState<'rules' | 'alerts' | 'history'>('rules');
  const [showCreateRule, setShowCreateRule] = useState(false);
  const [selectedSeverity, setSelectedSeverity] = useState<'all' | 'info' | 'warning' | 'critical'>('all');

  const activeAlerts = alerts.filter((a) => !a.resolved);
  const acknowledgedAlerts = alerts.filter((a) => a.acknowledged && !a.resolved);
  const recentAlerts = alerts
    .filter((a) => a.timestamp > Date.now() - 24 * 60 * 60 * 1000)
    .sort((a, b) => b.timestamp - a.timestamp);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'info':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return '🔴';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '⚪';
    }
  };

  const filteredAlerts =
    selectedSeverity === 'all'
      ? activeAlerts
      : activeAlerts.filter((a) => a.severity === selectedSeverity);

  const alertHistoryData = recentAlerts.map((alert, idx) => ({
    time: new Date(alert.timestamp).toLocaleTimeString(),
    [alert.severity]: 1,
    index: idx,
  }));

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Alerts & Notifications</h2>
        <button
          onClick={() => setShowCreateRule(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Create Alert Rule
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Active Alerts</div>
          <div className="text-3xl font-bold text-red-600">{activeAlerts.length}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Acknowledged</div>
          <div className="text-3xl font-bold text-yellow-600">{acknowledgedAlerts.length}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Rules Active</div>
          <div className="text-3xl font-bold text-blue-600">
            {rules.filter((r) => r.enabled).length}
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Last 24h</div>
          <div className="text-3xl font-bold text-green-600">{recentAlerts.length}</div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="border-b">
          <div className="flex gap-4 px-6 pt-4">
            <button
              onClick={() => setActiveTab('rules')}
              className={`pb-2 border-b-2 ${
                activeTab === 'rules'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600'
              }`}
            >
              Alert Rules ({rules.length})
            </button>
            <button
              onClick={() => setActiveTab('alerts')}
              className={`pb-2 border-b-2 ${
                activeTab === 'alerts'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600'
              }`}
            >
              Active Alerts ({activeAlerts.length})
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`pb-2 border-b-2 ${
                activeTab === 'history'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600'
              }`}
            >
              History
            </button>
          </div>
        </div>

        <div className="p-6">
          {activeTab === 'rules' && (
            <div className="space-y-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Search rules..."
                  className="flex-1 px-3 py-2 border rounded"
                />
                <select className="px-3 py-2 border rounded">
                  <option>All Metrics</option>
                  <option>CPU Usage</option>
                  <option>Memory</option>
                  <option>Response Time</option>
                </select>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Name</th>
                      <th className="text-left py-2">Metric</th>
                      <th className="text-left py-2">Condition</th>
                      <th className="text-left py-2">Severity</th>
                      <th className="text-left py-2">Duration</th>
                      <th className="text-left py-2">Status</th>
                      <th className="text-right py-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rules.map((rule) => (
                      <tr key={rule.id} className="border-b hover:bg-gray-50">
                        <td className="py-3">
                          <div className="font-semibold">{rule.name}</div>
                          <div className="text-sm text-gray-600">{rule.description}</div>
                        </td>
                        <td className="py-3">{rule.metric}</td>
                        <td className="py-3">
                          {rule.condition === 'greater_than' && `> ${rule.threshold}`}
                          {rule.condition === 'less_than' && `< ${rule.threshold}`}
                          {rule.condition === 'equals' && `= ${rule.threshold}`}
                          {rule.condition === 'between' && `${rule.threshold} - ${rule.thresholdSecondary}`}
                          {rule.condition === 'changes' && 'Changed'}
                        </td>
                        <td className="py-3">
                          <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(rule.severity)}`}>
                            {rule.severity.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3">{rule.duration}s</td>
                        <td className="py-3">
                          <label className="inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={rule.enabled}
                              onChange={(e) => onRuleUpdate?.(rule.id, { enabled: e.target.checked })}
                              className="sr-only peer"
                            />
                            <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                          </label>
                        </td>
                        <td className="py-3 text-right">
                          <button
                            onClick={() => onRuleDelete?.(rule.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'alerts' && (
            <div className="space-y-4">
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setSelectedSeverity('all')}
                  className={`px-3 py-1 rounded ${
                    selectedSeverity === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'
                  }`}
                >
                  All ({activeAlerts.length})
                </button>
                <button
                  onClick={() => setSelectedSeverity('critical')}
                  className={`px-3 py-1 rounded ${
                    selectedSeverity === 'critical' ? 'bg-red-600 text-white' : 'bg-gray-200'
                  }`}
                >
                  Critical ({activeAlerts.filter((a) => a.severity === 'critical').length})
                </button>
                <button
                  onClick={() => setSelectedSeverity('warning')}
                  className={`px-3 py-1 rounded ${
                    selectedSeverity === 'warning' ? 'bg-yellow-600 text-white' : 'bg-gray-200'
                  }`}
                >
                  Warning ({activeAlerts.filter((a) => a.severity === 'warning').length})
                </button>
              </div>

              <div className="space-y-2">
                {filteredAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)}`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xl">{getSeverityIcon(alert.severity)}</span>
                          <span className="font-semibold">{alert.ruleName}</span>
                        </div>
                        <div className="text-sm">{alert.message}</div>
                        <div className="text-xs mt-1">
                          Value: {alert.value.toFixed(2)} |{' '}
                          {new Date(alert.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {!alert.acknowledged && (
                          <button
                            onClick={() => onAlertAcknowledge?.(alert.id, 'Current User')}
                            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                          >
                            Acknowledge
                          </button>
                        )}
                        <button
                          onClick={() => onAlertResolve?.(alert.id)}
                          className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
                        >
                          Resolve
                        </button>
                      </div>
                    </div>
                    {alert.acknowledged && (
                      <div className="mt-2 text-xs">
                        Acknowledged by {alert.acknowledgedBy} at{' '}
                        {alert.acknowledgedAt ? new Date(alert.acknowledgedAt).toLocaleString() : ''}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-6">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={alertHistoryData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="critical" stroke="#ef4444" name="Critical" />
                    <Line type="monotone" dataKey="warning" stroke="#f59e0b" name="Warning" />
                    <Line type="monotone" dataKey="info" stroke="#3b82f6" name="Info" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Time</th>
                      <th className="text-left py-2">Rule</th>
                      <th className="text-left py-2">Severity</th>
                      <th className="text-left py-2">Message</th>
                      <th className="text-left py-2">Value</th>
                      <th className="text-left py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentAlerts.slice(0, 50).map((alert) => (
                      <tr key={alert.id} className="border-b hover:bg-gray-50">
                        <td className="py-2 text-sm">
                          {new Date(alert.timestamp).toLocaleString()}
                        </td>
                        <td className="py-2">{alert.ruleName}</td>
                        <td className="py-2">
                          <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(alert.severity)}`}>
                            {alert.severity.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-2 text-sm">{alert.message}</td>
                        <td className="py-2 text-sm">{alert.value.toFixed(2)}</td>
                        <td className="py-2">
                          {alert.resolved ? (
                            <span className="text-green-600">Resolved</span>
                          ) : alert.acknowledged ? (
                            <span className="text-yellow-600">Acknowledged</span>
                          ) : (
                            <span className="text-red-600">Active</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {showCreateRule && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full">
            <h3 className="text-xl font-bold mb-4">Create Alert Rule</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target as HTMLFormElement);
                const newRule: AlertRule = {
                  id: `rule-${Date.now()}`,
                  name: formData.get('name') as string,
                  description: formData.get('description') as string,
                  metric: formData.get('metric') as string,
                  condition: formData.get('condition') as any,
                  threshold: parseFloat(formData.get('threshold') as string),
                  thresholdSecondary: formData.get('thresholdSecondary')
                    ? parseFloat(formData.get('thresholdSecondary') as string)
                    : undefined,
                  duration: parseInt(formData.get('duration') as string),
                  severity: formData.get('severity') as any,
                  enabled: true,
                  actions: [],
                  tags: [],
                };
                onRuleCreate?.(newRule);
                setShowCreateRule(false);
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm font-medium mb-1">Rule Name</label>
                <input name="name" type="text" required className="w-full px-3 py-2 border rounded" />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea name="description" required className="w-full px-3 py-2 border rounded" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Metric</label>
                  <select name="metric" required className="w-full px-3 py-2 border rounded">
                    <option>cpu_usage</option>
                    <option>memory_usage</option>
                    <option>response_time</option>
                    <option>error_rate</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Condition</label>
                  <select name="condition" required className="w-full px-3 py-2 border rounded">
                    <option value="greater_than">Greater Than</option>
                    <option value="less_than">Less Than</option>
                    <option value="equals">Equals</option>
                    <option value="between">Between</option>
                    <option value="changes">Changes</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Threshold</label>
                  <input name="threshold" type="number" step="0.01" required className="w-full px-3 py-2 border rounded" />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Threshold 2 (optional)</label>
                  <input name="thresholdSecondary" type="number" step="0.01" className="w-full px-3 py-2 border rounded" />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Duration (seconds)</label>
                  <input name="duration" type="number" required defaultValue="60" className="w-full px-3 py-2 border rounded" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Severity</label>
                <select name="severity" required className="w-full px-3 py-2 border rounded">
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowCreateRule(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                  Create Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertsEngine;

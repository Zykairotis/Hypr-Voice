import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
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
  ScatterChart,
  Scatter,
} from 'recharts';

interface AgentMetrics {
  agentId: string;
  agentType: string;
  timestamp: number;
  responseTime: number;
  tasksCompleted: number;
  tasksSucceeded: number;
  tasksFailed: number;
  tokensUsed: number;
  efficiency: number;
  status: 'idle' | 'busy' | 'error' | 'offline';
  subagents?: Array<{
    id: string;
    performance: number;
  }>;
}

interface AgentPerformanceProps {
  data: AgentMetrics[];
  agentFilter?: string;
  realTime?: boolean;
  refreshInterval?: number;
}

export const AgentPerformance: React.FC<AgentPerformanceProps> = ({
  data,
  agentFilter,
  realTime = false,
  refreshInterval = 2000,
}) => {
  const [metrics, setMetrics] = useState<AgentMetrics[]>(data);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  useEffect(() => {
    if (realTime) {
      const interval = setInterval(() => {
        setMetrics((prev) => {
          const updated = prev.map((agent) => ({
            ...agent,
            timestamp: Date.now(),
            responseTime: agent.responseTime + (Math.random() - 0.5) * 50,
            tasksCompleted: agent.tasksCompleted + (Math.random() > 0.7 ? 1 : 0),
            efficiency: Math.min(100, Math.max(0, agent.efficiency + (Math.random() - 0.5) * 5)),
          }));
          return updated;
        });
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [realTime, refreshInterval]);

  const filteredData = agentFilter
    ? metrics.filter((m) => m.agentType === agentFilter)
    : metrics;

  const aggregatedMetrics = filteredData.reduce((acc, agent) => {
    const existing = acc.get(agent.agentType) || {
      agentType: agent.agentType,
      totalResponseTime: 0,
      totalTasks: 0,
      totalSuccess: 0,
      totalFailure: 0,
      totalTokens: 0,
      totalEfficiency: 0,
      count: 0,
    };
    existing.totalResponseTime += agent.responseTime;
    existing.totalTasks += agent.tasksCompleted;
    existing.totalSuccess += agent.tasksSucceeded;
    existing.totalFailure += agent.tasksFailed;
    existing.totalTokens += agent.tokensUsed;
    existing.totalEfficiency += agent.efficiency;
    existing.count += 1;
    acc.set(agent.agentType, existing);
    return acc;
  }, new Map());

  const typeData = Array.from(aggregatedMetrics.values()).map((agg) => ({
    agentType: agg.agentType,
    avgResponseTime: agg.totalResponseTime / agg.count,
    avgEfficiency: agg.totalEfficiency / agg.count,
    successRate: (agg.totalSuccess / Math.max(1, agg.totalTasks)) * 100,
    totalTasks: agg.totalTasks,
  }));

  const timeSeriesData = filteredData
    .slice(-100)
    .map((m) => ({
      time: new Date(m.timestamp).toLocaleTimeString(),
      responseTime: m.responseTime,
      efficiency: m.efficiency,
      tokens: m.tokensUsed,
    }));

  const efficiencyVsTasks = filteredData.map((m) => ({
    tasks: m.tasksCompleted,
    efficiency: m.efficiency,
    agent: m.agentId,
  }));

  const radarData = selectedAgent
    ? [
        {
          metric: 'Response Time',
          value: 100 - Math.min(100, (filteredData.find((m) => m.agentId === selectedAgent)?.responseTime || 0) / 10),
          fullMark: 100,
        },
        {
          metric: 'Efficiency',
          value: filteredData.find((m) => m.agentId === selectedAgent)?.efficiency || 0,
          fullMark: 100,
        },
        {
          metric: 'Success Rate',
          value:
            filteredData.length > 0
              ? (filteredData.find((m) => m.agentId === selectedAgent)?.tasksSucceeded || 0) /
                Math.max(
                  1,
                  (filteredData.find((m) => m.agentId === selectedAgent)?.tasksCompleted || 0)
                ) *
                100
              : 0,
          fullMark: 100,
        },
        {
          metric: 'Token Usage',
          value: 100 - Math.min(100, (filteredData.find((m) => m.agentId === selectedAgent)?.tokensUsed || 0) / 1000),
          fullMark: 100,
        },
      ]
    : [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'idle':
        return 'text-green-600 bg-green-100';
      case 'busy':
        return 'text-blue-600 bg-blue-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      case 'offline':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-800">Agent Performance Analytics</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {typeData.map((type) => (
          <div key={type.agentType} className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-sm font-semibold text-gray-600 mb-2">{type.agentType}</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Avg Response</span>
                <span className="font-semibold">{type.avgResponseTime.toFixed(0)}ms</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Efficiency</span>
                <span className="font-semibold">{type.avgEfficiency.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Success Rate</span>
                <span className="font-semibold">{type.successRate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total Tasks</span>
                <span className="font-semibold">{type.totalTasks}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Response Time Trends</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="responseTime"
                stroke="#8884d8"
                name="Response Time (ms)"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Efficiency Trends</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="efficiency"
                stroke="#82ca9d"
                name="Efficiency (%)"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Performance by Agent Type</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={typeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="agentType" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="avgEfficiency" fill="#8884d8" name="Avg Efficiency (%)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Efficiency vs Tasks Completed</h3>
          <ResponsiveContainer width="100%" height={250}>
            <ScatterChart data={efficiencyVsTasks}>
              <CartesianGrid />
              <XAxis dataKey="tasks" type="number" />
              <YAxis dataKey="efficiency" type="number" domain={[0, 100]} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="Agents" data={efficiencyVsTasks} fill="#8884d8" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Agent Status Overview</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Agent ID</th>
                <th className="text-left py-2">Type</th>
                <th className="text-center py-2">Status</th>
                <th className="text-right py-2">Response Time</th>
                <th className="text-right py-2">Tasks</th>
                <th className="text-right py-2">Success Rate</th>
                <th className="text-right py-2">Efficiency</th>
                <th className="text-right py-2">Tokens Used</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map((agent) => {
                const successRate =
                  agent.tasksCompleted > 0
                    ? (agent.tasksSucceeded / agent.tasksCompleted) * 100
                    : 0;
                return (
                  <tr
                    key={agent.agentId}
                    className="border-b hover:bg-gray-50 cursor-pointer"
                    onClick={() => setSelectedAgent(agent.agentId)}
                  >
                    <td className="py-2">{agent.agentId}</td>
                    <td className="py-2">{agent.agentType}</td>
                    <td className="py-2 text-center">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                          agent.status
                        )}`}
                      >
                        {agent.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2 text-right">{agent.responseTime.toFixed(0)}ms</td>
                    <td className="py-2 text-right">{agent.tasksCompleted}</td>
                    <td className="py-2 text-right">{successRate.toFixed(1)}%</td>
                    <td className="py-2 text-right">{agent.efficiency.toFixed(1)}%</td>
                    <td className="py-2 text-right">{agent.tokensUsed.toLocaleString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {selectedAgent && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">
            Performance Radar - {selectedAgent}
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
        <h3 className="text-lg font-semibold mb-4">Token Usage Analytics</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={timeSeriesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" hide />
            <YAxis />
            <Tooltip formatter={(value: number) => [value.toLocaleString(), 'Tokens']} />
            <Legend />
            <Line
              type="monotone"
              dataKey="tokens"
              stroke="#ffc658"
              name="Tokens Used"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {filteredData.some((m) => m.subagents && m.subagents.length > 0) && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Subagent Performance</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredData
              .filter((m) => m.subagents)
              .map((agent) =>
                agent.subagents?.map((subagent) => (
                  <div key={subagent.id} className="border rounded-lg p-3">
                    <div className="text-sm font-semibold text-gray-700">{subagent.id}</div>
                    <div className="mt-2">
                      <div className="text-sm text-gray-600">Parent: {agent.agentId}</div>
                      <div className="text-lg font-bold text-blue-600">
                        {subagent.performance.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                ))
              )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentPerformance;

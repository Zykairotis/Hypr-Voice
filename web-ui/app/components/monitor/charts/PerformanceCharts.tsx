"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { TrendingUp, TrendingDown, Activity, Clock, Zap } from "lucide-react";
import { motion } from "framer-motion";
import { useWebSocket } from "lib/websocket";

export default function PerformanceCharts() {
  const { metrics, events } = useWebSocket();

  const performanceData = useMemo(() => {
    const data = [];
    const now = Date.now();
    const points = 20;

    for (let i = points - 1; i >= 0; i--) {
      const timestamp = now - i * 5000;
      data.push({
        time: new Date(timestamp).toLocaleTimeString(),
        responseTime: metrics?.averageResponseTime || Math.random() * 100,
        throughput: metrics?.requestsPerSecond || Math.random() * 20,
        errorRate: metrics?.errorRate || Math.random() * 5,
        cpu: metrics?.cpu || Math.random() * 100,
        memory: metrics?.memory || Math.random() * 100,
      });
    }

    return data;
  }, [metrics]);

  const agentMetrics = useMemo(() => {
    const agentMap = new Map();
    events.forEach(event => {
      if (event.agentId && event.type === "agent_output") {
        const count = agentMap.get(event.agentId) || 0;
        agentMap.set(event.agentId, count + 1);
      }
    });

    return Array.from(agentMap.entries())
      .slice(0, 10)
      .map(([name, value]) => ({ name, value }));
  }, [events]);

  const toolUsage = useMemo(() => {
    const toolMap = new Map();
    events.forEach(event => {
      if (event.type === "tool_execution") {
        const tool = event.data.tool || "unknown";
        const count = toolMap.get(tool) || 0;
        toolMap.set(tool, count + 1);
      }
    });

    return Array.from(toolMap.entries())
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);
  }, [events]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-black/90 border border-white/20 rounded-lg p-3 shadow-xl">
          <p className="text-white/70 text-sm mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Avg Response Time"
          value={`${metrics?.averageResponseTime?.toFixed(0) || 0}ms`}
          trend={-12}
          icon={Clock}
          color="text-blue-400"
        />
        <MetricCard
          title="Throughput"
          value={`${metrics?.requestsPerSecond?.toFixed(1) || 0}/s`}
          trend={8}
          icon={Zap}
          color="text-green-400"
        />
        <MetricCard
          title="Error Rate"
          value={`${metrics?.errorRate?.toFixed(2) || 0}%`}
          trend={-5}
          icon={Activity}
          color={metrics && metrics.errorRate > 5 ? "text-red-400" : "text-yellow-400"}
        />
        <MetricCard
          title="Active Agents"
          value={metrics?.activeAgents?.toString() || "0"}
          trend={15}
          icon={Activity}
          color="text-purple-400"
        />
      </div>

      {/* Response Time Chart */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardHeader>
          <CardTitle>Response Time Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="time" stroke="rgba(255,255,255,0.5)" />
              <YAxis stroke="rgba(255,255,255,0.5)" />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line
                type="monotone"
                dataKey="responseTime"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: '#3b82f6', r: 4 }}
                name="Response Time (ms)"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Throughput and Error Rate */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
          <CardHeader>
            <CardTitle>Request Throughput</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="time" stroke="rgba(255,255,255,0.5)" />
                <YAxis stroke="rgba(255,255,255,0.5)" />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="throughput"
                  stroke="#10b981"
                  fill="url(#colorThroughput)"
                  fillOpacity={0.3}
                  name="Requests/sec"
                />
                <defs>
                  <linearGradient id="colorThroughput" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
          <CardHeader>
            <CardTitle>Error Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="time" stroke="rgba(255,255,255,0.5)" />
                <YAxis stroke="rgba(255,255,255,0.5)" />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="errorRate"
                  stroke="#f59e0b"
                  fill="url(#colorError)"
                  fillOpacity={0.3}
                  name="Error Rate (%)"
                />
                <defs>
                  <linearGradient id="colorError" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                  </linearGradient>
                </defs>
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Resource Usage */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardHeader>
          <CardTitle>System Resource Usage</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="time" stroke="rgba(255,255,255,0.5)" />
              <YAxis stroke="rgba(255,255,255,0.5)" />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line
                type="monotone"
                dataKey="cpu"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={{ fill: '#8b5cf6', r: 4 }}
                name="CPU %"
              />
              <Line
                type="monotone"
                dataKey="memory"
                stroke="#06b6d4"
                strokeWidth={2}
                dot={{ fill: '#06b6d4', r: 4 }}
                name="Memory %"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Agent Output Distribution */}
      {agentMetrics.length > 0 && (
        <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
          <CardHeader>
            <CardTitle>Agent Output Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={agentMetrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" />
                <YAxis stroke="rgba(255,255,255,0.5)" />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" fill="#3b82f6" name="Outputs" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Tool Usage */}
      {toolUsage.length > 0 && (
        <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
          <CardHeader>
            <CardTitle>Tool Usage Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={toolUsage} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis type="number" stroke="rgba(255,255,255,0.5)" />
                <YAxis dataKey="name" type="category" stroke="rgba(255,255,255,0.5)" width={100} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" fill="#10b981" name="Executions" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function MetricCard({
  title,
  value,
  trend,
  icon: Icon,
  color
}: {
  title: string;
  value: string;
  trend: number;
  icon: any;
  color: string;
}) {
  return (
    <motion.div whileHover={{ scale: 1.02 }}>
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <Icon className={`w-6 h-6 ${color}`} />
            <div className={`flex items-center gap-1 text-sm ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {trend > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              {Math.abs(trend)}%
            </div>
          </div>
          <p className="text-sm text-white/60">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
        </CardContent>
      </Card>
    </motion.div>
  );
}

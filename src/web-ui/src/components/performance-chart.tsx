'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PerformanceMetrics } from '@/types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { TrendingUp, Cpu, HardDrive, Clock, Zap } from 'lucide-react';
import { formatDuration, formatDate } from '@/lib/utils';

interface PerformanceChartProps {
  metrics: PerformanceMetrics[];
  className?: string;
}

export function PerformanceChart({ metrics, className }: PerformanceChartProps) {
  const sortedMetrics = [...metrics].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
  const latestMetrics = sortedMetrics[0];

  const chartData = sortedMetrics.map(metric => ({
    time: metric.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    cpu: metric.cpu,
    memory: metric.memory / 1024 / 1024, // Convert to MB
    transcriptionLatency: metric.transcriptionLatency / 1000, // Convert to seconds
    llmLatency: metric.llmLatency / 1000, // Convert to seconds
    networkIn: metric.network.inbound,
    networkOut: metric.network.outbound,
  }));

  const formatTooltipValue = (value: number, name: string) => {
    switch (name) {
      case 'memory':
        return [`${value.toFixed(1)} MB`, 'Memory'];
      case 'transcriptionLatency':
        return [`${value.toFixed(2)} s`, 'Transcription'];
      case 'llmLatency':
        return [`${value.toFixed(2)} s`, 'LLM'];
      case 'networkIn':
        return [`${value.toFixed(0)} B/s`, 'Network In'];
      case 'networkOut':
        return [`${value.toFixed(0)} B/s`, 'Network Out'];
      default:
        return [`${value.toFixed(1)}%`, name.charAt(0).toUpperCase() + name.slice(1)];
    }
  };

  return (
    <div className={className}>
      {/* Current Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestMetrics ? `${latestMetrics.cpu.toFixed(1)}%` : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              Current processor load
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestMetrics ? `${(latestMetrics.memory / 1024 / 1024).toFixed(0)} MB` : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              RAM usage
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Transcription</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestMetrics ? `${(latestMetrics.transcriptionLatency / 1000).toFixed(1)}s` : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              Average latency
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">LLM Processing</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestMetrics ? `${(latestMetrics.llmLatency / 1000).toFixed(1)}s` : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              AI response time
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU and Memory Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Resource Usage
            </CardTitle>
            <CardDescription>
              CPU and memory usage over time (last 60 data points)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  fontSize={12}
                  tick={{ fontSize: 12 }}
                />
                <YAxis fontSize={12} />
                <Tooltip
                  formatter={formatTooltipValue}
                  labelStyle={{ color: '#000' }}
                />
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke="#8884d8"
                  strokeWidth={2}
                  dot={false}
                  name="cpu"
                />
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke="#82ca9d"
                  strokeWidth={2}
                  dot={false}
                  name="memory"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Latency Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Processing Latency
            </CardTitle>
            <CardDescription>
              Transcription and LLM processing times
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  fontSize={12}
                  tick={{ fontSize: 12 }}
                />
                <YAxis fontSize={12} />
                <Tooltip
                  formatter={formatTooltipValue}
                  labelStyle={{ color: '#000' }}
                />
                <Area
                  type="monotone"
                  dataKey="transcriptionLatency"
                  stackId="1"
                  stroke="#ffc658"
                  fill="#ffc658"
                  fillOpacity={0.6}
                  name="transcriptionLatency"
                />
                <Area
                  type="monotone"
                  dataKey="llmLatency"
                  stackId="2"
                  stroke="#ff7300"
                  fill="#ff7300"
                  fillOpacity={0.6}
                  name="llmLatency"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Network Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Network Activity</CardTitle>
            <CardDescription>
              Network inbound and outbound traffic
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  fontSize={12}
                  tick={{ fontSize: 12 }}
                />
                <YAxis fontSize={12} />
                <Tooltip
                  formatter={formatTooltipValue}
                  labelStyle={{ color: '#000' }}
                />
                <Area
                  type="monotone"
                  dataKey="networkIn"
                  stroke="#8884d8"
                  fill="#8884d8"
                  fillOpacity={0.6}
                  name="networkIn"
                />
                <Area
                  type="monotone"
                  dataKey="networkOut"
                  stroke="#82ca9d"
                  fill="#82ca9d"
                  fillOpacity={0.6}
                  name="networkOut"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Performance Summary */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Performance Summary</CardTitle>
          <CardDescription>
            Key performance indicators and system health
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {latestMetrics && latestMetrics.cpu < 50 ? 'Good' : latestMetrics && latestMetrics.cpu < 80 ? 'Fair' : 'Poor'}
              </div>
              <div className="text-sm text-muted-foreground">CPU Performance</div>
              <div className="text-xs text-muted-foreground mt-1">
                {latestMetrics ? `Average: ${(sortedMetrics.reduce((acc, m) => acc + m.cpu, 0) / sortedMetrics.length).toFixed(1)}%` : 'N/A'}
              </div>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {latestMetrics && latestMetrics.transcriptionLatency < 2000 ? 'Fast' : latestMetrics && latestMetrics.transcriptionLatency < 5000 ? 'Normal' : 'Slow'}
              </div>
              <div className="text-sm text-muted-foreground">Transcription Speed</div>
              <div className="text-xs text-muted-foreground mt-1">
                {latestMetrics ? `Average: ${(sortedMetrics.reduce((acc, m) => acc + m.transcriptionLatency, 0) / sortedMetrics.length / 1000).toFixed(1)}s` : 'N/A'}
              </div>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {latestMetrics && latestMetrics.llmLatency < 3000 ? 'Excellent' : latestMetrics && latestMetrics.llmLatency < 6000 ? 'Good' : 'Needs Attention'}
              </div>
              <div className="text-sm text-muted-foreground">LLM Response Time</div>
              <div className="text-xs text-muted-foreground mt-1">
                {latestMetrics ? `Average: ${(sortedMetrics.reduce((acc, m) => acc + m.llmLatency, 0) / sortedMetrics.length / 1000).toFixed(1)}s` : 'N/A'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
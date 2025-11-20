"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  RadialBarChart,
  RadialBar,
  PieChart,
  Pie,
  Cell,
  ComposedChart,
} from "recharts";
import {
  Activity,
  Cpu,
  Database,
  HardDrive,
  Clock,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle2,
  Mic,
  Bot,
  Volume2,
  Timer,
  Wifi,
  WifiOff,
  RefreshCw,
} from "lucide-react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";

interface SystemMetrics {
  timestamp: number;
  cpu: number;
  memory: number;
  disk: number;
  networkIn: number;
  networkOut: number;
}

interface PerformanceMetrics {
  timestamp: number;
  responseTime: number;
  throughput: number;
  errorRate: number;
  successRate: number;
}

interface VoiceTranscriptionStats {
  timestamp: number;
  totalTranscriptions: number;
  successful: number;
  failed: number;
  avgAccuracy: number;
  avgLatency: number;
  languageDistribution: Array<{ language: string; count: number }>;
}

interface AgentActivity {
  agentId: string;
  agentName: string;
  status: "active" | "idle" | "error";
  tasksCompleted: number;
  tasksInProgress: number;
  avgResponseTime: number;
  successRate: number;
}

interface TTSMetrics {
  timestamp: number;
  totalRequests: number;
  successful: number;
  failed: number;
  avgSynthesisTime: number;
  voiceDistribution: Array<{ voice: string; count: number }>;
}

interface ErrorEvent {
  timestamp: number;
  type: string;
  message: string;
  severity: "low" | "medium" | "high" | "critical";
}

type TimeFilter = "1h" | "24h" | "7d";

interface AnalyticsData {
  system: SystemMetrics[];
  performance: PerformanceMetrics[];
  voiceTranscription: VoiceTranscriptionStats[];
  agentActivity: AgentActivity[];
  ttsMetrics: TTSMetrics[];
  errors: ErrorEvent[];
}

const COLORS = {
  primary: "#3b82f6",
  secondary: "#8b5cf6",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
  info: "#06b6d4",
  purple: "#a855f7",
  pink: "#ec4899",
  gradients: {
    blue: ["#3b82f6", "#60a5fa"],
    purple: ["#8b5cf6", "#a78bfa"],
    green: ["#10b981", "#34d399"],
    orange: ["#f59e0b", "#fbbf24"],
    red: ["#ef4444", "#f87171"],
  },
};

const CHART_COLORS = [COLORS.primary, COLORS.secondary, COLORS.success, COLORS.warning, COLORS.danger, COLORS.info, COLORS.purple, COLORS.pink];

export default function AnalyticsDashboard() {
  const [timeFilter, setTimeFilter] = useState<TimeFilter>("24h");
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      setError(null);
      await new Promise((resolve) => setTimeout(resolve, 800));

      const mockData: AnalyticsData = {
        system: generateMockSystemMetrics(timeFilter),
        performance: generateMockPerformanceMetrics(timeFilter),
        voiceTranscription: generateMockVoiceTranscriptionStats(timeFilter),
        agentActivity: generateMockAgentActivity(),
        ttsMetrics: generateMockTTSMetrics(timeFilter),
        errors: generateMockErrors(timeFilter),
      };

      setData(mockData);
    } catch (err) {
      setError("Failed to fetch analytics data");
      console.error("Analytics data fetch error:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [timeFilter]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
  };

  const currentMetrics = useMemo(() => {
    if (!data) return null;

    const latest = {
      system: data.system[data.system.length - 1],
      performance: data.performance[data.performance.length - 1],
      voiceTranscription: data.voiceTranscription[data.voiceTranscription.length - 1],
      ttsMetrics: data.ttsMetrics[data.ttsMetrics.length - 1],
      agents: data.agentActivity.length,
      activeAgents: data.agentActivity.filter((a) => a.status === "active").length,
    };

    return latest;
  }, [data]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full"
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen space-y-4">
        <AlertCircle className="w-16 h-16 text-danger" />
        <h2 className="text-2xl font-bold text-white">Error Loading Analytics</h2>
        <p className="text-white/60">{error}</p>
        <Button onClick={handleRefresh} className="mt-4">
          Retry
        </Button>
      </div>
    );
  }

  if (!data || !currentMetrics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-white/60">No data available</p>
      </div>
    );
  }

  const recentErrors = data.errors
    .sort((a, b) => b.timestamp - a.timestamp)
    .slice(0, 5);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics Dashboard</h1>
          <p className="text-white/60 mt-1">
            Real-time monitoring and performance insights
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Select value={timeFilter} onValueChange={(v) => setTimeFilter(v as TimeFilter)}>
            <SelectTrigger className="w-[180px] bg-black/30 border-white/10">
              <SelectValue placeholder="Select time range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">Last Hour</SelectItem>
              <SelectItem value="24h">Last 24 Hours</SelectItem>
              <SelectItem value="7d">Last 7 Days</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="icon"
            onClick={handleRefresh}
            disabled={refreshing}
            className="border-white/10 bg-black/30"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="System Health"
          value={`${currentMetrics.system.cpu.toFixed(0)}%`}
          subtitle="CPU Usage"
          icon={Cpu}
          color={COLORS.primary}
          trend={-5}
          status={
            currentMetrics.system.cpu < 70
              ? "good"
              : currentMetrics.system.cpu < 90
              ? "warning"
              : "critical"
          }
        />
        <MetricCard
          title="Active Agents"
          value={`${currentMetrics.activeAgents}/${currentMetrics.agents}`}
          subtitle="Running Tasks"
          icon={Bot}
          color={COLORS.success}
          trend={12}
          status="good"
        />
        <MetricCard
          title="Transcriptions"
          value={`${currentMetrics.voiceTranscription.totalTranscriptions}`}
          subtitle="Today"
          icon={Mic}
          color={COLORS.info}
          trend={8}
          status="good"
        />
        <MetricCard
          title="Avg Response"
          value={`${currentMetrics.performance.responseTime.toFixed(0)}ms`}
          subtitle="Last Hour"
          icon={Timer}
          color={COLORS.warning}
          trend={-3}
          status={
            currentMetrics.performance.responseTime < 500
              ? "good"
              : currentMetrics.performance.responseTime < 1000
              ? "warning"
              : "critical"
          }
        />
      </div>

      {/* Main Charts */}
      <Tabs defaultValue="system" className="space-y-4">
        <TabsList className="bg-black/30 border border-white/10">
          <TabsTrigger value="system" className="data-[state=active]:bg-white/10">
            System
          </TabsTrigger>
          <TabsTrigger value="performance" className="data-[state=active]:bg-white/10">
            Performance
          </TabsTrigger>
          <TabsTrigger value="voice" className="data-[state=active]:bg-white/10">
            Voice/TTS
          </TabsTrigger>
          <TabsTrigger value="agents" className="data-[state=active]:bg-white/10">
            Agents
          </TabsTrigger>
          <TabsTrigger value="errors" className="data-[state=active]:bg-white/10">
            Errors
          </TabsTrigger>
        </TabsList>

        <TabsContent value="system" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white/90">CPU & Memory Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={data.system}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis
                      dataKey="timestamp"
                      stroke="rgba(255,255,255,0.5)"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                      }
                    />
                    <YAxis stroke="rgba(255,255,255,0.5)" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(0,0,0,0.9)",
                        border: "1px solid rgba(255,255,255,0.2)",
                        borderRadius: "8px",
                      }}
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="cpu"
                      fill="url(#colorCpu)"
                      stroke={COLORS.primary}
                      strokeWidth={2}
                      name="CPU %"
                    />
                    <Area
                      type="monotone"
                      dataKey="memory"
                      fill="url(#colorMemory)"
                      stroke={COLORS.secondary}
                      strokeWidth={2}
                      name="Memory %"
                    />
                    <defs>
                      <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.8} />
                        <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={COLORS.secondary} stopOpacity={0.8} />
                        <stop offset="95%" stopColor={COLORS.secondary} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white/90">Disk & Network I/O</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={data.system}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis
                      dataKey="timestamp"
                      stroke="rgba(255,255,255,0.5)"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                      }
                    />
                    <YAxis stroke="rgba(255,255,255,0.5)" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(0,0,0,0.9)",
                        border: "1px solid rgba(255,255,255,0.2)",
                        borderRadius: "8px",
                      }}
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="disk"
                      stroke={COLORS.warning}
                      strokeWidth={2}
                      dot={{ fill: COLORS.warning, r: 3 }}
                      name="Disk I/O (MB/s)"
                    />
                    <Line
                      type="monotone"
                      dataKey="networkIn"
                      stroke={COLORS.success}
                      strokeWidth={2}
                      dot={{ fill: COLORS.success, r: 3 }}
                      name="Network In (MB/s)"
                    />
                    <Line
                      type="monotone"
                      dataKey="networkOut"
                      stroke={COLORS.info}
                      strokeWidth={2}
                      dot={{ fill: COLORS.info, r: 3 }}
                      name="Network Out (MB/s)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatCard title="CPU Usage" value={`${currentMetrics.system.cpu.toFixed(1)}%`} icon={Cpu} color={COLORS.primary} />
            <StatCard title="Memory Usage" value={`${currentMetrics.system.memory.toFixed(1)}%`} icon={Database} color={COLORS.secondary} />
            <StatCard title="Disk Usage" value={`${currentMetrics.system.disk.toFixed(1)}%`} icon={HardDrive} color={COLORS.warning} />
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white/90">Response Time Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={data.performance}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis
                      dataKey="timestamp"
                      stroke="rgba(255,255,255,0.5)"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                      }
                    />
                    <YAxis stroke="rgba(255,255,255,0.5)" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(0,0,0,0.9)",
                        border: "1px solid rgba(255,255,255,0.2)",
                        borderRadius: "8px",
                      }}
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Line
                      type="monotone"
                      dataKey="responseTime"
                      stroke={COLORS.primary}
                      strokeWidth={2}
                      dot={{ fill: COLORS.primary, r: 3 }}
                      name="Response Time (ms)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white/90">Throughput & Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={data.performance}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis
                      dataKey="timestamp"
                      stroke="rgba(255,255,255,0.5)"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                      }
                    />
                    <YAxis yAxisId="left" stroke="rgba(255,255,255,0.5)" />
                    <YAxis yAxisId="right" orientation="right" stroke="rgba(255,255,255,0.5)" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(0,0,0,0.9)",
                        border: "1px solid rgba(255,255,255,0.2)",
                        borderRadius: "8px",
                      }}
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Legend />
                    <Bar
                      yAxisId="left"
                      dataKey="throughput"
                      fill={COLORS.success}
                      name="Throughput (req/s)"
                      opacity={0.8}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="successRate"
                      stroke={COLORS.info}
                      strokeWidth={2}
                      dot={{ fill: COLORS.info, r: 3 }}
                      name="Success Rate (%)"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              title="Avg Response Time"
              value={`${currentMetrics.performance.responseTime.toFixed(0)}ms`}
              icon={Timer}
              color={COLORS.primary}
            />
            <StatCard
              title="Throughput"
              value={`${currentMetrics.performance.throughput.toFixed(1)}/s`}
              icon={TrendingUp}
              color={COLORS.success}
            />
            <StatCard
              title="Success Rate"
              value={`${currentMetrics.performance.successRate.toFixed(1)}%`}
              icon={CheckCircle2}
              color={COLORS.info}
            />
            <StatCard
              title="Error Rate"
              value={`${currentMetrics.performance.errorRate.toFixed(2)}%`}
              icon={AlertCircle}
              color={COLORS.danger}
            />
          </div>
        </TabsContent>

        <TabsContent value="voice" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white/90">Transcription Accuracy & Latency</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={data.voiceTranscription}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis
                      dataKey="timestamp"
                      stroke="rgba(255,255,255,0.5)"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                      }
                    />
                    <YAxis yAxisId="left" stroke="rgba(255,255,255,0.5)" />
                    <YAxis yAxisId="right" orientation="right" stroke="rgba(255,255,255,0.5)" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(0,0,0,0.9)",
                        border: "1px solid rgba(255,255,255,0.2)",
                        borderRadius: "8px",
                      }}
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Legend />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="avgAccuracy"
                      stroke={COLORS.success}
                      strokeWidth={2}
                      dot={{ fill: COLORS.success, r: 3 }}
                      name="Accuracy (%)"
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="avgLatency"
                      stroke={COLORS.warning}
                      strokeWidth={2}
                      dot={{ fill: COLORS.warning, r: 3 }}
                      name="Latency (ms)"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white/90">Language Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={data.voiceTranscription[data.voiceTranscription.length - 1]?.languageDistribution || []}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ language, percent }) => `${language}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {(data.voiceTranscription[data.voiceTranscription.length - 1]?.languageDistribution || []).map(
                        (entry, index) => (
                          <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        )
                      )}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(0,0,0,0.9)",
                        border: "1px solid rgba(255,255,255,0.2)",
                        borderRadius: "8px",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              title="Total Transcriptions"
              value={currentMetrics.voiceTranscription.totalTranscriptions.toString()}
              icon={Mic}
              color={COLORS.info}
            />
            <StatCard
              title="Success Rate"
              value={`${((currentMetrics.voiceTranscription.successful / currentMetrics.voiceTranscription.totalTranscriptions) * 100).toFixed(1)}%`}
              icon={CheckCircle2}
              color={COLORS.success}
            />
            <StatCard
              title="Avg Accuracy"
              value={`${currentMetrics.voiceTranscription.avgAccuracy.toFixed(1)}%`}
              icon={Activity}
              color={COLORS.primary}
            />
            <StatCard
              title="TTS Requests"
              value={currentMetrics.ttsMetrics.totalRequests.toString()}
              icon={Volume2}
              color={COLORS.purple}
            />
          </div>
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white/90">Agent Status Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data.agentActivity.map((agent) => (
                    <div
                      key={agent.agentId}
                      className="p-4 rounded-lg bg-black/20 border border-white/5"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <div className={`w-3 h-3 rounded-full ${
                            agent.status === "active" ? "bg-green-500" :
                            agent.status === "idle" ? "bg-yellow-500" : "bg-red-500"
                          }`} />
                          <h4 className="font-medium text-white">{agent.agentName}</h4>
                        </div>
                        <Badge
                          variant="outline"
                          className={`${
                            agent.status === "active"
                              ? "border-green-500/30 text-green-400"
                              : agent.status === "idle"
                              ? "border-yellow-500/30 text-yellow-400"
                              : "border-red-500/30 text-red-400"
                          }`}
                        >
                          {agent.status}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="text-white/60">Completed: {agent.tasksCompleted}</div>
                        <div className="text-white/60">In Progress: {agent.tasksInProgress}</div>
                        <div className="text-white/60">Avg Response: {agent.avgResponseTime.toFixed(0)}ms</div>
                        <div className="text-white/60">Success Rate: {agent.successRate.toFixed(1)}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
              <CardHeader>
                <CardTitle className="text-white/90">Agent Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={data.agentActivity}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="agentName" stroke="rgba(255,255,255,0.5)" />
                    <YAxis stroke="rgba(255,255,255,0.5)" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(0,0,0,0.9)",
                        border: "1px solid rgba(255,255,255,0.2)",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend />
                    <Bar dataKey="tasksCompleted" fill={COLORS.success} name="Completed" />
                    <Bar dataKey="tasksInProgress" fill={COLORS.warning} name="In Progress" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              title="Total Agents"
              value={data.agentActivity.length.toString()}
              icon={Bot}
              color={COLORS.info}
            />
            <StatCard
              title="Active Agents"
              value={data.agentActivity.filter((a) => a.status === "active").length.toString()}
              icon={Activity}
              color={COLORS.success}
            />
            <StatCard
              title="Tasks Completed"
              value={data.agentActivity.reduce((sum, a) => sum + a.tasksCompleted, 0).toString()}
              icon={CheckCircle2}
              color={COLORS.primary}
            />
            <StatCard
              title="Avg Success Rate"
              value={`${(data.agentActivity.reduce((sum, a) => sum + a.successRate, 0) / data.agentActivity.length).toFixed(1)}%`}
              icon={TrendingUp}
              color={COLORS.purple}
            />
          </div>
        </TabsContent>

        <TabsContent value="errors" className="space-y-4">
          <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
            <CardHeader>
              <CardTitle className="text-white/90">Recent Errors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {recentErrors.length > 0 ? (
                  recentErrors.map((error, index) => (
                    <div
                      key={index}
                      className="p-3 rounded-lg bg-black/20 border border-white/5 flex items-start gap-3"
                    >
                      <AlertCircle className={`w-5 h-5 mt-0.5 ${
                        error.severity === "critical" ? "text-red-500" :
                        error.severity === "high" ? "text-orange-500" :
                        error.severity === "medium" ? "text-yellow-500" : "text-blue-500"
                      }`} />
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-white">{error.type}</span>
                          <span className="text-xs text-white/60">
                            {new Date(error.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm text-white/70">{error.message}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-white/60">
                    <CheckCircle2 className="w-12 h-12 mx-auto mb-2 text-green-500" />
                    <p>No recent errors</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              title="Total Errors"
              value={data.errors.length.toString()}
              icon={AlertCircle}
              color={COLORS.danger}
            />
            <StatCard
              title="Critical"
              value={data.errors.filter((e) => e.severity === "critical").length.toString()}
              icon={AlertCircle}
              color={COLORS.danger}
            />
            <StatCard
              title="High"
              value={data.errors.filter((e) => e.severity === "high").length.toString()}
              icon={AlertCircle}
              color={COLORS.warning}
            />
            <StatCard
              title="Medium/Low"
              value={data.errors.filter((e) => e.severity === "medium" || e.severity === "low").length.toString()}
              icon={AlertCircle}
              color={COLORS.info}
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
  trend,
  status,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: any;
  color: string;
  trend?: number;
  status?: "good" | "warning" | "critical";
}) {
  return (
    <motion.div whileHover={{ scale: 1.02 }}>
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <Icon className={`w-5 h-5`} style={{ color }} />
            {trend !== undefined && (
              <div className={`flex items-center gap-1 text-sm ${trend > 0 ? "text-green-400" : "text-red-400"}`}>
                {trend > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                {Math.abs(trend)}%
              </div>
            )}
          </div>
          <p className="text-sm text-white/60">{title}</p>
          <div className="flex items-baseline gap-2 mt-1">
            <p className="text-2xl font-bold text-white">{value}</p>
            <p className="text-xs text-white/60">{subtitle}</p>
          </div>
          {status && (
            <div className="flex items-center gap-1 mt-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  status === "good" ? "bg-green-500" :
                  status === "warning" ? "bg-yellow-500" : "bg-red-500"
                }`}
              />
              <span className="text-xs text-white/60 capitalize">{status}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string;
  value: string;
  icon: any;
  color: string;
}) {
  return (
    <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <Icon className={`w-5 h-5`} style={{ color }} />
          <p className="text-sm text-white/60">{title}</p>
        </div>
        <p className="text-2xl font-bold text-white">{value}</p>
      </CardContent>
    </Card>
  );
}

function generateMockSystemMetrics(timeFilter: TimeFilter): SystemMetrics[] {
  const points = timeFilter === "1h" ? 12 : timeFilter === "24h" ? 48 : 168;
  const interval = timeFilter === "1h" ? 5 * 60 * 1000 : timeFilter === "24h" ? 30 * 60 * 1000 : 60 * 60 * 1000;
  const now = Date.now();

  return Array.from({ length: points }, (_, i) => ({
    timestamp: now - (points - i) * interval,
    cpu: 30 + Math.random() * 40,
    memory: 40 + Math.random() * 30,
    disk: 20 + Math.random() * 20,
    networkIn: Math.random() * 100,
    networkOut: Math.random() * 100,
  }));
}

function generateMockPerformanceMetrics(timeFilter: TimeFilter): PerformanceMetrics[] {
  const points = timeFilter === "1h" ? 12 : timeFilter === "24h" ? 48 : 168;
  const interval = timeFilter === "1h" ? 5 * 60 * 1000 : timeFilter === "24h" ? 30 * 60 * 1000 : 60 * 60 * 1000;
  const now = Date.now();

  return Array.from({ length: points }, (_, i) => ({
    timestamp: now - (points - i) * interval,
    responseTime: 100 + Math.random() * 200,
    throughput: 5 + Math.random() * 15,
    errorRate: Math.random() * 5,
    successRate: 95 - Math.random() * 5,
  }));
}

function generateMockVoiceTranscriptionStats(timeFilter: TimeFilter): VoiceTranscriptionStats[] {
  const points = timeFilter === "1h" ? 12 : timeFilter === "24h" ? 48 : 168;
  const interval = timeFilter === "1h" ? 5 * 60 * 1000 : timeFilter === "24h" ? 30 * 60 * 1000 : 60 * 60 * 1000;
  const now = Date.now();

  return Array.from({ length: points }, (_, i) => ({
    timestamp: now - (points - i) * interval,
    totalTranscriptions: Math.floor(50 + Math.random() * 100),
    successful: Math.floor(45 + Math.random() * 90),
    failed: Math.floor(Math.random() * 10),
    avgAccuracy: 85 + Math.random() * 10,
    avgLatency: 200 + Math.random() * 100,
    languageDistribution: [
      { language: "English", count: Math.floor(50 + Math.random() * 50) },
      { language: "Spanish", count: Math.floor(20 + Math.random() * 30) },
      { language: "French", count: Math.floor(10 + Math.random() * 20) },
      { language: "German", count: Math.floor(5 + Math.random() * 15) },
    ],
  }));
}

function generateMockAgentActivity(): AgentActivity[] {
  const agents = [
    "TranscriptionAgent",
    "TTSAgent",
    "AnalysisAgent",
    "ProcessingAgent",
    "OptimizationAgent",
  ];

  return agents.map((name, i) => ({
    agentId: `agent-${i}`,
    agentName: name,
    status: (Math.random() > 0.7 ? "idle" : Math.random() > 0.1 ? "active" : "error") as "active" | "idle" | "error",
    tasksCompleted: Math.floor(Math.random() * 100),
    tasksInProgress: Math.floor(Math.random() * 10),
    avgResponseTime: 100 + Math.random() * 200,
    successRate: 85 + Math.random() * 15,
  }));
}

function generateMockTTSMetrics(timeFilter: TimeFilter): TTSMetrics[] {
  const points = timeFilter === "1h" ? 12 : timeFilter === "24h" ? 48 : 168;
  const interval = timeFilter === "1h" ? 5 * 60 * 1000 : timeFilter === "24h" ? 30 * 60 * 1000 : 60 * 60 * 1000;
  const now = Date.now();

  return Array.from({ length: points }, (_, i) => ({
    timestamp: now - (points - i) * interval,
    totalRequests: Math.floor(30 + Math.random() * 50),
    successful: Math.floor(28 + Math.random() * 45),
    failed: Math.floor(Math.random() * 5),
    avgSynthesisTime: 150 + Math.random() * 100,
    voiceDistribution: [
      { voice: "Default", count: Math.floor(20 + Math.random() * 30) },
      { voice: "Neural A", count: Math.floor(10 + Math.random() * 20) },
      { voice: "Neural B", count: Math.floor(5 + Math.random() * 15) },
    ],
  }));
}

function generateMockErrors(timeFilter: TimeFilter): ErrorEvent[] {
  const points = timeFilter === "1h" ? 5 : timeFilter === "24h" ? 20 : 50;
  const now = Date.now();
  const types = ["Connection Error", "Timeout", "API Error", "Database Error", "Memory Error"];
  const severities: Array<"low" | "medium" | "high" | "critical"> = ["low", "medium", "high", "critical"];

  return Array.from({ length: points }, (_, i) => ({
    timestamp: now - Math.random() * (timeFilter === "1h" ? 60 * 60 * 1000 : timeFilter === "24h" ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000),
    type: types[Math.floor(Math.random() * types.length)],
    message: `Error occurred in ${types[Math.floor(Math.random() * types.length)].toLowerCase()} module`,
    severity: severities[Math.floor(Math.random() * severities.length)],
  }));
}

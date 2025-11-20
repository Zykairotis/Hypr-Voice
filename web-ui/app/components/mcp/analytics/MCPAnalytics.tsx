"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  Server,
  AlertTriangle,
  Download,
  RefreshCw,
} from "lucide-react";
import { motion } from "framer-motion";
import {
  LineChart,
  Line,
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
} from "recharts";
import { useMCPStore } from "@/lib/mcp-store";

export default function MCPAnalytics() {
  const { analytics, servers, loadAnalytics } = useMCPStore();
  const [timeRange, setTimeRange] = useState("24h");

  useEffect(() => {
    loadAnalytics();
  }, []);

  // Mock data for charts
  const requestData = [
    { time: "00:00", requests: 120, errors: 2 },
    { time: "04:00", requests: 89, errors: 1 },
    { time: "08:00", requests: 234, errors: 5 },
    { time: "12:00", requests: 345, errors: 3 },
    { time: "16:00", requests: 456, errors: 8 },
    { time: "20:00", requests: 378, errors: 4 },
  ];

  const responseTimeData = [
    { time: "00:00", avg: 45, p95: 120 },
    { time: "04:00", avg: 38, p95: 95 },
    { time: "08:00", avg: 52, p95: 145 },
    { time: "12:00", avg: 61, p95: 180 },
    { time: "16:00", avg: 58, p95: 165 },
    { time: "20:00", avg: 48, p95: 130 },
  ];

  const categoryData = analytics?.categories.map((cat) => ({
    name: cat.category,
    value: cat.count,
    active: cat.active,
  })) || [];

  const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

  if (!analytics) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Loading analytics...</h3>
          <p className="text-muted-foreground">Please wait while we gather server statistics</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">MCP Analytics Dashboard</h2>
          <p className="text-muted-foreground">
            Comprehensive insights into server performance and usage
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="px-3 py-2 bg-background border rounded-md text-sm"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <Button variant="outline" size="sm" onClick={loadAnalytics}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Requests"
          value={analytics.totalRequests.toLocaleString()}
          icon={Activity}
          color="text-blue-500"
          bgColor="bg-blue-500/10"
          trend="+12.5%"
        />
        <MetricCard
          title="Avg Response Time"
          value={`${analytics.avgResponseTime}ms`}
          icon={Clock}
          color="text-purple-500"
          bgColor="bg-purple-500/10"
          trend="-5.2%"
        />
        <MetricCard
          title="Active Servers"
          value={`${analytics.activeServers}/${analytics.totalServers}`}
          icon={Server}
          color="text-green-500"
          bgColor="bg-green-500/10"
          trend="+2"
        />
        <MetricCard
          title="Error Rate"
          value="2.3%"
          icon={AlertTriangle}
          color="text-red-500"
          bgColor="bg-red-500/10"
          trend="-1.1%"
        />
      </div>

      <Tabs defaultValue="requests" className="space-y-4">
        <TabsList>
          <TabsTrigger value="requests">Requests</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="categories">Categories</TabsTrigger>
          <TabsTrigger value="servers">Servers</TabsTrigger>
        </TabsList>

        <TabsContent value="requests" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Request Volume</CardTitle>
                <CardDescription>Number of requests over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={requestData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="time" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #374151",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="requests"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      name="Requests"
                    />
                    <Line
                      type="monotone"
                      dataKey="errors"
                      stroke="#ef4444"
                      strokeWidth={2}
                      name="Errors"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Error Distribution</CardTitle>
                <CardDescription>Error breakdown by server type</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analytics.errors.slice(0, 5).map((error, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-red-500" />
                        <span className="text-sm">{error.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="destructive" className="text-xs">
                          {error.errorCount} errors
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {error.lastError}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Response Time Trends</CardTitle>
              <CardDescription>Average and P95 response times</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={responseTimeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f2937",
                      border: "1px solid #374151",
                      borderRadius: "8px",
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="avg"
                    stroke="#10b981"
                    strokeWidth={2}
                    name="Average (ms)"
                  />
                  <Line
                    type="monotone"
                    dataKey="p95"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    name="P95 (ms)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Top Servers by Uptime</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analytics.uptime.slice(0, 5).map((server, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>{server.name}</span>
                        <span className="text-green-500">{server.uptimePercentage.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-green-500"
                          initial={{ width: 0 }}
                          animate={{ width: `${server.uptimePercentage}%` }}
                          transition={{ duration: 1, delay: index * 0.1 }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Server Load Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="categories" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Servers by Category</CardTitle>
              <CardDescription>Distribution of servers across categories</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={categoryData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="name" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f2937",
                      border: "1px solid #374151",
                      borderRadius: "8px",
                    }}
                  />
                  <Legend />
                  <Bar dataKey="value" fill="#3b82f6" name="Total" />
                  <Bar dataKey="active" fill="#10b981" name="Active" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="servers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Most Popular Servers</CardTitle>
              <CardDescription>Servers ranked by request count</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.popularServers.map((server, index) => (
                  <motion.div
                    key={index}
                    className="flex items-center justify-between p-4 bg-secondary/50 rounded-lg"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-medium">{server.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {server.requestCount.toLocaleString()} requests
                        </p>
                      </div>
                    </div>
                    <Badge variant="outline">#{server.serverId}</Badge>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function MetricCard({
  title,
  value,
  icon: Icon,
  color,
  bgColor,
  trend,
}: {
  title: string;
  value: string | number;
  icon: any;
  color: string;
  bgColor: string;
  trend?: string;
}) {
  return (
    <motion.div whileHover={{ scale: 1.02 }}>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{title}</p>
              <p className="text-2xl font-bold mt-1">{value}</p>
              {trend && (
                <div className="flex items-center gap-1 mt-2">
                  {trend.startsWith("+") ? (
                    <TrendingUp className="w-3 h-3 text-green-500" />
                  ) : (
                    <TrendingDown className="w-3 h-3 text-red-500" />
                  )}
                  <span
                    className={`text-xs ${
                      trend.startsWith("+") ? "text-green-500" : "text-red-500"
                    }`}
                  >
                    {trend}
                  </span>
                </div>
              )}
            </div>
            <div className={`p-3 rounded-lg ${bgColor}`}>
              <Icon className={`w-6 h-6 ${color}`} />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

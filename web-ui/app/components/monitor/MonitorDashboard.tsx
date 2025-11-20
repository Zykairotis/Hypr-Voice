"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "components/ui/tabs";
import { Badge } from "components/ui/badge";
import { Button } from "components/ui/button";
import {
  Activity,
  Bell,
  Database,
  LineChart,
  Timer,
  Download,
  Wifi,
  WifiOff
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useWebSocket } from "lib/websocket";
import EventStream from "./EventStream";
import SystemMetrics from "./metrics/SystemMetrics";
import AgentActivity from "./AgentActivity";
import LogViewer from "./logs/LogViewer";
import PerformanceCharts from "./charts/PerformanceCharts";
import AlertCenter from "./alerts/AlertCenter";
import ActivityTimeline from "./timeline/ActivityTimeline";
import MetricsHistory from "./metrics/MetricsHistory";

export default function MonitorDashboard() {
  const { isConnected, metrics, alerts } = useWebSocket();
  const [activeTab, setActiveTab] = useState("events");
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.toggle("dark", darkMode);
  }, [darkMode]);

  const connectionStatus = {
    connected: { text: "Connected", color: "text-green-500" },
    disconnected: { text: "Disconnected", color: "text-red-500" },
  };

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <motion.div
              className="p-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30"
              whileHover={{ scale: 1.05 }}
            >
              <Activity className="w-6 h-6 text-blue-400" />
            </motion.div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
                Real-time Activity Monitor
              </h1>
              <p className="text-white/50">Comprehensive system monitoring and analytics</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              {isConnected ? (
                <Wifi className="w-5 h-5 text-green-500" />
              ) : (
                <WifiOff className="w-5 h-5 text-red-500" />
              )}
              <Badge variant="outline" className={isConnected ? "text-green-500 border-green-500/30" : "text-red-500 border-red-500/30"}>
                {isConnected ? "Live" : "Offline"}
              </Badge>
            </div>

            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            title="Active Agents"
            value={metrics?.activeAgents || 0}
            icon={Activity}
            trend={+12}
            color="blue"
          />
          <StatCard
            title="CPU Usage"
            value={`${metrics?.cpu?.toFixed(1) || 0}%`}
            icon={LineChart}
            trend={-5}
            color="purple"
          />
          <StatCard
            title="Memory"
            value={`${metrics?.memory?.toFixed(1) || 0}%`}
            icon={Database}
            trend={+3}
            color="green"
          />
          <StatCard
            title="Alerts"
            value={alerts.length}
            icon={Bell}
            trend={alerts.length > 0 ? +1 : 0}
            color="orange"
            critical={alerts.length > 0}
          />
        </div>
      </div>

      {/* Main Content */}
      <Card className="border-white/10 bg-black/20 backdrop-blur-xl">
        <CardContent className="p-0">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <div className="px-6 pt-6">
              <TabsList className="bg-black/30 border border-white/10">
                <TabsTrigger value="events" className="data-[state=active]:bg-blue-500/20">
                  <Timer className="w-4 h-4 mr-2" />
                  Event Stream
                </TabsTrigger>
                <TabsTrigger value="metrics" className="data-[state=active]:bg-blue-500/20">
                  <LineChart className="w-4 h-4 mr-2" />
                  System Metrics
                </TabsTrigger>
                <TabsTrigger value="agents" className="data-[state=active]:bg-blue-500/20">
                  <Activity className="w-4 h-4 mr-2" />
                  Agent Activity
                </TabsTrigger>
                <TabsTrigger value="logs" className="data-[state=active]:bg-blue-500/20">
                  <Database className="w-4 h-4 mr-2" />
                  Logs
                </TabsTrigger>
                <TabsTrigger value="performance" className="data-[state=active]:bg-blue-500/20">
                  <LineChart className="w-4 h-4 mr-2" />
                  Performance
                </TabsTrigger>
                <TabsTrigger value="alerts" className="data-[state=active]:bg-blue-500/20">
                  <Bell className="w-4 h-4 mr-2" />
                  Alerts ({alerts.length})
                </TabsTrigger>
                <TabsTrigger value="timeline" className="data-[state=active]:bg-blue-500/20">
                  <Timer className="w-4 h-4 mr-2" />
                  Timeline
                </TabsTrigger>
              </TabsList>
            </div>

            <div className="p-6">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <TabsContent value="events" className="mt-0">
                    <EventStream />
                  </TabsContent>

                  <TabsContent value="metrics" className="mt-0">
                    <SystemMetrics />
                  </TabsContent>

                  <TabsContent value="agents" className="mt-0">
                    <AgentActivity />
                  </TabsContent>

                  <TabsContent value="logs" className="mt-0">
                    <LogViewer />
                  </TabsContent>

                  <TabsContent value="performance" className="mt-0">
                    <PerformanceCharts />
                  </TabsContent>

                  <TabsContent value="alerts" className="mt-0">
                    <AlertCenter />
                  </TabsContent>

                  <TabsContent value="timeline" className="mt-0">
                    <ActivityTimeline />
                  </TabsContent>
                </motion.div>
              </AnimatePresence>
            </div>
          </Tabs>
        </CardContent>
      </Card>

      {/* Floating Metrics History */}
      <motion.div
        className="fixed bottom-6 right-6 z-50"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <MetricsHistory />
      </motion.div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  color,
  critical = false
}: {
  title: string;
  value: string | number;
  icon: any;
  trend: number;
  color: string;
  critical?: boolean;
}) {
  const colorClasses = {
    blue: "from-blue-500/20 to-blue-600/20 border-blue-500/30",
    purple: "from-purple-500/20 to-purple-600/20 border-purple-500/30",
    green: "from-green-500/20 to-green-600/20 border-green-500/30",
    orange: "from-orange-500/20 to-orange-600/20 border-orange-500/30",
  };

  return (
    <motion.div whileHover={{ scale: 1.02 }} transition={{ type: "spring", stiffness: 400, damping: 17 }}>
      <Card className={`bg-gradient-to-br ${colorClasses[color as keyof typeof colorClasses]} border backdrop-blur-xl`}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white/60">{title}</p>
              <p className="text-2xl font-bold text-white mt-1">{value}</p>
            </div>
            <Icon className={`w-8 h-8 text-${color}-400`} />
          </div>
          {trend !== 0 && (
            <div className={`flex items-center mt-2 text-xs ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

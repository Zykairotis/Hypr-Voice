"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Progress } from "components/ui/progress";
import {
  Cpu,
  Database,
  Network,
  Activity,
  Clock,
  TrendingUp,
  AlertCircle,
  CheckCircle2
} from "lucide-react";
import { motion } from "framer-motion";
import { useWebSocket } from "lib/websocket";

export default function SystemMetrics() {
  const { metrics } = useWebSocket();

  const metricsData = useMemo(() => {
    if (!metrics) {
      return {
        cpuUsage: 0,
        memoryUsage: 0,
        activeAgents: 0,
        connections: 0,
        throughput: 0,
        responseTime: 0,
        errorRate: 0,
        status: "unknown"
      };
    }

    return {
      cpuUsage: metrics.cpu,
      memoryUsage: metrics.memory,
      activeAgents: metrics.activeAgents,
      connections: metrics.websocketConnections,
      throughput: metrics.requestsPerSecond,
      responseTime: metrics.averageResponseTime,
      errorRate: metrics.errorRate,
      status: metrics.errorRate > 10 ? "error" : metrics.errorRate > 5 ? "warning" : "healthy"
    };
  }, [metrics]);

  const getStatusColor = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return "text-red-500";
    if (value >= thresholds.warning) return "text-yellow-500";
    return "text-green-500";
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "healthy":
        return (
          <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Healthy
          </Badge>
        );
      case "warning":
        return (
          <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
            <AlertCircle className="w-3 h-3 mr-1" />
            Warning
          </Badge>
        );
      case "error":
        return (
          <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
            <AlertCircle className="w-3 h-3 mr-1" />
            Critical
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            Unknown
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* System Status Overview */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>System Status</span>
            {getStatusBadge(metricsData.status)}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricDisplay
              title="CPU Usage"
              value={`${metricsData.cpuUsage.toFixed(1)}%`}
              icon={Cpu}
              color={getStatusColor(metricsData.cpuUsage, { warning: 70, critical: 90 })}
              progress={metricsData.cpuUsage}
              thresholds={{ warning: 70, critical: 90 }}
            />
            <MetricDisplay
              title="Memory Usage"
              value={`${metricsData.memoryUsage.toFixed(1)}%`}
              icon={Database}
              color={getStatusColor(metricsData.memoryUsage, { warning: 80, critical: 95 })}
              progress={metricsData.memoryUsage}
              thresholds={{ warning: 80, critical: 95 }}
            />
            <MetricDisplay
              title="Active Agents"
              value={metricsData.activeAgents.toString()}
              icon={Activity}
              color="text-blue-400"
            />
            <MetricDisplay
              title="Connections"
              value={metricsData.connections.toString()}
              icon={Network}
              color="text-purple-400"
            />
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-sm text-white/60">Request Throughput</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between mb-2">
              <div className="text-3xl font-bold text-white">
                {metricsData.throughput.toFixed(1)}
              </div>
              <TrendingUp className="w-5 h-5 text-green-400" />
            </div>
            <p className="text-sm text-white/60">requests/second</p>
          </CardContent>
        </Card>

        <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-sm text-white/60">Avg Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between mb-2">
              <div className="text-3xl font-bold text-white">
                {metricsData.responseTime.toFixed(0)}
              </div>
              <Clock className="w-5 h-5 text-blue-400" />
            </div>
            <p className="text-sm text-white/60">milliseconds</p>
          </CardContent>
        </Card>

        <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-sm text-white/60">Error Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between mb-2">
              <div className={`text-3xl font-bold ${getStatusColor(metricsData.errorRate, { warning: 5, critical: 10 })}`}>
                {metricsData.errorRate.toFixed(2)}%
              </div>
              <AlertCircle className={`w-5 h-5 ${getStatusColor(metricsData.errorRate, { warning: 5, critical: 10 })}`} />
            </div>
            <p className="text-sm text-white/60">of total requests</p>
          </CardContent>
        </Card>
      </div>

      {/* Resource Usage Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-lg">Resource Distribution</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ResourceBar
              label="System CPU"
              value={metricsData.cpuUsage}
              max={100}
              color="bg-blue-500"
            />
            <ResourceBar
              label="Application Memory"
              value={metricsData.memoryUsage}
              max={100}
              color="bg-purple-500"
            />
            <ResourceBar
              label="Available Agents"
              value={Math.max(0, 100 - metricsData.activeAgents * 2)}
              max={100}
              color="bg-green-500"
            />
            <ResourceBar
              label="Network I/O"
              value={Math.min(100, metricsData.throughput * 2)}
              max={100}
              color="bg-orange-500"
            />
          </CardContent>
        </Card>

        <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-lg">Performance Health</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <HealthMetric
              label="Response Time"
              status={metricsData.responseTime < 100 ? "good" : metricsData.responseTime < 500 ? "warning" : "critical"}
              value={`${metricsData.responseTime.toFixed(0)}ms`}
            />
            <HealthMetric
              label="Error Rate"
              status={metricsData.errorRate < 1 ? "good" : metricsData.errorRate < 5 ? "warning" : "critical"}
              value={`${metricsData.errorRate.toFixed(2)}%`}
            />
            <HealthMetric
              label="Throughput"
              status={metricsData.throughput > 10 ? "good" : metricsData.throughput > 5 ? "warning" : "critical"}
              value={`${metricsData.throughput.toFixed(1)} req/s`}
            />
            <HealthMetric
              label="Connection Stability"
              status={metricsData.connections > 0 ? "good" : "critical"}
              value={`${metricsData.connections} active`}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricDisplay({
  title,
  value,
  icon: Icon,
  color,
  progress,
  thresholds
}: {
  title: string;
  value: string;
  icon: any;
  color: string;
  progress?: number;
  thresholds?: { warning: number; critical: number };
}) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="p-4 rounded-lg bg-gradient-to-br from-white/5 to-white/0 border border-white/10"
    >
      <div className="flex items-center justify-between mb-2">
        <Icon className={`w-5 h-5 ${color}`} />
        <span className={`text-xs font-medium ${color}`}>{value}</span>
      </div>
      <p className="text-sm text-white/60">{title}</p>
      {progress !== undefined && thresholds && (
        <div className="mt-2">
          <Progress
            value={progress}
            className="h-2"
            style={{
              '--progress-color': progress >= thresholds.critical ? 'rgb(239 68 68)' :
                               progress >= thresholds.warning ? 'rgb(234 179 8)' :
                               'rgb(34 197 94)'
            } as any}
          />
        </div>
      )}
    </motion.div>
  );
}

function ResourceBar({
  label,
  value,
  max,
  color
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const percentage = (value / max) * 100;

  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm text-white/70">{label}</span>
        <span className="text-sm text-white/70">{value.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-white/10 rounded-full overflow-hidden">
        <motion.div
          className={`h-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
    </div>
  );
}

function HealthMetric({
  label,
  status,
  value
}: {
  label: string;
  status: "good" | "warning" | "critical";
  value: string;
}) {
  const statusConfig = {
    good: { color: "text-green-400", bg: "bg-green-500/20" },
    warning: { color: "text-yellow-400", bg: "bg-yellow-500/20" },
    critical: { color: "text-red-400", bg: "bg-red-500/20" }
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-black/20 border border-white/5">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${config.bg}`} />
        <span className="text-sm text-white/70">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`text-sm font-medium ${config.color}`}>{value}</span>
        <CheckCircle2 className={`w-4 h-4 ${config.color}`} />
      </div>
    </div>
  );
}

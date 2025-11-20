"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  Activity,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  TrendingDown,
  Server,
} from "lucide-react";
import { motion } from "framer-motion";
import { useMCPStore } from "@/lib/mcp-store";
import type { MCPServerHealth } from "@/types/mcp";

interface Props {
  compact?: boolean;
}

export default function ServerHealthMonitor({ compact = false }: Props) {
  const { servers, serverHealth, serverMetrics } = useMCPStore();
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(new Date());
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const healthStats = {
    healthy: 0,
    degraded: 0,
    unhealthy: 0,
    unknown: 0,
  };

  Object.values(serverHealth).forEach((health) => {
    healthStats[health.status]++;
  });

  const overallHealth = (() => {
    const total = Object.keys(servers).length;
    if (total === 0) return "unknown";
    const healthyRatio = healthStats.healthy / total;
    if (healthyRatio >= 0.9) return "healthy";
    if (healthyRatio >= 0.7) return "degraded";
    return "unhealthy";
  })();

  if (compact) {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                overallHealth === "healthy"
                  ? "bg-green-500"
                  : overallHealth === "degraded"
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
            />
            <span className="text-sm font-medium">
              {overallHealth === "healthy"
                ? "All Systems Operational"
                : overallHealth === "degraded"
                ? "Degraded Performance"
                : "System Issues Detected"}
            </span>
          </div>
          <span className="text-xs text-muted-foreground">
            Updated {lastUpdate.toLocaleTimeString()}
          </span>
        </div>

        <div className="grid grid-cols-4 gap-2">
          <div className="text-center">
            <div className="text-lg font-bold text-green-500">{healthStats.healthy}</div>
            <div className="text-xs text-muted-foreground">Healthy</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-yellow-500">{healthStats.degraded}</div>
            <div className="text-xs text-muted-foreground">Degraded</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-red-500">{healthStats.unhealthy}</div>
            <div className="text-xs text-muted-foreground">Unhealthy</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-gray-500">{healthStats.unknown}</div>
            <div className="text-xs text-muted-foreground">Unknown</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Server Health Monitor</h2>
          <p className="text-muted-foreground">
            Real-time health status of all MCP servers
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className={
              overallHealth === "healthy"
                ? "text-green-500 border-green-500/30"
                : overallHealth === "degraded"
                ? "text-yellow-500 border-yellow-500/30"
                : "text-red-500 border-red-500/30"
            }
          >
            {overallHealth === "healthy"
              ? "All Systems Operational"
              : overallHealth === "degraded"
              ? "Degraded Performance"
              : "System Issues"}
          </Badge>
          <Button variant="outline" size="sm" onClick={() => setLastUpdate(new Date())}>
            <Activity className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Healthy Servers"
          value={healthStats.healthy}
          icon={CheckCircle}
          color="text-green-500"
          bgColor="bg-green-500/10"
          trend="+2"
        />
        <MetricCard
          title="Degraded Servers"
          value={healthStats.degraded}
          icon={AlertTriangle}
          color="text-yellow-500"
          bgColor="bg-yellow-500/10"
          trend="-1"
        />
        <MetricCard
          title="Unhealthy Servers"
          value={healthStats.unhealthy}
          icon={XCircle}
          color="text-red-500"
          bgColor="bg-red-500/10"
          trend="+1"
        />
        <MetricCard
          title="Unknown Status"
          value={healthStats.unknown}
          icon={Clock}
          color="text-gray-500"
          bgColor="bg-gray-500/10"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {Object.entries(serverHealth).map(([serverId, health]) => {
          const server = servers[serverId];
          if (!server) return null;

          return (
            <HealthCard key={serverId} server={server} health={health} />
          );
        })}
      </div>

      {Object.keys(serverHealth).length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <Server className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No health data available</h3>
            <p className="text-muted-foreground">
              Health monitoring will appear here once servers are configured and running
            </p>
          </CardContent>
        </Card>
      )}
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
  value: number;
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
              <p className="text-2xl font-bold">{value}</p>
              {trend && (
                <div className="flex items-center gap-1 mt-1">
                  {trend.startsWith("+") ? (
                    <TrendingUp className="w-3 h-3 text-green-500" />
                  ) : (
                    <TrendingDown className="w-3 h-3 text-red-500" />
                  )}
                  <span className={`text-xs ${trend.startsWith("+") ? "text-green-500" : "text-red-500"}`}>
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

function HealthCard({ server, health }: { server: any; health: MCPServerHealth }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "text-green-500";
      case "degraded":
        return "text-yellow-500";
      case "unhealthy":
        return "text-red-500";
      default:
        return "text-gray-500";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "degraded":
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case "unhealthy":
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const passedChecks = health.checks.filter((c) => c.status === "pass").length;
  const totalChecks = health.checks.length;
  const healthPercentage = (passedChecks / totalChecks) * 100;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{server.name}</CardTitle>
          {getStatusIcon(health.status)}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Health Score</span>
            <span className={getStatusColor(health.status)}>
              {healthPercentage.toFixed(0)}%
            </span>
          </div>
          <Progress value={healthPercentage} className="h-2" />

          <div className="space-y-2">
            {health.checks.map((check, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  {check.status === "pass" ? (
                    <CheckCircle className="w-3 h-3 text-green-500" />
                  ) : check.status === "fail" ? (
                    <XCircle className="w-3 h-3 text-red-500" />
                  ) : (
                    <AlertTriangle className="w-3 h-3 text-yellow-500" />
                  )}
                  <span>{check.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  {check.latency && (
                    <span className="text-xs text-muted-foreground">
                      {check.latency}ms
                    </span>
                  )}
                  {check.message && (
                    <Badge variant="outline" className="text-xs">
                      {check.message}
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t text-xs text-muted-foreground">
            Last checked: {health.lastCheck.toLocaleString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

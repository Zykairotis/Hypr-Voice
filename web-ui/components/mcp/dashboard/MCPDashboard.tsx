"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import {
  Activity,
  Server,
  Play,
  Square,
  RotateCcw,
  Settings,
  FileText,
  BarChart3,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Cpu,
  HardDrive,
  MemoryStick,
  Wifi,
  WifiOff,
  Search,
  Filter,
  Download,
} from "lucide-react";
import { toast } from "sonner";

// Type definitions
interface McpServer {
  id: string;
  name: string;
  description: string;
  status: "running" | "stopped" | "starting" | "stopping" | "error";
  enabled: boolean;
  pid?: number;
  uptime?: number;
  lastHealthCheck?: Date;
  version?: string;
  endpoint?: string;
}

interface Agent {
  id: string;
  name: string;
  type: string;
  status: "active" | "idle" | "busy" | "error";
  serverId: string;
  lastActivity?: Date;
  tasksCompleted?: number;
}

interface LogEntry {
  id: string;
  timestamp: Date;
  level: "info" | "warn" | "error" | "debug";
  source: string;
  message: string;
  serverId?: string;
}

interface PerformanceMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    inbound: number;
    outbound: number;
  };
  activeConnections: number;
  requestsPerSecond: number;
}

interface ConnectionStatus {
  name: string;
  type: "github" | "filesystem" | "database" | "webhook" | "external-api";
  status: "connected" | "disconnected" | "error" | "connecting";
  lastCheck?: Date;
  endpoint?: string;
  latency?: number;
}

export default function MCPDashboard() {
  // State management
  const [servers, setServers] = useState<McpServer[]>([
    {
      id: "claude-flow",
      name: "claude-flow",
      description: "Claude Flow coordination server",
      status: "running",
      enabled: true,
      pid: 1234,
      uptime: 3600,
      lastHealthCheck: new Date(),
      version: "2.0.0",
      endpoint: "ws://localhost:8080",
    },
    {
      id: "ruv-swarm",
      name: "ruv-swarm",
      description: "RUV Swarm coordination server",
      status: "running",
      enabled: true,
      pid: 1235,
      uptime: 3600,
      lastHealthCheck: new Date(),
      version: "1.5.2",
      endpoint: "ws://localhost:8081",
    },
    {
      id: "flow-nexus",
      name: "flow-nexus",
      description: "Flow Nexus cloud services",
      status: "running",
      enabled: true,
      pid: 1236,
      uptime: 3500,
      lastHealthCheck: new Date(),
      version: "3.0.1",
      endpoint: "ws://localhost:8082",
    },
    {
      id: "filesystem",
      name: "filesystem",
      description: "File system operations server",
      status: "stopped",
      enabled: false,
      version: "1.0.0",
      endpoint: "ws://localhost:8083",
    },
    {
      id: "github",
      name: "github",
      description: "GitHub API integration server",
      status: "error",
      enabled: true,
      uptime: 0,
      lastHealthCheck: new Date(),
      version: "2.1.0",
      endpoint: "ws://localhost:8084",
    },
  ]);

  const [agents, setAgents] = useState<Agent[]>([
    {
      id: "agent-1",
      name: "coordinator",
      type: "hierarchical-coordinator",
      status: "active",
      serverId: "claude-flow",
      lastActivity: new Date(),
      tasksCompleted: 45,
    },
    {
      id: "agent-2",
      name: "mesh-coordinator",
      type: "mesh-coordinator",
      status: "active",
      serverId: "claude-flow",
      lastActivity: new Date(),
      tasksCompleted: 32,
    },
    {
      id: "agent-3",
      name: "swarm-executor",
      type: "swarm-executor",
      status: "idle",
      serverId: "ruv-swarm",
      lastActivity: new Date(Date.now() - 300000),
      tasksCompleted: 18,
    },
    {
      id: "agent-4",
      name: "neural-trainer",
      type: "neural-trainer",
      status: "busy",
      serverId: "flow-nexus",
      lastActivity: new Date(),
      tasksCompleted: 12,
    },
  ]);

  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: "1",
      timestamp: new Date(),
      level: "info",
      source: "claude-flow",
      message: "Agent swarm initialized successfully",
      serverId: "claude-flow",
    },
    {
      id: "2",
      timestamp: new Date(Date.now() - 30000),
      level: "info",
      source: "ruv-swarm",
      message: "Coordinator node connected",
      serverId: "ruv-swarm",
    },
    {
      id: "3",
      timestamp: new Date(Date.now() - 60000),
      level: "warn",
      source: "github",
      message: "Rate limit approaching - 80% used",
      serverId: "github",
    },
    {
      id: "4",
      timestamp: new Date(Date.now() - 90000),
      level: "error",
      source: "github",
      message: "Failed to authenticate with GitHub API",
      serverId: "github",
    },
    {
      id: "5",
      timestamp: new Date(Date.now() - 120000),
      level: "debug",
      source: "flow-nexus",
      message: "Neural pattern training started",
      serverId: "flow-nexus",
    },
  ]);

  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    cpu: 45,
    memory: 62,
    disk: 38,
    network: {
      inbound: 1250,
      outbound: 890,
    },
    activeConnections: 24,
    requestsPerSecond: 15.7,
  });

  const [connections, setConnections] = useState<ConnectionStatus[]>([
    {
      name: "GitHub API",
      type: "github",
      status: "connected",
      lastCheck: new Date(),
      endpoint: "api.github.com",
      latency: 120,
    },
    {
      name: "Local Filesystem",
      type: "filesystem",
      status: "connected",
      lastCheck: new Date(),
      latency: 5,
    },
    {
      name: "PostgreSQL Database",
      type: "database",
      status: "connected",
      lastCheck: new Date(),
      endpoint: "localhost:5432",
      latency: 15,
    },
    {
      name: "Webhook Service",
      type: "webhook",
      status: "disconnected",
      lastCheck: new Date(),
      endpoint: "webhooks.example.com",
    },
    {
      name: "OpenAI API",
      type: "external-api",
      status: "connected",
      lastCheck: new Date(),
      endpoint: "api.openai.com",
      latency: 245,
    },
  ]);

  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [logFilter, setLogFilter] = useState<"all" | "info" | "warn" | "error" | "debug">("all");
  const [searchTerm, setSearchTerm] = useState("");

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Update metrics with slight variations
      setMetrics(prev => ({
        ...prev,
        cpu: Math.max(10, Math.min(90, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.max(20, Math.min(90, prev.memory + (Math.random() - 0.5) * 5)),
        requestsPerSecond: Math.max(5, Math.min(30, prev.requestsPerSecond + (Math.random() - 0.5) * 2)),
      }));

      // Add new log entries occasionally
      if (Math.random() > 0.7) {
        const levels = ["info", "debug"] as const;
        const sources = servers.map(s => s.name);
        const newLog: LogEntry = {
          id: Date.now().toString(),
          timestamp: new Date(),
          level: levels[Math.floor(Math.random() * levels.length)],
          source: sources[Math.floor(Math.random() * sources.length)],
          message: "System status check completed",
        };
        setLogs(prev => [newLog, ...prev.slice(0, 99)]);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [servers]);

  // Helper functions
  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
      case "active":
      case "connected":
        return "bg-green-500/20 text-green-500 border-green-500/30";
      case "stopped":
      case "idle":
      case "disconnected":
        return "bg-gray-500/20 text-gray-500 border-gray-500/30";
      case "starting":
      case "busy":
      case "connecting":
        return "bg-yellow-500/20 text-yellow-500 border-yellow-500/30";
      case "stopping":
        return "bg-orange-500/20 text-orange-500 border-orange-500/30";
      case "error":
        return "bg-red-500/20 text-red-500 border-red-500/30";
      default:
        return "bg-gray-500/20 text-gray-500 border-gray-500/30";
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case "info":
        return "text-blue-400";
      case "warn":
        return "text-yellow-400";
      case "error":
        return "text-red-400";
      case "debug":
        return "text-purple-400";
      default:
        return "text-gray-400";
    }
  };

  const formatUptime = (seconds?: number) => {
    if (!seconds) return "N/A";
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const handleServerAction = (serverId: string, action: "start" | "stop" | "restart") => {
    setServers(prev =>
      prev.map(server => {
        if (server.id === serverId) {
          if (action === "start") {
            return { ...server, status: "starting" as const, uptime: 0 };
          } else if (action === "stop") {
            return { ...server, status: "stopping" as const };
          } else {
            return { ...server, status: "restarting" as const };
          }
        }
        return server;
      })
    );

    setTimeout(() => {
      setServers(prev =>
        prev.map(server => {
          if (server.id === serverId) {
            if (action === "start") {
              toast.success(`${server.name} server started successfully`);
              return { ...server, status: "running" as const, uptime: 0, pid: Math.floor(Math.random() * 10000) };
            } else if (action === "stop") {
              toast.info(`${server.name} server stopped`);
              return { ...server, status: "stopped" as const, uptime: 0, pid: undefined };
            } else {
              toast.success(`${server.name} server restarted`);
              return { ...server, status: "running" as const, uptime: 0 };
            }
          }
          return server;
        })
      );
    }, 2000);
  };

  const filteredLogs = logs.filter(log => {
    const matchesFilter = logFilter === "all" || log.level === logFilter;
    const matchesSearch = log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.source.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getConnectionIcon = (type: string) => {
    switch (type) {
      case "github":
        return "🐙";
      case "filesystem":
        return "📁";
      case "database":
        return "🗄️";
      case "webhook":
        return "🔗";
      case "external-api":
        return "🌐";
      default:
        return "🔌";
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">
            MCP Dashboard
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Model Context Protocol Server Management & Monitoring
          </p>
        </div>
        <Badge className={`${getStatusColor(metrics.cpu < 70 ? "running" : "error")} px-4 py-2`} variant="outline">
          <Activity className="w-4 h-4 mr-2" />
          System Healthy
        </Badge>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass border-border/50 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Active Servers</p>
              <p className="text-2xl font-bold">
                {servers.filter(s => s.status === "running").length}
              </p>
            </div>
            <Server className="w-8 h-8 text-primary opacity-60" />
          </div>
        </Card>

        <Card className="glass border-border/50 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Active Agents</p>
              <p className="text-2xl font-bold">
                {agents.filter(a => a.status === "active").length}
              </p>
            </div>
            <Activity className="w-8 h-8 text-green-500 opacity-60" />
          </div>
        </Card>

        <Card className="glass border-border/50 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">CPU Usage</p>
              <p className="text-2xl font-bold">{metrics.cpu.toFixed(0)}%</p>
            </div>
            <Cpu className="w-8 h-8 text-blue-500 opacity-60" />
          </div>
        </Card>

        <Card className="glass border-border/50 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Memory</p>
              <p className="text-2xl font-bold">{metrics.memory.toFixed(0)}%</p>
            </div>
            <MemoryStick className="w-8 h-8 text-purple-500 opacity-60" />
          </div>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="servers" className="space-y-4">
        <TabsList className="glass border-border/50 p-1">
          <TabsTrigger value="servers" className="data-[state=active]:bg-primary/20">
            Servers
          </TabsTrigger>
          <TabsTrigger value="agents" className="data-[state=active]:bg-primary/20">
            Agents
          </TabsTrigger>
          <TabsTrigger value="metrics" className="data-[state=active]:bg-primary/20">
            Metrics
          </TabsTrigger>
          <TabsTrigger value="logs" className="data-[state=active]:bg-primary/20">
            Logs
          </TabsTrigger>
          <TabsTrigger value="connections" className="data-[state=active]:bg-primary/20">
            Connections
          </TabsTrigger>
        </TabsList>

        {/* Servers Tab */}
        <TabsContent value="servers" className="space-y-4">
          <Card className="glass border-border/50 p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-lg font-semibold">Server Management</Label>
                <Button size="sm" className="glow-hover">
                  <Settings className="w-4 h-4 mr-2" />
                  Configure All
                </Button>
              </div>

              <div className="space-y-3">
                {servers.map(server => (
                  <div
                    key={server.id}
                    className={`p-4 rounded-lg glass-hover border cursor-pointer transition-all ${
                      selectedServer === server.id ? "border-primary/50 bg-primary/5" : "border-border/50"
                    }`}
                    onClick={() => setSelectedServer(selectedServer === server.id ? null : server.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <div className={`p-2 rounded-lg ${
                          server.status === "running"
                            ? "bg-green-500/10 border border-green-500/20"
                            : server.status === "error"
                            ? "bg-red-500/10 border border-red-500/20"
                            : "bg-muted/10 border border-border/20"
                        }`}>
                          <Server className={`w-5 h-5 ${
                            server.status === "running" ? "text-green-500" :
                            server.status === "error" ? "text-red-500" :
                            "text-muted-foreground"
                          }`} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{server.name}</span>
                            <Badge className={getStatusColor(server.status)} variant="outline">
                              {server.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mt-0.5">
                            {server.description}
                          </p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                            {server.version && <span>v{server.version}</span>}
                            {server.pid && <span>PID: {server.pid}</span>}
                            {server.uptime !== undefined && (
                              <span>Uptime: {formatUptime(server.uptime)}</span>
                            )}
                            {server.endpoint && <span>{server.endpoint}</span>}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {server.status === "running" && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              className="glass-hover"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleServerAction(server.id, "restart");
                              }}
                            >
                              <RotateCcw className="w-3 h-3" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="glass-hover"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleServerAction(server.id, "stop");
                              }}
                            >
                              <Square className="w-3 h-3" />
                            </Button>
                          </>
                        )}
                        {server.status === "stopped" && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="glass-hover"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleServerAction(server.id, "start");
                            }}
                          >
                            <Play className="w-3 h-3" />
                          </Button>
                        )}
                        {server.status === "error" && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="glass-hover"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleServerAction(server.id, "start");
                            }}
                          >
                            <AlertCircle className="w-3 h-3" />
                          </Button>
                        )}
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {selectedServer === server.id && (
                      <div className="mt-4 pt-4 border-t border-border/50 space-y-3">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <Label className="text-muted-foreground">Health Check</Label>
                            <p>
                              {server.lastHealthCheck
                                ? server.lastHealthCheck.toLocaleTimeString()
                                : "Never"}
                            </p>
                          </div>
                          <div>
                            <Label className="text-muted-foreground">Status</Label>
                            <Badge className={getStatusColor(server.status)} variant="outline">
                              {server.status}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* Agents Tab */}
        <TabsContent value="agents" className="space-y-4">
          <Card className="glass border-border/50 p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-lg font-semibold">Agent Status</Label>
                <Badge variant="outline" className="glass">
                  {agents.filter(a => a.status === "active").length}/{agents.length} active
                </Badge>
              </div>

              <div className="space-y-3">
                {agents.map(agent => (
                  <div
                    key={agent.id}
                    className="p-4 rounded-lg glass-hover border border-border/50"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <div className={`p-2 rounded-lg ${
                          agent.status === "active"
                            ? "bg-green-500/10 border border-green-500/20"
                            : agent.status === "busy"
                            ? "bg-yellow-500/10 border border-yellow-500/20"
                            : agent.status === "idle"
                            ? "bg-gray-500/10 border border-gray-500/20"
                            : "bg-red-500/10 border border-red-500/20"
                        }`}>
                          <Activity className={`w-5 h-5 ${
                            agent.status === "active" ? "text-green-500" :
                            agent.status === "busy" ? "text-yellow-500" :
                            agent.status === "idle" ? "text-gray-500" :
                            "text-red-500"
                          }`} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{agent.name}</span>
                            <Badge className={getStatusColor(agent.status)} variant="outline">
                              {agent.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mt-0.5">
                            {agent.type}
                          </p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                            <span>Server: {agent.serverId}</span>
                            <span>Tasks: {agent.tasksCompleted || 0}</span>
                            {agent.lastActivity && (
                              <span>
                                Last: {Math.floor((Date.now() - agent.lastActivity.getTime()) / 60000)}m ago
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Performance Metrics */}
            <Card className="glass border-border/50 p-6">
              <div className="space-y-4">
                <Label className="text-lg font-semibold flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Performance Metrics
                </Label>

                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground flex items-center gap-2">
                        <Cpu className="w-4 h-4" />
                        CPU Usage
                      </span>
                      <span className="text-sm font-medium">{metrics.cpu.toFixed(0)}%</span>
                    </div>
                    <Progress value={metrics.cpu} className="h-2" />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground flex items-center gap-2">
                        <MemoryStick className="w-4 h-4" />
                        Memory Usage
                      </span>
                      <span className="text-sm font-medium">{metrics.memory.toFixed(0)}%</span>
                    </div>
                    <Progress value={metrics.memory} className="h-2" />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground flex items-center gap-2">
                        <HardDrive className="w-4 h-4" />
                        Disk Usage
                      </span>
                      <span className="text-sm font-medium">{metrics.disk.toFixed(0)}%</span>
                    </div>
                    <Progress value={metrics.disk} className="h-2" />
                  </div>
                </div>
              </div>
            </Card>

            {/* Network Metrics */}
            <Card className="glass border-border/50 p-6">
              <div className="space-y-4">
                <Label className="text-lg font-semibold flex items-center gap-2">
                  <Wifi className="w-5 h-5" />
                  Network Activity
                </Label>

                <div className="space-y-4">
                  <div className="p-3 rounded-lg bg-card/50 border border-border/50">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Inbound</span>
                      <span className="text-sm font-medium">
                        {(metrics.network.inbound / 1024).toFixed(2)} KB/s
                      </span>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-card/50 border border-border/50">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Outbound</span>
                      <span className="text-sm font-medium">
                        {(metrics.network.outbound / 1024).toFixed(2)} KB/s
                      </span>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-card/50 border border-border/50">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Active Connections</span>
                      <span className="text-sm font-medium">{metrics.activeConnections}</span>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-card/50 border border-border/50">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Requests/sec</span>
                      <span className="text-sm font-medium">{metrics.requestsPerSecond.toFixed(1)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          <Card className="glass border-border/50 p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <Label className="text-lg font-semibold flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  System Logs
                </Label>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Search logs..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-9 pr-4 py-2 rounded-lg bg-card/50 border border-border/50 focus:outline-none focus:ring-2 focus:ring-primary/50 w-64"
                    />
                  </div>
                  <select
                    value={logFilter}
                    onChange={(e) => setLogFilter(e.target.value as any)}
                    className="px-3 py-2 rounded-lg bg-card/50 border border-border/50 focus:outline-none focus:ring-2 focus:ring-primary/50"
                  >
                    <option value="all">All Levels</option>
                    <option value="info">Info</option>
                    <option value="warn">Warning</option>
                    <option value="error">Error</option>
                    <option value="debug">Debug</option>
                  </select>
                  <Button variant="outline" size="sm" className="glass-hover">
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <ScrollArea className="h-[400px] rounded-lg border border-border/50">
                <div className="p-4 space-y-2">
                  {filteredLogs.map(log => (
                    <div
                      key={log.id}
                      className="p-3 rounded-lg bg-card/30 border border-border/30 hover:border-border/50 transition-all"
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex items-center gap-2 min-w-[100px]">
                          <Clock className="w-3 h-3 text-muted-foreground" />
                          <span className="text-xs text-muted-foreground">
                            {log.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                        <Badge className={`${getLevelColor(log.level)} bg-transparent border-current`} variant="outline">
                          {log.level.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-muted-foreground min-w-[100px]">
                          {log.source}
                        </span>
                        <span className="text-sm flex-1">{log.message}</span>
                      </div>
                    </div>
                  ))}
                  {filteredLogs.length === 0 && (
                    <div className="text-center text-muted-foreground py-8">
                      No logs match your filters
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          </Card>
        </TabsContent>

        {/* Connections Tab */}
        <TabsContent value="connections" className="space-y-4">
          <Card className="glass border-border/50 p-6">
            <div className="space-y-4">
              <Label className="text-lg font-semibold flex items-center gap-2">
                <Wifi className="w-5 h-5" />
                External Service Connections
              </Label>

              <div className="space-y-3">
                {connections.map((conn, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-lg glass-hover border border-border/50"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <div className="text-2xl">{getConnectionIcon(conn.type)}</div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{conn.name}</span>
                            <Badge className={getStatusColor(conn.status)} variant="outline">
                              {conn.status}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                            {conn.endpoint && <span>{conn.endpoint}</span>}
                            {conn.latency && <span>Latency: {conn.latency}ms</span>}
                            {conn.lastCheck && (
                              <span>
                                Checked: {Math.floor((Date.now() - conn.lastCheck.getTime()) / 1000)}s ago
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {conn.status === "connected" ? (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        ) : conn.status === "error" ? (
                          <XCircle className="w-5 h-5 text-red-500" />
                        ) : (
                          <WifiOff className="w-5 h-5 text-gray-500" />
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Search,
  Filter,
  Play,
  Square,
  MoreVertical,
  Settings,
  Trash2,
  Activity,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useMCPStore } from "@/lib/mcp-store";
import type { MCPServerConfig, MCPServerStatus } from "@/types/mcp";
import { toast } from "sonner";

export default function ServerList() {
  const {
    servers,
    serverMetrics,
    serverHealth,
    filterCategory,
    filterStatus,
    searchQuery,
    setFilterCategory,
    setFilterStatus,
    setSearchQuery,
    startServer,
    stopServer,
    restartServer,
    testServer,
    removeServer,
    setSelectedServer,
  } = useMCPStore();

  const [selectedServers, setSelectedServers] = useState<string[]>([]);

  const filteredServers = Object.values(servers).filter((server) => {
    const matchesSearch =
      server.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      server.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !filterCategory || server.category === filterCategory;
    const matchesStatus = !filterStatus || server.status === filterStatus;
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const handleServerAction = async (serverId: string, action: string) => {
    try {
      switch (action) {
        case "start":
          await startServer(serverId);
          toast.success("Server starting...");
          break;
        case "stop":
          await stopServer(serverId);
          toast.success("Server stopping...");
          break;
        case "restart":
          await restartServer(serverId);
          toast.success("Server restarting...");
          break;
        case "test":
          const result = await testServer(serverId);
          toast[result ? "success" : "error"](
            result ? "Server test passed" : "Server test failed"
          );
          break;
        case "delete":
          if (confirm("Are you sure you want to delete this server?")) {
            removeServer(serverId);
            toast.success("Server deleted");
          }
          break;
      }
    } catch (error) {
      toast.error(`Failed to ${action} server`);
    }
  };

  const handleBulkAction = async (action: string) => {
    for (const serverId of selectedServers) {
      await handleServerAction(serverId, action);
    }
    setSelectedServers([]);
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search servers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            <select
              className="px-3 py-2 bg-background border rounded-md"
              value={filterCategory || ""}
              onChange={(e) => setFilterCategory(e.target.value || null)}
            >
              <option value="">All Categories</option>
              <option value="filesystem">Filesystem</option>
              <option value="github">GitHub</option>
              <option value="git">Git</option>
              <option value="web">Web</option>
              <option value="database">Database</option>
              <option value="memory">Memory</option>
              <option value="ai">AI</option>
              <option value="custom">Custom</option>
            </select>

            <select
              className="px-3 py-2 bg-background border rounded-md"
              value={filterStatus || ""}
              onChange={(e) => setFilterStatus(e.target.value || null)}
            >
              <option value="">All Statuses</option>
              <option value="online">Online</option>
              <option value="offline">Offline</option>
              <option value="error">Error</option>
              <option value="starting">Starting</option>
              <option value="stopping">Stopping</option>
            </select>

            {selectedServers.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {selectedServers.length} selected
                </span>
                <Button size="sm" onClick={() => handleBulkAction("start")}>
                  Start All
                </Button>
                <Button size="sm" onClick={() => handleBulkAction("stop")}>
                  Stop All
                </Button>
                <Button size="sm" variant="outline" onClick={() => setSelectedServers([])}>
                  Clear
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Server Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {filteredServers.map((server) => (
            <ServerCard
              key={server.id}
              server={server}
              metrics={serverMetrics[server.id]}
              health={serverHealth[server.id]}
              isSelected={selectedServers.includes(server.id)}
              onSelect={(selected) => {
                setSelectedServers((prev) =>
                  selected
                    ? [...prev, server.id]
                    : prev.filter((id) => id !== server.id)
                );
              }}
              onAction={(action) => handleServerAction(server.id, action)}
              onEdit={() => setSelectedServer(server.id)}
            />
          ))}
        </AnimatePresence>
      </div>

      {filteredServers.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <Server className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No servers found</h3>
            <p className="text-muted-foreground">
              {Object.keys(servers).length === 0
                ? "Get started by adding your first MCP server"
                : "Try adjusting your filters or search query"}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ServerCard({
  server,
  metrics,
  health,
  isSelected,
  onSelect,
  onAction,
  onEdit,
}: {
  server: MCPServerConfig;
  metrics?: any;
  health?: any;
  isSelected: boolean;
  onSelect: (selected: boolean) => void;
  onAction: (action: string) => void;
  onEdit: () => void;
}) {
  const getStatusColor = (status: MCPServerStatus) => {
    switch (status) {
      case "online":
        return "bg-green-500";
      case "offline":
        return "bg-gray-500";
      case "starting":
      case "stopping":
        return "bg-yellow-500";
      case "error":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStatusIcon = (status: MCPServerStatus) => {
    switch (status) {
      case "online":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "offline":
        return <XCircle className="w-4 h-4 text-gray-500" />;
      case "error":
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <Activity className="w-4 h-4 text-yellow-500" />;
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ y: -2 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      <Card
        className={`cursor-pointer transition-all ${
          isSelected ? "ring-2 ring-primary" : "hover:shadow-lg"
        }`}
        onClick={() => onEdit()}
      >
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isSelected}
                onChange={(e) => {
                  e.stopPropagation();
                  onSelect(e.target.checked);
                }}
                className="rounded"
              />
              <div className={`w-2 h-2 rounded-full ${getStatusColor(server.status)}`} />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                <Button variant="ghost" size="icon-sm">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onAction("start")}>
                  <Play className="w-4 h-4 mr-2" />
                  Start
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onAction("stop")}>
                  <Square className="w-4 h-4 mr-2" />
                  Stop
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onAction("restart")}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Restart
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onAction("test")}>
                  <Activity className="w-4 h-4 mr-2" />
                  Test
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onEdit}>
                  <Settings className="w-4 h-4 mr-2" />
                  Configure
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => onAction("delete")}
                  className="text-destructive"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          <CardTitle className="text-lg">{server.name}</CardTitle>
          <CardDescription className="line-clamp-2">{server.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-xs">
                {server.category}
              </Badge>
              <div className="flex items-center gap-1">
                {getStatusIcon(server.status)}
                <span className="text-xs capitalize">{server.status}</span>
              </div>
            </div>

            {metrics && (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Uptime</span>
                  <span>{formatUptime(metrics.uptime)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Requests</span>
                  <span>{metrics.totalRequests}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Avg Response</span>
                  <span>{metrics.avgResponseTime}ms</span>
                </div>
                <div className="w-full bg-secondary h-1.5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{
                      width: `${Math.min(100, (metrics.avgResponseTime / 1000) * 100)}%`,
                    }}
                  />
                </div>
              </div>
            )}

            {health && (
              <div className="flex items-center gap-1 text-xs">
                <div
                  className={`w-2 h-2 rounded-full ${
                    health.status === "healthy"
                      ? "bg-green-500"
                      : health.status === "degraded"
                      ? "bg-yellow-500"
                      : "bg-red-500"
                  }`}
                />
                <span className="capitalize text-muted-foreground">
                  {health.status} ({health.checks.filter((c: any) => c.status === "pass").length}/
                  {health.checks.length} checks)
                </span>
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <Button
                size="sm"
                variant="outline"
                className="flex-1"
                onClick={(e) => {
                  e.stopPropagation();
                  onAction(server.status === "online" ? "stop" : "start");
                }}
              >
                {server.status === "online" ? (
                  <>
                    <Square className="w-3 h-3 mr-1" />
                    Stop
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3 mr-1" />
                    Start
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function formatUptime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

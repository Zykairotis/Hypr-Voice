"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Server,
  Activity,
  Settings,
  Store,
  Wrench,
  Users,
  BarChart3,
  Play,
  Square,
  RefreshCw,
  Search,
  Filter,
  Plus,
  Download,
  Upload,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useMCPStore } from "@/lib/mcp-store";
import ServerList from "./ServerList";
import ServerConfig from "./ServerConfig";
import MCPAnalytics from "../analytics/MCPAnalytics";
import ServerStore from "../store/ServerStore";
import CustomServerBuilder from "../custom/CustomServerBuilder";
import AgentMCPPanel from "../agents/AgentMCPPanel";
import ServerHealthMonitor from "./ServerHealthMonitor";
import { toast } from "sonner";

export default function MCPDashboard() {
  const {
    servers,
    analytics,
    isLoading,
    error,
    loadAnalytics,
    connectWebSocket,
    disconnectWebSocket,
    exportConfig,
    importConfig,
  } = useMCPStore();

  const [activeTab, setActiveTab] = useState("servers");
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    loadAnalytics();
    connectWebSocket();

    return () => {
      disconnectWebSocket();
    };
  }, []);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.toggle("dark", darkMode);
  }, [darkMode]);

  const serverStats = {
    total: Object.keys(servers).length,
    online: Object.values(servers).filter((s) => s.status === "online").length,
    offline: Object.values(servers).filter((s) => s.status === "offline").length,
    error: Object.values(servers).filter((s) => s.status === "error").length,
  };

  const handleExport = () => {
    const config = exportConfig();
    const blob = new Blob([config], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mcp-servers-${Date.now()}.json`;
    a.click();
    toast.success("Configuration exported successfully");
  };

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const config = e.target?.result as string;
        importConfig(config);
        toast.success("Configuration imported successfully");
      } catch (err) {
        toast.error("Failed to import configuration");
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <motion.div
              className="p-3 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30"
              whileHover={{ scale: 1.05 }}
            >
              <Server className="w-6 h-6 text-purple-400" />
            </motion.div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
                MCP Servers Manager
              </h1>
              <p className="text-white/50">
                Comprehensive Model Context Protocol server management and orchestration
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="file"
              accept=".json"
              onChange={handleImport}
              className="hidden"
              id="import-config"
            />
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
            <label htmlFor="import-config">
              <Button variant="outline" size="sm" asChild>
                <span>
                  <Upload className="w-4 h-4 mr-2" />
                  Import
                </span>
              </Button>
            </label>
            <Button variant="outline" size="sm">
              <Plus className="w-4 h-4 mr-2" />
              Add Server
            </Button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <StatCard
            title="Total Servers"
            value={serverStats.total}
            icon={Server}
            color="blue"
          />
          <StatCard
            title="Online"
            value={serverStats.online}
            icon={Play}
            color="green"
          />
          <StatCard
            title="Offline"
            value={serverStats.offline}
            icon={Square}
            color="gray"
          />
          <StatCard
            title="Errors"
            value={serverStats.error}
            icon={Activity}
            color="red"
            alert={serverStats.error > 0}
          />
        </div>

        {/* Health Monitor Mini */}
        <Card className="mb-6">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">System Health Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <ServerHealthMonitor compact />
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="servers" className="flex items-center gap-2">
            <Server className="w-4 h-4" />
            Servers
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="store" className="flex items-center gap-2">
            <Store className="w-4 h-4" />
            Store
          </TabsTrigger>
          <TabsTrigger value="agents" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Agents
          </TabsTrigger>
          <TabsTrigger value="builder" className="flex items-center gap-2">
            <Wrench className="w-4 h-4" />
            Builder
          </TabsTrigger>
          <TabsTrigger value="config" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Config
          </TabsTrigger>
        </TabsList>

        <TabsContent value="servers" className="space-y-4">
          <ServerList />
        </TabsContent>

        <TabsContent value="analytics">
          <MCPAnalytics />
        </TabsContent>

        <TabsContent value="store">
          <ServerStore />
        </TabsContent>

        <TabsContent value="agents">
          <AgentMCPPanel />
        </TabsContent>

        <TabsContent value="builder">
          <CustomServerBuilder />
        </TabsContent>

        <TabsContent value="config">
          <ServerConfig />
        </TabsContent>
      </Tabs>

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-destructive text-white p-4 rounded-lg shadow-lg">
          {error}
        </div>
      )}
    </div>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
  alert = false,
}: {
  title: string;
  value: number | string;
  icon: any;
  color: "blue" | "green" | "red" | "gray" | "purple";
  alert?: boolean;
}) {
  const colorClasses = {
    blue: "from-blue-500/20 to-blue-600/20 border-blue-500/30",
    green: "from-green-500/20 to-green-600/20 border-green-500/30",
    red: "from-red-500/20 to-red-600/20 border-red-500/30",
    gray: "from-gray-500/20 to-gray-600/20 border-gray-500/30",
    purple: "from-purple-500/20 to-purple-600/20 border-purple-500/30",
  };

  const iconColorClasses = {
    blue: "text-blue-400",
    green: "text-green-400",
    red: "text-red-400",
    gray: "text-gray-400",
    purple: "text-purple-400",
  };

  return (
    <motion.div whileHover={{ scale: 1.02 }} transition={{ type: "spring", stiffness: 300 }}>
      <Card className={`bg-gradient-to-br ${colorClasses[color]} border`}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white/60">{title}</p>
              <p className={`text-2xl font-bold ${alert ? "text-red-400" : "text-white"}`}>
                {value}
              </p>
            </div>
            <Icon className={`w-8 h-8 ${iconColorClasses[color]} ${alert ? "animate-pulse" : ""}`} />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

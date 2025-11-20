"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Settings,
  CheckCircle,
  XCircle,
  Download,
  ExternalLink,
  Key,
  Server,
} from "lucide-react";
import type { MCPServer } from "@/types/skills";

export default function ToolsMarketplace() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState<string>("all");

  useEffect(() => {
    fetchMCPServers();
  }, []);

  const fetchMCPServers = async () => {
    try {
      const response = await fetch("/api/skills/mcp");
      const data = await response.json();
      setServers(data.servers);
    } catch (error) {
      console.error("Failed to fetch MCP servers:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredServers =
    filterCategory === "all"
      ? servers
      : servers.filter((server) => server.category === filterCategory);

  const handleToggleServer = (serverId: string, enabled: boolean) => {
    setServers((prev) =>
      prev.map((server) =>
        server.id === serverId ? { ...server, enabled } : server
      )
    );
  };

  const categories = [...new Set(servers.map((s) => s.category))];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
          Tools Marketplace
        </h2>
        <p className="text-white/60 mt-1">
          MCP servers and third-party tool integrations
        </p>
      </div>

      <div className="flex items-center gap-4">
        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-[200px] bg-white/5 border-white/10">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map((category) => (
              <SelectItem key={category} value={category}>
                {category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="h-64 bg-white/5 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredServers.map((server) => (
            <motion.div
              key={server.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              whileHover={{ y: -4 }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
            >
              <Card className="h-full">
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${
                    server.enabled
                      ? "from-white/5 to-white/0"
                      : "from-gray-500/5 to-gray-500/0"
                  } to-transparent opacity-50`}
                />

                <CardHeader className="relative">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Server className="w-5 h-5 text-blue-400" />
                        <CardTitle className="text-lg">{server.name}</CardTitle>
                      </div>
                      <CardDescription className="text-sm text-white/60">
                        {server.description}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="relative space-y-4">
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className="bg-white/5 border-white/10 text-white/70"
                    >
                      {server.category}
                    </Badge>
                    {server.auth_required && (
                      <Badge
                        variant="outline"
                        className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                      >
                        <Key className="w-3 h-3 mr-1" />
                        Auth
                      </Badge>
                    )}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-white/60">Version</span>
                      <span className="text-white">{server.version}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-white/60">Installed</span>
                      {server.installed ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400" />
                      )}
                    </div>
                  </div>

                  {server.maintainer && (
                    <div className="text-sm text-white/60">
                      <span className="font-medium">Maintainer:</span>{" "}
                      {server.maintainer}
                    </div>
                  )}
                </CardContent>

                <CardContent className="relative pt-0">
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1"
                      disabled={!server.installed}
                    >
                      <Settings className="w-4 h-4 mr-2" />
                      Configure
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1"
                      onClick={() =>
                        handleToggleServer(server.id, !server.enabled)
                      }
                    >
                      {server.enabled ? (
                        <>
                          <XCircle className="w-4 h-4 mr-2" />
                          Disable
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Enable
                        </>
                      )}
                    </Button>
                  </div>

                  {!server.installed && (
                    <Button size="sm" className="w-full mt-2">
                      <Download className="w-4 h-4 mr-2" />
                      Install
                    </Button>
                  )}
                </CardContent>

                {server.homepage && (
                  <div className="p-4 pt-0">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="w-full text-blue-400 hover:text-blue-300"
                      asChild
                    >
                      <a
                        href={server.homepage}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        View Documentation
                      </a>
                    </Button>
                  </div>
                )}
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

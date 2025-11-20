"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Save, Server, FileCode, Github, Database, Globe, Play, Square } from "lucide-react";
import { toast } from "sonner";

interface McpServer {
  name: string;
  description: string;
  enabled: boolean;
  status: "running" | "stopped" | "error";
  icon: React.ReactNode;
}

export default function McpServers() {
  const [servers, setServers] = useState<McpServer[]>([
    {
      name: "filesystem",
      description: "File system operations MCP server",
      enabled: true,
      status: "running",
      icon: <FileCode className="w-4 h-4" />,
    },
    {
      name: "github",
      description: "GitHub operations MCP server",
      enabled: true,
      status: "running",
      icon: <Github className="w-4 h-4" />,
    },
    {
      name: "git",
      description: "Git operations MCP server",
      enabled: true,
      status: "running",
      icon: <Server className="w-4 h-4" />,
    },
    {
      name: "fetch",
      description: "HTTP fetch MCP server",
      enabled: true,
      status: "running",
      icon: <Globe className="w-4 h-4" />,
    },
    {
      name: "sqlite",
      description: "SQLite database MCP server",
      enabled: false,
      status: "stopped",
      icon: <Database className="w-4 h-4" />,
    },
    {
      name: "postgres",
      description: "PostgreSQL database MCP server",
      enabled: false,
      status: "stopped",
      icon: <Database className="w-4 h-4" />,
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorCount, setErrorCount] = useState(0);

  useEffect(() => {
    loadMcpConfig();
  }, []);

  const loadMcpConfig = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/config/mcp", {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const config = await response.json();
        if (config.servers) {
          setServers(prevServers =>
            prevServers.map(server => ({
              ...server,
              enabled: config.servers[server.name]?.enabled ?? server.enabled,
              status: config.servers[server.name]?.status || server.status,
            }))
          );
          setErrorCount(0);
        }
      }
    } catch (error) {
      // Only log once to avoid console spam
      if (errorCount === 0) {
        console.warn("Backend not available. Using default MCP server configuration.");
      }
      setErrorCount(prev => prev + 1);
    }
  };

  const toggleServer = (index: number) => {
    setServers(prevServers => {
      const updated = [...prevServers];
      updated[index].enabled = !updated[index].enabled;
      updated[index].status = updated[index].enabled ? "running" : "stopped";
      return updated;
    });
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const config = {
        servers: servers.reduce((acc, server) => ({
          ...acc,
          [server.name]: {
            enabled: server.enabled,
            status: server.status,
          },
        }), {}),
      };

      const response = await fetch("http://localhost:8934/api/config/mcp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        toast.success("MCP server configuration saved successfully", {
          description: "Server restart may be required"
        });
      } else {
        toast.error("Failed to save configuration");
      }
    } catch (error) {
      toast.error("Error saving configuration");
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-green-500/20 text-green-500 border-green-500/30";
      case "stopped":
        return "bg-gray-500/20 text-gray-500 border-gray-500/30";
      case "error":
        return "bg-red-500/20 text-red-500 border-red-500/30";
      default:
        return "bg-gray-500/20 text-gray-500 border-gray-500/30";
    }
  };

  return (
    <div className="space-y-6">
      {/* MCP Servers Info */}
      <div className="p-4 rounded-lg glass border border-border/50">
        <div className="flex items-start gap-3">
          <Server className="w-5 h-5 text-primary mt-0.5" />
          <div>
            <p className="font-medium">Model Context Protocol (MCP)</p>
            <p className="text-sm text-muted-foreground mt-1">
              MCP servers extend agent capabilities with external tools and data sources.
              Enable the servers you need for your workflows.
            </p>
          </div>
        </div>
      </div>

      {/* Server List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">Available Servers</Label>
          <Badge variant="outline" className="glass">
            {servers.filter(s => s.enabled).length}/{servers.length} enabled
          </Badge>
        </div>

        <div className="space-y-3">
          {servers.map((server, index) => (
            <Card key={server.name} className="glass-hover border-border/50 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <div className={`p-2 rounded-lg ${
                    server.enabled 
                      ? "bg-primary/10 border border-primary/20" 
                      : "bg-muted/10 border border-border/20"
                  }`}>
                    {server.icon}
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
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {server.enabled && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="glass-hover"
                      onClick={() => {
                        toast.info(`${server.status === "running" ? "Stopping" : "Starting"} ${server.name}...`);
                      }}
                    >
                      {server.status === "running" ? (
                        <Square className="w-3 h-3" />
                      ) : (
                        <Play className="w-3 h-3" />
                      )}
                    </Button>
                  )}
                  <Switch
                    checked={server.enabled}
                    onCheckedChange={() => toggleServer(index)}
                  />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Statistics */}
      <Card className="glass border-border/50 p-4">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-green-500">
              {servers.filter(s => s.status === "running").length}
            </div>
            <div className="text-sm text-muted-foreground">Running</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-500">
              {servers.filter(s => s.status === "stopped").length}
            </div>
            <div className="text-sm text-muted-foreground">Stopped</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-500">
              {servers.filter(s => s.status === "error").length}
            </div>
            <div className="text-sm text-muted-foreground">Errors</div>
          </div>
        </div>
      </Card>

      {/* Save Button */}
      <div className="pt-4">
        <Button
          onClick={handleSave}
          disabled={isLoading}
          className="w-full glow-hover"
          size="lg"
        >
          <Save className="w-4 h-4 mr-2" />
          {isLoading ? "Saving..." : "Save MCP Configuration"}
        </Button>
      </div>
    </div>
  );
}


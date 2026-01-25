"use client";

import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Activity } from "lucide-react";
import { endpoints } from "@/lib/endpoints";

const AGENT_API_URL = endpoints.api.orchestratorStatus;
const AGENT_WEBSOCKET_URL = endpoints.ws.orchestrator;

interface AgentStats {
  status: "online" | "offline" | "error";
}

export default function AgentStatus() {
  const [stats, setStats] = useState<AgentStats>({
    status: "offline",
  });

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch(AGENT_API_URL, {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const data = await response.json();
        setStats({
          status: (data.status === "healthy" || data.status === "online") ? "online" : "offline",
        });
      } else {
        setStats({ status: "offline" });
      }
    } catch {
      setStats({ status: "offline" });
    }
  };

  const statusColors = {
    online: "bg-green-500/20 text-green-500 border-green-500/30",
    offline: "bg-gray-500/20 text-gray-500 border-gray-500/30",
    error: "bg-red-500/20 text-red-500 border-red-500/30",
  };

  return (
    <div className="space-y-4">
      {/* Status Badge */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className={`w-5 h-5 ${stats.status === "online" ? "text-green-500 animate-pulse" : "text-gray-500"}`} />
          <span className="font-medium">Agent Server</span>
        </div>
        <Badge className={statusColors[stats.status]} variant="outline">
          {stats.status}
        </Badge>
      </div>

      {/* Connection Info */}
      <div className="p-3 rounded-lg glass border border-border/50 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">API Endpoint</span>
          <code className="text-xs bg-background/50 px-2 py-1 rounded">{AGENT_API_URL}</code>
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-muted-foreground">WebSocket</span>
          <code className="text-xs bg-background/50 px-2 py-1 rounded">{AGENT_WEBSOCKET_URL}</code>
        </div>
      </div>

    </div>
  );
}

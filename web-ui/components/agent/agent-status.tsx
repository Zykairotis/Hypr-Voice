"use client";

import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Activity } from "lucide-react";

// Configurable agent endpoints
const AGENT_HOST = "localhost";
const AGENT_PORT = 8922;
const AGENT_API_URL = `http://${AGENT_HOST}:${AGENT_PORT}`;
const AGENT_WEBSOCKET_URL = `ws://${AGENT_HOST}:${AGENT_PORT}/ws`;

// Note: Agent system is under development - keeping it offline for now
const AGENT_STATUS_OVERRIDE = "offline";

interface AgentStats {
  status: "online" | "offline" | "error";
}

export default function AgentStatus() {
  const [stats, setStats] = useState<AgentStats>({
    status: AGENT_STATUS_OVERRIDE,
  });

  useEffect(() => {
    // Agent system is under development - keeping status offline
    // fetchStatus();
    // const interval = setInterval(fetchStatus, 3000);
    // return () => clearInterval(interval);
  }, []);

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

      {/* Development Notice */}
      <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30 text-sm">
        <p className="text-yellow-500/80">🔧 Agent system is under development. Status kept offline for now.</p>
      </div>
    </div>
  );
}


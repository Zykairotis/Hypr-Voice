"use client";

import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Activity } from "lucide-react";

// Configurable server endpoints
const WHISPER_HOST = "localhost";
const WHISPER_PORT = 9099;
const WHISPER_WEBSOCKET_URL = `ws://${WHISPER_HOST}:${WHISPER_PORT}`;
const WHISPER_REST_API_URL = `http://${WHISPER_HOST}:${WHISPER_PORT}`;

interface ServerStats {
  status: "online" | "offline" | "error";
}

export default function ServerStatus() {
  const [stats, setStats] = useState<ServerStats>({
    status: "offline",
  });
  const [errorCount, setErrorCount] = useState(0);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/whisper/status", {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const data = await response.json();
        setStats({
          status: data.status || "offline",
        });
        setErrorCount(0); // Reset error count on success
      } else {
        setStats(prev => ({ ...prev, status: "error" }));
      }
    } catch (error) {
      // Only log occasionally to avoid console spam
      if (errorCount === 0 || errorCount % 10 === 0) {
        console.warn("Failed to fetch Whisper status. Backend bridge may be unavailable.");
      }
      setErrorCount(prev => prev + 1);
      setStats(prev => ({ ...prev, status: "offline" }));
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
          <span className="font-medium">Server Status</span>
        </div>
        <Badge className={statusColors[stats.status]} variant="outline">
          {stats.status}
        </Badge>
      </div>

      {/* Connection Info */}
      <div className="p-3 rounded-lg glass border border-border/50 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">WebSocket</span>
          <code className="text-xs bg-background/50 px-2 py-1 rounded">{WHISPER_WEBSOCKET_URL}</code>
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-muted-foreground">REST API</span>
          <code className="text-xs bg-background/50 px-2 py-1 rounded">{WHISPER_REST_API_URL}</code>
        </div>
      </div>
    </div>
  );
}


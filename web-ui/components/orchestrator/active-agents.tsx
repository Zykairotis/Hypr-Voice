"use client";

import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Trash2, RefreshCw, Clock, Bot, Loader2, Zap, Users } from "lucide-react";
import { toast } from "sonner";
import { endpoints } from "@/lib/endpoints";
import { useOrchestratorWebSocket, OrchestratorEvent } from "@/lib/orchestrator-websocket";

interface AgentSession {
  session_id: string;
  agent_type: string;
  status: string;
  query: string;
  created_at: string;
  updated_at: string;
  parent_session?: string;
  children?: string[];
}

export default function ActiveAgents() {
  const [agents, setAgents] = useState<AgentSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [destroying, setDestroying] = useState<string | null>(null);
  const { isConnected, subscribe } = useOrchestratorWebSocket();

  const fetchAgents = useCallback(async () => {
    try {
      const response = await fetch(endpoints.direct.agents);
      if (response.ok) {
        const data = await response.json();
        setAgents(data.agents || []);
      }
    } catch {
      // Ignore errors
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, isConnected ? 10000 : 3000);
    return () => clearInterval(interval);
  }, [fetchAgents, isConnected]);

  useEffect(() => {
    const unsubCreated = subscribe("agent_created", (event: OrchestratorEvent) => {
      if (event.data) {
        setAgents(prev => [...prev, event.data]);
        toast.success(`Agent ${event.data.agent_type} spawned`);
      }
    });

    const unsubCompleted = subscribe("agent_completed", (event: OrchestratorEvent) => {
      if (event.data?.session_id) {
        setAgents(prev => prev.map(a => 
          a.session_id === event.data.session_id 
            ? { ...a, status: "completed" } 
            : a
        ));
      }
    });

    const unsubDestroyed = subscribe("agent_destroyed", (event: OrchestratorEvent) => {
      if (event.data?.session_id) {
        setAgents(prev => prev.filter(a => a.session_id !== event.data.session_id));
      }
    });

    return () => {
      unsubCreated();
      unsubCompleted();
      unsubDestroyed();
    };
  }, [subscribe]);

  const destroyAgent = async (sessionId: string) => {
    setDestroying(sessionId);
    try {
      const response = await fetch(`${endpoints.orchestrator}/agents/${sessionId}`, {
        method: "DELETE",
      });
      if (response.ok) {
        toast.success("Agent destroyed");
        setAgents(prev => prev.filter(a => a.session_id !== sessionId));
      } else {
        toast.error("Failed to destroy agent");
      }
    } catch {
      toast.error("Error destroying agent");
    } finally {
      setDestroying(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "completed":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "error":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-violet-400" />
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 sm:py-12 text-center">
        <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-violet-500/10 flex items-center justify-center mb-4">
          <Bot className="w-6 h-6 sm:w-8 sm:h-8 text-violet-400" />
        </div>
        <h3 className="text-base sm:text-lg font-medium text-white/80 mb-2">No Active Agents</h3>
        <p className="text-xs sm:text-sm text-white/50 max-w-md px-4">
          Agent sessions will appear here when you send queries.
        </p>
        <Button
          variant="outline"
          size="sm"
          className="mt-4 glass"
          onClick={fetchAgents}
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs sm:text-sm text-white/60">{agents.length} session(s)</span>
          {isConnected && (
            <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/30 text-xs">
              <Zap className="w-3 h-3 mr-1" />
              Live
            </Badge>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={fetchAgents}>
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {agents.map((agent) => (
        <Card
          key={agent.session_id}
          className="p-4 glass border-border/50 hover:border-violet-500/30 transition-colors"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline" className="text-xs">
                  {agent.agent_type}
                </Badge>
                <Badge className={`text-xs ${getStatusColor(agent.status)}`}>
                  {agent.status}
                </Badge>
              </div>
              <p className="text-sm text-white/80 truncate mb-2">
                {agent.query || "No query"}
              </p>
              <div className="flex items-center gap-4 text-xs text-white/40">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(agent.created_at).toLocaleTimeString()}
                </span>
                <span className="font-mono">{agent.session_id.slice(0, 8)}...</span>
              </div>
            </div>

            <Button
              variant="ghost"
              size="sm"
              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
              onClick={() => destroyAgent(agent.session_id)}
              disabled={destroying === agent.session_id}
            >
              {destroying === agent.session_id ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
}

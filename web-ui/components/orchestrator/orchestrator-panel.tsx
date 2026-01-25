"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Network, Bot, Terminal, Cpu, Activity, MessageSquare, Zap } from "lucide-react";
import OrchestratorStatus from "./orchestrator-status";
import AgentTypes from "./agent-types";
import ActiveAgents from "./active-agents";
import QueryInterface from "./query-interface";
import ConversationPanel from "./conversation-panel";
import { endpoints } from "@/lib/endpoints";
import { useOrchestratorWebSocket } from "@/lib/orchestrator-websocket";

interface OrchestratorPanelProps {
  onStatusChange: (status: "online" | "offline" | "error") => void;
}

export default function OrchestratorPanel({ onStatusChange }: OrchestratorPanelProps) {
  const [status, setStatus] = useState<"online" | "offline" | "error">("offline");
  const { isConnected: wsConnected } = useOrchestratorWebSocket();

  const checkOrchestratorStatus = useCallback(async () => {
    try {
      const response = await fetch(endpoints.direct.health, {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const data = await response.json();
        const newStatus = (data.status === "online" || data.status === "healthy") ? "online" : "offline";
        setStatus(newStatus);
        onStatusChange(newStatus);
      } else {
        setStatus("offline");
        onStatusChange("offline");
      }
    } catch {
      setStatus("offline");
      onStatusChange("offline");
    }
  }, [onStatusChange]);

  useEffect(() => {
    checkOrchestratorStatus();
    const interval = setInterval(checkOrchestratorStatus, wsConnected ? 10000 : 5000);
    return () => clearInterval(interval);
  }, [checkOrchestratorStatus, wsConnected]);

  return (
    <div className="space-y-6">
      {/* Orchestrator Status Card */}
      <Card className="glass glass-hover border-border/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/30">
              <Network className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <CardTitle className="flex flex-wrap items-center gap-2">
                <span className="text-base sm:text-lg">Agent Orchestrator</span>
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                  status === "online" 
                    ? "bg-green-500/20 text-green-400 border border-green-500/30" 
                    : "bg-gray-500/20 text-gray-400 border border-gray-500/30"
                }`}>
                  {status}
                </span>
                {wsConnected && (
                  <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/30 text-xs">
                    <Zap className="w-3 h-3 mr-1" />
                    Live
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                Claude Agent SDK orchestration system with specialized subagents
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <OrchestratorStatus status={status} />
        </CardContent>
      </Card>

      {/* Voice Conversation */}
      <ConversationPanel orchestratorOnline={status === "online"} />

      {/* Tabs for Agent Management */}
      <Card className="glass glass-hover border-border/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/30">
              <Cpu className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <CardTitle>Agent Management</CardTitle>
              <CardDescription>View and manage specialized agents</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="types" className="w-full">
            <TabsList className="grid w-full grid-cols-3 glass p-1">
              <TabsTrigger value="types" className="data-[state=active]:bg-violet-500/20">
                <Bot className="w-4 h-4 mr-2" />
                Agent Types
              </TabsTrigger>
              <TabsTrigger value="active" className="data-[state=active]:bg-violet-500/20">
                <Activity className="w-4 h-4 mr-2" />
                Active Sessions
              </TabsTrigger>
              <TabsTrigger value="query" className="data-[state=active]:bg-violet-500/20">
                <Terminal className="w-4 h-4 mr-2" />
                Query
              </TabsTrigger>
            </TabsList>

            <TabsContent value="types" className="mt-6">
              <AgentTypes />
            </TabsContent>

            <TabsContent value="active" className="mt-6">
              <ActiveAgents />
            </TabsContent>

            <TabsContent value="query" className="mt-6">
              <QueryInterface disabled={status !== "online"} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

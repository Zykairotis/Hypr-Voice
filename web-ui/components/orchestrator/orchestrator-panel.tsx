"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Network, Bot, Terminal, Cpu, Activity } from "lucide-react";
import OrchestratorStatus from "./orchestrator-status";
import AgentTypes from "./agent-types";
import ActiveAgents from "./active-agents";
import QueryInterface from "./query-interface";

interface OrchestratorPanelProps {
  onStatusChange: (status: "online" | "offline" | "error") => void;
}

export default function OrchestratorPanel({ onStatusChange }: OrchestratorPanelProps) {
  const [status, setStatus] = useState<"online" | "offline" | "error">("offline");

  useEffect(() => {
    checkOrchestratorStatus();
    const interval = setInterval(checkOrchestratorStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkOrchestratorStatus = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/orchestrator/status", {
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
  };

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
              <CardTitle className="flex items-center gap-2">
                Agent Orchestrator
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                  status === "online" 
                    ? "bg-green-500/20 text-green-400 border border-green-500/30" 
                    : "bg-gray-500/20 text-gray-400 border border-gray-500/30"
                }`}>
                  {status}
                </span>
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

      {/* Query Interface */}
      <Card className="glass glass-hover border-border/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30">
              <Terminal className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <CardTitle>Query Interface</CardTitle>
              <CardDescription>
                Send queries to the orchestrator (F10 for voice input)
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <QueryInterface disabled={status !== "online"} />
        </CardContent>
      </Card>

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
            <TabsList className="grid w-full grid-cols-2 glass p-1">
              <TabsTrigger value="types" className="data-[state=active]:bg-violet-500/20">
                <Bot className="w-4 h-4 mr-2" />
                Agent Types
              </TabsTrigger>
              <TabsTrigger value="active" className="data-[state=active]:bg-violet-500/20">
                <Activity className="w-4 h-4 mr-2" />
                Active Sessions
              </TabsTrigger>
            </TabsList>

            <TabsContent value="types" className="mt-6">
              <AgentTypes />
            </TabsContent>

            <TabsContent value="active" className="mt-6">
              <ActiveAgents />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

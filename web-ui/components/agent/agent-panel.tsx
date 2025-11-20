"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bot, Mic2, Server, Zap, MessageSquare } from "lucide-react";
import AgentManager from "./agent-manager";
import VoiceConfig from "./voice-config";
import McpServers from "./mcp-servers";
import SkillsConfig from "./skills-config";
import AgentStatus from "./agent-status";

interface AgentPanelProps {
  onStatusChange: (status: "online" | "offline" | "error") => void;
}

export default function AgentPanel({ onStatusChange }: AgentPanelProps) {
  useEffect(() => {
    // Agent system is under development - force status to offline
    onStatusChange("offline");
    // Commented out status checks until agent system is ready
    // checkAgentStatus();
    // const interval = setInterval(checkAgentStatus, 5000);
    // return () => clearInterval(interval);
  }, [onStatusChange]);

  const checkAgentStatus = async () => {
    // Agent system is under development - keeping offline for now
    onStatusChange("offline");
  };

  return (
    <div className="space-y-6">
      {/* Agent Status Card */}
      <Card className="glass glass-hover border-border/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
              <Bot className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle>Agent System Status</CardTitle>
              <CardDescription>Multi-agent orchestration with Claude SDK</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <AgentStatus />
        </CardContent>
      </Card>

      {/* Configuration Tabs */}
      <Card className="glass glass-hover border-border/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
              <Zap className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle>Configuration</CardTitle>
              <CardDescription>Manage agent services and settings</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="agents" className="w-full">
            <TabsList className="grid w-full grid-cols-4 glass p-1">
              <TabsTrigger value="agents">
                <Bot className="w-4 h-4 mr-2" />
                Agents
              </TabsTrigger>
              <TabsTrigger value="voice">
                <Mic2 className="w-4 h-4 mr-2" />
                Voice
              </TabsTrigger>
              <TabsTrigger value="mcp">
                <Server className="w-4 h-4 mr-2" />
                MCP
              </TabsTrigger>
              <TabsTrigger value="skills">
                <Zap className="w-4 h-4 mr-2" />
                Skills
              </TabsTrigger>
            </TabsList>

            <TabsContent value="agents" className="mt-6">
              <AgentManager />
            </TabsContent>

            <TabsContent value="voice" className="mt-6">
              <VoiceConfig />
            </TabsContent>

            <TabsContent value="mcp" className="mt-6">
              <McpServers />
            </TabsContent>

            <TabsContent value="skills" className="mt-6">
              <SkillsConfig />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}


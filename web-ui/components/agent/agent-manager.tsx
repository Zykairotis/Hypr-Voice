"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Plus, Play, Pause, Trash2, Bot, MessageSquare } from "lucide-react";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface Agent {
  id: string;
  name: string;
  status: "idle" | "running" | "paused" | "error";
  created_at: string;
  model: string;
}

export default function AgentManager() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [newAgentName, setNewAgentName] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [errorCount, setErrorCount] = useState(0);
  const [backendAvailable, setBackendAvailable] = useState(true);

  useEffect(() => {
    fetchAgents();
    // Poll for agents every 5 seconds
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/agent/status", {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const data = await response.json();
        setAgents(data.agents || []);
        setBackendAvailable(true);
        setErrorCount(0);
      } else {
        setBackendAvailable(false);
      }
    } catch (error) {
      // Only log warning occasionally to avoid console spam
      if (errorCount === 0 || errorCount % 10 === 0) {
        console.warn("Agent backend not available on port 8934. Run './start-ui.sh' to start the backend.");
      }
      setBackendAvailable(false);
      setErrorCount(prev => prev + 1);
    }
  };

  const createAgent = async () => {
    if (!newAgentName.trim()) return;

    setIsCreating(true);
    try {
      const response = await fetch("http://localhost:8934/api/agents/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newAgentName,
          model: "claude-3-5-sonnet-20241022",
        }),
      });

      if (response.ok) {
        toast.success(`Agent "${newAgentName}" created successfully`);
        setNewAgentName("");
        fetchAgents();
      } else {
        toast.error("Failed to create agent");
      }
    } catch (error) {
      toast.error("Error creating agent");
    } finally {
      setIsCreating(false);
    }
  };

  const deleteAgent = async (id: string, name: string) => {
    try {
      const response = await fetch(`http://localhost:8934/api/agents/${id}`, {
        method: "DELETE",
      });

      if (response.ok) {
        toast.success(`Agent "${name}" deleted`);
        fetchAgents();
      } else {
        toast.error("Failed to delete agent");
      }
    } catch (error) {
      toast.error("Error deleting agent");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-green-500/20 text-green-500 border-green-500/30";
      case "idle":
        return "bg-blue-500/20 text-blue-500 border-blue-500/30";
      case "paused":
        return "bg-yellow-500/20 text-yellow-500 border-yellow-500/30";
      case "error":
        return "bg-red-500/20 text-red-500 border-red-500/30";
      default:
        return "bg-gray-500/20 text-gray-500 border-gray-500/30";
    }
  };

  return (
    <div className="space-y-6">
      {/* Create New Agent */}
      <div className="space-y-3">
        <Label htmlFor="agentName" className="text-base font-semibold">
          Create New Agent
        </Label>
        <div className="flex gap-2">
          <Input
            id="agentName"
            placeholder="Agent name..."
            value={newAgentName}
            onChange={(e) => setNewAgentName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && createAgent()}
            className="glass"
          />
          <Button
            onClick={createAgent}
            disabled={isCreating || !newAgentName.trim()}
            className="glow-hover"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create
          </Button>
        </div>
      </div>

      <Separator className="bg-border/50" />

      {/* Active Agents */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">Active Agents</Label>
          {!backendAvailable && (
            <Badge variant="outline" className="text-amber-500 border-amber-500/30">
              Backend Offline
            </Badge>
          )}
        </div>
        
        {!backendAvailable ? (
          <Card className="glass border-border/50 p-8 text-center">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-amber-500/10 flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            </div>
            <p className="font-medium text-muted-foreground">Backend Not Running</p>
            <p className="text-sm text-muted-foreground mt-2">
              The backend bridge on port 8934 is not available.
            </p>
            <p className="text-xs font-mono bg-muted/30 rounded px-2 py-1 mt-3 inline-block">
              cd web-ui && ./start-ui.sh
            </p>
          </Card>
        ) : agents.length === 0 ? (
          <Card className="glass border-border/50 p-8 text-center">
            <Bot className="w-12 h-12 mx-auto mb-3 text-muted-foreground" />
            <p className="text-muted-foreground">No agents created yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Create your first agent to get started
            </p>
          </Card>
        ) : (
          <div className="space-y-3">
            {agents.map((agent) => (
              <Card key={agent.id} className="glass-hover border-border/50 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
                      <Bot className="w-4 h-4 text-primary" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{agent.name}</span>
                        <Badge className={getStatusColor(agent.status)} variant="outline">
                          {agent.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                        <span>{agent.model}</span>
                        <span>•</span>
                        <span>{new Date(agent.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="glass-hover"
                    >
                      <MessageSquare className="w-4 h-4" />
                    </Button>
                    
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="sm" className="glass-hover">
                          Actions
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent className="glass border-border/50">
                        <DropdownMenuItem>
                          <Play className="w-4 h-4 mr-2" />
                          Start
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Pause className="w-4 h-4 mr-2" />
                          Pause
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => deleteAgent(agent.id, agent.name)}
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


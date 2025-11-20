"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Users,
  Server,
  Plus,
  Minus,
  Activity,
  Clock,
  ArrowRight,
  Settings,
  TrendingUp,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useMCPStore } from "@/lib/mcp-store";
import type { AgentMCPServer } from "@/types/mcp";
import { toast } from "sonner";

export default function AgentMCPPanel() {
  const {
    servers,
    agentServers,
    getAgentServers,
    assignServerToAgent,
    unassignServerFromAgent,
    setSelectedAgent,
    selectedAgentId,
  } = useMCPStore();

  const [selectedServerId, setSelectedServerId] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Get unique agent IDs
  const agentIds = Array.from(new Set(agentServers.map((asg) => asg.agentId)));

  // Add mock agents if none exist
  const mockAgents = agentIds.length === 0 ? ["agent-1", "agent-2", "agent-3"] : agentIds;

  const filteredServers = Object.values(servers).filter((server) =>
    server.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAssign = () => {
    if (!selectedServerId || !selectedAgentId) {
      toast.error("Please select both a server and an agent");
      return;
    }

    // Check if already assigned
    const existing = agentServers.find(
      (asg) => asg.serverId === selectedServerId && asg.agentId === selectedAgentId
    );

    if (existing) {
      toast.error("Server is already assigned to this agent");
      return;
    }

    assignServerToAgent(selectedServerId, selectedAgentId);
    toast.success("Server assigned successfully");
    setSelectedServerId("");
  };

  const handleUnassign = (serverId: string, agentId: string) => {
    unassignServerFromAgent(serverId, agentId);
    toast.success("Server unassigned successfully");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Agent-MCP Integration</h2>
          <p className="text-muted-foreground">
            Manage MCP server assignments to agents
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          {agentServers.length} Active Assignments
        </Badge>
      </div>

      <Tabs defaultValue="assign" className="space-y-4">
        <TabsList>
          <TabsTrigger value="assign">Assign Servers</TabsTrigger>
          <TabsTrigger value="agents">Agent Overview</TabsTrigger>
          <TabsTrigger value="servers">Server Overview</TabsTrigger>
        </TabsList>

        <TabsContent value="assign" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Assign Server to Agent</CardTitle>
              <CardDescription>
                Select a server and agent to establish a connection
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Select Agent</label>
                  <Select value={selectedAgentId || ""} onValueChange={setSelectedAgent}>
                    <SelectTrigger>
                      <SelectValue placeholder="Choose an agent" />
                    </SelectTrigger>
                    <SelectContent>
                      {mockAgents.map((agentId) => (
                        <SelectItem key={agentId} value={agentId}>
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4" />
                            {agentId}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Select Server</label>
                  <div className="relative">
                    <Input
                      placeholder="Search servers..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="mb-2"
                    />
                    <Select value={selectedServerId} onValueChange={setSelectedServerId}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a server" />
                      </SelectTrigger>
                      <SelectContent>
                        {filteredServers.map((server) => (
                          <SelectItem key={server.id} value={server.id}>
                            <div className="flex items-center gap-2">
                              <Server className="w-4 h-4" />
                              <span>{server.name}</span>
                              <Badge variant="outline" className="text-xs">
                                {server.category}
                              </Badge>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {selectedAgentId && selectedServerId && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center justify-center p-4 bg-primary/10 rounded-lg"
                >
                  <ArrowRight className="w-6 h-6 text-primary" />
                </motion.div>
              )}

              <Button
                onClick={handleAssign}
                disabled={!selectedAgentId || !selectedServerId}
                className="w-full"
              >
                <Plus className="w-4 h-4 mr-2" />
                Assign Server to Agent
              </Button>
            </CardContent>
          </Card>

          {selectedAgentId && (
            <Card>
              <CardHeader>
                <CardTitle>Agent {selectedAgentId}</CardTitle>
                <CardDescription>Assigned servers and statistics</CardDescription>
              </CardHeader>
              <CardContent>
                <AgentServerList agentId={selectedAgentId} />
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {mockAgents.map((agentId) => (
              <AgentCard
                key={agentId}
                agentId={agentId}
                servers={getAgentServers(agentId)}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="servers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Server Assignment Matrix</CardTitle>
              <CardDescription>
                Overview of which agents have access to which servers
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.values(servers).map((server) => {
                  const assignedAgents = agentServers
                    .filter((asg) => asg.serverId === server.id)
                    .map((asg) => asg.agentId);

                  return (
                    <div key={server.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Server className="w-4 h-4" />
                          <span className="font-medium">{server.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {server.category}
                          </Badge>
                        </div>
                        <Badge variant="secondary">
                          {assignedAgents.length} agent{assignedAgents.length !== 1 ? "s" : ""}
                        </Badge>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {assignedAgents.length > 0 ? (
                          assignedAgents.map((agentId) => (
                            <Badge key={agentId} variant="outline" className="text-xs">
                              <Users className="w-3 h-3 mr-1" />
                              {agentId}
                            </Badge>
                          ))
                        ) : (
                          <span className="text-sm text-muted-foreground">
                            Not assigned to any agents
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function AgentCard({ agentId, servers }: { agentId: string; servers: AgentMCPServer[] }) {
  const totalRequests = servers.reduce((sum, s) => sum + s.usageCount, 0);
  const lastUsed = servers
    .map((s) => s.lastUsed)
    .filter(Boolean)
    .sort((a, b) => (b?.getTime() || 0) - (a?.getTime() || 0))[0];

  return (
    <motion.div whileHover={{ y: -2 }}>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="w-4 h-4" />
            {agentId}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Servers</span>
              <span className="font-medium">{servers.length}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Total Requests</span>
              <span className="font-medium">{totalRequests}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Last Activity</span>
              <span className="font-medium">
                {lastUsed ? lastUsed.toLocaleString() : "Never"}
              </span>
            </div>
            <div className="pt-2 border-t">
              <div className="space-y-2">
                {servers.slice(0, 3).map((server) => (
                  <div key={server.serverId} className="flex items-center justify-between text-xs">
                    <span className="truncate">{server.serverName}</span>
                    <Badge variant="outline" className="text-xs">
                      {server.usageCount}
                    </Badge>
                  </div>
                ))}
                {servers.length > 3 && (
                  <p className="text-xs text-muted-foreground text-center">
                    +{servers.length - 3} more
                  </p>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function AgentServerList({ agentId }: { agentId: string }) {
  const { agentServers, servers, unassignServerFromAgent } = useMCPStore();
  const assignedServers = agentServers.filter((asg) => asg.agentId === agentId);

  if (assignedServers.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Server className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No servers assigned to this agent</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {assignedServers.map((assignment) => {
        const server = servers[assignment.serverId];
        if (!server) return null;

        return (
          <motion.div
            key={assignment.serverId}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center justify-between p-3 border rounded-lg"
          >
            <div className="flex items-center gap-3">
              <Server className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="font-medium text-sm">{server.name}</p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline" className="text-xs">
                    {server.category}
                  </Badge>
                  <span>•</span>
                  <span>{assignment.usageCount} requests</span>
                  {assignment.lastUsed && (
                    <>
                      <span>•</span>
                      <span>Last used: {assignment.lastUsed.toLocaleString()}</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => unassignServerFromAgent(assignment.serverId, agentId)}
            >
              <Minus className="w-4 h-4" />
            </Button>
          </motion.div>
        );
      })}
    </div>
  );
}

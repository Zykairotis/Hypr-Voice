"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Badge } from "components/ui/badge";
import { ScrollArea } from "components/ui/scroll-area";
import {
  Bot,
  Activity,
  PlayCircle,
  Square,
  AlertCircle,
  CheckCircle2,
  Clock,
  Zap,
  GitBranch,
  MessageSquare
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useWebSocket, EventType } from "lib/websocket";

interface Agent {
  id: string;
  name: string;
  type: string;
  status: "idle" | "running" | "completed" | "error";
  startTime: number;
  endTime?: number;
  tasksCompleted: number;
  currentTask?: string;
  outputCount: number;
  errorCount: 0;
}

export default function AgentActivity() {
  const { events } = useWebSocket();
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const agents = useMemo(() => {
    const agentMap = new Map<string, Agent>();

    events.forEach(event => {
      if (event.agentId) {
        const existing = agentMap.get(event.agentId);

        if (event.type === "agent_created" && !existing) {
          agentMap.set(event.agentId, {
            id: event.agentId,
            name: event.data.name || event.agentId,
            type: event.data.type || "unknown",
            status: "idle",
            startTime: event.timestamp,
            tasksCompleted: 0,
            outputCount: 0,
            errorCount: 0,
          });
        } else if (existing) {
          switch (event.type) {
            case "agent_started":
              existing.status = "running";
              existing.currentTask = event.data.task;
              break;
            case "agent_output":
              existing.outputCount++;
              if (event.data.taskCompleted) {
                existing.tasksCompleted++;
              }
              break;
            case "agent_completed":
              existing.status = "completed";
              existing.endTime = event.timestamp;
              break;
            case "agent_error":
              existing.status = "error";
              existing.errorCount++;
              break;
          }
        }
      }
    });

    return Array.from(agentMap.values()).sort((a, b) => b.startTime - a.startTime);
  }, [events]);

  const agentStats = useMemo(() => {
    return {
      total: agents.length,
      running: agents.filter(a => a.status === "running").length,
      idle: agents.filter(a => a.status === "idle").length,
      completed: agents.filter(a => a.status === "completed").length,
      error: agents.filter(a => a.status === "error").length,
    };
  }, [agents]);

  return (
    <div className="space-y-6">
      {/* Agent Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard
          title="Total Agents"
          value={agentStats.total}
          icon={Bot}
          color="from-blue-500/20 to-blue-600/20 border-blue-500/30"
        />
        <StatCard
          title="Running"
          value={agentStats.running}
          icon={PlayCircle}
          color="from-green-500/20 to-green-600/20 border-green-500/30"
        />
        <StatCard
          title="Idle"
          value={agentStats.idle}
          icon={Square}
          color="from-gray-500/20 to-gray-600/20 border-gray-500/30"
        />
        <StatCard
          title="Completed"
          value={agentStats.completed}
          icon={CheckCircle2}
          color="from-emerald-500/20 to-emerald-600/20 border-emerald-500/30"
        />
        <StatCard
          title="Errors"
          value={agentStats.error}
          icon={AlertCircle}
          color="from-red-500/20 to-red-600/20 border-red-500/30"
        />
      </div>

      {/* Agent List */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardHeader>
          <CardTitle>Active Agents</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <div className="space-y-3">
              <AnimatePresence>
                {agents.map((agent) => (
                  <motion.div
                    key={agent.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    layout
                  >
                    <AgentCard
                      agent={agent}
                      isSelected={selectedAgent === agent.id}
                      onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Agent Detail */}
      <AnimatePresence>
        {selectedAgent && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <AgentDetail agentId={selectedAgent} events={events} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  color
}: {
  title: string;
  value: number;
  icon: any;
  color: string;
}) {
  return (
    <motion.div whileHover={{ scale: 1.02 }}>
      <Card className={`bg-gradient-to-br ${color} border backdrop-blur-xl`}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white/60">{title}</p>
              <p className="text-2xl font-bold text-white mt-1">{value}</p>
            </div>
            <Icon className="w-8 h-8 text-white/70" />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function AgentCard({
  agent,
  isSelected,
  onClick
}: {
  agent: Agent;
  isSelected: boolean;
  onClick: () => void;
}) {
  const statusConfig = {
    idle: { color: "text-gray-400", bg: "bg-gray-500/20 border-gray-500/30", icon: Square },
    running: { color: "text-green-400", bg: "bg-green-500/20 border-green-500/30", icon: PlayCircle },
    completed: { color: "text-emerald-400", bg: "bg-emerald-500/20 border-emerald-500/30", icon: CheckCircle2 },
    error: { color: "text-red-400", bg: "bg-red-500/20 border-red-500/30", icon: AlertCircle },
  };

  const config = statusConfig[agent.status];
  const StatusIcon = config.icon;

  return (
    <motion.div
      onClick={onClick}
      whileHover={{ scale: 1.01 }}
      className={`p-4 rounded-lg cursor-pointer transition-all ${isSelected ? 'bg-white/10' : 'bg-white/5 hover:bg-white/10'} border border-white/10`}
    >
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-lg ${config.bg}`}>
          <Bot className={`w-6 h-6 ${config.color}`} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-semibold text-white">{agent.name}</h3>
            <Badge variant="outline" className="text-xs">
              {agent.type}
            </Badge>
            <Badge className={`${config.bg} ${config.color} border-0`}>
              <StatusIcon className="w-3 h-3 mr-1" />
              {agent.status}
            </Badge>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="text-white/60">
              <div className="flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                Tasks
              </div>
              <div className="font-medium text-white">{agent.tasksCompleted}</div>
            </div>

            <div className="text-white/60">
              <div className="flex items-center gap-1">
                <MessageSquare className="w-3 h-3" />
                Outputs
              </div>
              <div className="font-medium text-white">{agent.outputCount}</div>
            </div>

            <div className="text-white/60">
              <div className="flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                Errors
              </div>
              <div className="font-medium text-white">{agent.errorCount}</div>
            </div>

            <div className="text-white/60">
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Duration
              </div>
              <div className="font-medium text-white">
                {agent.endTime
                  ? `${Math.floor((agent.endTime - agent.startTime) / 1000)}s`
                  : `${Math.floor((Date.now() - agent.startTime) / 1000)}s`
                }
              </div>
            </div>
          </div>

          {agent.currentTask && (
            <div className="mt-2 text-sm text-white/60">
              <span className="text-white/40">Current: </span>
              {agent.currentTask}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function AgentDetail({ agentId, events }: { agentId: string; events: any[] }) {
  const agentEvents = events.filter(e => e.agentId === agentId);

  return (
    <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="w-5 h-5" />
          Agent Timeline - {agentId}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px]">
          <div className="space-y-2">
            {agentEvents.map((event) => (
              <div
                key={event.id}
                className="p-3 rounded-lg bg-white/5 border border-white/10 flex items-start gap-3"
              >
                <div className="p-2 rounded-lg bg-black/30">
                  {event.type === "agent_started" && <PlayCircle className="w-4 h-4 text-green-400" />}
                  {event.type === "agent_output" && <MessageSquare className="w-4 h-4 text-blue-400" />}
                  {event.type === "agent_completed" && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  {event.type === "agent_error" && <AlertCircle className="w-4 h-4 text-red-400" />}
                  {event.type === "tool_execution" && <Zap className="w-4 h-4 text-purple-400" />}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-white">{event.type}</span>
                    <Badge variant="outline" className="text-xs">
                      {event.severity || "info"}
                    </Badge>
                  </div>
                  <p className="text-sm text-white/60 mb-1">
                    {JSON.stringify(event.data)}
                  </p>
                  <span className="text-xs text-white/40">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

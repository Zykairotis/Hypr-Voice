"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Input } from "components/ui/input";
import { Button } from "components/ui/button";
import { Badge } from "components/ui/badge";
import { ScrollArea } from "components/ui/scroll-area";
import {
  Search,
  Filter,
  Play,
  Pause,
  RotateCcw,
  Download,
  Eye,
  Bot,
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Activity
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useWebSocket, EventType } from "lib/websocket";

const EVENT_ICONS: Record<EventType, any> = {
  agent_created: Bot,
  agent_started: Activity,
  agent_output: CheckCircle,
  agent_error: XCircle,
  agent_completed: CheckCircle,
  tool_execution: Zap,
  mcp_event: Zap,
  skill_executed: Bot,
  voice_synthesis: Activity,
  system_metrics: Activity,
  alert_triggered: AlertTriangle,
  connection_status: Activity,
};

const EVENT_COLORS: Record<EventType, string> = {
  agent_created: "from-blue-500/20 to-blue-600/20 border-blue-500/30",
  agent_started: "from-green-500/20 to-green-600/20 border-green-500/30",
  agent_output: "from-cyan-500/20 to-cyan-600/20 border-cyan-500/30",
  agent_error: "from-red-500/20 to-red-600/20 border-red-500/30",
  agent_completed: "from-emerald-500/20 to-emerald-600/20 border-emerald-500/30",
  tool_execution: "from-purple-500/20 to-purple-600/20 border-purple-500/30",
  mcp_event: "from-indigo-500/20 to-indigo-600/20 border-indigo-500/30",
  skill_executed: "from-pink-500/20 to-pink-600/20 border-pink-500/30",
  voice_synthesis: "from-orange-500/20 to-orange-600/20 border-orange-500/30",
  system_metrics: "from-slate-500/20 to-slate-600/20 border-slate-500/30",
  alert_triggered: "from-yellow-500/20 to-yellow-600/20 border-yellow-500/30",
  connection_status: "from-gray-500/20 to-gray-600/20 border-gray-500/30",
};

export default function EventStream() {
  const { events, clearEvents } = useWebSocket();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTypes, setSelectedTypes] = useState<Set<EventType>>(new Set());
  const [isPaused, setIsPaused] = useState(false);
  const [severityFilter, setSeverityFilter] = useState<"all" | "info" | "warning" | "error" | "critical">("all");

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      const matchesSearch = !searchTerm ||
        event.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
        JSON.stringify(event.data).toLowerCase().includes(searchTerm.toLowerCase()) ||
        (event.agentId && event.agentId.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesType = selectedTypes.size === 0 || selectedTypes.has(event.type);

      const matchesSeverity = severityFilter === "all" || event.severity === severityFilter;

      return matchesSearch && matchesType && matchesSeverity;
    });
  }, [events, searchTerm, selectedTypes, severityFilter]);

  const eventTypes = useMemo(() => {
    const types = new Set<EventType>();
    events.forEach(event => types.add(event.type));
    return Array.from(types);
  }, [events]);

  const toggleEventType = (type: EventType) => {
    const newSelected = new Set(selectedTypes);
    if (newSelected.has(type)) {
      newSelected.delete(type);
    } else {
      newSelected.add(type);
    }
    setSelectedTypes(newSelected);
  };

  const exportEvents = () => {
    const dataStr = JSON.stringify(filteredEvents, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

    const exportFileDefaultName = `events-${new Date().toISOString()}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[300px]">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/40" />
              <Input
                placeholder="Search events, agents, or data..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-black/30 border-white/10"
              />
            </div>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value as any)}
              className="px-3 py-2 rounded-md bg-black/30 border border-white/10 text-white"
            >
              <option value="all">All Severities</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="critical">Critical</option>
            </select>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPaused(!isPaused)}
            >
              {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
              {isPaused ? "Resume" : "Pause"}
            </Button>

            <Button variant="outline" size="sm" onClick={clearEvents}>
              <RotateCcw className="w-4 h-4 mr-2" />
              Clear
            </Button>

            <Button variant="outline" size="sm" onClick={exportEvents}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Event Type Filters */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardContent className="p-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Filter className="w-4 h-4 text-white/60" />
            <span className="text-sm text-white/60">Event Types:</span>
            {eventTypes.map((type) => {
              const Icon = EVENT_ICONS[type];
              const isSelected = selectedTypes.has(type);

              return (
                <motion.button
                  key={type}
                  onClick={() => toggleEventType(type)}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Badge
                    variant={isSelected ? "default" : "outline"}
                    className={`cursor-pointer ${
                      isSelected
                        ? "bg-blue-500/50 border-blue-500"
                        : "hover:bg-white/10"
                    }`}
                  >
                    <Icon className="w-3 h-3 mr-1" />
                    {type}
                  </Badge>
                </motion.button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Events List */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Live Event Stream</span>
            <Badge variant="outline">{filteredEvents.length} events</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-2">
              <AnimatePresence>
                {filteredEvents.slice().reverse().map((event, index) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.2, delay: index * 0.01 }}
                  >
                    <EventCard event={event} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

function EventCard({ event }: { event: any }) {
  const Icon = EVENT_ICONS[event.type as EventType] || Activity;
  const colorClass = EVENT_COLORS[event.type as EventType] || "from-gray-500/20 to-gray-600/20 border-gray-500/30";

  return (
    <motion.div
      className={`p-4 rounded-lg bg-gradient-to-r ${colorClass} border backdrop-blur-xl cursor-pointer hover:scale-[1.01] transition-transform`}
      whileHover={{ x: 4 }}
    >
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-black/30">
          <Icon className="w-5 h-5 text-white" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-white">{event.type}</span>
            <Badge variant="outline" className="text-xs">
              {event.source}
            </Badge>
            {event.severity && (
              <Badge
                variant="outline"
                className={`text-xs ${
                  event.severity === 'critical' ? 'border-red-500 text-red-400' :
                  event.severity === 'error' ? 'border-orange-500 text-orange-400' :
                  event.severity === 'warning' ? 'border-yellow-500 text-yellow-400' :
                  'border-blue-500 text-blue-400'
                }`}
              >
                {event.severity}
              </Badge>
            )}
            {event.agentId && (
              <Badge variant="outline" className="text-xs">
                <Bot className="w-3 h-3 mr-1" />
                {event.agentId}
              </Badge>
            )}
          </div>

          <p className="text-sm text-white/70 mb-2">
            {JSON.stringify(event.data, null, 2)}
          </p>

          <div className="flex items-center gap-2 text-xs text-white/50">
            <Eye className="w-3 h-3" />
            {new Date(event.timestamp).toLocaleTimeString()}
            {event.correlationId && (
              <span>• Correlation: {event.correlationId}</span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Button } from "components/ui/button";
import { Badge } from "components/ui/badge";
import { ScrollArea } from "components/ui/scroll-area";
import {
  Play,
  Pause,
  SkipBack,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Calendar,
  Filter
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useWebSocket, EventType } from "lib/websocket";

const EVENT_ICONS: Record<EventType, any> = {
  agent_created: "🤖",
  agent_started: "▶️",
  agent_output: "💬",
  agent_error: "❌",
  agent_completed: "✅",
  tool_execution: "⚡",
  mcp_event: "🔌",
  skill_executed: "🎯",
  voice_synthesis: "🎵",
  system_metrics: "📊",
  alert_triggered: "⚠️",
  connection_status: "🔌",
};

export default function ActivityTimeline() {
  const { events } = useWebSocket();
  const [isPlaying, setIsPlaying] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [timeRange, setTimeRange] = useState<"1h" | "6h" | "24h" | "all">("all");

  const filteredEvents = useMemo(() => {
    let filtered = [...events].sort((a, b) => a.timestamp - b.timestamp);

    if (timeRange !== "all") {
      const now = Date.now();
      const ranges = {
        "1h": 3600000,
        "6h": 21600000,
        "24h": 86400000,
      };
      const cutoff = now - ranges[timeRange];
      filtered = filtered.filter(event => event.timestamp >= cutoff);
    }

    return filtered;
  }, [events, timeRange]);

  const timelineEvents = useMemo(() => {
    return filteredEvents.map(event => ({
      ...event,
      icon: EVENT_ICONS[event.type] || "📝",
    }));
  }, [filteredEvents]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setCurrentIndex(0);
  };

  const exportTimeline = () => {
    const dataStr = JSON.stringify(filteredEvents, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

    const exportFileDefaultName = `timeline-${new Date().toISOString()}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const groupedEvents = useMemo(() => {
    const groups: { [key: string]: any[] } = {};
    let currentGroup: any[] = [];
    let lastTimestamp = 0;
    const GAP_THRESHOLD = 30000;

    timelineEvents.forEach(event => {
      if (currentGroup.length > 0 && (event.timestamp - lastTimestamp) > GAP_THRESHOLD) {
        groups[`group_${Object.keys(groups).length}`] = currentGroup;
        currentGroup = [event];
      } else {
        currentGroup.push(event);
      }
      lastTimestamp = event.timestamp;
    });

    if (currentGroup.length > 0) {
      groups[`group_${Object.keys(groups).length}`] = currentGroup;
    }

    return groups;
  }, [timelineEvents]);

  return (
    <div className="space-y-6">
      {/* Controls */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardContent className="p-4">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handlePlayPause}>
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                {isPlaying ? "Pause" : "Play"}
              </Button>
              <Button variant="outline" size="sm" onClick={handleReset}>
                <SkipBack className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex items-center gap-2 border-l border-white/10 pl-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setZoomLevel(Math.max(0.5, zoomLevel - 0.25))}
              >
                <ZoomOut className="w-4 h-4" />
              </Button>
              <span className="text-sm text-white/60 px-2">
                Zoom: {(zoomLevel * 100).toFixed(0)}%
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setZoomLevel(Math.min(3, zoomLevel + 0.25))}
              >
                <ZoomIn className="w-4 h-4" />
              </Button>
            </div>

            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="px-3 py-2 rounded-md bg-black/30 border border-white/10 text-white"
            >
              <option value="1h">Last Hour</option>
              <option value="6h">Last 6 Hours</option>
              <option value="24h">Last 24 Hours</option>
              <option value="all">All Time</option>
            </select>

            <Button variant="outline" size="sm" onClick={exportTimeline}>
              <Calendar className="w-4 h-4 mr-2" />
              Export
            </Button>

            <div className="flex-1" />

            <div className="text-sm text-white/60">
              {filteredEvents.length} events
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Timeline */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardHeader>
          <CardTitle>Activity Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-6">
              {Object.entries(groupedEvents).map(([groupId, groupEvents], groupIndex) => (
                <TimelineGroup
                  key={groupId}
                  events={groupEvents}
                  groupIndex={groupIndex}
                  zoomLevel={zoomLevel}
                />
              ))}

              {Object.keys(groupedEvents).length === 0 && (
                <div className="text-center py-12 text-white/50">
                  <Calendar className="w-12 h-12 mx-auto mb-3 text-white/30" />
                  <p>No events in selected time range</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

function TimelineGroup({
  events,
  groupIndex,
  zoomLevel
}: {
  events: any[];
  groupIndex: number;
  zoomLevel: number;
}) {
  const startTime = events[0]?.timestamp;
  const endTime = events[events.length - 1]?.timestamp;
  const duration = endTime - startTime;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: groupIndex * 0.1 }}
      className="relative"
    >
      <div className="flex items-center gap-2 mb-3">
        <div className="h-px flex-1 bg-gradient-to-r from-white/20 to-transparent" />
        <Badge variant="outline" className="whitespace-nowrap">
          {new Date(startTime).toLocaleString()}
        </Badge>
        <div className="h-px flex-1 bg-gradient-to-l from-white/20 to-transparent" />
      </div>

      <div
        className="space-y-3 ml-4"
        style={{
          transform: `scale(${zoomLevel})`,
          transformOrigin: 'left top',
        }}
      >
        <AnimatePresence>
          {events.map((event, index) => (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: index * 0.05 }}
              className="relative pl-8"
            >
              <TimelineEvent event={event} index={index} duration={duration} startTime={startTime} />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

function TimelineEvent({
  event,
  index,
  duration,
  startTime
}: {
  event: any;
  index: number;
  duration: number;
  startTime: number;
}) {
  const timeOffset = event.timestamp - startTime;
  const position = duration > 0 ? (timeOffset / duration) * 100 : 0;

  const severityColors = {
    critical: "border-red-500 bg-red-500/20",
    error: "border-orange-500 bg-orange-500/20",
    warning: "border-yellow-500 bg-yellow-500/20",
    info: "border-blue-500 bg-blue-500/20",
  };

  return (
    <div className="relative">
      <div
        className={`absolute left-0 top-0 bottom-0 w-0.5 ${
          event.severity && severityColors[event.severity as keyof typeof severityColors]
            ? severityColors[event.severity as keyof typeof severityColors].split(' ')[0]
            : 'bg-white/20'
        }`}
        style={{ left: '-4px' }}
      />

      <div className="relative">
        <div
          className={`absolute -left-6 top-2 w-4 h-4 rounded-full border-2 ${
            event.severity && severityColors[event.severity as keyof typeof severityColors]
              ? severityColors[event.severity as keyof typeof severityColors]
              : 'border-blue-500 bg-blue-500/20'
          }`}
          style={{ zIndex: 1 }}
        >
          <div className="absolute inset-0 flex items-center justify-center text-xs">
            {event.icon}
          </div>
        </div>

        <motion.div
          className="p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
          whileHover={{ scale: 1.02 }}
        >
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <Badge variant="outline" className="text-xs">
              {event.type}
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
                🤖 {event.agentId}
              </Badge>
            )}
            <span className="text-xs text-white/40 ml-auto">
              {new Date(event.timestamp).toLocaleTimeString()}
            </span>
          </div>

          <p className="text-sm text-white/70 mb-1">
            {JSON.stringify(event.data)}
          </p>

          <div className="flex items-center gap-2 text-xs text-white/50">
            <span>{event.source}</span>
            <span>•</span>
            <span>{timeOffset}ms into session</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

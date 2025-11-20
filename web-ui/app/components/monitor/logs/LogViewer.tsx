"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "components/ui/card";
import { Input } from "components/ui/input";
import { Button } from "components/ui/button";
import { Badge } from "components/ui/badge";
import { ScrollArea } from "components/ui/scroll-area";
import {
  Search,
  Download,
  Filter,
  Trash2,
  AlertTriangle,
  Info,
  AlertCircle,
  XCircle,
  FileText
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useWebSocket } from "lib/websocket";

type LogLevel = "debug" | "info" | "warning" | "error" | "critical";

export default function LogViewer() {
  const { events } = useWebSocket();
  const [searchTerm, setSearchTerm] = useState("");
  const [levelFilter, setLevelFilter] = useState<LogLevel | "all">("all");
  const [sourceFilter, setSourceFilter] = useState<string>("all");

  const logs = useMemo(() => {
    return events
      .filter(event => event.type === "agent_error" || event.type === "tool_execution" || event.type === "mcp_event")
      .map(event => ({
        id: event.id,
        timestamp: event.timestamp,
        level: event.severity || "info",
        source: event.source,
        message: JSON.stringify(event.data),
        agentId: event.agentId,
        type: event.type
      }))
      .sort((a, b) => b.timestamp - a.timestamp);
  }, [events]);

  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      const matchesSearch = !searchTerm ||
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (log.agentId && log.agentId.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesLevel = levelFilter === "all" || log.level === levelFilter;

      const matchesSource = sourceFilter === "all" || log.source === sourceFilter;

      return matchesSearch && matchesLevel && matchesSource;
    });
  }, [logs, searchTerm, levelFilter, sourceFilter]);

  const uniqueSources = useMemo(() => {
    return Array.from(new Set(logs.map(log => log.source)));
  }, [logs]);

  const logStats = useMemo(() => {
    return {
      total: logs.length,
      debug: logs.filter(l => l.level === "info").length,
      info: logs.filter(l => l.level === "info").length,
      warning: logs.filter(l => l.level === "warning").length,
      error: logs.filter(l => l.level === "error").length,
      critical: logs.filter(l => l.level === "critical").length,
    };
  }, [logs]);

  const exportLogs = () => {
    const dataStr = JSON.stringify(filteredLogs, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

    const exportFileDefaultName = `logs-${new Date().toISOString()}.json`;

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
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-black/30 border-white/10"
              />
            </div>

            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value as any)}
              className="px-3 py-2 rounded-md bg-black/30 border border-white/10 text-white"
            >
              <option value="all">All Levels</option>
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="critical">Critical</option>
            </select>

            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="px-3 py-2 rounded-md bg-black/30 border border-white/10 text-white"
            >
              <option value="all">All Sources</option>
              {uniqueSources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>

            <Button variant="outline" size="sm" onClick={exportLogs}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Log Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <LogStatCard title="Total" value={logStats.total} icon={FileText} color="text-blue-400" />
        <LogStatCard title="Info" value={logStats.info} icon={Info} color="text-blue-400" />
        <LogStatCard title="Warning" value={logStats.warning} icon={AlertTriangle} color="text-yellow-400" />
        <LogStatCard title="Error" value={logStats.error} icon={AlertCircle} color="text-orange-400" />
        <LogStatCard title="Critical" value={logStats.critical} icon={XCircle} color="text-red-400" />
      </div>

      {/* Logs List */}
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Log Entries</span>
            <Badge variant="outline">{filteredLogs.length} logs</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px] pr-4">
            <div className="space-y-2">
              <AnimatePresence>
                {filteredLogs.slice().reverse().map((log, index) => (
                  <motion.div
                    key={log.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.2, delay: index * 0.005 }}
                  >
                    <LogEntry log={log} />
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

function LogStatCard({
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
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white/60">{title}</p>
              <p className="text-2xl font-bold text-white mt-1">{value}</p>
            </div>
            <Icon className={`w-6 h-6 ${color}`} />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function LogEntry({ log }: { log: any }) {
  const levelConfig = {
    debug: { color: "text-gray-400", bg: "bg-gray-500/20 border-gray-500/30", icon: FileText },
    info: { color: "text-blue-400", bg: "bg-blue-500/20 border-blue-500/30", icon: Info },
    warning: { color: "text-yellow-400", bg: "bg-yellow-500/20 border-yellow-500/30", icon: AlertTriangle },
    error: { color: "text-orange-400", bg: "bg-orange-500/20 border-orange-500/30", icon: AlertCircle },
    critical: { color: "text-red-400", bg: "bg-red-500/20 border-red-500/30", icon: XCircle },
  };

  const config = levelConfig[log.level as LogLevel] || levelConfig.info;
  const LevelIcon = config.icon;

  return (
    <motion.div
      className={`p-4 rounded-lg border backdrop-blur-xl cursor-pointer hover:scale-[1.01] transition-transform ${config.bg}`}
      whileHover={{ x: 4 }}
    >
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-black/30">
          <LevelIcon className={`w-5 h-5 ${config.color}`} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <Badge variant="outline" className="text-xs">
              {log.source}
            </Badge>
            <Badge className={`${config.bg} ${config.color} border-0 text-xs`}>
              {log.level.toUpperCase()}
            </Badge>
            {log.agentId && (
              <Badge variant="outline" className="text-xs">
                {log.agentId}
              </Badge>
            )}
            <span className="text-xs text-white/40 ml-auto">
              {new Date(log.timestamp).toLocaleString()}
            </span>
          </div>

          <p className="text-sm text-white/80 mb-1 font-mono">
            {log.message}
          </p>

          <div className="text-xs text-white/50">
            Type: {log.type}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

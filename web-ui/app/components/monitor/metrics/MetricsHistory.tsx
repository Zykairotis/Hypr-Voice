"use client";

import { useState } from "react";
import { Card, CardContent } from "components/ui/card";
import { Button } from "components/ui/button";
import { Badge } from "components/ui/badge";
import { LineChart, Line, ResponsiveContainer } from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import { useWebSocket } from "lib/websocket";
import { Activity, X } from "lucide-react";

export default function MetricsHistory() {
  const { metrics } = useWebSocket();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isMinimized, setIsMinimized] = useState(true);

  if (isMinimized) {
    return (
      <motion.button
        onClick={() => setIsMinimized(false)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="p-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 backdrop-blur-xl shadow-lg"
      >
        <Activity className="w-5 h-5 text-blue-400" />
      </motion.button>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: 20 }}
      className="w-80"
    >
      <Card className="border-white/10 bg-black/30 backdrop-blur-xl">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              <h3 className="font-semibold text-white">Live Metrics</h3>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="h-8 w-8 p-0"
              >
                {isExpanded ? "−" : "+"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMinimized(true)}
                className="h-8 w-8 p-0"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <AnimatePresence>
            {!isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="space-y-3"
              >
                <MetricRow label="CPU" value={`${metrics?.cpu?.toFixed(1) || 0}%`} />
                <MetricRow label="Memory" value={`${metrics?.memory?.toFixed(1) || 0}%`} />
                <MetricRow label="Agents" value={metrics?.activeAgents?.toString() || "0"} />
                <MetricRow label="RPS" value={metrics?.requestsPerSecond?.toFixed(1) || "0"} />
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-4"
              >
                <MiniChart label="Response Time" value={metrics?.averageResponseTime || 0} />
                <MiniChart label="Throughput" value={metrics?.requestsPerSecond || 0} />
                <MiniChart label="Error Rate" value={metrics?.errorRate || 0} />

                <div className="pt-2 border-t border-white/10">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="text-white/60">Connections</div>
                    <div className="text-white text-right">{metrics?.websocketConnections || 0}</div>
                    <div className="text-white/60">Uptime</div>
                    <div className="text-white text-right">
                      {Math.floor((Date.now() - (metrics?.timestamp || Date.now())) / 1000)}s
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-white/60">{label}</span>
      <Badge variant="outline" className="font-mono">
        {value}
      </Badge>
    </div>
  );
}

function MiniChart({ label, value }: { label: string; value: number }) {
  const data = Array.from({ length: 20 }, (_, i) => ({
    value: Math.random() * 100,
  }));

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-white/60">{label}</span>
        <span className="text-xs font-mono text-white">{value.toFixed(1)}</span>
      </div>
      <div className="h-8">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <Line
              type="monotone"
              dataKey="value"
              stroke="#3b82f6"
              strokeWidth={1.5}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

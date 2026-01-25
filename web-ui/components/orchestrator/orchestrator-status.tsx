"use client";

import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Server, Cpu, Clock, Zap } from "lucide-react";

interface OrchestratorStatusProps {
  status: "online" | "offline" | "error";
}

export default function OrchestratorStatus({ status }: OrchestratorStatusProps) {
  const [stats, setStats] = useState({
    activeAgents: 0,
    totalSessions: 0,
    uptime: "0s",
    version: "0.2.0",
  });

  useEffect(() => {
    if (status === "online") {
      fetchStats();
      const interval = setInterval(fetchStats, 10000);
      return () => clearInterval(interval);
    }
  }, [status]);

  const fetchStats = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/orchestrator/agents");
      if (response.ok) {
        const data = await response.json();
        setStats({
          activeAgents: data.agents?.length || 0,
          totalSessions: data.agents?.length || 0,
          uptime: "Running",
          version: "0.2.0",
        });
      }
    } catch {
      // Ignore errors
    }
  };

  if (status !== "online") {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <div className="w-16 h-16 rounded-full bg-gray-500/10 flex items-center justify-center mb-4">
          <Server className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-white/80 mb-2">Orchestrator Offline</h3>
        <p className="text-sm text-white/50 max-w-md">
          The agent orchestrator is not running. Start it with:
        </p>
        <code className="mt-3 px-4 py-2 rounded-lg bg-black/30 border border-white/10 text-sm font-mono text-violet-400">
          python -m hypr_voice.server
        </code>
        <p className="mt-4 text-xs text-white/40">
          Or use F10 keybinding for voice input (requires Whisper server)
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard
        icon={Cpu}
        label="Active Agents"
        value={stats.activeAgents.toString()}
        color="violet"
      />
      <StatCard
        icon={Server}
        label="Total Sessions"
        value={stats.totalSessions.toString()}
        color="blue"
      />
      <StatCard
        icon={Clock}
        label="Status"
        value={stats.uptime}
        color="green"
      />
      <StatCard
        icon={Zap}
        label="Version"
        value={stats.version}
        color="amber"
      />
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  color: "violet" | "blue" | "green" | "amber";
}) {
  const colorClasses = {
    violet: "from-violet-500/20 to-purple-500/20 border-violet-500/30 text-violet-400",
    blue: "from-blue-500/20 to-cyan-500/20 border-blue-500/30 text-blue-400",
    green: "from-green-500/20 to-emerald-500/20 border-green-500/30 text-green-400",
    amber: "from-amber-500/20 to-orange-500/20 border-amber-500/30 text-amber-400",
  };

  return (
    <div className={`p-4 rounded-xl bg-gradient-to-br ${colorClasses[color]} border backdrop-blur-sm`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4" />
        <span className="text-xs text-white/60">{label}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  );
}

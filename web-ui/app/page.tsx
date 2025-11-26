"use client";

import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Mic, Bot, Activity, Sparkles, Mic2, Server, Monitor, Network } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import WhisperPanel from "@/components/whisper/whisper-panel";
import AgentPanel from "@/components/agent/agent-panel";
import SkillsLibrary from "@/components/skills/SkillsLibrary";
import Dock from "@/components/layout/dock";
import VocabularyDashboard from "@/components/vocabulary/dashboard";
import TTSControlPanel from "@/components/tts/tts-control-panel";
import MCPDashboard from "@/components/mcp/dashboard/MCPDashboard";
import AnalyticsDashboard from "@/components/analytics/AnalyticsDashboard";
import OrchestratorPanel from "@/components/orchestrator/orchestrator-panel";
import { endpoints } from "@/lib/endpoints";

export default function Dashboard() {
  const [activeView, setActiveView] = useState<"whisper" | "agent" | "orchestrator" | "skills" | "vocabulary" | "tts" | "mcp" | "analytics">("whisper");
  const [whisperStatus, setWhisperStatus] = useState<"online" | "offline" | "error">("offline");
  const [agentStatus, setAgentStatus] = useState<"online" | "offline" | "error">("offline");
  const [orchestratorStatus, setOrchestratorStatus] = useState<"online" | "offline" | "error">("offline");
  const [isClient, setIsClient] = useState(false);
  const [isDarkReader, setIsDarkReader] = useState(false);

  // Independent status checks for header indicators
  useEffect(() => {
    const checkAllStatuses = async () => {
      // Check Whisper status
      try {
        const whisperRes = await fetch(endpoints.api.whisperStatus, {
          signal: AbortSignal.timeout(2000),
        });
        if (whisperRes.ok) {
          const data = await whisperRes.json();
          setWhisperStatus(data.status === "online" ? "online" : "offline");
        } else {
          setWhisperStatus("offline");
        }
      } catch {
        setWhisperStatus("offline");
      }

      // Check Orchestrator status
      try {
        const orchRes = await fetch(endpoints.api.orchestratorStatus, {
          signal: AbortSignal.timeout(2000),
        });
        if (orchRes.ok) {
          const data = await orchRes.json();
          setOrchestratorStatus((data.status === "online" || data.status === "healthy") ? "online" : "offline");
        } else {
          setOrchestratorStatus("offline");
        }
      } catch {
        setOrchestratorStatus("offline");
      }

      // Check Agent status (same as orchestrator now)
      try {
        const agentRes = await fetch(endpoints.api.orchestratorStatus, {
          signal: AbortSignal.timeout(2000),
        });
        if (agentRes.ok) {
          const data = await agentRes.json();
          setAgentStatus((data.status === "online" || data.status === "healthy") ? "online" : "offline");
        } else {
          setAgentStatus("offline");
        }
      } catch {
        setAgentStatus("offline");
      }
    };

    checkAllStatuses();
    const interval = setInterval(checkAllStatuses, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    setIsClient(true);

    // Check for DarkReader extension
    const checkDarkReader = () => {
      const isDarkReaderActive = document.documentElement.hasAttribute('data-darkreader-mode');
      setIsDarkReader(isDarkReaderActive);
    };

    checkDarkReader();

    // Hide DarkReader attributes that cause hydration issues
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName?.startsWith('data-darkreader')) {
          const el = mutation.target as Element;
          el.removeAttribute(mutation.attributeName!);
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-darkreader-mode', 'data-darkreader-scheme', 'data-darkreader-inline-bgcolor', 'data-darkreader-inline-bgimage', 'data-darkreader-inline-boxshadow', 'data-darkreader-inline-stroke']
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div className="min-h-screen w-full bg-background pb-32 overflow-hidden">
      {/* Ambient background effects */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
      </div>

      {/* Header with liquid glass */}
      <div className="sticky top-0 z-40 w-full border-b border-white/10 backdrop-blur-2xl bg-gradient-to-b from-black/70 to-black/50" suppressHydrationWarning>
        <div className="absolute inset-0 shadow-[0_0_0_1px_rgba(255,255,255,0.05)_inset]" />
        <div className="relative container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <motion.div
                  className="p-2.5 rounded-2xl overflow-hidden relative"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-500/30 to-pink-500/30 shadow-[0_0_20px_rgba(168,85,247,0.3)_inset]" />
                  <div className="absolute inset-0 bg-gradient-to-tr from-white/20 to-transparent" />
                  <Activity className="w-6 h-6 text-white relative z-10 drop-shadow-lg" />
                </motion.div>
                <div>
                  <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
                    Hypr-Voice
                  </h1>
                  <p className="text-sm text-white/50">Control Panel</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <StatusIndicator label="Whisper" status={whisperStatus} icon={Mic} />
              <StatusIndicator label="Agent" status={agentStatus} icon={Bot} />
              <StatusIndicator label="Orchestrator" status={orchestratorStatus} icon={Network} />
              <StatusIndicator label="Skills" status="online" icon={Sparkles} />
              <StatusIndicator label="Vocabulary" status="online" icon={Monitor} />
              <StatusIndicator label="TTS" status="online" icon={Mic2} />
              <StatusIndicator label="MCP" status="online" icon={Server} />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content with liquid page transitions */}
      <div className="relative container mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {activeView === "whisper" && (
            <motion.div
              key="whisper"
              initial={{ opacity: 0, x: -40, filter: "blur(10px)" }}
              animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, x: 40, filter: "blur(10px)" }}
              transition={{ 
                type: "spring",
                stiffness: 300,
                damping: 30,
                mass: 0.8
              }}
            >
              <WhisperPanel onStatusChange={setWhisperStatus} />
            </motion.div>
          )}

          {activeView === "agent" && (
            <motion.div
              key="agent"
              initial={{ opacity: 0, x: -40, filter: "blur(10px)" }}
              animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, x: 40, filter: "blur(10px)" }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
                mass: 0.8
              }}
            >
              <AgentPanel onStatusChange={setAgentStatus} />
            </motion.div>
          )}

          {activeView === "orchestrator" && (
            <motion.div
              key="orchestrator"
              initial={{ opacity: 0, x: -40, filter: "blur(10px)" }}
              animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, x: 40, filter: "blur(10px)" }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
                mass: 0.8
              }}
            >
              <OrchestratorPanel onStatusChange={setOrchestratorStatus} />
            </motion.div>
          )}

          {activeView === "skills" && (
            <motion.div
              key="skills"
              initial={{ opacity: 0, x: -40, filter: "blur(10px)" }}
              animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, x: 40, filter: "blur(10px)" }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
                mass: 0.8
              }}
            >
              <SkillsLibrary />
            </motion.div>
          )}

          {activeView === "vocabulary" && (
            <motion.div
              key="vocabulary"
              initial={{ opacity: 0, x: -40, filter: "blur(10px)" }}
              animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, x: 40, filter: "blur(10px)" }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
                mass: 0.8
              }}
            >
              <VocabularyDashboard />
            </motion.div>
          )}

          {activeView === "tts" && (
            <motion.div
              key="tts"
              initial={{ opacity: 0, x: -40, filter: "blur(10px)" }}
              animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, x: 40, filter: "blur(10px)" }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
                mass: 0.8
              }}
            >
              <TTSControlPanel />
            </motion.div>
          )}

          {activeView === "mcp" && (
            <motion.div
              key="mcp"
              initial={{ opacity: 0, x: -40, filter: "blur(10px)" }}
              animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, x: 40, filter: "blur(10px)" }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
                mass: 0.8
              }}
            >
              <MCPDashboard />
            </motion.div>
          )}

          {activeView === "analytics" && (
            <motion.div
              key="analytics"
              initial={{ opacity: 0, x: -40, filter: "blur(10px)" }}
              animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, x: 40, filter: "blur(10px)" }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
                mass: 0.8
              }}
            >
              <AnalyticsDashboard />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* macOS-style Liquid Dock */}
      <Dock activeView={activeView} onViewChange={setActiveView} />
    </div>
  );
}

function StatusIndicator({ 
  label, 
  status, 
  icon: Icon 
}: { 
  label: string; 
  status: "online" | "offline" | "error";
  icon: React.ComponentType<{ className?: string }>;
}) {
  const statusConfig = {
    online: { 
      bg: "from-green-500/20 to-emerald-500/20", 
      text: "text-green-400", 
      border: "border-green-500/30",
      glow: "shadow-green-500/20"
    },
    offline: { 
      bg: "from-gray-500/20 to-slate-500/20", 
      text: "text-gray-400", 
      border: "border-gray-500/30",
      glow: "shadow-gray-500/20"
    },
    error: { 
      bg: "from-red-500/20 to-rose-500/20", 
      text: "text-red-400", 
      border: "border-red-500/30",
      glow: "shadow-red-500/20"
    },
  };

  const config = statusConfig[status];

  return (
    <motion.div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-xl backdrop-blur-xl border ${config.border} ${config.glow} shadow-lg bg-gradient-to-br from-white/[0.05] to-white/[0.02] shadow-[0_0_0_1px_rgba(255,255,255,0.05)_inset]`}
      suppressHydrationWarning
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 17 }}
    >
      <Icon className={`w-4 h-4 ${config.text}`} />
      <span className="text-sm font-medium text-white/70">{label}</span>
      <Badge
        className={`bg-gradient-to-r ${config.bg} ${config.text} ${config.border} backdrop-blur-sm`}
        variant="outline"
      >
        {status}
      </Badge>
    </motion.div>
  );
}

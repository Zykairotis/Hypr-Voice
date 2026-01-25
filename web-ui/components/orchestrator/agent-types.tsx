"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Code, Search, Terminal, Mic2, Loader2 } from "lucide-react";

interface AgentType {
  name: string;
  description: string;
  tools: string[];
  model: string;
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  "code-worker": Code,
  "research-worker": Search,
  "shell-worker": Terminal,
  "voice-worker": Mic2,
};

const colorMap: Record<string, string> = {
  "code-worker": "from-blue-500/20 to-cyan-500/20 border-blue-500/30",
  "research-worker": "from-green-500/20 to-emerald-500/20 border-green-500/30",
  "shell-worker": "from-orange-500/20 to-amber-500/20 border-orange-500/30",
  "voice-worker": "from-purple-500/20 to-pink-500/20 border-purple-500/30",
};

export default function AgentTypes() {
  const [agentTypes, setAgentTypes] = useState<AgentType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgentTypes();
  }, []);

  const fetchAgentTypes = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/orchestrator/agent-types");
      if (response.ok) {
        const data = await response.json();
        setAgentTypes(data.types || []);
      }
    } catch {
      // Use default types
      setAgentTypes([
        {
          name: "code-worker",
          description: "Code analysis, generation, and refactoring tasks",
          tools: ["Read", "Write", "Edit", "Grep", "Glob"],
          model: "sonnet",
        },
        {
          name: "research-worker",
          description: "Research, information gathering, and documentation tasks",
          tools: ["Read", "Grep", "Glob"],
          model: "haiku",
        },
        {
          name: "shell-worker",
          description: "System operations and bash commands",
          tools: ["Bash", "Read", "Grep"],
          model: "sonnet",
        },
        {
          name: "voice-worker",
          description: "Text-to-speech and speech-to-text operations",
          tools: ["Read"],
          model: "haiku",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-violet-400" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {agentTypes.map((agent) => {
        const Icon = iconMap[agent.name] || Code;
        const colorClass = colorMap[agent.name] || "from-gray-500/20 to-slate-500/20 border-gray-500/30";

        return (
          <Card
            key={agent.name}
            className={`p-4 bg-gradient-to-br ${colorClass} border backdrop-blur-sm hover:scale-[1.02] transition-transform cursor-pointer`}
          >
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-white/10">
                <Icon className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-white truncate">{agent.name}</h3>
                  <Badge variant="outline" className="text-xs bg-black/20">
                    {agent.model}
                  </Badge>
                </div>
                <p className="text-sm text-white/60 mb-3 line-clamp-2">
                  {agent.description}
                </p>
                <div className="flex flex-wrap gap-1">
                  {agent.tools.map((tool) => (
                    <Badge
                      key={tool}
                      variant="secondary"
                      className="text-xs bg-white/10 text-white/80"
                    >
                      {tool}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}

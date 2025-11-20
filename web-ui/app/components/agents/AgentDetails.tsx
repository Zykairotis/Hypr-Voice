// AgentDetails component with tabbed interface for agent management

'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Monitor,
  GitBranch,
  Wrench,
  Server,
  Settings,
  FolderOpen,
  Code,
  Activity,
} from 'lucide-react';
import { Agent } from './types';
import { AgentControlPanel } from './AgentControlPanel';
import { SubagentManager } from './SubagentManager';
import { SkillsManagement } from './SkillsManagement';
import { MCPServersConfig } from './MCPServersConfig';
import { cn } from '@/app/lib/utils';

interface AgentDetailsProps {
  agent: Agent | null;
  onClose: () => void;
  className?: string;
}

type TabType = 'control' | 'subagents' | 'skills' | 'mcp' | 'settings';

const TABS = [
  { id: 'control' as TabType, label: 'Control Panel', icon: Monitor },
  { id: 'subagents' as TabType, label: 'Subagents', icon: GitBranch },
  { id: 'skills' as TabType, label: 'Skills', icon: Wrench },
  { id: 'mcp' as TabType, label: 'MCP Servers', icon: Server },
  { id: 'settings' as TabType, label: 'Settings', icon: Settings },
];

export function AgentDetails({ agent, onClose, className }: AgentDetailsProps) {
  const [activeTab, setActiveTab] = useState<TabType>('control');
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [selectedServers, setSelectedServers] = useState<string[]>([]);

  useEffect(() => {
    if (agent) {
      // Initialize with agent's current configuration
      setSelectedSkills([]);
      setSelectedServers([]);
    }
  }, [agent]);

  if (!agent) {
    return (
      <div className={cn("flex items-center justify-center h-full bg-slate-900/50", className)}>
        <div className="text-center">
          <Activity className="w-16 h-16 text-white/20 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white/60 mb-2">No Agent Selected</h3>
          <p className="text-sm text-white/40">Select an agent to view details</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={cn("flex flex-col h-full bg-slate-900/50 border-l border-white/10", className)}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex-1 min-w-0">
          <h2 className="text-xl font-bold text-white truncate">{agent.name}</h2>
          <div className="flex items-center gap-3 mt-1">
            <p className="text-xs text-white/50 font-mono">
              ID: {agent.agent_id.slice(0, 12)}...
            </p>
            <div className="flex items-center gap-1.5">
              <FolderOpen className="w-3.5 h-3.5 text-white/40" />
              <p className="text-xs text-white/50 truncate max-w-[200px]" title={agent.working_directory}>
                {agent.working_directory.split('/').pop()}
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-white/5 text-white/60 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-2 border-b border-white/10 bg-white/[0.02]">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <motion.button
              key={tab.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                isActive
                  ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                  : "text-white/60 hover:text-white hover:bg-white/5"
              )}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{tab.label}</span>
            </motion.button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {activeTab === 'control' && (
            <motion.div
              key="control"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full"
            >
              <AgentControlPanel agent={agent} />
            </motion.div>
          )}

          {activeTab === 'subagents' && (
            <motion.div
              key="subagents"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full"
            >
              <SubagentManager agent={agent} />
            </motion.div>
          )}

          {activeTab === 'skills' && (
            <motion.div
              key="skills"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full"
            >
              <SkillsManagement
                agent={agent}
                selectedSkills={selectedSkills}
                onSkillsChange={setSelectedSkills}
              />
            </motion.div>
          )}

          {activeTab === 'mcp' && (
            <motion.div
              key="mcp"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full"
            >
              <MCPServersConfig
                agent={agent}
                selectedServers={selectedServers}
                onServersChange={setSelectedServers}
              />
            </motion.div>
          )}

          {activeTab === 'settings' && (
            <motion.div
              key="settings"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full p-6 overflow-y-auto"
            >
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wider mb-4">
                    Agent Configuration
                  </h3>

                  <div className="space-y-4">
                    <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                      <label className="block text-sm font-medium text-white/70 mb-2">
                        Agent Name
                      </label>
                      <p className="text-white">{agent.name}</p>
                    </div>

                    <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                      <label className="block text-sm font-medium text-white/70 mb-2">
                        Agent ID
                      </label>
                      <p className="text-white/60 font-mono text-sm">{agent.agent_id}</p>
                    </div>

                    <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                      <label className="block text-sm font-medium text-white/70 mb-2">
                        Working Directory
                      </label>
                      <p className="text-white/80 font-mono text-sm">{agent.working_directory}</p>
                    </div>

                    <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                      <label className="block text-sm font-medium text-white/70 mb-2">
                        Status
                      </label>
                      <span className={cn(
                        "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium",
                        agent.status === 'running'
                          ? "bg-emerald-500/20 text-emerald-400"
                          : agent.status === 'error'
                          ? "bg-red-500/20 text-red-400"
                          : "bg-white/10 text-white/70"
                      )}>
                        {agent.status}
                      </span>
                    </div>

                    <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                      <label className="block text-sm font-medium text-white/70 mb-2">
                        Parent Agent
                      </label>
                      <p className="text-white/80">
                        {agent.parent_id ? (
                          <span className="font-mono text-sm">{agent.parent_id.slice(0, 12)}...</span>
                        ) : (
                          <span className="text-white/50">None (root agent)</span>
                        )}
                      </p>
                    </div>

                    <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                      <label className="block text-sm font-medium text-white/70 mb-2">
                        Subagents Count
                      </label>
                      <p className="text-white">{agent.subagents.length}</p>
                    </div>

                    {agent.conversation_length !== undefined && (
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                        <label className="block text-sm font-medium text-white/70 mb-2">
                          Conversation Length
                        </label>
                        <p className="text-white">{agent.conversation_length} messages</p>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wider mb-4">
                    Agent Capabilities
                  </h3>

                  <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="flex items-center gap-2 text-sm text-white/70">
                          <input type="checkbox" checked readOnly className="rounded" />
                          Claude SDK Integration
                        </label>
                      </div>
                      <div>
                        <label className="flex items-center gap-2 text-sm text-white/70">
                          <input type="checkbox" checked readOnly className="rounded" />
                          WebSocket Monitoring
                        </label>
                      </div>
                      <div>
                        <label className="flex items-center gap-2 text-sm text-white/70">
                          <input type="checkbox" readOnly className="rounded" />
                          Voice Synthesis
                        </label>
                      </div>
                      <div>
                        <label className="flex items-center gap-2 text-sm text-white/70">
                          <input type="checkbox" checked readOnly className="rounded" />
                          Hyprland Monitoring
                        </label>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wider mb-4">
                    Actions
                  </h3>

                  <div className="grid grid-cols-2 gap-3">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 font-medium border border-blue-500/30 transition-colors"
                    >
                      <Code className="w-4 h-4" />
                      View Logs
                    </motion.button>

                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 font-medium border border-emerald-500/30 transition-colors"
                    >
                      <Activity className="w-4 h-4" />
                      Performance
                    </motion.button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

// AgentsDashboard main page component

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  Zap,
  Users,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { Agent, AgentStatus, AgentEvent, EventType } from './types';
import { AgentsAPI } from './api';
import { useAgentWebSocket } from './useWebSocket';
import { AgentList } from './AgentList';
import { AgentDetails } from './AgentDetails';
import { CreateAgentModal } from './CreateAgentModal';
import { cn } from '@/app/lib/utils';

export function AgentsDashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    running: 0,
    error: 0,
    completed: 0,
  });

  const { isConnected, connectionStatus } = useAgentWebSocket({
    onEvent: (event: AgentEvent) => {
      handleAgentEvent(event);
    },
  });

  const loadAgents = useCallback(async () => {
    try {
      setLoading(true);
      const { agents } = await AgentsAPI.listAgents();
      setAgents(agents);
      setError(null);

      // Update stats
      const newStats = {
        total: agents.length,
        running: agents.filter(a => a.status === AgentStatus.RUNNING).length,
        error: agents.filter(a => a.status === AgentStatus.ERROR).length,
        completed: agents.filter(a => a.status === AgentStatus.COMPLETED).length,
      };
      setStats(newStats);
    } catch (err: any) {
      setError(err.message || 'Failed to load agents');
      console.error('Failed to load agents:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAgents();

    // Refresh agents every 5 seconds
    const interval = setInterval(loadAgents, 5000);
    return () => clearInterval(interval);
  }, [loadAgents]);

  const handleAgentEvent = (event: AgentEvent) => {
    // Handle real-time updates
    switch (event.event_type) {
      case EventType.AGENT_CREATED:
        // Reload agents when a new one is created
        loadAgents();
        break;

      case EventType.AGENT_ERROR:
        // Show error notification
        console.error('Agent error:', event.data);
        // Optionally reload agents
        loadAgents();
        break;

      case EventType.AGENT_COMPLETED:
        // Agent finished execution
        loadAgents();
        break;
    }
  };

  const handleCreateSuccess = (agentId: string) => {
    setShowCreateModal(false);
    loadAgents();
  };

  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;

    try {
      await AgentsAPI.deleteAgent(agentId);
      setAgents(prev => prev.filter(a => a.agent_id !== agentId));
      if (selectedAgent?.agent_id === agentId) {
        setSelectedAgent(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete agent');
    }
  };

  const handleExecuteAgent = async (agentId: string) => {
    // In a real implementation, this would open an instruction dialog
    // For now, we'll just show a message
    console.log('Execute agent:', agentId);
  };

  const handlePauseAgent = async (agentId: string) => {
    console.log('Pause agent:', agentId);
  };

  const handleResumeAgent = async (agentId: string) => {
    console.log('Resume agent:', agentId);
  };

  const handleOpenLogs = (agentId: string) => {
    const agent = agents.find(a => a.agent_id === agentId);
    if (agent) {
      setSelectedAgent(agent);
    }
  };

  const handleOpenDetails = (agentId: string) => {
    const agent = agents.find(a => a.agent_id === agentId);
    if (agent) {
      setSelectedAgent(agent);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -right-1/2 w-full h-full bg-purple-500/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-1/2 -left-1/2 w-full h-full bg-blue-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 flex h-screen">
        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <header className="p-6 border-b border-white/10 bg-white/[0.02] backdrop-blur-xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent mb-2">
                  Multi-Agent Orchestration
                </h1>
                <p className="text-white/60">
                  Manage and monitor AI agents in real-time
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border",
                  isConnected
                    ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                    : "bg-red-500/20 text-red-400 border-red-500/30"
                )}>
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    isConnected ? "bg-emerald-400" : "bg-red-400"
                  )} />
                  {connectionStatus}
                </div>
              </div>
            </div>

            {/* Stats cards */}
            <div className="grid grid-cols-4 gap-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-xl"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="p-2 rounded-lg bg-purple-500/20">
                    <Users className="w-5 h-5 text-purple-400" />
                  </div>
                  <TrendingUp className="w-4 h-4 text-white/30" />
                </div>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
                <p className="text-xs text-white/60">Total Agents</p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 }}
                className="p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-xl"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="p-2 rounded-lg bg-emerald-500/20">
                    <Activity className="w-5 h-5 text-emerald-400" />
                  </div>
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                </div>
                <p className="text-2xl font-bold text-emerald-400">{stats.running}</p>
                <p className="text-xs text-white/60">Running</p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-xl"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="p-2 rounded-lg bg-amber-500/20">
                    <Zap className="w-5 h-5 text-amber-400" />
                  </div>
                  <CheckCircle2 className="w-4 h-4 text-amber-400" />
                </div>
                <p className="text-2xl font-bold text-amber-400">{stats.completed}</p>
                <p className="text-xs text-white/60">Completed</p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-xl"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="p-2 rounded-lg bg-red-500/20">
                    <AlertCircle className="w-5 h-5 text-red-400" />
                  </div>
                  <AlertCircle className="w-4 h-4 text-red-400" />
                </div>
                <p className="text-2xl font-bold text-red-400">{stats.error}</p>
                <p className="text-xs text-white/60">Errors</p>
              </motion.div>
            </div>
          </header>

          {/* Error message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mx-6 mt-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-400 mb-1">Error</p>
                <p className="text-sm text-red-300">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-red-400 hover:text-red-300"
              >
                ×
              </button>
            </motion.div>
          )}

          {/* Agents list */}
          <main className="flex-1 overflow-y-auto p-6">
            <AgentList
              agents={agents}
              loading={loading}
              onCreateAgent={() => setShowCreateModal(true)}
              onExecute={handleExecuteAgent}
              onPause={handlePauseAgent}
              onResume={handleResumeAgent}
              onDelete={handleDeleteAgent}
              onOpenLogs={handleOpenLogs}
              onOpenDetails={handleOpenDetails}
              onRefresh={loadAgents}
            />
          </main>
        </div>

        {/* Agent details panel */}
        <AgentDetails
          agent={selectedAgent}
          onClose={() => setSelectedAgent(null)}
          className="w-[600px] max-w-[600px]"
        />
      </div>

      {/* Create agent modal */}
      <CreateAgentModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleCreateSuccess}
      />
    </div>
  );
}

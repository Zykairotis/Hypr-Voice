// AgentList component for displaying all agents

'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Search, Filter, RefreshCw } from 'lucide-react';
import { Agent, AgentStatus } from './types';
import { AgentCard } from './AgentCard';
import { cn } from '@/app/lib/utils';

interface AgentListProps {
  agents: Agent[];
  loading?: boolean;
  onCreateAgent?: () => void;
  onExecute?: (agentId: string) => void;
  onPause?: (agentId: string) => void;
  onResume?: (agentId: string) => void;
  onDelete?: (agentId: string) => void;
  onOpenLogs?: (agentId: string) => void;
  onOpenDetails?: (agentId: string) => void;
  onRefresh?: () => void;
  className?: string;
}

const statusFilterOptions = [
  { value: 'all', label: 'All Agents' },
  { value: AgentStatus.IDLE, label: 'Idle' },
  { value: AgentStatus.RUNNING, label: 'Running' },
  { value: AgentStatus.PAUSED, label: 'Paused' },
  { value: AgentStatus.ERROR, label: 'Error' },
  { value: AgentStatus.COMPLETED, label: 'Completed' },
];

export function AgentList({
  agents,
  loading = false,
  onCreateAgent,
  onExecute,
  onPause,
  onResume,
  onDelete,
  onOpenLogs,
  onOpenDetails,
  onRefresh,
  className,
}: AgentListProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'status' | 'created'>('name');

  // Filter agents
  const filteredAgents = agents.filter((agent) => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         agent.agent_id.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' || agent.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  // Sort agents
  const sortedAgents = [...filteredAgents].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.name.localeCompare(b.name);
      case 'status':
        return a.status.localeCompare(b.status);
      case 'created':
        return a.agent_id.localeCompare(b.agent_id);
      default:
        return 0;
    }
  });

  const runningCount = agents.filter(a => a.status === AgentStatus.RUNNING).length;
  const errorCount = agents.filter(a => a.status === AgentStatus.ERROR).length;

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Agents</h2>
          <p className="text-sm text-white/60">
            {runningCount} running • {errorCount} errors • {agents.length} total
          </p>
        </div>
        <div className="flex items-center gap-3">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onRefresh}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10 transition-colors"
          >
            <RefreshCw className={cn("w-5 h-5", loading && "animate-spin")} />
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onCreateAgent}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white text-sm font-medium shadow-lg shadow-purple-500/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            Create Agent
          </motion.button>
        </div>
      </div>

      {/* Filters and search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
          <input
            type="text"
            placeholder="Search agents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
          />
        </div>

        <div className="flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
          >
            {statusFilterOptions.map((option) => (
              <option key={option.value} value={option.value} className="bg-slate-900">
                {option.label}
              </option>
            ))}
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
          >
            <option value="name" className="bg-slate-900">Sort by Name</option>
            <option value="status" className="bg-slate-900">Sort by Status</option>
            <option value="created" className="bg-slate-900">Sort by Created</option>
          </select>
        </div>
      </div>

      {/* Agents grid */}
      <AnimatePresence mode="popLayout">
        {sortedAgents.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16"
          >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/5 mb-4">
              <Filter className="w-8 h-8 text-white/30" />
            </div>
            <h3 className="text-lg font-medium text-white/60 mb-2">No agents found</h3>
            <p className="text-sm text-white/40 mb-6">
              {searchQuery || statusFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Create your first agent to get started'}
            </p>
            {(!searchQuery && statusFilter === 'all') && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onCreateAgent}
                className="px-6 py-3 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-medium shadow-lg shadow-purple-500/20 transition-all"
              >
                Create Your First Agent
              </motion.button>
            )}
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedAgents.map((agent) => (
              <AgentCard
                key={agent.agent_id}
                agent={agent}
                onExecute={onExecute}
                onPause={onPause}
                onResume={onResume}
                onDelete={onDelete}
                onOpenLogs={onOpenLogs}
                onOpenDetails={onOpenDetails}
              />
            ))}
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

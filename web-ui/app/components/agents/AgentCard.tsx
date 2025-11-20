// AgentCard component with status display and actions

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  Play,
  Pause,
  Square,
  Trash2,
  FolderOpen,
  MessageSquare,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { Agent, AgentStatus } from './types';
import { cn } from '@/app/lib/utils';

interface AgentCardProps {
  agent: Agent;
  onExecute?: (agentId: string) => void;
  onPause?: (agentId: string) => void;
  onResume?: (agentId: string) => void;
  onDelete?: (agentId: string) => void;
  onOpenLogs?: (agentId: string) => void;
  onOpenDetails?: (agentId: string) => void;
  className?: string;
}

const statusConfig = {
  [AgentStatus.IDLE]: {
    icon: Clock,
    label: 'Idle',
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/20',
  },
  [AgentStatus.RUNNING]: {
    icon: Activity,
    label: 'Running',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
  },
  [AgentStatus.PAUSED]: {
    icon: Pause,
    label: 'Paused',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
  },
  [AgentStatus.ERROR]: {
    icon: XCircle,
    label: 'Error',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
  },
  [AgentStatus.COMPLETED]: {
    icon: CheckCircle,
    label: 'Completed',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
  },
};

export function AgentCard({
  agent,
  onExecute,
  onPause,
  onResume,
  onDelete,
  onOpenLogs,
  onOpenDetails,
  className,
}: AgentCardProps) {
  const config = statusConfig[agent.status];
  const StatusIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className={cn(
        "group relative p-6 rounded-2xl border backdrop-blur-xl",
        "bg-white/5 dark:bg-black/10",
        "hover:bg-white/10 dark:hover:bg-black/20",
        "transition-all duration-300",
        config.borderColor,
        "shadow-lg shadow-black/5",
        className
      )}
    >
      {/* Status indicator */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <div className={cn("flex items-center gap-1.5 px-3 py-1 rounded-full", config.bgColor)}>
          <StatusIcon className={cn("w-3.5 h-3.5", config.color)} />
          <span className={cn("text-xs font-medium", config.color)}>{config.label}</span>
        </div>
      </div>

      {/* Agent info */}
      <div className="mb-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1 pr-20">
            <h3 className="text-lg font-semibold text-white mb-1 truncate">
              {agent.name}
            </h3>
            <p className="text-xs text-white/50 font-mono">
              {agent.agent_id.slice(0, 8)}...
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs text-white/60">
          <div className="flex items-center gap-1">
            <FolderOpen className="w-3.5 h-3.5" />
            <span className="truncate max-w-[200px]" title={agent.working_directory}>
              {agent.working_directory.split('/').pop()}
            </span>
          </div>
          {agent.conversation_length !== undefined && (
            <div className="flex items-center gap-1">
              <MessageSquare className="w-3.5 h-3.5" />
              <span>{agent.conversation_length} messages</span>
            </div>
          )}
        </div>
      </div>

      {/* Subagents indicator */}
      {agent.subagents.length > 0 && (
        <div className="mb-4 p-2 rounded-lg bg-purple-500/10 border border-purple-500/20">
          <p className="text-xs text-purple-300 font-medium">
            {agent.subagents.length} subagent{agent.subagents.length !== 1 ? 's' : ''}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 mt-4 opacity-0 group-hover:opacity-100 transition-opacity">
        {agent.status === AgentStatus.IDLE && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onExecute?.(agent.agent_id)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 text-xs font-medium border border-emerald-500/30 transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            Execute
          </motion.button>
        )}

        {agent.status === AgentStatus.RUNNING && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onPause?.(agent.agent_id)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 text-xs font-medium border border-amber-500/30 transition-colors"
          >
            <Pause className="w-3.5 h-3.5" />
            Pause
          </motion.button>
        )}

        {agent.status === AgentStatus.PAUSED && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onResume?.(agent.agent_id)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 text-xs font-medium border border-emerald-500/30 transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            Resume
          </motion.button>
        )}

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onOpenLogs?.(agent.agent_id)}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 text-xs font-medium border border-blue-500/30 transition-colors"
        >
          <Activity className="w-3.5 h-3.5" />
          Logs
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onOpenDetails?.(agent.agent_id)}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 text-xs font-medium border border-purple-500/30 transition-colors"
        >
          Details
        </motion.button>

        <div className="flex-1" />

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onDelete?.(agent.agent_id)}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 text-xs font-medium border border-red-500/30 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </motion.button>
      </div>
    </motion.div>
  );
}

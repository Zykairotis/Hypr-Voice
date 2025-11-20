// SubagentManager component for managing subagents

'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Trash2,
  GitBranch,
  Play,
  Square,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
} from 'lucide-react';
import { Agent, SubagentCreateRequest } from './types';
import { AgentsAPI } from './api';
import { cn } from '@/app/lib/utils';

interface SubagentManagerProps {
  agent: Agent | null;
  className?: string;
}

interface Subagent {
  agent_id: string;
  name: string;
  status: string;
  skills: string[];
}

export function SubagentManager({ agent, className }: SubagentManagerProps) {
  const [subagents, setSubagents] = useState<Subagent[]>([]);
  const [loading, setLoading] = useState(false);
  const [newSubagentName, setNewSubagentName] = useState('');
  const [newSubagentSkills, setNewSubagentSkills] = useState<string[]>([]);
  const [availableSkills, setAvailableSkills] = useState<string[]>(['file_operations', 'bash_execution', 'voice_synthesis']);
  const [executionMode, setExecutionMode] = useState<'parallel' | 'sequential'>('parallel');
  const [instruction, setInstruction] = useState('');

  const handleCreateSubagent = async () => {
    if (!agent || !newSubagentName.trim()) return;

    setLoading(true);
    try {
      const request: SubagentCreateRequest = {
        name: newSubagentName.trim(),
        skills: newSubagentSkills.length > 0 ? newSubagentSkills : ['file_operations'],
      };

      const response = await AgentsAPI.createSubagent(agent.agent_id, request);

      setSubagents(prev => [
        ...prev,
        {
          agent_id: response.subagent_id,
          name: response.name,
          status: 'idle',
          skills: request.skills,
        },
      ]);

      setNewSubagentName('');
      setNewSubagentSkills([]);
    } catch (error) {
      console.error('Failed to create subagent:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSubagent = async (subagentId: string) => {
    try {
      setSubagents(prev => prev.filter(s => s.agent_id !== subagentId));
    } catch (error) {
      console.error('Failed to delete subagent:', error);
    }
  };

  const handleExecuteAll = async () => {
    if (!instruction.trim() || subagents.length === 0) return;

    // This would trigger execution on all subagents
    console.log(`Executing instruction on ${subagents.length} subagents in ${executionMode} mode`);
  };

  const toggleSkill = (skill: string) => {
    setNewSubagentSkills(prev =>
      prev.includes(skill)
        ? prev.filter(s => s !== skill)
        : [...prev, skill]
    );
  };

  if (!agent) {
    return (
      <div className={cn("flex items-center justify-center h-full", className)}>
        <div className="text-center">
          <GitBranch className="w-12 h-12 text-white/30 mx-auto mb-4" />
          <p className="text-white/60">Select an agent to manage subagents</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Subagent Manager</h3>

        {/* Create new subagent */}
        <div className="space-y-3">
          <input
            type="text"
            value={newSubagentName}
            onChange={(e) => setNewSubagentName(e.target.value)}
            placeholder="Subagent name..."
            className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
          />

          <div>
            <p className="text-xs text-white/60 mb-2">Skills:</p>
            <div className="flex flex-wrap gap-2">
              {availableSkills.map(skill => (
                <motion.button
                  key={skill}
                  type="button"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => toggleSkill(skill)}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                    newSubagentSkills.includes(skill)
                      ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                      : "bg-white/5 text-white/60 border border-white/10 hover:bg-white/10"
                  )}
                >
                  {skill}
                </motion.button>
              ))}
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleCreateSubagent}
            disabled={!newSubagentName.trim() || loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 font-medium border border-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            Create Subagent
          </motion.button>
        </div>
      </div>

      {/* Subagents list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {subagents.length === 0 ? (
          <div className="text-center py-8">
            <GitBranch className="w-12 h-12 text-white/30 mx-auto mb-4" />
            <p className="text-white/60">No subagents created yet</p>
            <p className="text-sm text-white/40 mt-1">Create your first subagent above</p>
          </div>
        ) : (
          <AnimatePresence>
            {subagents.map((subagent) => (
              <motion.div
                key={subagent.agent_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="p-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-medium text-white">{subagent.name}</h4>
                    <p className="text-xs text-white/50 font-mono mt-1">
                      {subagent.agent_id.slice(0, 12)}...
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className={cn(
                      "flex items-center gap-1 px-2 py-1 rounded text-xs",
                      subagent.status === 'running'
                        ? "bg-emerald-500/20 text-emerald-400"
                        : subagent.status === 'error'
                        ? "bg-red-500/20 text-red-400"
                        : "bg-white/10 text-white/60"
                    )}>
                      {subagent.status === 'running' && <Loader2 className="w-3 h-3 animate-spin" />}
                      {subagent.status === 'idle' && <Clock className="w-3 h-3" />}
                      {subagent.status === 'error' && <XCircle className="w-3 h-3" />}
                      {subagent.status === 'completed' && <CheckCircle className="w-3 h-3" />}
                      {subagent.status}
                    </div>

                    <button
                      onClick={() => handleDeleteSubagent(subagent.agent_id)}
                      className="p-1.5 rounded hover:bg-red-500/20 text-red-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="flex flex-wrap gap-1">
                  {subagent.skills.map(skill => (
                    <span
                      key={skill}
                      className="px-2 py-1 rounded text-xs bg-purple-500/10 text-purple-300 border border-purple-500/20"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Execute panel */}
      {subagents.length > 0 && (
        <div className="p-4 border-t border-white/10">
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Execute on {subagents.length} subagent{subagents.length !== 1 ? 's' : ''}
              </label>

              <select
                value={executionMode}
                onChange={(e) => setExecutionMode(e.target.value as any)}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all mb-2"
              >
                <option value="parallel" className="bg-slate-900">Parallel Execution</option>
                <option value="sequential" className="bg-slate-900">Sequential Execution</option>
              </select>
            </div>

            <textarea
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder="Enter instruction for subagents..."
              className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all resize-none"
              rows={2}
            />

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleExecuteAll}
              disabled={!instruction.trim()}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20 transition-all"
            >
              <Play className="w-4 h-4" />
              Execute All Subagents
            </motion.button>
          </div>
        </div>
      )}
    </div>
  );
}

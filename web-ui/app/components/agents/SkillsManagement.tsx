// SkillsManagement component for managing agent skills

'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wrench, CheckCircle, XCircle, Info, Search, Filter } from 'lucide-react';
import { Skill } from './types';
import { AgentsAPI } from './api';
import { cn } from '@/app/lib/utils';

interface SkillsManagementProps {
  agent: Agent | null;
  selectedSkills: string[];
  onSkillsChange: (skills: string[]) => void;
  className?: string;
}

export function SkillsManagement({
  agent,
  selectedSkills,
  onSkillsChange,
  className,
}: SkillsManagementProps) {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterEnabled, setFilterEnabled] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSkills();
  }, []);

  const loadSkills = async () => {
    setLoading(true);
    try {
      const { skills } = await AgentsAPI.listSkills();
      setSkills(skills);
    } catch (error) {
      console.error('Failed to load skills:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredSkills = skills.filter(skill => {
    const matchesSearch = skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         skill.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesFilter = filterEnabled === 'all' ||
                         (filterEnabled === 'enabled' && skill.enabled) ||
                         (filterEnabled === 'disabled' && !skill.enabled);

    return matchesSearch && matchesFilter;
  });

  const toggleSkill = (skillName: string) => {
    const isSelected = selectedSkills.includes(skillName);
    if (isSelected) {
      onSkillsChange(selectedSkills.filter(s => s !== skillName));
    } else {
      onSkillsChange([...selectedSkills, skillName]);
    }
  };

  const enabledCount = selectedSkills.length;
  const totalCount = skills.length;

  if (!agent) {
    return (
      <div className={cn("flex items-center justify-center h-full", className)}>
        <div className="text-center">
          <Wrench className="w-12 h-12 text-white/30 mx-auto mb-4" />
          <p className="text-white/60">Select an agent to manage skills</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Skills Management</h3>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <p className="text-xs text-white/60 mb-1">Selected</p>
            <p className="text-xl font-bold text-purple-400">{enabledCount}</p>
          </div>
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <p className="text-xs text-white/60 mb-1">Available</p>
            <p className="text-xl font-bold text-white">{totalCount}</p>
          </div>
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <p className="text-xs text-white/60 mb-1">Percentage</p>
            <p className="text-xl font-bold text-emerald-400">
              {totalCount > 0 ? Math.round((enabledCount / totalCount) * 100) : 0}%
            </p>
          </div>
        </div>

        {/* Search and filter */}
        <div className="flex gap-2 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
            <input
              type="text"
              placeholder="Search skills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
            />
          </div>

          <select
            value={filterEnabled}
            onChange={(e) => setFilterEnabled(e.target.value as any)}
            className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
          >
            <option value="all" className="bg-slate-900">All</option>
            <option value="enabled" className="bg-slate-900">Enabled</option>
            <option value="disabled" className="bg-slate-900">Disabled</option>
          </select>
        </div>
      </div>

      {/* Skills list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400" />
          </div>
        ) : filteredSkills.length === 0 ? (
          <div className="text-center py-8">
            <Filter className="w-12 h-12 text-white/30 mx-auto mb-4" />
            <p className="text-white/60">No skills found</p>
            <p className="text-sm text-white/40 mt-1">
              {searchQuery ? 'Try adjusting your search' : 'No skills available'}
            </p>
          </div>
        ) : (
          <AnimatePresence>
            {filteredSkills.map((skill) => {
              const isSelected = selectedSkills.includes(skill.name);
              return (
                <motion.div
                  key={skill.name}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  whileHover={{ scale: 1.01 }}
                  className={cn(
                    "group p-4 rounded-lg border cursor-pointer transition-all",
                    isSelected
                      ? "bg-purple-500/10 border-purple-500/30"
                      : "bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20"
                  )}
                  onClick={() => toggleSkill(skill.name)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className={cn(
                          "font-medium truncate",
                          isSelected ? "text-purple-300" : "text-white"
                        )}>
                          {skill.name}
                        </h4>
                        <div className={cn(
                          "flex items-center gap-1 px-2 py-0.5 rounded text-xs",
                          skill.enabled
                            ? "bg-emerald-500/20 text-emerald-400"
                            : "bg-white/10 text-white/60"
                        )}>
                          {skill.enabled ? (
                            <>
                              <CheckCircle className="w-3 h-3" />
                              Enabled
                            </>
                          ) : (
                            <>
                              <XCircle className="w-3 h-3" />
                              Disabled
                            </>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-white/60 line-clamp-2">
                        {skill.description}
                      </p>
                    </div>

                    <motion.div
                      whileHover={{ scale: 1.1 }}
                      className={cn(
                        "flex items-center justify-center w-5 h-5 rounded border-2 transition-all",
                        isSelected
                          ? "bg-purple-500 border-purple-500"
                          : "border-white/30 group-hover:border-white/50"
                      )}
                    >
                      {isSelected && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="w-2 h-2 bg-white rounded-full"
                        />
                      )}
                    </motion.div>
                  </div>

                  {isSelected && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="mt-3 pt-3 border-t border-purple-500/20"
                    >
                      <div className="flex items-start gap-2 text-xs text-purple-300">
                        <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                        <p>
                          This skill will be available to the agent. Skills can provide additional
                          capabilities like file operations, command execution, or specialized tools.
                        </p>
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>

      {/* Footer */}
      {selectedSkills.length > 0 && (
        <div className="p-4 border-t border-white/10 bg-white/[0.02]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white">
                {selectedSkills.length} skill{selectedSkills.length !== 1 ? 's' : ''} selected
              </p>
              <p className="text-xs text-white/50">
                These skills will be available to the agent
              </p>
            </div>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onSkillsChange([])}
              className="px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 text-sm font-medium border border-red-500/30 transition-colors"
            >
              Clear All
            </motion.button>
          </div>
        </div>
      )}
    </div>
  );
}

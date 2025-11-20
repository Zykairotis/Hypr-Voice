// CreateAgentModal component for creating new agents with advanced options

'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Plus, Trash2, Info, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { AgentConfig, Skill } from './types';
import { AgentsAPI } from './api';
import { cn } from '@/app/lib/utils';

interface CreateAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (agentId: string) => void;
}

const MODEL_OPTIONS = [
  { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
  { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
  { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
  { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' },
];

const TTS_PROVIDERS = [
  { value: 'kokoro', label: 'Kokoro' },
  { value: 'deepgram', label: 'Deepgram' },
  { value: 'elevenlabs', label: 'ElevenLabs' },
];

export function CreateAgentModal({ isOpen, onClose, onSuccess }: CreateAgentModalProps) {
  const [loading, setLoading] = useState(false);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [config, setConfig] = useState<AgentConfig>({
    name: '',
    working_directory: '/tmp/agents',
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 8096,
    temperature: 1.0,
    skills: [],
    mcp_servers: [],
    custom_tools: [],
    enable_voice: false,
    enable_monitoring: true,
    monitor_interval: 0.15,
    use_claude_code: true,
    enable_tts_agent: false,
    tts_provider: 'kokoro',
    tts_voice: null,
    auto_synthesize: true,
  });

  const [customSkillName, setCustomSkillName] = useState('');
  const [customToolName, setCustomToolName] = useState('');
  const [mcpPresetName, setMcpPresetName] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadSkills();
    }
  }, [isOpen]);

  const loadSkills = async () => {
    try {
      const { skills } = await AgentsAPI.listSkills();
      setSkills(skills);
    } catch (err) {
      console.error('Failed to load skills:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await AgentsAPI.createAgent(config);
      onSuccess(response.agent_id);
      onClose();
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Failed to create agent');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setConfig({
      name: '',
      working_directory: '/tmp/agents',
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 8096,
      temperature: 1.0,
      skills: [],
      mcp_servers: [],
      custom_tools: [],
      enable_voice: false,
      enable_monitoring: true,
      monitor_interval: 0.15,
      use_claude_code: true,
      enable_tts_agent: false,
      tts_provider: 'kokoro',
      tts_voice: null,
      auto_synthesize: true,
    });
  };

  const toggleSkill = (skillName: string) => {
    setConfig(prev => ({
      ...prev,
      skills: prev.skills.includes(skillName)
        ? prev.skills.filter(s => s !== skillName)
        : [...prev.skills, skillName],
    }));
  };

  const addCustomSkill = () => {
    if (customSkillName.trim() && !config.custom_tools.includes(customSkillName)) {
      setConfig(prev => ({
        ...prev,
        custom_tools: [...prev.custom_tools, customSkillName],
      }));
      setCustomSkillName('');
    }
  };

  const removeCustomSkill = (skillName: string) => {
    setConfig(prev => ({
      ...prev,
      custom_tools: prev.custom_tools.filter(s => s !== skillName),
    }));
  };

  const toggleMCPServer = (serverName: string) => {
    setConfig(prev => ({
      ...prev,
      mcp_servers: prev.mcp_servers.includes(serverName)
        ? prev.mcp_servers.filter(s => s !== serverName)
        : [...prev.mcp_servers, serverName],
    }));
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl bg-slate-900 border border-white/10 shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-white/10">
              <h2 className="text-xl font-bold text-white">Create New Agent</h2>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-white/5 text-white/60 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="overflow-y-auto max-h-[calc(90vh-8rem)]">
              <div className="p-6 space-y-6">
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-2 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400"
                  >
                    <AlertCircle className="w-5 h-5" />
                    <span className="text-sm">{error}</span>
                  </motion.div>
                )}

                {/* Basic Configuration */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wider">
                    Basic Configuration
                  </h3>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-white/70 mb-2">
                        Agent Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={config.name}
                        onChange={(e) => setConfig(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
                        placeholder="My Agent"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-white/70 mb-2">
                        Working Directory
                      </label>
                      <input
                        type="text"
                        value={config.working_directory}
                        onChange={(e) => setConfig(prev => ({ ...prev, working_directory: e.target.value }))}
                        className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-white/70 mb-2">
                        Model
                      </label>
                      <select
                        value={config.model}
                        onChange={(e) => setConfig(prev => ({ ...prev, model: e.target.value }))}
                        className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
                      >
                        {MODEL_OPTIONS.map(option => (
                          <option key={option.value} value={option.value} className="bg-slate-900">
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-white/70 mb-2">
                        Temperature: {config.temperature}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={config.temperature}
                        onChange={(e) => setConfig(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                        className="w-full"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-white/70 mb-2">
                      Max Tokens
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="8192"
                      value={config.max_tokens}
                      onChange={(e) => setConfig(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
                      className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
                    />
                  </div>
                </div>

                {/* Skills */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wider">
                    Skills
                  </h3>

                  <div className="grid grid-cols-3 gap-2">
                    {skills.map(skill => (
                      <motion.button
                        key={skill.name}
                        type="button"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => toggleSkill(skill.name)}
                        className={cn(
                          "flex items-center gap-2 p-3 rounded-lg border text-left transition-all",
                          config.skills.includes(skill.name)
                            ? "bg-purple-500/20 border-purple-500/30 text-purple-300"
                            : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10"
                        )}
                      >
                        <CheckCircle className={cn(
                          "w-4 h-4",
                          config.skills.includes(skill.name) ? "text-purple-400" : "text-white/40"
                        )} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{skill.name}</p>
                          <p className="text-xs text-white/50 truncate">{skill.description}</p>
                        </div>
                      </motion.button>
                    ))}
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-white/70">
                      Custom Skills
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={customSkillName}
                        onChange={(e) => setCustomSkillName(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomSkill())}
                        className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
                        placeholder="Enter custom skill name"
                      />
                      <button
                        type="button"
                        onClick={addCustomSkill}
                        className="px-4 py-2 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 border border-purple-500/30 transition-colors"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {config.custom_tools.map(tool => (
                        <motion.div
                          key={tool}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm"
                        >
                          {tool}
                          <button
                            type="button"
                            onClick={() => removeCustomSkill(tool)}
                            className="text-blue-400 hover:text-blue-300"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* MCP Servers */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wider">
                    MCP Servers
                  </h3>
                  <p className="text-xs text-white/50">
                    Enable Model Context Protocol servers for additional capabilities
                  </p>

                  <div className="grid grid-cols-2 gap-2">
                    {['filesystem', 'github', 'git', 'brave-search'].map(server => (
                      <motion.button
                        key={server}
                        type="button"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => toggleMCPServer(server)}
                        className={cn(
                          "flex items-center gap-2 p-3 rounded-lg border text-left transition-all",
                          config.mcp_servers.includes(server)
                            ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-300"
                            : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10"
                        )}
                      >
                        <CheckCircle className={cn(
                          "w-4 h-4",
                          config.mcp_servers.includes(server) ? "text-emerald-400" : "text-white/40"
                        )} />
                        <div>
                          <p className="text-sm font-medium">{server}</p>
                        </div>
                      </motion.button>
                    ))}
                  </div>
                </div>

                {/* Voice & TTS */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wider">
                    Voice & TTS
                  </h3>

                  <div className="space-y-4">
                    <label className="flex items-center gap-3 p-4 rounded-lg bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors">
                      <input
                        type="checkbox"
                        checked={config.enable_voice}
                        onChange={(e) => setConfig(prev => ({ ...prev, enable_voice: e.target.checked }))}
                        className="w-4 h-4 text-purple-500 rounded focus:ring-purple-500/50"
                      />
                      <div>
                        <p className="text-sm font-medium text-white">Enable Voice Synthesis</p>
                        <p className="text-xs text-white/50">Convert agent responses to speech</p>
                      </div>
                    </label>

                    <label className="flex items-center gap-3 p-4 rounded-lg bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors">
                      <input
                        type="checkbox"
                        checked={config.enable_tts_agent}
                        onChange={(e) => setConfig(prev => ({ ...prev, enable_tts_agent: e.target.checked }))}
                        className="w-4 h-4 text-purple-500 rounded focus:ring-purple-500/50"
                      />
                      <div>
                        <p className="text-sm font-medium text-white">Enable TTS Agent</p>
                        <p className="text-xs text-white/50">Advanced text-to-speech with multiple providers</p>
                      </div>
                    </label>

                    {config.enable_tts_agent && (
                      <div className="grid grid-cols-2 gap-4 pl-7">
                        <div>
                          <label className="block text-sm font-medium text-white/70 mb-2">
                            TTS Provider
                          </label>
                          <select
                            value={config.tts_provider}
                            onChange={(e) => setConfig(prev => ({ ...prev, tts_provider: e.target.value }))}
                            className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
                          >
                            {TTS_PROVIDERS.map(provider => (
                              <option key={provider.value} value={provider.value} className="bg-slate-900">
                                {provider.label}
                              </option>
                            ))}
                          </select>
                        </div>

                        <label className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={config.auto_synthesize}
                            onChange={(e) => setConfig(prev => ({ ...prev, auto_synthesize: e.target.checked }))}
                            className="w-4 h-4 text-purple-500 rounded focus:ring-purple-500/50"
                          />
                          <span className="text-sm text-white/70">Auto-synthesize responses</span>
                        </label>
                      </div>
                    )}
                  </div>
                </div>

                {/* Advanced Options */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-white/90 uppercase tracking-wider">
                    Advanced Options
                  </h3>

                  <div className="grid grid-cols-2 gap-4">
                    <label className="flex items-center gap-3 p-4 rounded-lg bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors">
                      <input
                        type="checkbox"
                        checked={config.enable_monitoring}
                        onChange={(e) => setConfig(prev => ({ ...prev, enable_monitoring: e.target.checked }))}
                        className="w-4 h-4 text-purple-500 rounded focus:ring-purple-500/50"
                      />
                      <div>
                        <p className="text-sm font-medium text-white">Enable Monitoring</p>
                        <p className="text-xs text-white/50">Monitor application context</p>
                      </div>
                    </label>

                    <label className="flex items-center gap-3 p-4 rounded-lg bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors">
                      <input
                        type="checkbox"
                        checked={config.use_claude_code}
                        onChange={(e) => setConfig(prev => ({ ...prev, use_claude_code: e.target.checked }))}
                        className="w-4 h-4 text-purple-500 rounded focus:ring-purple-500/50"
                      />
                      <div>
                        <p className="text-sm font-medium text-white">Use Claude Code</p>
                        <p className="text-xs text-white/50">Enhanced code execution</p>
                      </div>
                    </label>
                  </div>

                  {config.enable_monitoring && (
                    <div>
                      <label className="block text-sm font-medium text-white/70 mb-2">
                        Monitor Interval: {config.monitor_interval}s
                      </label>
                      <input
                        type="range"
                        min="0.1"
                        max="1"
                        step="0.05"
                        value={config.monitor_interval}
                        onChange={(e) => setConfig(prev => ({ ...prev, monitor_interval: parseFloat(e.target.value) }))}
                        className="w-full"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end gap-3 p-6 border-t border-white/10 bg-white/[0.02]">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 rounded-lg text-white/70 hover:text-white hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
                <motion.button
                  type="submit"
                  disabled={loading || !config.name.trim()}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex items-center gap-2 px-6 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20 transition-all"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Agent'
                  )}
                </motion.button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

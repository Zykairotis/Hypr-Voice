// AgentControlPanel component for sending instructions and monitoring agent output

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Download,
  Trash2,
  Copy,
  Volume2,
  VolumeX,
  Loader2,
  FileText,
  Terminal,
  Activity,
} from 'lucide-react';
import { Agent, AgentStatus, AgentEvent, EventType } from './types';
import { useAgentWebSocket } from './useWebSocket';
import { cn } from '@/app/lib/utils';

interface AgentControlPanelProps {
  agent: Agent | null;
  onClose?: () => void;
  className?: string;
}

interface LogEntry {
  id: string;
  timestamp: string;
  type: 'user' | 'assistant' | 'system' | 'error' | 'event';
  content: string;
  data?: any;
}

export function AgentControlPanel({ agent, onClose, className }: AgentControlPanelProps) {
  const [instruction, setInstruction] = useState('');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const { isConnected, subscribeToAgent, unsubscribeFromAgent } = useAgentWebSocket({
    onEvent: (event: AgentEvent) => {
      handleAgentEvent(event);
    },
  });

  useEffect(() => {
    if (agent) {
      subscribeToAgent(agent.agent_id);
      loadAgentStatus();

      // Add initial log
      addLog('system', `Monitoring agent ${agent.name} (${agent.agent_id.slice(0, 8)})`);
    }

    return () => {
      if (agent) {
        unsubscribeFromAgent(agent.agent_id);
      }
    };
  }, [agent]);

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadAgentStatus = async () => {
    // This would fetch initial agent status if needed
  };

  const handleAgentEvent = (event: AgentEvent) => {
    switch (event.event_type) {
      case EventType.AGENT_STARTED:
        addLog('system', `Agent started executing instruction`);
        break;

      case EventType.AGENT_OUTPUT:
        if (event.data.type === 'text' || event.data.type === 'text_delta') {
          const content = event.data.content || '';
          if (event.data.type === 'text_delta') {
            // Append to last assistant message
            setLogs(prev => {
              if (prev.length === 0) return prev;
              const newLogs = [...prev];
              const lastIndex = newLogs.length - 1;
              if (newLogs[lastIndex].type === 'assistant') {
                newLogs[lastIndex] = {
                  ...newLogs[lastIndex],
                  content: newLogs[lastIndex].content + content,
                };
              }
              return newLogs;
            });
          } else {
            addLog('assistant', content);
          }
        }
        break;

      case EventType.AGENT_ERROR:
        addLog('error', `Error: ${event.data.error || 'Unknown error'}`);
        setIsExecuting(false);
        break;

      case EventType.AGENT_COMPLETED:
        addLog('system', `Agent completed execution`);
        setIsExecuting(false);
        break;

      case EventType.TOOL_EXECUTION:
        addLog('event', `Executed tool: ${event.data.tool_name}`, event.data);
        break;

      case EventType.MCP_EVENT:
        addLog('event', `MCP Event: ${event.data.server_name} - ${event.data.action}`, event.data);
        break;

      case EventType.VOICE_SYNTHESIS:
        addLog('event', `Voice synthesis: ${event.data.text?.slice(0, 50)}...`, event.data);
        break;

      case EventType.SUBAGENT_CREATED:
        addLog('system', `Created subagent: ${event.data.name}`);
        break;
    }
  };

  const addLog = (type: LogEntry['type'], content: string, data?: any) => {
    setLogs(prev => [
      ...prev,
      {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        type,
        content,
        data,
      },
    ]);
  };

  const handleSendInstruction = async () => {
    if (!instruction.trim() || !agent || isExecuting) return;

    addLog('user', instruction);
    setInstruction('');
    setIsExecuting(true);

    try {
      // In a real implementation, this would call the API
      // For now, we'll just simulate it
      addLog('system', 'Instruction queued for execution');
    } catch (error) {
      addLog('error', `Failed to send instruction: ${error}`);
      setIsExecuting(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSendInstruction();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const exportLogs = () => {
    const logText = logs.map(log => {
      const time = new Date(log.timestamp).toLocaleTimeString();
      return `[${time}] ${log.type.toUpperCase()}: ${log.content}`;
    }).join('\n');

    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-logs-${agent?.agent_id.slice(0, 8)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearLogs = () => {
    setLogs([]);
  };

  if (!agent) {
    return (
      <div className={cn("flex items-center justify-center h-full", className)}>
        <div className="text-center">
          <Activity className="w-12 h-12 text-white/30 mx-auto mb-4" />
          <p className="text-white/60">Select an agent to view control panel</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full bg-slate-900/50", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-2 h-2 rounded-full",
            isConnected ? "bg-emerald-400" : "bg-red-400"
          )} />
          <h3 className="font-semibold text-white">{agent.name}</h3>
          <span className={cn(
            "px-2 py-0.5 rounded text-xs font-medium",
            agent.status === AgentStatus.RUNNING
              ? "bg-emerald-500/20 text-emerald-400"
              : agent.status === AgentStatus.ERROR
              ? "bg-red-500/20 text-red-400"
              : "bg-white/10 text-white/70"
          )}>
            {agent.status}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setVoiceEnabled(!voiceEnabled)}
            className={cn(
              "p-2 rounded-lg transition-colors",
              voiceEnabled
                ? "bg-purple-500/20 text-purple-400"
                : "bg-white/5 text-white/40 hover:text-white/70"
            )}
          >
            {voiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>
          <button
            onClick={exportLogs}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={clearLogs}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Logs */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <AnimatePresence>
          {logs.map((log) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={cn(
                "group flex gap-3 p-4 rounded-lg border",
                log.type === 'user'
                  ? "bg-blue-500/10 border-blue-500/20"
                  : log.type === 'assistant'
                  ? "bg-purple-500/10 border-purple-500/20"
                  : log.type === 'error'
                  ? "bg-red-500/10 border-red-500/20"
                  : log.type === 'event'
                  ? "bg-emerald-500/10 border-emerald-500/20"
                  : "bg-white/5 border-white/10"
              )}
            >
              <div className="flex-shrink-0 mt-1">
                {log.type === 'user' && <FileText className="w-4 h-4 text-blue-400" />}
                {log.type === 'assistant' && <Terminal className="w-4 h-4 text-purple-400" />}
                {log.type === 'error' && <Activity className="w-4 h-4 text-red-400" />}
                {log.type === 'event' && <Activity className="w-4 h-4 text-emerald-400" />}
                {log.type === 'system' && <Activity className="w-4 h-4 text-white/60" />}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <p className="text-sm text-white/90 whitespace-pre-wrap break-words">
                      {log.content}
                    </p>
                    {log.data && (
                      <pre className="mt-2 p-2 rounded bg-black/20 text-xs text-white/60 overflow-x-auto">
                        {JSON.stringify(log.data, null, 2)}
                      </pre>
                    )}
                  </div>

                  <button
                    onClick={() => copyToClipboard(log.content)}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-white/10 transition-all"
                  >
                    <Copy className="w-3.5 h-3.5 text-white/40" />
                  </button>
                </div>

                <p className="mt-2 text-xs text-white/40">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={logsEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/10">
        <div className="flex gap-2">
          <textarea
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter instruction... (Cmd/Ctrl+Enter to send)"
            className="flex-1 px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all resize-none"
            rows={2}
            disabled={isExecuting}
          />
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSendInstruction}
            disabled={!instruction.trim() || isExecuting}
            className="px-4 py-3 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20 transition-all"
          >
            {isExecuting ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </motion.button>
        </div>

        <p className="mt-2 text-xs text-white/40">
          Press Cmd/Ctrl+Enter to send • WebSocket: {isConnected ? 'Connected' : 'Disconnected'}
        </p>
      </div>
    </div>
  );
}

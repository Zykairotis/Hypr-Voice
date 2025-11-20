// MCPServersConfig component for configuring MCP servers

'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Server, CheckCircle, XCircle, ExternalLink, Info, AlertCircle } from 'lucide-react';
import { AgentsAPI } from './api';
import { cn } from '@/app/lib/utils';

interface MCPServersConfigProps {
  agent: Agent | null;
  selectedServers: string[];
  onServersChange: (servers: string[]) => void;
  className?: string;
}

interface MCPServerInfo {
  name: string;
  description: string;
  category: 'development' | 'productivity' | 'search' | 'cloud';
  requiredEnv?: boolean;
  docsUrl?: string;
}

const MCP_SERVERS: MCPServerInfo[] = [
  {
    name: 'filesystem',
    description: 'Provides file system operations including reading, writing, and managing files and directories.',
    category: 'development',
    requiredEnv: false,
    docsUrl: 'https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem',
  },
  {
    name: 'github',
    description: 'Enables GitHub operations including repository management, issues, and pull requests.',
    category: 'development',
    requiredEnv: true,
    docsUrl: 'https://github.com/modelcontextprotocol/servers/tree/main/src/github',
  },
  {
    name: 'git',
    description: 'Provides Git repository operations including commits, branches, and version control.',
    category: 'development',
    requiredEnv: false,
    docsUrl: 'https://github.com/modelcontextprotocol/servers/tree/main/src/git',
  },
  {
    name: 'brave-search',
    description: 'Integrates Brave Search API for web searches and information retrieval.',
    category: 'search',
    requiredEnv: true,
    docsUrl: 'https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search',
  },
];

const CATEGORIES = {
  development: { label: 'Development', icon: '🔧', color: 'from-blue-500 to-cyan-500' },
  productivity: { label: 'Productivity', icon: '⚡', color: 'from-purple-500 to-pink-500' },
  search: { label: 'Search', icon: '🔍', color: 'from-emerald-500 to-teal-500' },
  cloud: { label: 'Cloud', icon: '☁️', color: 'from-orange-500 to-red-500' },
};

export function MCPServersConfig({
  agent,
  selectedServers,
  onServersChange,
  className,
}: MCPServersConfigProps) {
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [showDetails, setShowDetails] = useState<string | null>(null);

  useEffect(() => {
    // Could load preset MCP servers from API here
  }, []);

  const filteredServers = filterCategory === 'all'
    ? MCP_SERVERS
    : MCP_SERVERS.filter(server => server.category === filterCategory);

  const toggleServer = (serverName: string) => {
    const isSelected = selectedServers.includes(serverName);
    if (isSelected) {
      onServersChange(selectedServers.filter(s => s !== serverName));
    } else {
      onServersChange([...selectedServers, serverName]);
    }
  };

  const enabledCount = selectedServers.length;
  const totalCount = MCP_SERVERS.length;

  if (!agent) {
    return (
      <div className={cn("flex items-center justify-center h-full", className)}>
        <div className="text-center">
          <Server className="w-12 h-12 text-white/30 mx-auto mb-4" />
          <p className="text-white/60">Select an agent to configure MCP servers</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">MCP Servers</h3>

        {/* Info */}
        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 mb-4">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-blue-300">
              <p className="font-medium mb-1">Model Context Protocol Servers</p>
              <p>
                MCP servers provide additional capabilities to agents through standardized interfaces.
                Enable servers that match your agent's requirements.
              </p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <p className="text-xs text-white/60 mb-1">Enabled</p>
            <p className="text-xl font-bold text-emerald-400">{enabledCount}</p>
          </div>
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <p className="text-xs text-white/60 mb-1">Available</p>
            <p className="text-xl font-bold text-white">{totalCount}</p>
          </div>
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <p className="text-xs text-white/60 mb-1">Categories</p>
            <p className="text-xl font-bold text-purple-400">
              {Object.keys(CATEGORIES).length}
            </p>
          </div>
        </div>

        {/* Category filter */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setFilterCategory('all')}
            className={cn(
              "px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all",
              filterCategory === 'all'
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                : "bg-white/5 text-white/60 border border-white/10 hover:bg-white/10"
            )}
          >
            All Servers
          </button>
          {Object.entries(CATEGORIES).map(([key, category]) => (
            <button
              key={key}
              onClick={() => setFilterCategory(key)}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all",
                filterCategory === key
                  ? `bg-gradient-to-r ${category.color} text-white border-0`
                  : "bg-white/5 text-white/60 border border-white/10 hover:bg-white/10"
              )}
            >
              <span>{category.icon}</span>
              {category.label}
            </button>
          ))}
        </div>
      </div>

      {/* Servers list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <AnimatePresence>
          {filteredServers.map((server) => {
            const isSelected = selectedServers.includes(server.name);
            return (
              <motion.div
                key={server.name}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={cn(
                  "group p-4 rounded-lg border cursor-pointer transition-all",
                  isSelected
                    ? "bg-emerald-500/10 border-emerald-500/30"
                    : "bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20"
                )}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className={cn(
                        "font-medium",
                        isSelected ? "text-emerald-300" : "text-white"
                      )}>
                        {server.name}
                      </h4>

                      <span className={cn(
                        "px-2 py-0.5 rounded text-xs",
                        CATEGORIES[server.category]?.color
                          ? "bg-white/10 text-white/70"
                          : "bg-white/10 text-white/70"
                      )}>
                        {CATEGORIES[server.category]?.label || server.category}
                      </span>

                      {server.requiredEnv && (
                        <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 text-xs">
                          <AlertCircle className="w-3 h-3" />
                          Env Required
                        </div>
                      )}
                    </div>

                    <p className="text-sm text-white/60 mb-2">
                      {server.description}
                    </p>

                    <div className="flex items-center gap-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDetails(showDetails === server.name ? null : server.name);
                        }}
                        className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
                      >
                        {showDetails === server.name ? 'Hide details' : 'Show details'}
                      </button>

                      {server.docsUrl && (
                        <a
                          href={server.docsUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                        >
                          Documentation
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>

                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleServer(server.name);
                    }}
                    className={cn(
                      "flex items-center justify-center w-6 h-6 rounded-full border-2 transition-all",
                      isSelected
                        ? "bg-emerald-500 border-emerald-500"
                        : "border-white/30 group-hover:border-white/50"
                    )}
                  >
                    {isSelected && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="w-3 h-3 bg-white rounded-full"
                      />
                    )}
                  </motion.button>
                </div>

                {showDetails === server.name && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-3 pt-3 border-t border-white/10 space-y-2"
                  >
                    {server.requiredEnv && (
                      <div className="p-2 rounded bg-amber-500/10 border border-amber-500/20">
                        <p className="text-xs text-amber-300">
                          <strong>Environment Variable Required:</strong> This server requires environment
                          variables to be configured. Check the documentation for details.
                        </p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-white/50">Category:</span>
                        <span className="ml-2 text-white/70">{CATEGORIES[server.category]?.label}</span>
                      </div>
                      <div>
                        <span className="text-white/50">Type:</span>
                        <span className="ml-2 text-white/70">External Server</span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Footer */}
      {selectedServers.length > 0 && (
        <div className="p-4 border-t border-white/10 bg-white/[0.02]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white">
                {selectedServers.length} server{selectedServers.length !== 1 ? 's' : ''} enabled
              </p>
              <p className="text-xs text-white/50">
                These MCP servers will be available to the agent
              </p>
            </div>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onServersChange([])}
              className="px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 text-sm font-medium border border-red-500/30 transition-colors"
            >
              Disable All
            </motion.button>
          </div>
        </div>
      )}
    </div>
  );
}

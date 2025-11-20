// MCP Server State Management Store

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import type {
  MCPServerConfig,
  MCPServerMetrics,
  MCPServerHealth,
  MCPServerLog,
  AgentMCPServer,
  MCPServerStore,
  CustomMCPServer,
  MCPAnalytics,
  MCPServerTest,
} from '@/types/mcp';

interface MCPState {
  // Servers
  servers: Record<string, MCPServerConfig>;
  serverMetrics: Record<string, MCPServerMetrics>;
  serverHealth: Record<string, MCPServerHealth>;

  // Logs and Analytics
  logs: Record<string, MCPServerLog[]>;
  analytics: MCPAnalytics | null;

  // Agent Integration
  agentServers: AgentMCPServer[];

  // Store and Custom
  availableServers: MCPServerStore[];
  customServers: CustomMCPServer[];

  // Testing
  tests: Record<string, MCPServerTest[]>;

  // UI State
  selectedServerId: string | null;
  selectedAgentId: string | null;
  isLoading: boolean;
  error: string | null;

  // Filters
  filterCategory: string | null;
  filterStatus: string | null;
  searchQuery: string;
}

interface MCPActions {
  // Server Management
  addServer: (server: MCPServerConfig) => void;
  updateServer: (id: string, updates: Partial<MCPServerConfig>) => void;
  removeServer: (id: string) => void;
  startServer: (id: string) => Promise<void>;
  stopServer: (id: string) => Promise<void>;
  restartServer: (id: string) => Promise<void>;
  testServer: (id: string) => Promise<boolean>;

  // Metrics and Health
  updateMetrics: (serverId: string, metrics: MCPServerMetrics) => void;
  updateHealth: (serverId: string, health: MCPServerHealth) => void;
  addLog: (serverId: string, log: MCPServerLog) => void;

  // Agent Integration
  assignServerToAgent: (serverId: string, agentId: string) => void;
  unassignServerFromAgent: (serverId: string, agentId: string) => void;
  getAgentServers: (agentId: string) => AgentMCPServer[];

  // Store
  loadAvailableServers: () => Promise<void>;
  installServer: (serverId: string) => Promise<void>;
  uninstallServer: (serverId: string) => Promise<void>;

  // Custom Servers
  createCustomServer: (server: CustomMCPServer) => void;
  updateCustomServer: (id: string, updates: Partial<CustomMCPServer>) => void;
  deleteCustomServer: (id: string) => void;

  // Testing
  addTest: (serverId: string, test: MCPServerTest) => void;
  runTest: (serverId: string, testId: string) => Promise<void>;
  runAllTests: (serverId: string) => Promise<void>;

  // Analytics
  loadAnalytics: () => Promise<void>;

  // UI Actions
  setSelectedServer: (id: string | null) => void;
  setSelectedAgent: (id: string | null) => void;
  setFilterCategory: (category: string | null) => void;
  setFilterStatus: (status: string | null) => void;
  setSearchQuery: (query: string) => void;

  // Server management
  exportConfig: () => string;
  importConfig: (config: string) => void;

  // Connection
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
}

export const useMCPStore = create<MCPState & MCPActions>()(
  subscribeWithSelector((set, get) => ({
    // Initial State
    servers: {},
    serverMetrics: {},
    serverHealth: {},
    logs: {},
    analytics: null,
    agentServers: [],
    availableServers: [],
    customServers: [],
    tests: {},
    selectedServerId: null,
    selectedAgentId: null,
    isLoading: false,
    error: null,
    filterCategory: null,
    filterStatus: null,
    searchQuery: '',

    // Server Management Actions
    addServer: (server) => {
      set((state) => ({
        servers: { ...state.servers, [server.id]: server },
      }));
    },

    updateServer: (id, updates) => {
      set((state) => ({
        servers: {
          ...state.servers,
          [id]: { ...state.servers[id], ...updates, updatedAt: new Date() },
        },
      }));
    },

    removeServer: (id) => {
      set((state) => {
        const { [id]: removed, ...rest } = state.servers;
        return { servers: rest };
      });
    },

    async startServer(id) {
      set({ isLoading: true });
      try {
        // API call to start server
        await fetch(`/api/mcp/servers/${id}/start`, { method: 'POST' });
        get().updateServer(id, { status: 'starting' });
      } catch (error) {
        set({ error: `Failed to start server: ${error}` });
      } finally {
        set({ isLoading: false });
      }
    },

    async stopServer(id) {
      set({ isLoading: true });
      try {
        await fetch(`/api/mcp/servers/${id}/stop`, { method: 'POST' });
        get().updateServer(id, { status: 'stopping' });
      } catch (error) {
        set({ error: `Failed to stop server: ${error}` });
      } finally {
        set({ isLoading: false });
      }
    },

    async restartServer(id) {
      set({ isLoading: true });
      try {
        await fetch(`/api/mcp/servers/${id}/restart`, { method: 'POST' });
        get().updateServer(id, { status: 'starting' });
      } catch (error) {
        set({ error: `Failed to restart server: ${error}` });
      } finally {
        set({ isLoading: false });
      }
    },

    async testServer(id) {
      try {
        const response = await fetch(`/api/mcp/servers/${id}/test`);
        const result = await response.json();
        return result.success;
      } catch (error) {
        set({ error: `Failed to test server: ${error}` });
        return false;
      }
    },

    // Metrics and Health
    updateMetrics: (serverId, metrics) => {
      set((state) => ({
        serverMetrics: { ...state.serverMetrics, [serverId]: metrics },
      }));
    },

    updateHealth: (serverId, health) => {
      set((state) => ({
        serverHealth: { ...state.serverHealth, [serverId]: health },
      }));
    },

    addLog: (serverId, log) => {
      set((state) => ({
        logs: {
          ...state.logs,
          [serverId]: [log, ...(state.logs[serverId] || [])].slice(0, 100),
        },
      }));
    },

    // Agent Integration
    assignServerToAgent: (serverId, agentId) => {
      const assignment: AgentMCPServer = {
        agentId,
        agentName: `Agent ${agentId}`,
        serverId,
        serverName: get().servers[serverId]?.name || 'Unknown',
        assignedAt: new Date(),
        usageCount: 0,
      };

      set((state) => ({
        agentServers: [...state.agentServers, assignment],
      }));
    },

    unassignServerFromAgent: (serverId, agentId) => {
      set((state) => ({
        agentServers: state.agentServers.filter(
          (asg) => !(asg.serverId === serverId && asg.agentId === agentId)
        ),
      }));
    },

    getAgentServers: (agentId) => {
      return get().agentServers.filter((asg) => asg.agentId === agentId);
    },

    // Store Actions
    async loadAvailableServers() {
      try {
        const response = await fetch('/api/mcp/store/servers');
        const servers = await response.json();
        set({ availableServers: servers });
      } catch (error) {
        set({ error: `Failed to load servers: ${error}` });
      }
    },

    async installServer(serverId) {
      try {
        await fetch(`/api/mcp/store/install/${serverId}`, { method: 'POST' });
        // Reload available servers after install
        get().loadAvailableServers();
      } catch (error) {
        set({ error: `Failed to install server: ${error}` });
      }
    },

    async uninstallServer(serverId) {
      try {
        await fetch(`/api/mcp/store/uninstall/${serverId}`, { method: 'DELETE' });
        get().removeServer(serverId);
      } catch (error) {
        set({ error: `Failed to uninstall server: ${error}` });
      }
    },

    // Custom Server Actions
    createCustomServer: (server) => {
      set((state) => ({
        customServers: [...state.customServers, server],
      }));
    },

    updateCustomServer: (id, updates) => {
      set((state) => ({
        customServers: state.customServers.map((server) =>
          server.id === id ? { ...server, ...updates, updatedAt: new Date() } : server
        ),
      }));
    },

    deleteCustomServer: (id) => {
      set((state) => ({
        customServers: state.customServers.filter((server) => server.id !== id),
      }));
    },

    // Testing Actions
    addTest: (serverId, test) => {
      set((state) => ({
        tests: {
          ...state.tests,
          [serverId]: [...(state.tests[serverId] || []), test],
        },
      }));
    },

    async runTest(serverId, testId) {
      try {
        const response = await fetch(`/api/mcp/servers/${serverId}/tests/${testId}/run`, {
          method: 'POST',
        });
        const result = await response.json();

        // Update test status
        set((state) => ({
          tests: {
            ...state.tests,
            [serverId]: state.tests[serverId]?.map((test) =>
              test.id === testId ? { ...test, ...result } : test
            ) || [],
          },
        }));
      } catch (error) {
        set({ error: `Failed to run test: ${error}` });
      }
    },

    async runAllTests(serverId) {
      const tests = get().tests[serverId] || [];
      for (const test of tests) {
        await get().runTest(serverId, test.id);
      }
    },

    // Analytics
    async loadAnalytics() {
      try {
        const response = await fetch('/api/mcp/analytics');
        const analytics = await response.json();
        set({ analytics });
      } catch (error) {
        set({ error: `Failed to load analytics: ${error}` });
      }
    },

    // UI Actions
    setSelectedServer: (id) => set({ selectedServerId: id }),
    setSelectedAgent: (id) => set({ selectedAgentId: id }),
    setFilterCategory: (category) => set({ filterCategory: category }),
    setFilterStatus: (status) => set({ filterStatus: status }),
    setSearchQuery: (query) => set({ searchQuery: query }),

    // Import/Export
    exportConfig: () => {
      const state = get();
      return JSON.stringify(
        {
          servers: state.servers,
          customServers: state.customServers,
          tests: state.tests,
        },
        null,
        2
      );
    },

    importConfig: (config) => {
      try {
        const parsed = JSON.parse(config);
        set((state) => ({
          servers: { ...state.servers, ...parsed.servers },
          customServers: [...state.customServers, ...(parsed.customServers || [])],
          tests: { ...state.tests, ...parsed.tests },
        }));
      } catch (error) {
        set({ error: `Failed to import config: ${error}` });
      }
    },

    // WebSocket
    connectWebSocket: () => {
      // Implementation would connect to WebSocket for real-time updates
      console.log('Connecting to MCP WebSocket...');
    },

    disconnectWebSocket: () => {
      // Implementation would disconnect WebSocket
      console.log('Disconnecting from MCP WebSocket...');
    },
  }))
);

// Subscribe to server changes for persistence
useMCPStore.subscribe(
  (state) => state.servers,
  (servers) => {
    // Auto-save to localStorage
    localStorage.setItem('mcp-servers', JSON.stringify(servers));
  }
);

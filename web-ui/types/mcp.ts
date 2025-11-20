// MCP Server Types and Interfaces

export type MCPServerStatus =
  | 'online'
  | 'offline'
  | 'starting'
  | 'stopping'
  | 'error'
  | 'maintenance';

export type MCPServerCategory =
  | 'filesystem'
  | 'github'
  | 'git'
  | 'web'
  | 'database'
  | 'memory'
  | 'ai'
  | 'custom'
  | 'development'
  | 'monitoring';

export type ServerCapability =
  | 'read'
  | 'write'
  | 'delete'
  | 'search'
  | 'analytics'
  | 'real-time'
  | 'batch'
  | 'streaming';

export interface MCPServerConfig {
  id: string;
  name: string;
  description: string;
  category: MCPServerCategory;
  version: string;
  status: MCPServerStatus;

  // Connection
  command: string;
  args?: string[];
  env?: Record<string, string>;
  host?: string;
  port?: number;

  // Authentication
  apiKey?: string;
  apiKeyEncrypted?: boolean;
  authType?: 'none' | 'api-key' | 'oauth' | 'bearer';

  // Settings
  enabled: boolean;
  autoStart: boolean;
  timeout?: number;
  retryAttempts?: number;
  healthCheckInterval?: number;

  // Capabilities
  capabilities: ServerCapability[];
  resources?: Record<string, any>;

  // Metadata
  author?: string;
  license?: string;
  homepage?: string;
  repository?: string;
  tags: string[];

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
  lastStarted?: Date;
  lastHeartbeat?: Date;
}

export interface MCPServerMetrics {
  serverId: string;
  uptime: number;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  avgResponseTime: number;
  lastError?: string;
  memoryUsage?: number;
  cpuUsage?: number;
  activeConnections: number;
  requestsPerSecond: number;
  errorRate: number;
}

export interface MCPServerLog {
  id: string;
  serverId: string;
  timestamp: Date;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  metadata?: Record<string, any>;
}

export interface MCPServerHealth {
  serverId: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  checks: {
    name: string;
    status: 'pass' | 'fail' | 'warn';
    message?: string;
    latency?: number;
  }[];
  lastCheck: Date;
}

export interface AgentMCPServer {
  agentId: string;
  agentName: string;
  serverId: string;
  serverName: string;
  assignedAt: Date;
  lastUsed?: Date;
  usageCount: number;
}

export interface MCPServerStore {
  serverId: string;
  name: string;
  description: string;
  category: MCPServerCategory;
  version: string;
  author: string;
  rating: number;
  downloads: number;
  verified: boolean;
  tags: string[];
  readme?: string;
  screenshots?: string[];
  lastUpdated: Date;
  repository?: string;
  homepage?: string;
}

export interface CustomMCPServer {
  id: string;
  name: string;
  description: string;
  category: MCPServerCategory;
  template: string;
  config: Partial<MCPServerConfig>;
  code?: string;
  testingEnabled: boolean;
  testingResults?: {
    passed: number;
    failed: number;
    total: number;
    lastRun: Date;
  };
  createdAt: Date;
  updatedAt: Date;
}

export interface MCPAnalytics {
  totalServers: number;
  activeServers: number;
  totalRequests: number;
  avgResponseTime: number;
  popularServers: {
    serverId: string;
    name: string;
    requestCount: number;
  }[];
  categories: {
    category: MCPServerCategory;
    count: number;
    active: number;
  }[];
  errors: {
    serverId: string;
    name: string;
    errorCount: number;
    lastError: string;
  }[];
  uptime: {
    serverId: string;
    name: string;
    uptimePercentage: number;
  }[];
}

export interface MCPServerTest {
  id: string;
  serverId: string;
  name: string;
  description?: string;
  command: string;
  expectedOutput?: string;
  timeout?: number;
  enabled: boolean;
  lastRun?: Date;
  status?: 'pending' | 'running' | 'passed' | 'failed';
  output?: string;
  error?: string;
}

export interface MCPServerPreset {
  id: string;
  name: string;
  description: string;
  category: MCPServerCategory;
  servers: MCPServerConfig[];
  tags: string[];
}

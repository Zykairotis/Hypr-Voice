export interface VoiceState {
  isRecording: boolean;
  isActive: boolean;
  isProcessing: boolean;
  audioLevel: number;
  f9Pressed: boolean;
  f10Pressed: boolean;
}

export interface ServerStatus {
  running: boolean;
  pid?: number;
  port?: number;
  uptime?: number;
  memory?: number;
  cpu?: number;
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  source: string;
  metadata?: Record<string, any>;
}

export interface ConfigSection {
  name: string;
  path: string;
  content: string;
  valid: boolean;
  error?: string;
}

export interface Session {
  id: string;
  startTime: Date;
  endTime?: Date;
  duration?: number;
  transcriptions: number;
  characters: number;
  applications: string[];
  status: 'active' | 'completed' | 'error';
}

export interface PerformanceMetrics {
  timestamp: Date;
  cpu: number;
  memory: number;
  disk: number;
  network: {
    inbound: number;
    outbound: number;
  };
  transcriptionLatency: number;
  llmLatency: number;
}

export interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  language: string;
  autoStart: boolean;
  notifications: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  refreshInterval: number;
  maxLogEntries: number;
}

export interface WebSocketMessage {
  type: 'voice_state' | 'server_status' | 'log' | 'session' | 'metrics' | 'error';
  data: any;
  timestamp: Date;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}
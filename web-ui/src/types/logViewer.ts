export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  FATAL = 4
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  level: LogLevel;
  source: string;
  message: string;
  metadata?: Record<string, any>;
  raw?: string;
  sessionId?: string;
  bookmarked?: boolean;
  annotations?: string[];
}

export interface LogFilter {
  levels: LogLevel[];
  sources: string[];
  searchQuery?: string;
  startTime?: Date;
  endTime?: Date;
  sessionId?: string;
}

export interface LogViewerConfig {
  maxEntries: number;
  bufferSize: number;
  updateInterval: number;
  autoScroll: boolean;
  theme: 'light' | 'dark' | 'auto';
  timeZone: string;
  timestampFormat: string;
  enableVirtualScrolling: boolean;
  enablePerformanceMetrics: boolean;
}

export interface PerformanceMetrics {
  totalEntries: number;
  entriesPerSecond: number;
  memoryUsage: number;
  averageProcessingTime: number;
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting' | 'error';
  lastUpdate: Date;
}

export interface Bookmark {
  id: string;
  logId: string;
  timestamp: Date;
  note?: string;
  tags: string[];
}

export interface LogExportOptions {
  format: 'json' | 'csv' | 'txt';
  includeMetadata: boolean;
  dateRange?: {
    start: Date;
    end: Date;
  };
  levels?: LogLevel[];
  sources?: string[];
}

export interface WebSocketMessage {
  type: 'log' | 'metrics' | 'status' | 'error';
  data: any;
  timestamp: Date;
}

export interface VirtualScrollItem {
  index: number;
  entry: LogEntry;
  height: number;
  offset: number;
}

export interface LogViewerState {
  entries: LogEntry[];
  filteredEntries: LogEntry[];
  bookmarks: Bookmark[];
  config: LogViewerConfig;
  filter: LogFilter;
  metrics: PerformanceMetrics;
  isLoading: boolean;
  error?: string;
  searchTerm: string;
  isAutoScrolling: boolean;
  isPaused: boolean;
  selectedItem?: LogEntry;
  visibleRange: { start: number; end: number };
}
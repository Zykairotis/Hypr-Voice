export interface ShellCommand {
  id: string;
  command: string;
  timestamp: number;
  category?: string;
  tags?: string[];
}

export interface ClipboardEntry {
  id: string;
  content: string;
  timestamp: number;
  type: 'text' | 'code' | 'url' | 'file' | 'other';
  category?: string;
}

export interface ActiveWindow {
  class: string;
  title: string;
  pid: number;
  category: string;
  timestamp: number;
}

export interface ApplicationStats {
  name: string;
  category: string;
  usageTime: number;
  usageCount: number;
  lastUsed: number;
  keywords: string[];
}

export interface ContextData {
  shell: {
    commands: ShellCommand[];
    statistics: {
      totalCommands: number;
      uniqueCommands: number;
      mostUsedCommands: Array<{ command: string; count: number }>;
      commandCategories: Record<string, number>;
    };
  };
  clipboard: {
    entries: ClipboardEntry[];
    statistics: {
      totalEntries: number;
      contentTypes: Record<string, number>;
      mostRecentEntries: ClipboardEntry[];
    };
  };
  applications: {
    activeWindow: ActiveWindow | null;
    usageStats: ApplicationStats[];
    history: ActiveWindow[];
  };
}

export interface ContextFilter {
  timeRange?: '1h' | '6h' | '24h' | '7d' | 'all';
  categories?: string[];
  keywords?: string[];
  application?: string;
}

export interface ContextTimelineEvent {
  id: string;
  type: 'command' | 'clipboard' | 'window_change';
  timestamp: number;
  data: any;
}

export interface ContextAnalytics {
  sessionMetrics: {
    totalCommands: number;
    totalClipboardEntries: number;
    activeTime: number;
    mostProductiveHour: number;
  };
  keywordFrequency: Array<{ keyword: string; count: number; sources: string[] }>;
  applicationUsage: Array<{ name: string; timeSpent: number; category: string }>;
  commandPatterns: Array<{ pattern: string; frequency: number }>;
  contextEffectiveness: {
    score: number;
    contributingFactors: string[];
  };
}

export interface ContextState {
  data: ContextData | null;
  loading: boolean;
  error: string | null;
  lastUpdate: number;
  filters: ContextFilter;
  realtimeEnabled: boolean;
}

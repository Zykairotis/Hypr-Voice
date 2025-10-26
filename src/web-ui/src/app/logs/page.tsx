'use client';

import { useState, useEffect, useRef } from 'react';
import { LogViewer } from '@/components/log-viewer';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LogEntry } from '@/types';
import {
  FileText,
  Download,
  Trash2,
  RefreshCw,
  Search,
  Filter,
  CheckCircle,
  AlertTriangle,
  Pause,
  Play,
  Settings,
  Activity
} from 'lucide-react';

// Mock log data for development
const generateMockLogs = (): LogEntry[] => {
  const sources = ['server', 'websocket', 'audio', 'transcription', 'llm', 'clipboard', 'hyprland'];
  const levels: LogEntry['level'][] = ['debug', 'info', 'warn', 'error'];
  const messages = [
    'Hypr-Voice server started successfully',
    'WebSocket connection established from client',
    'Audio device initialized: USB Microphone',
    'Voice activity detected - starting transcription',
    'Transcription completed: "Hello world"',
    'Text pasted to active window',
    'Application detected: kitty',
    'Memory usage: 256MB',
    'Processing latency: 1.2s',
    'Configuration loaded from audio_config.yaml',
    'API request sent to LLM provider',
    'Response received from xAI Grok',
    'Text enhancement applied',
    'Voice input buffer cleared',
    'System check completed successfully',
    'Audio level monitoring started',
    'VAD parameters updated',
    'Session metrics saved',
  ];

  return Array.from({ length: 50 }, (_, i) => {
    const timestamp = new Date(Date.now() - i * 30000); // 30 seconds apart
    const level = levels[Math.floor(Math.random() * levels.length)];
    const source = sources[Math.floor(Math.random() * sources.length)];
    const message = messages[Math.floor(Math.random() * messages.length)];

    return {
      id: `log-${Date.now()}-${i}`,
      timestamp,
      level,
      message: `${message} (${timestamp.toLocaleTimeString()})`,
      source,
      metadata: i % 5 === 0 ? {
        latency: Math.random() * 2000,
        memory: Math.floor(Math.random() * 500),
        details: 'Additional context information'
      } : undefined,
    };
  });
};

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>(generateMockLogs());
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>(logs);
  const [isLive, setIsLive] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevel, setSelectedLevel] = useState<string>('all');
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [notification, setNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);

  const logContainerRef = useRef<HTMLDivElement>(null);

  // Get unique sources for filter
  const sources = Array.from(new Set(logs.map(log => log.source))).sort();

  // Simulate real-time log updates
  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      const newLog: LogEntry = {
        id: `log-${Date.now()}`,
        timestamp: new Date(),
        level: Math.random() > 0.7 ? 'info' : Math.random() > 0.5 ? 'debug' : 'warn',
        message: `Real-time log entry at ${new Date().toLocaleTimeString()}`,
        source: ['server', 'websocket', 'audio', 'transcription'][Math.floor(Math.random() * 4)],
        metadata: Math.random() > 0.8 ? {
          realTime: true,
          sessionId: 'session-' + Math.floor(Math.random() * 1000),
        } : undefined,
      };

      setLogs(prev => [newLog, ...prev.slice(0, 999)]);
    }, 2000);

    return () => clearInterval(interval);
  }, [isLive]);

  // Filter logs based on search and filters
  useEffect(() => {
    let filtered = logs;

    if (searchTerm) {
      filtered = filtered.filter(log =>
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.source.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedLevel !== 'all') {
      filtered = filtered.filter(log => log.level === selectedLevel);
    }

    if (selectedSource !== 'all') {
      filtered = filtered.filter(log => log.source === selectedSource);
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, selectedLevel, selectedSource]);

  const handleClearLogs = () => {
    setLogs([]);
    setFilteredLogs([]);
    showNotification('info', 'All logs cleared');
  };

  const handleExportLogs = () => {
    const logText = filteredLogs
      .map(log => `[${log.timestamp.toISOString()}] [${log.level.toUpperCase()}] [${log.source}] ${log.message}`)
      .join('\n');

    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hypr-voice-logs-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showNotification('success', 'Logs exported successfully');
  };

  const handleRefreshLogs = () => {
    setLogs(generateMockLogs());
    showNotification('info', 'Logs refreshed');
  };

  const showNotification = (type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 3000);
  };

  const getLogStats = () => {
    const total = filteredLogs.length;
    const byLevel = {
      debug: filteredLogs.filter(l => l.level === 'debug').length,
      info: filteredLogs.filter(l => l.level === 'info').length,
      warn: filteredLogs.filter(l => l.level === 'warn').length,
      error: filteredLogs.filter(l => l.level === 'error').length,
    };

    return { total, byLevel };
  };

  const stats = getLogStats();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Logs</h1>
          <p className="text-muted-foreground">
            Real-time system logs and event monitoring
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isLive ? "default" : "secondary"} className="flex items-center gap-1">
            <div className={cn(
              "w-2 h-2 rounded-full",
              isLive ? "bg-green-500 animate-pulse" : "bg-gray-500"
            )} />
            {isLive ? "Live" : "Paused"}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsLive(!isLive)}
            className="flex items-center gap-2"
          >
            {isLive ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {isLive ? "Pause" : "Resume"}
          </Button>
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <Alert className={cn(
          notification.type === 'success' && "border-green-200 bg-green-50 dark:bg-green-950/20",
          notification.type === 'error' && "border-red-200 bg-red-50 dark:bg-red-950/20",
          notification.type === 'info' && "border-blue-200 bg-blue-50 dark:bg-blue-950/20"
        )}>
          <div className="flex items-center gap-2">
            {notification.type === 'success' && <CheckCircle className="h-4 w-4 text-green-600" />}
            {notification.type === 'error' && <AlertTriangle className="h-4 w-4 text-red-600" />}
            {notification.type === 'info' && <Activity className="h-4 w-4 text-blue-600" />}
            <AlertDescription>{notification.message}</AlertDescription>
          </div>
        </Alert>
      )}

      {/* Log Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Logs</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">
              {isLive ? 'Live streaming' : 'Paused'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Info</CardTitle>
            <div className="w-3 h-3 bg-green-500 rounded-full" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.byLevel.info}</div>
            <p className="text-xs text-muted-foreground">
              {stats.total > 0 ? `${((stats.byLevel.info / stats.total) * 100).toFixed(0)}%` : '0%'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Warnings</CardTitle>
            <div className="w-3 h-3 bg-yellow-500 rounded-full" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.byLevel.warn}</div>
            <p className="text-xs text-muted-foreground">
              {stats.total > 0 ? `${((stats.byLevel.warn / stats.total) * 100).toFixed(0)}%` : '0%'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Errors</CardTitle>
            <div className="w-3 h-3 bg-red-500 rounded-full" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.byLevel.error}</div>
            <p className="text-xs text-muted-foreground">
              {stats.total > 0 ? `${((stats.byLevel.error / stats.total) * 100).toFixed(0)}%` : '0%'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Debug</CardTitle>
            <div className="w-3 h-3 bg-blue-500 rounded-full" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.byLevel.debug}</div>
            <p className="text-xs text-muted-foreground">
              {stats.total > 0 ? `${((stats.byLevel.debug / stats.total) * 100).toFixed(0)}%` : '0%'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Log Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Log Controls
          </CardTitle>
          <CardDescription>
            Filter, search, and manage log entries
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search logs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background text-sm"
            >
              <option value="all">All Levels</option>
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warn">Warning</option>
              <option value="error">Error</option>
            </select>

            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background text-sm"
            >
              <option value="all">All Sources</option>
              {sources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefreshLogs}
                className="flex items-center gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={handleExportLogs}
                className="flex items-center gap-2"
              >
                <Download className="h-4 w-4" />
                Export
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={handleClearLogs}
                className="flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Log Viewer */}
      <div ref={logContainerRef}>
        <LogViewer
          logs={filteredLogs}
          onClearLogs={handleClearLogs}
        />
      </div>
    </div>
  );
}

// Helper function for className conditional styling
function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
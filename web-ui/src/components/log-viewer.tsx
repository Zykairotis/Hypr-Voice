'use client';

import { useState, useMemo, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { LogEntry } from '@/types';
import {
  Trash2,
  Download,
  Search,
  Filter,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  Info,
  AlertTriangle,
  XCircle,
  CheckCircle
} from 'lucide-react';
import { cn, formatDate } from '@/lib/utils';

interface LogViewerProps {
  logs: LogEntry[];
  onClearLogs?: () => void;
  className?: string;
}

const LOG_LEVELS = {
  debug: { icon: Info, color: 'text-blue-600', bgColor: 'bg-blue-50' },
  info: { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-50' },
  warn: { icon: AlertTriangle, color: 'text-yellow-600', bgColor: 'bg-yellow-50' },
  error: { icon: XCircle, color: 'text-red-600', bgColor: 'bg-red-50' },
} as const;

export function LogViewer({ logs, onClearLogs, className }: LogViewerProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevel, setSelectedLevel] = useState<string>('all');
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [expandedEntries, setExpandedEntries] = useState<Set<string>>(new Set());
  const [autoScroll, setAutoScroll] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Get unique sources for filter
  const sources = useMemo(() => {
    const uniqueSources = new Set(logs.map(log => log.source));
    return Array.from(uniqueSources).sort();
  }, [logs]);

  // Filter logs based on search and filters
  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      const matchesSearch = searchTerm === '' ||
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.source.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesLevel = selectedLevel === 'all' || log.level === selectedLevel;
      const matchesSource = selectedSource === 'all' || log.source === selectedSource;

      return matchesSearch && matchesLevel && matchesSource;
    });
  }, [logs, searchTerm, selectedLevel, selectedSource]);

  // Auto scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredLogs.length, autoScroll]);

  const toggleEntryExpanded = (id: string) => {
    setExpandedEntries(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const exportLogs = () => {
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
  };

  const getLogLevelIcon = (level: LogEntry['level']) => {
    const config = LOG_LEVELS[level];
    const Icon = config.icon;
    return <Icon className="h-4 w-4" />;
  };

  const getLogLevelColor = (level: LogEntry['level']) => {
    return LOG_LEVELS[level].color;
  };

  const getLogLevelBgColor = (level: LogEntry['level']) => {
    return LOG_LEVELS[level].bgColor;
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Log Viewer
            </CardTitle>
            <CardDescription>
              Real-time system logs and events
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {filteredLogs.length} / {logs.length} entries
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoScroll(!autoScroll)}
              className={cn(autoScroll && "bg-primary text-primary-foreground")}
            >
              Auto-scroll
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={exportLogs}
              disabled={filteredLogs.length === 0}
            >
              <Download className="h-4 w-4 mr-1" />
              Export
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onClearLogs}
            >
              <Trash2 className="h-4 w-4 mr-1" />
              Clear
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            className="px-3 py-2 border rounded-md bg-background text-sm"
          >
            <option value="all">All Levels</option>
            {Object.keys(LOG_LEVELS).map(level => (
              <option key={level} value={level}>{level.toUpperCase()}</option>
            ))}
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
        </div>

        {/* Log Entries */}
        <div className="border rounded-lg overflow-hidden">
          <div className="max-h-96 overflow-y-auto">
            {filteredLogs.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No logs to display</p>
              </div>
            ) : (
              <div className="space-y-0">
                {filteredLogs.map((log) => (
                  <div
                    key={log.id}
                    className={cn(
                      "border-b last:border-b-0 hover:bg-muted/50 transition-colors",
                      getLogLevelBgColor(log.level)
                    )}
                  >
                    <div className="p-3">
                      <div className="flex items-start gap-3">
                        <div className={cn("mt-0.5", getLogLevelColor(log.level))}>
                          {getLogLevelIcon(log.level)}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline" className="text-xs">
                              {log.level.toUpperCase()}
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {log.source}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {formatDate(log.timestamp)}
                            </span>
                          </div>

                          <div className="text-sm">{log.message}</div>

                          {log.metadata && Object.keys(log.metadata).length > 0 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleEntryExpanded(log.id)}
                              className="mt-2 h-auto p-0 text-xs"
                            >
                              {expandedEntries.has(log.id) ? (
                                <ChevronDown className="h-3 w-3 mr-1" />
                              ) : (
                                <ChevronRight className="h-3 w-3 mr-1" />
                              )}
                              {expandedEntries.has(log.id) ? 'Hide' : 'Show'} Details
                            </Button>
                          )}
                        </div>
                      </div>

                      {expandedEntries.has(log.id) && log.metadata && (
                        <div className="mt-3 ml-8 p-3 bg-background rounded border">
                          <pre className="text-xs overflow-x-auto">
                            {JSON.stringify(log.metadata, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div ref={bottomRef} />
        </div>
      </CardContent>
    </Card>
  );
}
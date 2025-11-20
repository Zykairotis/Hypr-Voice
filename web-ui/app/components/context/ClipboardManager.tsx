'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Switch } from '@/components/ui/switch';
import {
  Clipboard,
  Search,
  Copy,
  Trash2,
  Shield,
  Eye,
  EyeOff,
  Download,
  Filter,
  Clock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { ClipboardEntry } from './types';

interface ClipboardManagerProps {
  entries: ClipboardEntry[];
  statistics: any;
  onCopy?: (entry: ClipboardEntry) => void;
  onClear?: () => void;
  onSearch?: (query: string) => void;
  loading?: boolean;
}

export function ClipboardManager({
  entries,
  statistics,
  onCopy,
  onClear,
  onSearch,
  loading = false
}: ClipboardManagerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showSensitive, setShowSensitive] = useState(false);
  const [selectedType, setSelectedType] = useState<string>('all');

  const filteredEntries = entries.filter(entry => {
    const matchesSearch = !searchQuery ||
      entry.content.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === 'all' || entry.type === selectedType;
    return matchesSearch && matchesType;
  });

  const handleCopy = async (entry: ClipboardEntry) => {
    try {
      await navigator.clipboard.writeText(entry.content);
      onCopy?.(entry);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleExport = () => {
    const data = JSON.stringify(entries, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `clipboard-history-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'code': return '💻';
      case 'url': return '🔗';
      case 'file': return '📄';
      default: return '📝';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'code': return 'bg-blue-500/20 text-blue-400';
      case 'url': return 'bg-green-500/20 text-green-400';
      case 'file': return 'bg-purple-500/20 text-purple-400';
      case 'text': return 'bg-gray-500/20 text-gray-400';
      default: return 'bg-orange-500/20 text-orange-400';
    }
  };

  const isLikelySensitive = (content: string): boolean => {
    const patterns = [
      /password/i,
      /api[_-]?key/i,
      /secret/i,
      /token/i,
      /credential/i,
      /\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}/, // Credit cards
      /[\w.-]+@[\w.-]+\.\w+/, // Emails
    ];
    return patterns.some(pattern => pattern.test(content));
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Clipboard className="w-5 h-5 text-primary" />
              Clipboard Manager
            </CardTitle>
            <CardDescription>
              Clipboard history viewer with privacy controls (last 50 entries)
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={handleExport}
              title="Export history"
            >
              <Download className="w-4 h-4" />
            </Button>
            {onClear && (
              <Button
                variant="outline"
                size="icon"
                onClick={onClear}
                title="Clear clipboard"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col space-y-4">
        {/* Privacy Controls */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-green-500" />
            <span className="text-sm font-medium">Privacy Mode</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Show sensitive</span>
            <Switch
              checked={showSensitive}
              onCheckedChange={setShowSensitive}
            />
          </div>
        </div>

        {/* Search and Filter Controls */}
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              placeholder="Search clipboard content..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                onSearch?.(e.target.value);
              }}
              className="pl-10"
            />
          </div>

          <div className="flex gap-2 items-center">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-3 py-1.5 text-sm border rounded-md bg-background"
            >
              <option value="all">All Types</option>
              <option value="text">Text</option>
              <option value="code">Code</option>
              <option value="url">URL</option>
              <option value="file">File</option>
            </select>

            <div className="flex items-center gap-2 text-sm text-muted-foreground ml-auto">
              <Clock className="w-4 h-4" />
              {filteredEntries.length} entries
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          {Object.entries(statistics.contentTypes || {}).map(([type, count]) => (
            <div key={type} className="flex items-center justify-between p-2 bg-muted/30 rounded">
              <span className="flex items-center gap-1">
                {getTypeIcon(type)} {type}
              </span>
              <Badge variant="outline">{count as number}</Badge>
            </div>
          ))}
        </div>

        {/* Clipboard Entries */}
        <ScrollArea className="flex-1">
          <div className="space-y-2">
            <AnimatePresence>
              {filteredEntries.map((entry, index) => {
                const sensitive = isLikelySensitive(entry.content);
                const maskedContent = sensitive && !showSensitive
                  ? '•'.repeat(Math.min(entry.content.length, 50))
                  : entry.content;

                return (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ delay: index * 0.02 }}
                    className="group p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm break-all">
                          {maskedContent}
                          {sensitive && !showSensitive && (
                            <span className="ml-2 inline-flex items-center gap-1 text-xs text-amber-500">
                              <EyeOff className="w-3 h-3" />
                              Sensitive
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline" className={`text-xs ${getTypeColor(entry.type)}`}>
                            {getTypeIcon(entry.type)} {entry.type}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {new Date(entry.timestamp * 1000).toLocaleString()}
                          </Badge>
                          {sensitive && (
                            <Badge variant="outline" className="text-xs text-amber-500 border-amber-500">
                              <Shield className="w-3 h-3 mr-1" />
                              Sensitive
                            </Badge>
                          )}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleCopy(entry)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Copy to clipboard"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {filteredEntries.length === 0 && !loading && (
              <div className="text-center py-8 text-muted-foreground">
                No clipboard entries found
              </div>
            )}

            {loading && (
              <div className="text-center py-8">
                <div className="animate-pulse space-y-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-16 bg-muted rounded-lg" />
                  ))}
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

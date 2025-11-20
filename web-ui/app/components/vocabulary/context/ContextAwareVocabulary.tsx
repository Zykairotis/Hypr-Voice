'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { RefreshCw, Terminal, Clipboard, Hash, Clock } from 'lucide-react';
import { ContextData } from '@/lib/vocabulary/types';
import { vocabularyAPI } from '@/lib/vocabulary/api';
import { vocabularyWS } from '@/lib/vocabulary/websocket';

export function ContextAwareVocabulary() {
  const [contextData, setContextData] = useState<ContextData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<number>(Date.now());

  useEffect(() => {
    loadContext();

    // Subscribe to context updates
    vocabularyWS.on('context_update', (update) => {
      setContextData(update.payload);
      setLastUpdate(Date.now());
    });

    // Periodic refresh
    const interval = setInterval(loadContext, 10000);

    return () => {
      clearInterval(interval);
      vocabularyWS.off('context_update', () => {});
    };
  }, []);

  const loadContext = async () => {
    try {
      const data = await vocabularyAPI.getCurrentContext();
      setContextData(data);
      setLastUpdate(Date.now());
    } catch (error) {
      console.error('Failed to load context:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    loadContext();
  };

  if (loading && !contextData) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!contextData) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No context data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Context-Aware Vocabulary</h2>
          <p className="text-muted-foreground">
            Keywords extracted from shell history and clipboard
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-muted-foreground">
            Last update: {new Date(lastUpdate).toLocaleTimeString()}
          </div>
          <Button onClick={handleRefresh} disabled={loading} variant="outline" size="icon">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Terminal className="h-5 w-5" />
              Shell History Keywords
            </CardTitle>
            <CardDescription>
              Keywords extracted from recent shell commands
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span>Recent Commands</span>
              <Badge variant="secondary">
                {contextData.context.shell.command_count}
              </Badge>
            </div>
            <Separator />
            <ScrollArea className="h-[200px] pr-4">
              <div className="space-y-2">
                {contextData.context.shell.recent_commands.slice(0, 10).map((command, index) => (
                  <div key={index} className="p-2 bg-muted rounded text-sm font-mono">
                    {command}
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clipboard className="h-5 w-5" />
              Clipboard History
            </CardTitle>
            <CardDescription>
              Keywords extracted from clipboard entries
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span>Recent Entries</span>
              <Badge variant="secondary">
                {contextData.context.clipboard.entry_count}
              </Badge>
            </div>
            <Separator />
            <ScrollArea className="h-[200px] pr-4">
              <div className="space-y-2">
                {contextData.context.clipboard.recent_entries.map((entry, index) => (
                  <div key={index} className="p-2 bg-muted rounded text-sm break-all">
                    {entry}
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {contextData.context.window && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Hash className="h-5 w-5" />
              Window Context
            </CardTitle>
            <CardDescription>
              Keywords extracted from active window information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium">Application</p>
                <p className="text-sm text-muted-foreground">
                  {contextData.context.window.application}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium">Title</p>
                <p className="text-sm text-muted-foreground">
                  {contextData.context.window.title}
                </p>
              </div>
            </div>
            {contextData.context.window.metadata && (
              <div>
                <p className="text-sm font-medium mb-2">Metadata</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {Object.entries(contextData.context.window.metadata).map(([key, value]) => (
                    <div key={key}>
                      <span className="font-medium">{key}:</span>{' '}
                      <span className="text-muted-foreground">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Extracted Vocabulary</CardTitle>
          <CardDescription>
            Technical terms and keywords extracted from all context sources
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {contextData.vocabulary.length > 0 ? (
              contextData.vocabulary.map((word, index) => (
                <Badge key={index} variant="outline" className="font-mono">
                  {word}
                </Badge>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">
                No vocabulary extracted yet. Try using different applications or commands.
              </p>
            )}
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            <Clock className="inline h-4 w-4 mr-1" />
            Last extracted: {new Date(contextData.context.shell.timestamp).toLocaleString()}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

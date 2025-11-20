'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Activity,
  Brain,
  TrendingUp,
  Clock,
  Zap,
  RefreshCw,
  Download,
  Settings
} from 'lucide-react';
import { motion } from 'framer-motion';
import { useContextData } from './hooks/useContextData';
import { ShellHistoryManager } from './ShellHistoryManager';
import { ClipboardManager } from './ClipboardManager';
import { ApplicationDetector } from './ApplicationDetector';
import { ContextTimeline } from './visualization/ContextTimeline';
import { ContextAnalyticsPanel } from './analytics/ContextAnalyticsPanel';

export function ContextDashboard() {
  const {
    data,
    loading,
    error,
    lastUpdate,
    fetchContextData,
    clearContext,
    exportContext
  } = useContextData();

  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 seconds

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchContextData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchContextData]);

  const handleExport = () => {
    exportContext('json');
  };

  const getContextStrength = (): number => {
    if (!data) return 0;

    let score = 0;
    // Shell commands contribute 30%
    score += Math.min(data.shell.commands.length / 50, 1) * 30;
    // Clipboard entries contribute 20%
    score += Math.min(data.clipboard.entries.length / 30, 1) * 20;
    // Active window contributes 25%
    score += data.applications.activeWindow ? 25 : 0;
    // Application history contributes 25%
    score += Math.min(data.applications.history.length / 20, 1) * 25;

    return Math.min(score, 100);
  };

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center text-red-500">
          <p className="font-semibold">Error loading context</p>
          <p className="text-sm mt-1">{error}</p>
          <Button onClick={fetchContextData} className="mt-4">
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Context Manager Dashboard</h2>
          <p className="text-muted-foreground">
            Real-time context from shell history, clipboard, and application detection
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? 'bg-primary/10' : ''}
          >
            <Activity className={`w-4 h-4 mr-2 ${autoRefresh ? 'animate-pulse' : ''}`} />
            Auto-refresh
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" onClick={clearContext}>
            Clear
          </Button>
          <Button variant="outline" onClick={fetchContextData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Context Strength Indicator */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-primary" />
                  <div>
                    <h3 className="font-semibold">Context Strength</h3>
                    <p className="text-sm text-muted-foreground">
                      Overall context quality for transcription
                    </p>
                  </div>
                </div>
                <Badge variant={getContextStrength() > 70 ? 'default' : 'secondary'}>
                  {getContextStrength().toFixed(0)}%
                </Badge>
              </div>
              <Progress value={getContextStrength()} className="h-3" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Shell commands</span>
                  <div className="font-semibold">{data?.shell.commands.length || 0}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Clipboard entries</span>
                  <div className="font-semibold">{data?.clipboard.entries.length || 0}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Active app</span>
                  <div className="font-semibold">{data?.applications.activeWindow?.class || 'None'}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Last update</span>
                  <div className="font-semibold">
                    {new Date(lastUpdate).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Dashboard */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="shell">Shell History</TabsTrigger>
          <TabsTrigger value="clipboard">Clipboard</TabsTrigger>
          <TabsTrigger value="applications">Applications</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <ShellHistoryManager
              commands={data?.shell.commands || []}
              statistics={data?.shell.statistics || {}}
              loading={loading}
            />
            <ClipboardManager
              entries={data?.clipboard.entries || []}
              statistics={data?.clipboard.statistics || {}}
              loading={loading}
            />
          </div>
          <ApplicationDetector
            activeWindow={data?.applications.activeWindow || null}
            usageStats={data?.applications.usageStats || []}
            history={data?.applications.history || []}
          />
        </TabsContent>

        <TabsContent value="shell">
          <ShellHistoryManager
            commands={data?.shell.commands || []}
            statistics={data?.shell.statistics || {}}
            onClear={clearContext}
            loading={loading}
          />
        </TabsContent>

        <TabsContent value="clipboard">
          <ClipboardManager
            entries={data?.clipboard.entries || []}
            statistics={data?.clipboard.statistics || {}}
            onClear={clearContext}
            loading={loading}
          />
        </TabsContent>

        <TabsContent value="applications">
          <ApplicationDetector
            activeWindow={data?.applications.activeWindow || null}
            usageStats={data?.applications.usageStats || []}
            history={data?.applications.history || []}
          />
        </TabsContent>

        <TabsContent value="timeline">
          <ContextTimeline data={data} />
        </TabsContent>

        <TabsContent value="analytics">
          <ContextAnalyticsPanel data={data} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BarChart,
  TrendingUp,
  Target,
  Activity,
  Clock,
  Hash,
  Brain,
  Zap,
  Award,
  AlertCircle
} from 'lucide-react';
import { motion } from 'framer-motion';
import { ContextData } from '../types';

interface ContextAnalyticsPanelProps {
  data: ContextData | null;
}

export function ContextAnalyticsPanel({ data }: ContextAnalyticsPanelProps) {
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');

  if (!data) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8 text-muted-foreground">
            No analytics data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate analytics
  const analytics = calculateAnalytics(data);

  return (
    <div className="space-y-6">
      {/* Header with Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Commands</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.sessionMetrics.totalCommands}</div>
            <p className="text-xs text-muted-foreground">
              {analytics.sessionMetrics.totalCommands > 0 ? 'Active session' : 'No activity'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatDuration(analytics.sessionMetrics.activeTime)}
            </div>
            <p className="text-xs text-muted-foreground">Tracked this session</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Context Score</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.contextEffectiveness.score}%</div>
            <Progress value={analytics.contextEffectiveness.score} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Peak Hour</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.sessionMetrics.mostProductiveHour}:00</div>
            <p className="text-xs text-muted-foreground">Most activity</p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      <Tabs defaultValue="keywords" className="space-y-4">
        <TabsList>
          <TabsTrigger value="keywords">Keyword Frequency</TabsTrigger>
          <TabsTrigger value="patterns">Command Patterns</TabsTrigger>
          <TabsTrigger value="applications">App Usage</TabsTrigger>
          <TabsTrigger value="effectiveness">Effectiveness</TabsTrigger>
        </TabsList>

        <TabsContent value="keywords" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Hash className="w-4 h-4" />
                Most Frequent Keywords
              </CardTitle>
              <CardDescription>
                Keywords extracted from commands, clipboard, and applications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {analytics.keywordFrequency.length > 0 ? (
                    analytics.keywordFrequency.slice(0, 20).map((item, index) => (
                      <motion.div
                        key={item.keyword}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.02 }}
                        className="space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="font-mono">
                              {item.keyword}
                            </Badge>
                            <span className="text-sm text-muted-foreground">
                              {item.count} occurrences
                            </span>
                          </div>
                          <div className="flex gap-1">
                            {item.sources.map((source) => (
                              <Badge
                                key={source}
                                variant="secondary"
                                className="text-xs"
                              >
                                {source}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <Progress
                          value={(item.count / analytics.keywordFrequency[0].count) * 100}
                          className="h-1.5"
                        />
                      </motion.div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No keywords extracted yet
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="patterns" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Command Patterns</CardTitle>
                <CardDescription>
                  Most frequently used command patterns
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analytics.commandPatterns.length > 0 ? (
                    analytics.commandPatterns.slice(0, 10).map((pattern, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <span className="font-mono text-sm">{pattern.pattern}</span>
                        <Badge variant="secondary">{pattern.frequency}</Badge>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-4 text-sm text-muted-foreground">
                      No patterns detected
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Command Categories</CardTitle>
                <CardDescription>
                  Distribution of command types
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(data.shell.statistics.commandCategories || {}).map(([category, count]) => (
                    <div key={category} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span>{category}</span>
                        <Badge variant="outline">{count}</Badge>
                      </div>
                      <Progress
                        value={(count as number / data.shell.statistics.totalCommands) * 100}
                        className="h-1.5"
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="applications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Application Usage Over Time</CardTitle>
              <CardDescription>
                Time spent in different applications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {analytics.applicationUsage.length > 0 ? (
                    analytics.applicationUsage.slice(0, 15).map((app, index) => (
                      <motion.div
                        key={app.name}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.02 }}
                        className="flex items-center justify-between p-3 rounded-lg border"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{getCategoryIcon(app.category)}</span>
                          <div>
                            <div className="font-semibold">{app.name}</div>
                            <div className="text-xs text-muted-foreground">{app.category}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold">{formatDuration(app.timeSpent)}</div>
                          <div className="text-xs text-muted-foreground">
                            {((app.timeSpent / analytics.applicationUsage.reduce((sum, a) => sum + a.timeSpent, 0)) * 100).toFixed(1)}%
                          </div>
                        </div>
                      </motion.div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No application data available
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="effectiveness" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Context Effectiveness Score
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-6xl font-bold mb-2">
                    {analytics.contextEffectiveness.score}%
                  </div>
                  <Badge variant={analytics.contextEffectiveness.score > 70 ? 'default' : 'secondary'}>
                    {analytics.contextEffectiveness.score > 70 ? 'Excellent' : 'Needs Improvement'}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <div className="text-sm font-medium">Contributing Factors:</div>
                  {analytics.contextEffectiveness.contributingFactors.map((factor, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                      <Award className="w-3 h-3 text-green-500" />
                      <span>{factor}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {getRecommendations(analytics).map((rec, index) => (
                  <div key={index} className="flex items-start gap-2 text-sm p-3 rounded-lg bg-muted/50">
                    <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                    <span>{rec}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Helper functions
function calculateAnalytics(data: ContextData) {
  // Calculate session metrics
  const allTimestamps = [
    ...data.shell.commands.map(c => c.timestamp),
    ...data.clipboard.entries.map(e => e.timestamp),
    ...data.applications.history.map(w => w.timestamp)
  ].sort((a, b) => a - b);

  const activeTime = allTimestamps.length > 0
    ? allTimestamps[allTimestamps.length - 1] - allTimestamps[0]
    : 0;

  // Calculate most productive hour
  const hourCounts = Array(24).fill(0);
  allTimestamps.forEach(ts => {
    const hour = new Date(ts * 1000).getHours();
    hourCounts[hour]++;
  });
  const mostProductiveHour = hourCounts.indexOf(Math.max(...hourCounts));

  // Calculate keyword frequency
  const keywordFreq: Record<string, { count: number; sources: Set<string> }> = {};

  data.shell.commands.forEach(cmd => {
    const keywords = extractKeywords(cmd.command);
    keywords.forEach(keyword => {
      if (!keywordFreq[keyword]) {
        keywordFreq[keyword] = { count: 0, sources: new Set() };
      }
      keywordFreq[keyword].count++;
      keywordFreq[keyword].sources.add('shell');
    });
  });

  data.clipboard.entries.forEach(entry => {
    const keywords = extractKeywords(entry.content);
    keywords.forEach(keyword => {
      if (!keywordFreq[keyword]) {
        keywordFreq[keyword] = { count: 0, sources: new Set() };
      }
      keywordFreq[keyword].count++;
      keywordFreq[keyword].sources.add('clipboard');
    });
  });

  if (data.applications.activeWindow) {
    const keywords = extractKeywords(data.applications.activeWindow.title + ' ' + data.applications.activeWindow.class);
    keywords.forEach(keyword => {
      if (!keywordFreq[keyword]) {
        keywordFreq[keyword] = { count: 0, sources: new Set() };
      }
      keywordFreq[keyword].count++;
      keywordFreq[keyword].sources.add('application');
    });
  }

  // Calculate command patterns
  const patterns: Record<string, number> = {};
  data.shell.commands.forEach(cmd => {
    const firstWord = cmd.command.split(' ')[0];
    patterns[firstWord] = (patterns[firstWord] || 0) + 1;
  });

  // Calculate application usage
  const appUsage: Record<string, number> = {};
  data.applications.usageStats.forEach(app => {
    appUsage[app.name] = (appUsage[app.name] || 0) + app.usageTime;
  });

  // Calculate context effectiveness score
  let score = 0;
  const factors: string[] = [];

  if (data.shell.commands.length > 20) {
    score += 25;
    factors.push('Rich shell history');
  }
  if (data.clipboard.entries.length > 10) {
    score += 20;
    factors.push('Active clipboard usage');
  }
  if (data.applications.activeWindow) {
    score += 25;
    factors.push('Application context detected');
  }
  if (Object.keys(keywordFreq).length > 30) {
    score += 20;
    factors.push('Extensive keyword vocabulary');
  }
  if (activeTime > 3600) {
    score += 10;
    factors.push('Long session duration');
  }

  return {
    sessionMetrics: {
      totalCommands: data.shell.commands.length,
      totalClipboardEntries: data.clipboard.entries.length,
      activeTime,
      mostProductiveHour,
    },
    keywordFrequency: Object.entries(keywordFreq)
      .map(([keyword, data]) => ({
        keyword,
        count: data.count,
        sources: Array.from(data.sources),
      }))
      .sort((a, b) => b.count - a.count),
    commandPatterns: Object.entries(patterns)
      .map(([pattern, frequency]) => ({ pattern, frequency }))
      .sort((a, b) => b.frequency - a.frequency),
    applicationUsage: data.applications.usageStats
      .map(app => ({
        name: app.name,
        timeSpent: app.usageTime,
        category: app.category,
      }))
      .sort((a, b) => b.timeSpent - a.timeSpent),
    contextEffectiveness: {
      score,
      contributingFactors: factors,
    },
  };
}

function extractKeywords(text: string): string[] {
  const keywords = new Set<string>();

  // Extract CamelCase words
  const camelCaseMatches = text.match(/[A-Z][a-z]+(?:[A-Z][a-z]+)+/g) || [];
  camelCaseMatches.forEach(match => {
    if (match.length > 3) keywords.add(match);
  });

  // Extract file extensions
  const extMatches = text.match(/\b\w+\.\w+\b/g) || [];
  extMatches.forEach(match => keywords.add(match));

  // Extract paths
  const pathMatches = text.match(/\/[^\s]+/g) || [];
  pathMatches.forEach(match => {
    const parts = match.split('/');
    parts.forEach(part => {
      if (part.length > 3 && !part.includes('.')) {
        keywords.add(part);
      }
    });
  });

  return Array.from(keywords);
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    development: '💻',
    browser: '🌐',
    terminal: '⌨️',
    editor: '📝',
    communication: '💬',
    media: '🎵',
    system: '⚙️',
    other: '📱',
  };
  return icons[category] || icons.other;
}

function getRecommendations(analytics: any): string[] {
  const recommendations: string[] = [];

  if (analytics.sessionMetrics.totalCommands < 10) {
    recommendations.push('Use more shell commands to build context history');
  }

  if (analytics.sessionMetrics.totalClipboardEntries < 5) {
    recommendations.push('Clipboard activity is low - consider copying relevant content');
  }

  if (analytics.contextEffectiveness.score < 50) {
    recommendations.push('Context strength is low - switch between different applications to generate more context');
  }

  if (analytics.keywordFrequency.length < 20) {
    recommendations.push('Work with more technical terms to improve vocabulary extraction');
  }

  if (recommendations.length === 0) {
    recommendations.push('Context quality is excellent! Keep up the productive work.');
  }

  return recommendations;
}

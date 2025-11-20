'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Monitor,
  Activity,
  Clock,
  Hash,
  TrendingUp,
  BarChart3,
  Window,
  Cpu
} from 'lucide-react';
import { motion } from 'framer-motion';
import { ActiveWindow, ApplicationStats } from './types';

interface ApplicationDetectorProps {
  activeWindow: ActiveWindow | null;
  usageStats: ApplicationStats[];
  history: ActiveWindow[];
  onRefresh?: () => void;
}

export function ApplicationDetector({
  activeWindow,
  usageStats,
  history,
  onRefresh
}: ApplicationDetectorProps) {
  const [selectedApp, setSelectedApp] = useState<string | null>(null);

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      development: 'bg-blue-500/20 text-blue-400',
      browser: 'bg-green-500/20 text-green-400',
      terminal: 'bg-gray-500/20 text-gray-400',
      editor: 'bg-purple-500/20 text-purple-400',
      communication: 'bg-pink-500/20 text-pink-400',
      media: 'bg-red-500/20 text-red-400',
      system: 'bg-yellow-500/20 text-yellow-400',
      other: 'bg-orange-500/20 text-orange-400',
    };
    return colors[category] || colors.other;
  };

  const getCategoryIcon = (category: string): string => {
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
  };

  const totalUsageTime = usageStats.reduce((sum, app) => sum + app.usageTime, 0);

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Monitor className="w-5 h-5 text-primary" />
              Application Detection
            </CardTitle>
            <CardDescription>
              Real-time window monitoring and application usage statistics
            </CardDescription>
          </div>
          <Badge variant={activeWindow ? 'default' : 'secondary'}>
            <Activity className="w-3 h-3 mr-1" />
            {activeWindow ? 'Active' : 'Idle'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col">
        <Tabs defaultValue="active" className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="active">Active Window</TabsTrigger>
            <TabsTrigger value="stats">Usage Stats</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>

          <TabsContent value="active" className="flex-1 space-y-4">
            {activeWindow ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-4"
              >
                <Card>
                  <CardContent className="pt-6">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{getCategoryIcon(activeWindow.category)}</span>
                          <div>
                            <div className="font-semibold">{activeWindow.class}</div>
                            <div className="text-sm text-muted-foreground">PID: {activeWindow.pid}</div>
                          </div>
                        </div>
                        <Badge className={getCategoryColor(activeWindow.category)}>
                          {activeWindow.category}
                        </Badge>
                      </div>

                      <div className="space-y-1">
                        <div className="text-sm font-medium">Window Title</div>
                        <div className="text-sm text-muted-foreground bg-muted/50 p-2 rounded break-words">
                          {activeWindow.title}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        Last updated: {new Date(activeWindow.timestamp * 1000).toLocaleTimeString()}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Context Snapshot */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Context Snapshot</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1.5">
                      {activeWindow.title.match(/\b[A-Z][a-z]+[A-Z]\w+|\w+\.\w+|\/[\w/-]+/g)?.map((term, i) => (
                        <Badge key={i} variant="outline" className="text-xs">
                          <Hash className="w-3 h-3 mr-1" />
                          {term}
                        </Badge>
                      )) || <span className="text-xs text-muted-foreground">No keywords detected</span>}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ) : (
              <div className="flex items-center justify-center h-full text-center text-muted-foreground">
                <div>
                  <Window className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No active window detected</p>
                  <p className="text-sm">Switch to an application to see details</p>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="stats" className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Total Tracking Time</span>
                <span>{formatTime(totalUsageTime)}</span>
              </div>
              <Progress value={100} className="h-2" />
            </div>

            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {usageStats.map((app, index) => (
                  <motion.div
                    key={app.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="p-3 rounded-lg border bg-card hover:bg-accent/50 cursor-pointer transition-colors"
                    onClick={() => setSelectedApp(selectedApp === app.name ? null : app.name)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-lg">{getCategoryIcon(app.category)}</span>
                          <span className="font-medium truncate">{app.name}</span>
                        </div>

                        <div className="flex items-center gap-3 text-xs text-muted-foreground mb-2">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatTime(app.usageTime)}
                          </span>
                          <span className="flex items-center gap-1">
                            <BarChart3 className="w-3 h-3" />
                            {app.usageCount} launches
                          </span>
                        </div>

                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span>Usage time</span>
                            <span>{((app.usageTime / totalUsageTime) * 100).toFixed(1)}%</span>
                          </div>
                          <Progress
                            value={(app.usageTime / totalUsageTime) * 100}
                            className="h-1.5"
                          />
                        </div>

                        {selectedApp === app.name && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-3 pt-3 border-t space-y-2"
                          >
                            <div className="text-xs">
                              <span className="text-muted-foreground">Last used: </span>
                              {new Date(app.lastUsed * 1000).toLocaleString()}
                            </div>
                            {app.keywords.length > 0 && (
                              <div className="space-y-1">
                                <div className="text-xs text-muted-foreground">Detected keywords:</div>
                                <div className="flex flex-wrap gap-1">
                                  {app.keywords.slice(0, 5).map((keyword, i) => (
                                    <Badge key={i} variant="outline" className="text-xs">
                                      {keyword}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </motion.div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <ScrollArea className="h-[500px]">
              <div className="space-y-2">
                {history.map((window, index) => (
                  <motion.div
                    key={`${window.class}-${window.timestamp}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.02 }}
                    className="flex items-center justify-between p-3 rounded-lg border bg-card"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <span className="text-lg">{getCategoryIcon(window.category)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{window.class}</div>
                        <div className="text-xs text-muted-foreground truncate">
                          {window.title}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className={getCategoryColor(window.category)}>
                        {window.category}
                      </Badge>
                      <div className="text-xs text-muted-foreground mt-1">
                        {new Date(window.timestamp * 1000).toLocaleTimeString()}
                      </div>
                    </div>
                  </motion.div>
                ))}

                {history.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    No window history available
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

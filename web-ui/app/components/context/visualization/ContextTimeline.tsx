'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Timeline,
  Clock,
  Terminal,
  Clipboard,
  Monitor,
  Activity,
  Hash,
  TrendingUp
} from 'lucide-react';
import { motion } from 'framer-motion';
import { ContextData } from '../types';

interface ContextTimelineProps {
  data: ContextData | null;
}

interface TimelineEvent {
  id: string;
  type: 'command' | 'clipboard' | 'window';
  timestamp: number;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
}

export function ContextTimeline({ data }: ContextTimelineProps) {
  if (!data) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8 text-muted-foreground">
            No timeline data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Combine all events from different sources
  const events: TimelineEvent[] = [
    // Shell commands
    ...data.shell.commands.map(cmd => ({
      id: `cmd-${cmd.id}`,
      type: 'command' as const,
      timestamp: cmd.timestamp,
      title: cmd.command.split(' ')[0], // First word as title
      description: cmd.command,
      icon: <Terminal className="w-4 h-4" />,
      color: 'bg-blue-500/20 text-blue-400'
    })),
    // Clipboard entries
    ...data.clipboard.entries.map(entry => ({
      id: `clip-${entry.id}`,
      type: 'clipboard' as const,
      timestamp: entry.timestamp,
      title: entry.type,
      description: entry.content.slice(0, 60) + (entry.content.length > 60 ? '...' : ''),
      icon: <Clipboard className="w-4 h-4" />,
      color: 'bg-green-500/20 text-green-400'
    })),
    // Window changes
    ...data.applications.history.map(window => ({
      id: `win-${window.class}-${window.timestamp}`,
      type: 'window' as const,
      timestamp: window.timestamp,
      title: window.class,
      description: window.title,
      icon: <Monitor className="w-4 h-4" />,
      color: 'bg-purple-500/20 text-purple-400'
    }))
  ].sort((a, b) => b.timestamp - a.timestamp); // Sort by timestamp descending

  // Group events by time periods
  const groupedEvents = {
    lastHour: events.filter(e => Date.now() / 1000 - e.timestamp < 3600),
    last6Hours: events.filter(e => Date.now() / 1000 - e.timestamp < 21600),
    last24Hours: events.filter(e => Date.now() / 1000 - e.timestamp < 86400),
    older: events.filter(e => Date.now() / 1000 - e.timestamp >= 86400)
  };

  const renderEvent = (event: TimelineEvent, index: number) => (
    <motion.div
      key={event.id}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.02 }}
      className="relative flex gap-3 pb-6"
    >
      <div className="flex flex-col items-center">
        <div className={`rounded-full p-2 ${event.color}`}>
          {event.icon}
        </div>
        {index < events.length - 1 && (
          <div className="w-px h-full bg-border mt-2" />
        )}
      </div>
      <div className="flex-1 min-w-0 pb-6">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-sm">{event.title}</span>
          <Badge variant="outline" className="text-xs">
            {new Date(event.timestamp * 1000).toLocaleTimeString()}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground break-words">{event.description}</p>
      </div>
    </motion.div>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Timeline className="w-5 h-5 text-primary" />
          Context Timeline
        </CardTitle>
        <CardDescription>
          Chronological view of all context changes and activities
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="all" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="all">All Events ({events.length})</TabsTrigger>
            <TabsTrigger value="recent">Recent ({groupedEvents.lastHour.length})</TabsTrigger>
            <TabsTrigger value="commands">
              <Terminal className="w-4 h-4 mr-1" />
              Commands
            </TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            <ScrollArea className="h-[500px]">
              <div className="space-y-1">
                {events.length > 0 ? (
                  events.map((event, index) => renderEvent(event, index))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No events recorded yet
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="recent">
            <ScrollArea className="h-[500px]">
              <div className="space-y-1">
                {groupedEvents.lastHour.length > 0 ? (
                  groupedEvents.lastHour.map((event, index) => renderEvent(event, index))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No events in the last hour
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="commands">
            <ScrollArea className="h-[500px]">
              <div className="space-y-1">
                {events.filter(e => e.type === 'command').length > 0 ? (
                  events.filter(e => e.type === 'command').map((event, index) => renderEvent(event, index))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No commands recorded yet
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="analysis" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Event Distribution</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Terminal className="w-4 h-4 text-blue-400" />
                      <span className="text-sm">Shell Commands</span>
                    </div>
                    <Badge variant="outline">
                      {data.shell.commands.length}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Clipboard className="w-4 h-4 text-green-400" />
                      <span className="text-sm">Clipboard Entries</span>
                    </div>
                    <Badge variant="outline">
                      {data.clipboard.entries.length}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Monitor className="w-4 h-4 text-purple-400" />
                      <span className="text-sm">Window Changes</span>
                    </div>
                    <Badge variant="outline">
                      {data.applications.history.length}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Activity Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Last hour</span>
                    <span className="font-semibold">{groupedEvents.lastHour.length} events</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Last 6 hours</span>
                    <span className="font-semibold">{groupedEvents.last6Hours.length} events</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Last 24 hours</span>
                    <span className="font-semibold">{groupedEvents.last24Hours.length} events</span>
                  </div>
                </CardContent>
              </Card>

              <Card className="md:col-span-2">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Peak Activity Hours</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols="12" gap-1">
                    {Array.from({ length: 24 }, (_, i) => {
                      const hourEvents = events.filter(e => {
                        const hour = new Date(e.timestamp * 1000).getHours();
                        return hour === i;
                      }).length;
                      const maxEvents = Math.max(...Array.from({ length: 24 }, (_, h) =>
                        events.filter(e => new Date(e.timestamp * 1000).getHours() === h).length
                      ));
                      const height = maxEvents > 0 ? (hourEvents / maxEvents) * 100 : 0;

                      return (
                        <div key={i} className="flex flex-col items-center gap-1">
                          <div
                            className="w-full bg-primary/20 rounded-t"
                            style={{ height: `${height}%`, minHeight: '4px' }}
                            title={`${i}:00 - ${hourEvents} events`}
                          />
                          <span className="text-xs text-muted-foreground">{i}</span>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

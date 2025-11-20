'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Activity, Zap, Target, TrendingUp, RefreshCw, Play, Pause } from 'lucide-react';
import { LiveUpdate, KeywordEffectiveness } from '@/lib/vocabulary/types';
import { vocabularyWS } from '@/lib/vocabulary/websocket';

export function LiveVocabularyMonitor() {
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [updates, setUpdates] = useState<LiveUpdate[]>([]);
  const [activeKeywords, setActiveKeywords] = useState<string[]>([]);
  const [recentMatches, setRecentMatches] = useState<Array<{ word: string; match: string; confidence: number; timestamp: number }>>([]);
  const [effectiveness, setEffectiveness] = useState<KeywordEffectiveness[]>([]);

  useEffect(() => {
    if (isMonitoring) {
      // Subscribe to WebSocket updates
      vocabularyWS.on('vocabulary_change', handleUpdate);
      vocabularyWS.on('keyword_match', handleMatch);
      vocabularyWS.on('application_switch', handleSwitch);
      vocabularyWS.on('stats_update', handleStats);

      return () => {
        vocabularyWS.off('vocabulary_change', handleUpdate);
        vocabularyWS.off('keyword_match', handleMatch);
        vocabularyWS.off('application_switch', handleSwitch);
        vocabularyWS.off('stats_update', handleStats);
      };
    }
  }, [isMonitoring]);

  const handleUpdate = (update: LiveUpdate) => {
    setUpdates(prev => [update, ...prev.slice(0, 49)]);
  };

  const handleMatch = (update: LiveUpdate) => {
    if (update.payload) {
      setRecentMatches(prev => [{
        word: update.payload.word,
        match: update.payload.match,
        confidence: update.payload.confidence,
        timestamp: update.timestamp,
      }, ...prev.slice(0, 19)]);
    }
  };

  const handleSwitch = (update: LiveUpdate) => {
    if (update.payload?.keywords) {
      setActiveKeywords(update.payload.keywords);
    }
  };

  const handleStats = (update: LiveUpdate) => {
    // Update effectiveness metrics
    if (update.payload?.effectiveness) {
      setEffectiveness(update.payload.effectiveness);
    }
  };

  const toggleMonitoring = () => {
    setIsMonitoring(!isMonitoring);
  };

  const getUpdateIcon = (type: string) => {
    switch (type) {
      case 'vocabulary_change':
        return <RefreshCw className="h-4 w-4" />;
      case 'keyword_match':
        return <Target className="h-4 w-4" />;
      case 'application_switch':
        return <Activity className="h-4 w-4" />;
      case 'stats_update':
        return <TrendingUp className="h-4 w-4" />;
      default:
        return <Zap className="h-4 w-4" />;
    }
  };

  const getUpdateColor = (type: string) => {
    switch (type) {
      case 'vocabulary_change':
        return 'bg-blue-500';
      case 'keyword_match':
        return 'bg-green-500';
      case 'application_switch':
        return 'bg-purple-500';
      case 'stats_update':
        return 'bg-orange-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Live Vocabulary Monitoring</h2>
          <p className="text-muted-foreground">
            Real-time vocabulary updates and keyword matching
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm">Monitoring</span>
            <Switch checked={isMonitoring} onCheckedChange={toggleMonitoring} />
          </div>
          <Button variant="outline" size="icon" onClick={toggleMonitoring}>
            {isMonitoring ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Keywords</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeKeywords.length}</div>
            <p className="text-xs text-muted-foreground">
              Currently loaded
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Matches</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recentMatches.length}</div>
            <p className="text-xs text-muted-foreground">
              Last 20 matches
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Update Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {updates.length > 0 ? `${Math.round(updates.length / 5)}/min` : '0/min'}
            </div>
            <p className="text-xs text-muted-foreground">
              Updates per minute
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="live" className="space-y-4">
        <TabsList>
          <TabsTrigger value="live">Live Feed</TabsTrigger>
          <TabsTrigger value="matches">Keyword Matches</TabsTrigger>
          <TabsTrigger value="effectiveness">Effectiveness</TabsTrigger>
        </TabsList>

        <TabsContent value="live" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Live Updates</CardTitle>
              <CardDescription>
                Real-time vocabulary and application changes
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {updates.length > 0 ? (
                  updates.map((update, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 border rounded-lg">
                      <div className={`p-2 rounded-full ${getUpdateColor(update.type)} text-white`}>
                        {getUpdateIcon(update.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline" className="text-xs">
                            {update.type}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(update.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <pre className="text-xs text-muted-foreground overflow-x-auto">
                          {JSON.stringify(update.payload, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No updates yet. Monitoring is {isMonitoring ? 'active' : 'inactive'}.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="matches" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Keyword Matches</CardTitle>
              <CardDescription>
                Successful vocabulary matches in real-time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentMatches.length > 0 ? (
                  recentMatches.map((match, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{match.word}</Badge>
                          <span>→</span>
                          <Badge variant="secondary">{match.match}</Badge>
                        </div>
                        <Badge variant={match.confidence > 0.9 ? 'default' : 'secondary'}>
                          {(match.confidence * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      <Progress value={match.confidence * 100} className="h-2" />
                      <p className="text-xs text-muted-foreground mt-2">
                        {new Date(match.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <Target className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No keyword matches detected yet.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="effectiveness" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Keyword Effectiveness</CardTitle>
              <CardDescription>
                Performance metrics for individual keywords
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {effectiveness.length > 0 ? (
                  effectiveness.map((item, index) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-medium">{item.word}</span>
                          <Badge variant="outline">{item.category}</Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          {item.trend === 'up' && <TrendingUp className="h-4 w-4 text-green-500" />}
                          {item.trend === 'down' && <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />}
                          <Badge variant={item.accuracy > 0.8 ? 'default' : 'secondary'}>
                            {item.accuracy > 0.8 ? 'High' : item.accuracy > 0.5 ? 'Medium' : 'Low'} Effectiveness
                          </Badge>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">Matches</p>
                          <p className="font-medium">{item.matches}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Corrections</p>
                          <p className="font-medium">{item.corrections}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Accuracy</p>
                          <p className="font-medium">{(item.accuracy * 100).toFixed(1)}%</p>
                        </div>
                      </div>
                      <Progress value={item.accuracy * 100} className="mt-2 h-2" />
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <Target className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No effectiveness data available yet.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

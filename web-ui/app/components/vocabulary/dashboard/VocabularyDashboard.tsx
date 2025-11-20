'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { RefreshCw, Activity, Database, TrendingUp, Layers } from 'lucide-react';
import { VocabularyStatistics } from '@/lib/vocabulary/types';
import { vocabularyAPI } from '@/lib/vocabulary/api';
import { vocabularyWS } from '@/lib/vocabulary/websocket';

export function VocabularyDashboard() {
  const [stats, setStats] = useState<VocabularyStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<number>(Date.now());

  useEffect(() => {
    loadStats();

    // Subscribe to WebSocket updates
    vocabularyWS.on('vocabulary_change', () => {
      loadStats();
    });
    vocabularyWS.on('stats_update', (update) => {
      setStats(update.payload);
      setLastUpdate(Date.now());
    });

    return () => {
      vocabularyWS.off('vocabulary_change', loadStats);
      vocabularyWS.off('stats_update', () => {});
    };
  }, []);

  const loadStats = async () => {
    try {
      const data = await vocabularyAPI.getStatistics();
      setStats(data);
      setLastUpdate(Date.now());
    } catch (error) {
      console.error('Failed to load vocabulary stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    loadStats();
  };

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading vocabulary statistics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Vocabulary Dashboard</h2>
          <p className="text-muted-foreground">
            Overview of all loaded vocabularies and their statistics
          </p>
        </div>
        <Button onClick={handleRefresh} disabled={loading} variant="outline" size="icon">
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Vocabularies</CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalVocabularies}</div>
            <p className="text-xs text-muted-foreground">
              {stats.vocabularies ? Object.keys(stats.vocabularies).length : 0} loaded
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Keywords</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeKeywords}</div>
            <p className="text-xs text-muted-foreground">
              Currently in use
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current App</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold truncate">
              {stats.currentApplication || 'None'}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats.currentVocabulary || 'Global'} vocabulary active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Accuracy Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.usageStats?.accuracyRate ? `${(stats.usageStats.accuracyRate * 100).toFixed(1)}%` : 'N/A'}
            </div>
            <Progress
              value={stats.usageStats?.accuracyRate ? stats.usageStats.accuracyRate * 100 : 0}
              className="mt-2"
            />
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="vocabularies">Vocabularies</TabsTrigger>
          <TabsTrigger value="applications">Applications</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Vocabulary Distribution</CardTitle>
              <CardDescription>
                Keywords per vocabulary category
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(stats.vocabularies || {}).map(([id, vocab]) => (
                  <div key={id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-medium">{vocab.name}</span>
                        <Badge variant="secondary" className="ml-2">
                          {vocab.totalKeywords} keywords
                        </Badge>
                      </div>
                      <Badge variant={id === stats.currentVocabulary ? 'default' : 'outline'}>
                        {id === stats.currentVocabulary ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    <Progress
                      value={(vocab.totalKeywords / stats.activeKeywords) * 100}
                      className="h-2"
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {stats.usageStats?.mostUsed && stats.usageStats.mostUsed.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Most Used Keywords</CardTitle>
                <CardDescription>
                  Top keywords by usage frequency
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {stats.usageStats.mostUsed.slice(0, 10).map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="font-mono text-sm">{item.word}</span>
                      <Badge variant="outline">{item.count} uses</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="vocabularies" className="space-y-4">
          <div className="grid gap-4">
            {Object.entries(stats.vocabularies || {}).map(([id, vocab]) => (
              <Card key={id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg">{vocab.name}</CardTitle>
                      <CardDescription>{vocab.description}</CardDescription>
                    </div>
                    <Badge variant={id === stats.currentVocabulary ? 'default' : 'secondary'}>
                      {vocab.totalKeywords} keywords
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="text-sm">
                      <span className="font-medium">ID:</span> {id}
                    </div>
                    {id === stats.currentVocabulary && (
                      <Badge variant="default" className="mt-2">
                        Currently Active
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="applications">
          <Card>
            <CardHeader>
              <CardTitle>Application Detection</CardTitle>
              <CardDescription>
                Current active application and matched vocabulary
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium">Current Application</p>
                <p className="text-lg">{stats.currentApplication || 'Not detected'}</p>
              </div>
              <div>
                <p className="text-sm font-medium">Active Vocabulary</p>
                <p className="text-lg">{stats.currentVocabulary || 'Global'}</p>
              </div>
              <div>
                <p className="text-sm font-medium">Last Update</p>
                <p className="text-sm text-muted-foreground">
                  {new Date(lastUpdate).toLocaleTimeString()}
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

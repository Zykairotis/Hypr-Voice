'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Activity, Target, Award, Clock } from 'lucide-react';
import { VocabularyStatistics as StatsType } from '@/lib/vocabulary/types';
import { vocabularyAPI } from '@/lib/vocabulary/api';
import { vocabularyWS } from '@/lib/vocabulary/websocket';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

export function VocabularyStatistics() {
  const [stats, setStats] = useState<StatsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');

  useEffect(() => {
    loadStats();

    vocabularyWS.on('stats_update', (update) => {
      setStats(update.payload);
    });

    return () => {
      vocabularyWS.off('stats_update', () => {});
    };
  }, []);

  const loadStats = async () => {
    try {
      const data = await vocabularyAPI.getStatistics();
      setStats(data);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading statistics...</p>
        </div>
      </div>
    );
  }

  // Prepare data for charts
  const vocabularyData = Object.entries(stats.vocabularies || {}).map(([id, vocab]) => ({
    name: vocab.name,
    keywords: vocab.totalKeywords,
    id,
  }));

  const usageData = stats.usageStats?.mostUsed?.slice(0, 10).map((item, index) => ({
    word: item.word,
    count: item.count,
    rank: index + 1,
  })) || [];

  const accuracyData = [
    { name: 'High Accuracy', value: 70, fill: '#00C49F' },
    { name: 'Medium Accuracy', value: 20, fill: '#FFBB28' },
    { name: 'Low Accuracy', value: 10, fill: '#FF8042' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Vocabulary Statistics</h2>
          <p className="text-muted-foreground">
            Analytics and performance metrics
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Keywords</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeKeywords}</div>
            <p className="text-xs text-muted-foreground">
              Across {stats.totalVocabularies} vocabularies
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Accuracy Rate</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
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

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Corrections</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.usageStats?.totalCorrections || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Automatic corrections applied
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Most Used</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usageData.length > 0 ? usageData[0].word : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              {usageData.length > 0 && `${usageData[0].count} uses`}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="usage">Usage</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Vocabulary Distribution</CardTitle>
                <CardDescription>
                  Number of keywords per vocabulary
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={vocabularyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="keywords" fill="#0088FE" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Accuracy Distribution</CardTitle>
                <CardDescription>
                  Accuracy rate breakdown
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={accuracyData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {accuracyData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Vocabulary Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(stats.vocabularies || {}).map(([id, vocab]) => (
                  <div key={id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">{vocab.name}</h4>
                      <Badge variant="outline">{vocab.totalKeywords} keywords</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      {vocab.description}
                    </p>
                    <Progress
                      value={(vocab.totalKeywords / stats.activeKeywords) * 100}
                      className="h-2"
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Most Used Keywords</CardTitle>
              <CardDescription>
                Top keywords by usage frequency
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={usageData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="word" type="category" width={100} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#00C49F" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Keyword Usage List</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {usageData.map((item, index) => (
                  <div key={item.word} className="flex items-center justify-between p-2 border rounded">
                    <div className="flex items-center gap-4">
                      <Badge variant="outline">#{index + 1}</Badge>
                      <span className="font-mono">{item.word}</span>
                    </div>
                    <Badge variant="secondary">{item.count} uses</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Accuracy Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Overall Accuracy</span>
                    <span className="text-sm font-medium">
                      {stats.usageStats?.accuracyRate ? `${(stats.usageStats.accuracyRate * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <Progress value={stats.usageStats?.accuracyRate ? stats.usageStats.accuracyRate * 100 : 0} />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Successful Matches</span>
                    <span className="text-sm font-medium">156</span>
                  </div>
                  <Progress value={78} />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Failed Matches</span>
                    <span className="text-sm font-medium">44</span>
                  </div>
                  <Progress value={22} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Correction Impact</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Total Corrections</span>
                    <span className="text-sm font-medium">{stats.usageStats?.totalCorrections || 0}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Context-Based</span>
                    <span className="text-sm font-medium">67</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Global Terms</span>
                    <span className="text-sm font-medium">23</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">App-Specific</span>
                    <span className="text-sm font-medium">45</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Usage Trends</CardTitle>
              <CardDescription>
                Keyword usage over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={[
                  { time: '00:00', keywords: 45 },
                  { time: '04:00', keywords: 52 },
                  { time: '08:00', keywords: 78 },
                  { time: '12:00', keywords: 65 },
                  { time: '16:00', keywords: 89 },
                  { time: '20:00', keywords: 72 },
                  { time: '24:00', keywords: 58 },
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="keywords" stroke="#0088FE" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  LayoutDashboard,
  Monitor,
  Edit,
  Brain,
  Settings,
  BarChart3,
  Activity,
  Package,
  BookOpen,
} from 'lucide-react';
import {
  VocabularyDashboard,
  ApplicationVocabulary,
  VocabularyEditor,
  ContextAwareVocabulary,
  GlobalVocabularySettings,
  VocabularyStatistics,
  LiveVocabularyMonitor,
  VocabularyPresets,
} from '@/components/vocabulary';
import { vocabularyWS } from '@/lib/vocabulary/websocket';

export default function VocabularyPage() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');

  useEffect(() => {
    // Connect to WebSocket
    const connect = async () => {
      try {
        await vocabularyWS.connect();
        setConnectionStatus('connected');
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        setConnectionStatus('disconnected');
      }
    };

    connect();

    // Handle connection status
    vocabularyWS.on('connect', () => setConnectionStatus('connected'));
    vocabularyWS.on('disconnect', () => setConnectionStatus('disconnected'));
    vocabularyWS.on('error', () => setConnectionStatus('disconnected'));

    return () => {
      vocabularyWS.disconnect();
    };
  }, []);

  const getStatusBadge = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Badge variant="default">Live</Badge>;
      case 'connecting':
        return <Badge variant="secondary">Connecting...</Badge>;
      case 'disconnected':
        return <Badge variant="destructive">Disconnected</Badge>;
    }
  };

  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Vocabulary Management</h1>
          <p className="text-muted-foreground mt-2">
            Comprehensive vocabulary management system for Hypr-Voice
          </p>
        </div>
        {getStatusBadge()}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid grid-cols-4 lg:grid-cols-8 h-auto p-1">
          <TabsTrigger value="dashboard" className="flex flex-col gap-1 py-3">
            <LayoutDashboard className="h-4 w-4" />
            <span className="text-xs">Dashboard</span>
          </TabsTrigger>
          <TabsTrigger value="application" className="flex flex-col gap-1 py-3">
            <Monitor className="h-4 w-4" />
            <span className="text-xs">Application</span>
          </TabsTrigger>
          <TabsTrigger value="editor" className="flex flex-col gap-1 py-3">
            <Edit className="h-4 w-4" />
            <span className="text-xs">Editor</span>
          </TabsTrigger>
          <TabsTrigger value="context" className="flex flex-col gap-1 py-3">
            <Brain className="h-4 w-4" />
            <span className="text-xs">Context</span>
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex flex-col gap-1 py-3">
            <Settings className="h-4 w-4" />
            <span className="text-xs">Settings</span>
          </TabsTrigger>
          <TabsTrigger value="statistics" className="flex flex-col gap-1 py-3">
            <BarChart3 className="h-4 w-4" />
            <span className="text-xs">Statistics</span>
          </TabsTrigger>
          <TabsTrigger value="monitoring" className="flex flex-col gap-1 py-3">
            <Activity className="h-4 w-4" />
            <span className="text-xs">Live</span>
          </TabsTrigger>
          <TabsTrigger value="presets" className="flex flex-col gap-1 py-3">
            <Package className="h-4 w-4" />
            <span className="text-xs">Presets</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <VocabularyDashboard />
        </TabsContent>

        <TabsContent value="application">
          <ApplicationVocabulary />
        </TabsContent>

        <TabsContent value="editor">
          <VocabularyEditor />
        </TabsContent>

        <TabsContent value="context">
          <ContextAwareVocabulary />
        </TabsContent>

        <TabsContent value="settings">
          <GlobalVocabularySettings />
        </TabsContent>

        <TabsContent value="statistics">
          <VocabularyStatistics />
        </TabsContent>

        <TabsContent value="monitoring">
          <LiveVocabularyMonitor />
        </TabsContent>

        <TabsContent value="presets">
          <VocabularyPresets />
        </TabsContent>
      </Tabs>

      <div className="bg-muted/50 border rounded-lg p-4">
        <div className="flex items-start gap-3">
          <BookOpen className="h-5 w-5 text-primary mt-0.5" />
          <div>
            <h3 className="font-semibold mb-1">Quick Start Guide</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Start with the <strong>Dashboard</strong> to see an overview of your vocabularies</li>
              <li>• Use <strong>Application</strong> to configure app-specific vocabulary</li>
              <li>• Edit vocabularies in the <strong>Editor</strong> with full CRUD operations</li>
              <li>• Monitor <strong>Live</strong> updates to track vocabulary changes in real-time</li>
              <li>• Check <strong>Statistics</strong> for usage analytics and performance metrics</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { VoiceControlPanel } from '@/components/voice-control-panel';
import { ServerControlPanel } from '@/components/server-control-panel';
import { LogViewer } from '@/components/log-viewer';
import { PerformanceChart } from '@/components/performance-chart';
import { SessionOverview } from '@/components/session-overview';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { useVoiceState, useServerStatus, useLogs, useSessions, usePerformanceMetrics } from '@/hooks/use-websocket';
import { VoiceState, ServerStatus, LogEntry, Session, PerformanceMetrics } from '@/types';
import { Mic, Server, FileText, Clock, TrendingUp, AlertCircle } from 'lucide-react';

// Mock data for development
const mockVoiceState: VoiceState = {
  isRecording: false,
  isActive: true,
  isProcessing: false,
  audioLevel: 0.3,
  f9Pressed: false,
  f10Pressed: false,
};

const mockServerStatus: ServerStatus = {
  running: true,
  pid: 12345,
  port: 8765,
  uptime: 3600,
  memory: 256 * 1024 * 1024, // 256MB
  cpu: 15.5,
};

const mockLogs: LogEntry[] = [
  {
    id: '1',
    timestamp: new Date(),
    level: 'info',
    message: 'Hypr-Voice server started successfully',
    source: 'server',
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 60000),
    level: 'debug',
    message: 'WebSocket connection established',
    source: 'websocket',
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 120000),
    level: 'warn',
    message: 'Audio device fallback activated',
    source: 'audio',
  },
];

const mockSessions: Session[] = [
  {
    id: 'session-1',
    startTime: new Date(Date.now() - 3600000),
    transcriptions: 25,
    characters: 1500,
    applications: ['firefox', 'kitty', 'vscode'],
    status: 'completed',
  },
  {
    id: 'session-2',
    startTime: new Date(),
    transcriptions: 5,
    characters: 300,
    applications: ['kitty'],
    status: 'active',
  },
];

const mockMetrics: PerformanceMetrics[] = Array.from({ length: 20 }, (_, i) => ({
  timestamp: new Date(Date.now() - i * 60000),
  cpu: 10 + Math.random() * 20,
  memory: 200 + Math.random() * 100,
  disk: 50 + Math.random() * 10,
  network: {
    inbound: Math.random() * 1000,
    outbound: Math.random() * 500,
  },
  transcriptionLatency: 1500 + Math.random() * 1000,
  llmLatency: 2000 + Math.random() * 2000,
}));

export default function Dashboard() {
  // In production, these would use real WebSocket connections
  const [voiceState, setVoiceState] = useState<VoiceState>(mockVoiceState);
  const [serverStatus, setServerStatus] = useState<ServerStatus>(mockServerStatus);
  const [logs, setLogs] = useState<LogEntry[]>(mockLogs);
  const [sessions, setSessions] = useState<Session[]>(mockSessions);
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>(mockMetrics);

  // Mock real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate audio level changes
      setVoiceState(prev => ({
        ...prev,
        audioLevel: Math.random() * 0.8,
      }));

      // Simulate new logs
      if (Math.random() > 0.8) {
        const newLog: LogEntry = {
          id: Date.now().toString(),
          timestamp: new Date(),
          level: Math.random() > 0.7 ? 'info' : Math.random() > 0.5 ? 'debug' : 'warn',
          message: `System activity detected at ${new Date().toLocaleTimeString()}`,
          source: ['server', 'audio', 'websocket', 'transcription'][Math.floor(Math.random() * 4)],
        };
        setLogs(prev => [newLog, ...prev.slice(0, 99)]);
      }

      // Simulate metrics updates
      setMetrics(prev => {
        const newMetric: PerformanceMetrics = {
          timestamp: new Date(),
          cpu: 10 + Math.random() * 20,
          memory: 200 + Math.random() * 100,
          disk: 50 + Math.random() * 10,
          network: {
            inbound: Math.random() * 1000,
            outbound: Math.random() * 500,
          },
          transcriptionLatency: 1500 + Math.random() * 1000,
          llmLatency: 2000 + Math.random() * 2000,
        };
        return [newMetric, ...prev.slice(0, 59)];
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const handleStartRecording = () => {
    setVoiceState(prev => ({ ...prev, isRecording: true, isProcessing: false }));
  };

  const handleStopRecording = () => {
    setVoiceState(prev => ({ ...prev, isRecording: false, isProcessing: true }));
    setTimeout(() => {
      setVoiceState(prev => ({ ...prev, isProcessing: false }));
    }, 2000);
  };

  const handleToggleServer = () => {
    if (serverStatus.running) {
      setServerStatus({ running: false });
    } else {
      setServerStatus({
        running: true,
        pid: Math.floor(Math.random() * 20000) + 10000,
        port: 8765,
        uptime: 0,
        memory: 200 * 1024 * 1024,
        cpu: 10,
      });
    }
  };

  const handleClearLogs = () => {
    setLogs([]);
  };

  const activeSession = sessions.find(s => s.status === 'active');
  const completedSessions = sessions.filter(s => s.status === 'completed');
  const currentMetrics = metrics[0];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time monitoring and control for Hypr-Voice
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={serverStatus.running ? "default" : "destructive"} className="flex items-center gap-1">
            <div className={cn(
              "w-2 h-2 rounded-full",
              serverStatus.running ? "bg-green-500" : "bg-red-500"
            )} />
            {serverStatus.running ? "Online" : "Offline"}
          </Badge>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Voice Status</CardTitle>
            <Mic className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {voiceState.isRecording ? "Recording" : voiceState.isProcessing ? "Processing" : "Ready"}
            </div>
            <p className="text-xs text-muted-foreground">
              F9: {voiceState.f9Pressed ? "Pressed" : "Ready"} | F10: {voiceState.f10Pressed ? "Pressed" : "Ready"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Server Uptime</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {serverStatus.uptime ? `${Math.floor(serverStatus.uptime / 3600)}h` : "Offline"}
            </div>
            <p className="text-xs text-muted-foreground">
              PID: {serverStatus.pid || "N/A"} | Port: {serverStatus.port || "N/A"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Session</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {activeSession ? `${activeSession.transcriptions} transcriptions` : "No active session"}
            </div>
            <p className="text-xs text-muted-foreground">
              {activeSession ? `${activeSession.characters} characters` : `${completedSessions.length} completed today`}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Load</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {currentMetrics ? `${currentMetrics.cpu.toFixed(1)}%` : "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">
              Memory: {currentMetrics ? `${(currentMetrics.memory / 1024 / 1024).toFixed(0)}MB` : "N/A"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="controls">Controls</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <VoiceControlPanel
              voiceState={voiceState}
              onStartRecording={handleStartRecording}
              onStopRecording={handleStopRecording}
              onToggleServer={handleToggleServer}
              serverRunning={serverStatus.running}
            />
            <ServerControlPanel
              serverStatus={serverStatus}
              onStart={() => setServerStatus({ ...mockServerStatus, running: true })}
              onStop={() => setServerStatus({ running: false })}
              onRestart={handleToggleServer}
            />
          </div>
          <SessionOverview sessions={sessions} />
        </TabsContent>

        <TabsContent value="controls" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <VoiceControlPanel
              voiceState={voiceState}
              onStartRecording={handleStartRecording}
              onStopRecording={handleStopRecording}
              onToggleServer={handleToggleServer}
              serverRunning={serverStatus.running}
            />
            <ServerControlPanel
              serverStatus={serverStatus}
              onStart={() => setServerStatus({ ...mockServerStatus, running: true })}
              onStop={() => setServerStatus({ running: false })}
              onRestart={handleToggleServer}
            />
          </div>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <LogViewer logs={logs} onClearLogs={handleClearLogs} />
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <PerformanceChart metrics={metrics} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
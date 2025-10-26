'use client';

import { useState, useEffect } from 'react';
import { SessionDetails } from '@/components/session-details';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Session } from '@/types';
import {
  MessageSquare,
  Calendar,
  Download,
  RefreshCw,
  Search,
  Filter,
  CheckCircle,
  AlertTriangle,
  PlayCircle,
  BarChart3,
  Clock,
  TrendingUp,
  Monitor,
  FileText,
  Users
} from 'lucide-react';

// Mock session data for development
const generateMockSessions = (): Session[] => {
  const applications = ['kitty', 'firefox', 'vscode', 'discord', 'slack', 'obsidian', 'chrome'];
  const statuses: Session['status'][] = ['completed', 'active', 'error'];

  return Array.from({ length: 20 }, (_, i) => {
    const startTime = new Date(Date.now() - i * 3600000); // 1 hour apart
    const duration = 1800000 + Math.random() * 3600000; // 30-90 minutes
    const endTime = i > 0 ? new Date(startTime.getTime() + duration) : undefined;
    const status = i === 0 ? 'active' : statuses[Math.floor(Math.random() * statuses.length)];

    const transcriptions = Math.floor(Math.random() * 50) + 10;
    const characters = transcriptions * (Math.floor(Math.random() * 50) + 20);
    const sessionApps = applications.slice(0, Math.floor(Math.random() * 3) + 1);

    return {
      id: `session-${Date.now()}-${i}`,
      startTime,
      endTime: status === 'completed' ? endTime : undefined,
      duration: status === 'completed' ? duration : undefined,
      transcriptions,
      characters,
      applications: sessionApps,
      status,
    };
  });
};

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>(generateMockSessions());
  const [filteredSessions, setFilteredSessions] = useState<Session[]>(sessions);
  const [selectedSession, setSelectedSession] = useState<Session | null>(sessions[0] || null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedApp, setSelectedApp] = useState<string>('all');
  const [notification, setNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);

  // Get unique applications and statuses for filters
  const applications = Array.from(new Set(sessions.flatMap(s => s.applications))).sort();
  const statuses = ['all', 'active', 'completed', 'error'];

  // Simulate real-time session updates
  useEffect(() => {
    const interval = setInterval(() => {
      const activeSession = sessions.find(s => s.status === 'active');
      if (activeSession) {
        setSessions(prev => prev.map(session =>
          session.id === activeSession.id
            ? {
                ...session,
                transcriptions: session.transcriptions + (Math.random() > 0.7 ? 1 : 0),
                characters: session.characters + (Math.random() > 0.8 ? Math.floor(Math.random() * 50) + 10 : 0),
              }
            : session
        ));
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [sessions]);

  // Filter sessions based on search and filters
  useEffect(() => {
    let filtered = sessions;

    if (searchTerm) {
      filtered = filtered.filter(session =>
        session.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        session.applications.some(app => app.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    if (selectedStatus !== 'all') {
      filtered = filtered.filter(session => session.status === selectedStatus);
    }

    if (selectedApp !== 'all') {
      filtered = filtered.filter(session => session.applications.includes(selectedApp));
    }

    setFilteredSessions(filtered);
  }, [sessions, searchTerm, selectedStatus, selectedApp]);

  const handleExportSession = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      const sessionData = JSON.stringify(session, null, 2);
      const blob = new Blob([sessionData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `session-${sessionId.slice(-8)}-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      showNotification('success', `Session ${sessionId.slice(-8)} exported successfully`);
    }
  };

  const handleRefreshSessions = () => {
    setSessions(generateMockSessions());
    showNotification('info', 'Sessions refreshed');
  };

  const showNotification = (type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 3000);
  };

  const getSessionStats = () => {
    const total = filteredSessions.length;
    const active = filteredSessions.filter(s => s.status === 'active').length;
    const completed = filteredSessions.filter(s => s.status === 'completed').length;
    const errors = filteredSessions.filter(s => s.status === 'error').length;
    const totalTranscriptions = filteredSessions.reduce((acc, s) => acc + s.transcriptions, 0);
    const totalCharacters = filteredSessions.reduce((acc, s) => acc + s.characters, 0);

    return { total, active, completed, errors, totalTranscriptions, totalCharacters };
  };

  const stats = getSessionStats();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sessions</h1>
          <p className="text-muted-foreground">
            Voice transcription session history and analytics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshSessions}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <Alert className={cn(
          notification.type === 'success' && "border-green-200 bg-green-50 dark:bg-green-950/20",
          notification.type === 'error' && "border-red-200 bg-red-50 dark:bg-red-950/20",
          notification.type === 'info' && "border-blue-200 bg-blue-50 dark:bg-blue-950/20"
        )}>
          <div className="flex items-center gap-2">
            {notification.type === 'success' && <CheckCircle className="h-4 w-4 text-green-600" />}
            {notification.type === 'error' && <AlertTriangle className="h-4 w-4 text-red-600" />}
            {notification.type === 'info' && <MessageSquare className="h-4 w-4 text-blue-600" />}
            <AlertDescription>{notification.message}</AlertDescription>
          </div>
        </Alert>
      )}

      {/* Session Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">
              {stats.active} active, {stats.completed} completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Transcriptions</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalTranscriptions}</div>
            <p className="text-xs text-muted-foreground">
              Across all sessions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Characters Dictated</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalCharacters.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Total text input
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              {stats.errors} errors
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Session Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Session Filters
          </CardTitle>
          <CardDescription>
            Search and filter voice sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search sessions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background text-sm"
            >
              {statuses.map(status => (
                <option key={status} value={status}>
                  {status.charAt(0).toUpperCase() + status.slice(1)} Sessions
                </option>
              ))}
            </select>

            <select
              value={selectedApp}
              onChange={(e) => setSelectedApp(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background text-sm"
            >
              <option value="all">All Applications</option>
              {applications.map(app => (
                <option key={app} value={app}>{app}</option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Session List and Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Session List */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Session List
              </CardTitle>
              <CardDescription>
                {filteredSessions.length} sessions found
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {filteredSessions.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No sessions found</p>
                  </div>
                ) : (
                  filteredSessions.map((session) => (
                    <div
                      key={session.id}
                      className={cn(
                        "p-3 border rounded-lg cursor-pointer transition-colors hover:bg-muted/50",
                        selectedSession?.id === session.id && "bg-muted border-primary"
                      )}
                      onClick={() => setSelectedSession(session)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {session.status === 'active' && <PlayCircle className="h-4 w-4 text-green-600" />}
                          {session.status === 'completed' && <CheckCircle className="h-4 w-4 text-blue-600" />}
                          {session.status === 'error' && <AlertTriangle className="h-4 w-4 text-red-600" />}
                          <Badge variant="outline" className="text-xs">
                            {session.id.slice(-8)}
                          </Badge>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {session.transcriptions}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {session.startTime.toLocaleDateString()} • {session.startTime.toLocaleTimeString()}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {session.characters.toLocaleString()} chars • {session.applications.length} apps
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Session Details */}
        <div className="lg:col-span-2">
          {selectedSession ? (
            <SessionDetails
              session={selectedSession}
              onExport={handleExportSession}
            />
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-96">
                <div className="text-center text-muted-foreground">
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>Select a session to view details</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

// Helper function for className conditional styling
function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
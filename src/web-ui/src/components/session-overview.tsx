'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Session } from '@/types';
import {
  Clock,
  MessageSquare,
  FileText,
  Monitor,
  Calendar,
  TrendingUp,
  PlayCircle,
  PauseCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { formatDate, formatDuration } from '@/lib/utils';

interface SessionOverviewProps {
  sessions: Session[];
  className?: string;
}

export function SessionOverview({ sessions, className }: SessionOverviewProps) {
  const activeSession = sessions.find(s => s.status === 'active');
  const completedSessions = sessions.filter(s => s.status === 'completed');
  const totalTranscriptions = sessions.reduce((acc, s) => acc + s.transcriptions, 0);
  const totalCharacters = sessions.reduce((acc, s) => acc + s.characters, 0);

  const getSessionIcon = (status: Session['status']) => {
    switch (status) {
      case 'active':
        return <PlayCircle className="h-4 w-4 text-green-600" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-blue-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <PauseCircle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusVariant = (status: Session['status']) => {
    switch (status) {
      case 'active':
        return 'default';
      case 'completed':
        return 'secondary';
      case 'error':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getUniqueApplications = (sessionList: Session[]) => {
    const apps = new Set<string>();
    sessionList.forEach(session => {
      session.applications.forEach(app => apps.add(app));
    });
    return Array.from(apps);
  };

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Session Overview
              </CardTitle>
              <CardDescription>
                Voice transcription sessions and activity history
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {sessions.length} total sessions
              </Badge>
              {activeSession && (
                <Badge variant="default" className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  Active
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {totalTranscriptions}
              </div>
              <div className="text-sm text-muted-foreground">Total Transcriptions</div>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {totalCharacters.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground">Characters Dictated</div>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {completedSessions.length}
              </div>
              <div className="text-sm text-muted-foreground">Completed Sessions</div>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {getUniqueApplications(sessions).length}
              </div>
              <div className="text-sm text-muted-foreground">Applications Used</div>
            </div>
          </div>

          {/* Active Session */}
          {activeSession && (
            <div className="space-y-4">
              <h4 className="text-lg font-medium flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                Current Session
              </h4>
              <div className="p-4 border rounded-lg bg-green-50 dark:bg-green-950/20">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm font-medium text-muted-foreground">Started</div>
                    <div className="text-lg">{formatDate(activeSession.startTime)}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-muted-foreground">Duration</div>
                    <div className="text-lg">
                      {formatDuration(Date.now() - activeSession.startTime.getTime())}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-muted-foreground">Productivity</div>
                    <div className="text-lg">
                      {activeSession.transcriptions} transcriptions, {activeSession.characters} chars
                    </div>
                  </div>
                </div>

                {activeSession.applications.length > 0 && (
                  <div className="mt-4">
                    <div className="text-sm font-medium text-muted-foreground mb-2">Applications Used</div>
                    <div className="flex flex-wrap gap-2">
                      {activeSession.applications.map(app => (
                        <Badge key={app} variant="secondary" className="flex items-center gap-1">
                          <Monitor className="h-3 w-3" />
                          {app}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Recent Sessions */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-lg font-medium">Recent Sessions</h4>
              <Button variant="outline" size="sm">
                View All
              </Button>
            </div>

            {completedSessions.length === 0 && !activeSession ? (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No sessions recorded yet</p>
                <p className="text-sm">Start using voice control to see your session history</p>
              </div>
            ) : (
              <div className="space-y-3">
                {[...(activeSession ? [activeSession] : []), ...completedSessions.slice(0, 5)].map((session) => (
                  <div key={session.id} className="p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        {getSessionIcon(session.status)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant={getStatusVariant(session.status)}>
                              {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
                            </Badge>
                            <span className="text-sm text-muted-foreground">
                              {formatDate(session.startTime)}
                            </span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="text-muted-foreground">Duration: </span>
                              {session.duration ? formatDuration(session.duration) : 'In progress'}
                            </div>
                            <div>
                              <span className="text-muted-foreground">Transcriptions: </span>
                              {session.transcriptions}
                            </div>
                            <div>
                              <span className="text-muted-foreground">Characters: </span>
                              {session.characters.toLocaleString()}
                            </div>
                          </div>

                          {session.applications.length > 0 && (
                            <div className="mt-2">
                              <div className="flex flex-wrap gap-1">
                                {session.applications.slice(0, 3).map(app => (
                                  <Badge key={app} variant="outline" className="text-xs">
                                    {app}
                                  </Badge>
                                ))}
                                {session.applications.length > 3 && (
                                  <Badge variant="outline" className="text-xs">
                                    +{session.applications.length - 3} more
                                  </Badge>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      <Button variant="ghost" size="sm">
                        <TrendingUp className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Application Usage */}
          <div className="space-y-4">
            <h4 className="text-lg font-medium">Application Usage</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {getUniqueApplications(sessions).map(app => {
                const appSessions = sessions.filter(s => s.applications.includes(app));
                const appTranscriptions = appSessions.reduce((acc, s) => acc + s.transcriptions, 0);
                const appCharacters = appSessions.reduce((acc, s) => acc + s.characters, 0);

                return (
                  <div key={app} className="p-3 border rounded-lg text-center">
                    <div className="text-lg font-bold">{app}</div>
                    <div className="text-sm text-muted-foreground">
                      {appTranscriptions} transcriptions
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {appCharacters.toLocaleString()} characters
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
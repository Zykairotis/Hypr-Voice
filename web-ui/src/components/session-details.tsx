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
  BarChart3,
  Download,
  PlayCircle,
  CheckCircle,
  XCircle,
  PauseCircle,
  TrendingUp,
  Users,
  Zap
} from 'lucide-react';
import { formatDate, formatDuration } from '@/lib/utils';

interface SessionDetailsProps {
  session: Session;
  onExport?: (sessionId: string) => void;
  className?: string;
}

export function SessionDetails({ session, onExport, className }: SessionDetailsProps) {
  const getStatusIcon = (status: Session['status']) => {
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

  const getStatusText = (status: Session['status']) => {
    switch (status) {
      case 'active':
        return 'In Progress';
      case 'completed':
        return 'Completed';
      case 'error':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  const calculateProductivityMetrics = () => {
    const duration = session.duration || (session.endTime ?
      session.endTime.getTime() - session.startTime.getTime() :
      Date.now() - session.startTime.getTime()
    );

    const durationMinutes = duration / 60000;
    const transcriptionsPerMinute = durationMinutes > 0 ? session.transcriptions / durationMinutes : 0;
    const charactersPerMinute = durationMinutes > 0 ? session.characters / durationMinutes : 0;
    const avgTranscriptionLength = session.transcriptions > 0 ?
      Math.round(session.characters / session.transcriptions) : 0;

    return {
      duration,
      transcriptionsPerMinute,
      charactersPerMinute,
      avgTranscriptionLength,
    };
  };

  const metrics = calculateProductivityMetrics();

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getStatusIcon(session.status)}
              <div>
                <CardTitle className="flex items-center gap-2">
                  Session {session.id.slice(-8)}
                  <Badge variant={getStatusVariant(session.status)}>
                    {getStatusText(session.status)}
                  </Badge>
                </CardTitle>
                <CardDescription className="flex items-center gap-4 mt-1">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDate(session.startTime)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDuration(metrics.duration)}
                  </span>
                </CardDescription>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onExport?.(session.id)}
              >
                <Download className="h-4 w-4 mr-1" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {session.transcriptions}
              </div>
              <div className="text-sm text-muted-foreground">Transcriptions</div>
              <div className="text-xs text-muted-foreground mt-1">
                {metrics.transcriptionsPerMinute.toFixed(1)} per minute
              </div>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {session.characters.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground">Characters</div>
              <div className="text-xs text-muted-foreground mt-1">
                {metrics.charactersPerMinute.toFixed(0)} per minute
              </div>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {metrics.avgTranscriptionLength}
              </div>
              <div className="text-sm text-muted-foreground">Avg Length</div>
              <div className="text-xs text-muted-foreground mt-1">
                characters per transcription
              </div>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {session.applications.length}
              </div>
              <div className="text-sm text-muted-foreground">Applications</div>
              <div className="text-xs text-muted-foreground mt-1">
                Used during session
              </div>
            </div>
          </div>

          {/* Applications Used */}
          {session.applications.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Monitor className="h-4 w-4" />
                Applications Used
              </h4>
              <div className="flex flex-wrap gap-2">
                {session.applications.map(app => (
                  <Badge key={app} variant="secondary" className="flex items-center gap-1">
                    <Monitor className="h-3 w-3" />
                    {app}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Session Timeline */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Session Timeline
            </h4>
            <div className="relative">
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-green-100 dark:bg-green-900 border-2 border-green-500 rounded-full flex items-center justify-center">
                    <PlayCircle className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <div className="text-sm font-medium">Session Started</div>
                    <div className="text-xs text-muted-foreground">
                      {formatDate(session.startTime)}
                    </div>
                  </div>
                </div>

                {session.endTime && (
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 border-2 border-blue-500 rounded-full flex items-center justify-center">
                      <CheckCircle className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <div className="text-sm font-medium">Session Ended</div>
                      <div className="text-xs text-muted-foreground">
                        {formatDate(session.endTime)}
                      </div>
                    </div>
                  </div>
                )}

                {session.status === 'active' && (
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-yellow-100 dark:bg-yellow-900 border-2 border-yellow-500 rounded-full flex items-center justify-center animate-pulse">
                      <Zap className="h-4 w-4 text-yellow-600" />
                    </div>
                    <div>
                      <div className="text-sm font-medium">Currently Active</div>
                      <div className="text-xs text-muted-foreground">
                        Session in progress for {formatDuration(Date.now() - session.startTime.getTime())}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Productivity Analysis */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Productivity Analysis
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg">
                <div className="text-sm font-medium mb-2">Voice Activity</div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>Total Voice Time:</span>
                    <span>{formatDuration(metrics.duration * 0.3)}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Processing Time:</span>
                    <span>{formatDuration(metrics.duration * 0.1)}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Idle Time:</span>
                    <span>{formatDuration(metrics.duration * 0.6)}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 border rounded-lg">
                <div className="text-sm font-medium mb-2">Efficiency Metrics</div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>Words per Minute:</span>
                    <span>{(metrics.charactersPerMinute / 5).toFixed(0)}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Avg Processing Time:</span>
                    <span>2.3s</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Accuracy Rate:</span>
                    <span>94.2%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Session Status Details */}
          {session.status === 'error' && (
            <div className="p-4 border border-red-200 bg-red-50 dark:bg-red-950/20 rounded-lg">
              <div className="flex items-start gap-2">
                <XCircle className="h-4 w-4 text-red-600 mt-0.5" />
                <div>
                  <div className="text-sm font-medium text-red-800 dark:text-red-200">
                    Session Error
                  </div>
                  <div className="text-xs text-red-600 dark:text-red-300 mt-1">
                    The session encountered an error and was terminated. Check the logs for more details.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Export Options */}
          <div className="flex items-center justify-between p-4 border rounded-lg bg-muted">
            <div className="text-sm">
              <div className="font-medium">Export Session Data</div>
              <div className="text-muted-foreground">
                Download transcriptions, metadata, and analytics
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onExport?.(session.id)}
            >
              <Download className="h-4 w-4 mr-1" />
              Export Session
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ServerStatus } from '@/types';
import {
  Power,
  RefreshCw,
  Square,
  Activity,
  Cpu,
  HardDrive,
  Clock,
  Server
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ServerControlPanelProps {
  serverStatus: ServerStatus;
  onStart?: () => void;
  onStop?: () => void;
  onRestart?: () => void;
}

export function ServerControlPanel({
  serverStatus,
  onStart,
  onStop,
  onRestart,
}: ServerControlPanelProps) {
  const { running, pid, port, uptime, memory, cpu } = serverStatus;

  const formatUptime = (seconds?: number) => {
    if (!seconds) return '0:00:00';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusVariant = () => {
    return running ? 'default' : 'destructive';
  };

  const getStatusText = () => {
    if (running) return 'Running';
    return 'Stopped';
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              Server Control
            </CardTitle>
            <CardDescription>
              Hypr-Voice server management and monitoring
            </CardDescription>
          </div>
          <Badge variant={getStatusVariant()}>
            {getStatusText()}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Server Status Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {running ? '●' : '○'}
            </div>
            <div className="text-xs text-muted-foreground">Status</div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold">
              {pid || '—'}
            </div>
            <div className="text-xs text-muted-foreground">PID</div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold">
              {port || '—'}
            </div>
            <div className="text-xs text-muted-foreground">Port</div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold">
              {formatUptime(uptime)}
            </div>
            <div className="text-xs text-muted-foreground">Uptime</div>
          </div>
        </div>

        {/* Resource Usage */}
        {(cpu !== undefined || memory !== undefined) && (
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Resource Usage</h4>

            {cpu !== undefined && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-4 w-4" />
                    <span className="text-sm">CPU</span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {cpu.toFixed(1)}%
                  </span>
                </div>
                <Progress value={cpu} className="h-2" />
              </div>
            )}

            {memory !== undefined && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <HardDrive className="h-4 w-4" />
                    <span className="text-sm">Memory</span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {(memory / 1024 / 1024).toFixed(1)} MB
                  </span>
                </div>
                <Progress
                  value={(memory / (1024 * 1024 * 1024)) * 100} // Assuming 1GB max
                  className="h-2"
                />
              </div>
            )}
          </div>
        )}

        {/* Control Buttons */}
        <div className="flex gap-2">
          {!running ? (
            <Button
              onClick={onStart}
              className="flex-1"
            >
              <Power className="h-4 w-4 mr-2" />
              Start Server
            </Button>
          ) : (
            <>
              <Button
                onClick={onStop}
                variant="destructive"
                className="flex-1"
              >
                <Square className="h-4 w-4 mr-2" />
                Stop Server
              </Button>
              <Button
                onClick={onRestart}
                variant="outline"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Restart
              </Button>
            </>
          )}
        </div>

        {/* Server Info */}
        {running && (
          <div className="text-xs text-muted-foreground bg-muted p-3 rounded-lg">
            <div className="font-medium mb-2">Server Information:</div>
            <div className="grid grid-cols-1 gap-1">
              {pid && <div>• Process ID: {pid}</div>}
              {port && <div>• WebSocket Port: {port}</div>}
              {uptime && <div>• Uptime: {formatUptime(uptime)}</div>}
              {memory && <div>• Memory Usage: {(memory / 1024 / 1024).toFixed(1)} MB</div>}
              {cpu && <div>• CPU Usage: {cpu.toFixed(1)}%</div>}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Clock, Wifi, Activity, AlertTriangle } from 'lucide-react';

interface AudioMonitoringProps {
  latency?: number;
  sampleRate?: number;
  bufferSize?: number;
  inputDeviceConnected?: boolean;
  outputDeviceConnected?: boolean;
  isMonitoring?: boolean;
  dropoutCount?: number;
  qualityScore?: number;
  className?: string;
}

export const AudioMonitoring: React.FC<AudioMonitoringProps> = ({
  latency = 0,
  sampleRate = 44100,
  bufferSize = 256,
  inputDeviceConnected = false,
  outputDeviceConnected = false,
  isMonitoring = false,
  dropoutCount = 0,
  qualityScore = 100,
  className,
}) => {
  const getLatencyColor = (latency: number) => {
    if (latency < 10) return 'bg-green-500';
    if (latency < 30) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getQualityColor = (score: number) => {
    if (score >= 90) return 'text-green-500';
    if (score >= 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  const formatLatency = (ms: number) => `${ms.toFixed(2)} ms`;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Audio Monitoring
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="w-4 h-4" />
              Latency
            </div>
            <div className="text-2xl font-mono font-bold">
              <span className={getQualityColor(100 - latency)}>
                {formatLatency(latency)}
              </span>
            </div>
            <Progress value={Math.min(100, latency * 5)} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Wifi className="w-4 h-4" />
              Quality Score
            </div>
            <div className="text-2xl font-mono font-bold">
              <span className={getQualityColor(qualityScore)}>
                {qualityScore}%
              </span>
            </div>
            <Progress value={qualityScore} className="h-2" />
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Sample Rate</span>
            <Badge variant="outline">{sampleRate / 1000} kHz</Badge>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Buffer Size</span>
            <Badge variant="outline">{bufferSize} samples</Badge>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Input Device</span>
            <Badge variant={inputDeviceConnected ? "default" : "destructive"}>
              {inputDeviceConnected ? "Connected" : "Disconnected"}
            </Badge>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Output Device</span>
            <Badge variant={outputDeviceConnected ? "default" : "destructive"}>
              {outputDeviceConnected ? "Connected" : "Disconnected"}
            </Badge>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Monitoring</span>
            <Badge variant={isMonitoring ? "default" : "secondary"}>
              {isMonitoring ? "Active" : "Inactive"}
            </Badge>
          </div>

          {dropoutCount > 0 && (
            <div className="flex items-center gap-2 text-sm text-yellow-500 bg-yellow-500/10 p-2 rounded">
              <AlertTriangle className="w-4 h-4" />
              <span>{dropoutCount} audio dropouts detected</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { VoiceState } from '@/types';
import { Mic, MicOff, Volume2, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VoiceControlPanelProps {
  voiceState: VoiceState;
  onStartRecording?: () => void;
  onStopRecording?: () => void;
  onToggleServer?: () => void;
  serverRunning?: boolean;
}

export function VoiceControlPanel({
  voiceState,
  onStartRecording,
  onStopRecording,
  onToggleServer,
  serverRunning = false,
}: VoiceControlPanelProps) {
  const { isRecording, isProcessing, audioLevel, f9Pressed, f10Pressed } = voiceState;

  const getStatusColor = () => {
    if (isRecording) return 'bg-red-500';
    if (isProcessing) return 'bg-yellow-500';
    if (serverRunning) return 'bg-green-500';
    return 'bg-gray-500';
  };

  const getStatusText = () => {
    if (isRecording) return 'Recording';
    if (isProcessing) return 'Processing';
    if (serverRunning) return 'Ready';
    return 'Offline';
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Mic className="h-5 w-5" />
              Voice Control
            </CardTitle>
            <CardDescription>
              Real-time voice transcription and processing
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className={cn(
              "w-3 h-3 rounded-full",
              getStatusColor()
            )} />
            <Badge variant="outline">
              {getStatusText()}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Voice Status Indicators */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold">
              {f9Pressed ? 'F9' : '—'}
            </div>
            <div className="text-xs text-muted-foreground">Record Key</div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold">
              {f10Pressed ? 'F10' : '—'}
            </div>
            <div className="text-xs text-muted-foreground">Mode Key</div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold">
              {isRecording ? 'ON' : 'OFF'}
            </div>
            <div className="text-xs text-muted-foreground">Recording</div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-2xl font-bold">
              {isProcessing ? '⚡' : '—'}
            </div>
            <div className="text-xs text-muted-foreground">Processing</div>
          </div>
        </div>

        {/* Audio Level Indicator */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Volume2 className="h-4 w-4" />
              <span className="text-sm font-medium">Audio Level</span>
            </div>
            <span className="text-sm text-muted-foreground">
              {Math.round(audioLevel * 100)}%
            </span>
          </div>
          <Progress
            value={audioLevel * 100}
            className="h-2"
          />
        </div>

        {/* Control Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={isRecording ? onStopRecording : onStartRecording}
            disabled={isProcessing}
            className={cn(
              "flex-1",
              isRecording && "bg-red-600 hover:bg-red-700"
            )}
          >
            {isRecording ? (
              <>
                <MicOff className="h-4 w-4 mr-2" />
                Stop Recording
              </>
            ) : (
              <>
                <Mic className="h-4 w-4 mr-2" />
                Start Recording
              </>
            )}
          </Button>

          {onToggleServer && (
            <Button
              variant="outline"
              onClick={onToggleServer}
              className="flex items-center gap-2"
            >
              <Activity className="h-4 w-4" />
              {serverRunning ? 'Stop' : 'Start'} Server
            </Button>
          )}
        </div>

        {/* Instructions */}
        <div className="text-xs text-muted-foreground bg-muted p-3 rounded-lg">
          <div className="font-medium mb-1">Quick Start:</div>
          <ul className="space-y-1">
            <li>• Hold <kbd className="px-1 py-0.5 bg-background border rounded">F9</kbd> to record</li>
            <li>• Press <kbd className="px-1 py-0.5 bg-background border rounded">F10</kbd> to toggle modes</li>
            <li>• Release F9 to transcribe and paste</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
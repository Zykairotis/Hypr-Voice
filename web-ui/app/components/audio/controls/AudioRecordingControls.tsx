'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatTime } from '@/lib/audio-utils';
import { RecordingSettings } from '@/lib/audio-utils';
import {
  Play,
  Pause,
  Square,
  Circle,
  Settings,
  Download
} from 'lucide-react';

interface AudioRecordingControlsProps {
  isRecording?: boolean;
  isPaused?: boolean;
  recordingTime?: number;
  onRecord?: () => void;
  onPause?: () => void;
  onStop?: () => void;
  onDownload?: () => void;
  onSettingsChange?: (settings: RecordingSettings) => void;
  className?: string;
}

export const AudioRecordingControls: React.FC<AudioRecordingControlsProps> = ({
  isRecording = false,
  isPaused = false,
  recordingTime = 0,
  onRecord,
  onPause,
  onStop,
  onDownload,
  onSettingsChange,
  className,
}) => {
  const [settings, setSettings] = useState<RecordingSettings>({
    format: 'wav',
    sampleRate: 44100,
    channels: 2,
    autoGain: true,
  });

  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSettingChange = (key: keyof RecordingSettings, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    onSettingsChange?.(newSettings);
  };

  const getRecordButtonIcon = () => {
    if (isRecording) {
      return <Pause className="w-6 h-6" />;
    }
    return <Circle className="w-6 h-6 fill-current" />;
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Recording Controls
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            <Settings className="w-5 h-5" />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-center gap-4">
          <Button
            size="lg"
            variant={isRecording ? "secondary" : "destructive"}
            onClick={isRecording ? onPause : onRecord}
            disabled={isPaused}
            className="w-20 h-20 rounded-full"
          >
            {getRecordButtonIcon()}
          </Button>
          <Button
            size="lg"
            variant="outline"
            onClick={onStop}
            disabled={!isRecording && !isPaused}
            className="w-20 h-20 rounded-full"
          >
            <Square className="w-6 h-6" />
          </Button>
          <Button
            size="lg"
            variant="outline"
            onClick={onDownload}
            disabled={recordingTime === 0}
            className="w-20 h-20 rounded-full"
          >
            <Download className="w-6 h-6" />
          </Button>
        </div>

        <div className="text-center">
          <div className="text-3xl font-mono font-bold">
            {formatTime(recordingTime)}
          </div>
          <div className="text-sm text-muted-foreground">
            {isRecording && !isPaused && 'Recording...'}
            {isRecording && isPaused && 'Paused'}
            {!isRecording && !isPaused && 'Ready'}
          </div>
        </div>

        {showAdvanced && (
          <div className="space-y-4 pt-4 border-t">
            <div className="space-y-2">
              <Label>Format</Label>
              <Select
                value={settings.format}
                onValueChange={(value) => handleSettingChange('format', value as any)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="wav">WAV (Uncompressed)</SelectItem>
                  <SelectItem value="mp3">MP3 (Compressed)</SelectItem>
                  <SelectItem value="flac">FLAC (Lossless)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Sample Rate</Label>
              <Select
                value={settings.sampleRate.toString()}
                onValueChange={(value) => handleSettingChange('sampleRate', parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="22050">22.05 kHz</SelectItem>
                  <SelectItem value="44100">44.1 kHz (CD)</SelectItem>
                  <SelectItem value="48000">48 kHz</SelectItem>
                  <SelectItem value="96000">96 kHz</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Channels</Label>
              <Select
                value={settings.channels.toString()}
                onValueChange={(value) => handleSettingChange('channels', parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Mono</SelectItem>
                  <SelectItem value="2">Stereo</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {settings.format === 'mp3' && (
              <div className="space-y-2">
                <Label>Bitrate</Label>
                <Select
                  value={settings.bitrate?.toString() || '320'}
                  onValueChange={(value) => handleSettingChange('bitrate', parseInt(value))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="128">128 kbps</SelectItem>
                    <SelectItem value="192">192 kbps</SelectItem>
                    <SelectItem value="256">256 kbps</SelectItem>
                    <SelectItem value="320">320 kbps (Max)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-2">
              <Label>Max Length (minutes, 0 = unlimited)</Label>
              <Slider
                value={[settings.maxLength || 0]}
                onValueChange={(value) => handleSettingChange('maxLength', value[0] || undefined)}
                max={60}
                min={0}
                step={5}
                className="w-full"
              />
              <div className="text-sm text-muted-foreground text-center">
                {settings.maxLength || 'Unlimited'}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="auto-gain">Auto Gain Control</Label>
              <Switch
                id="auto-gain"
                checked={settings.autoGain}
                onCheckedChange={(checked) => handleSettingChange('autoGain', checked)}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

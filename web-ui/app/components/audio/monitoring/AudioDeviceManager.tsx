'use client';

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { AudioDevice, AudioSettings } from '@/lib/audio-utils';
import { Mic, Headphones, Settings, TestTube } from 'lucide-react';

interface AudioDeviceManagerProps {
  settings: AudioSettings;
  onSettingsChange?: (settings: AudioSettings) => void;
  onTestInput?: (deviceId: string) => void;
  onTestOutput?: (deviceId: string) => void;
  className?: string;
}

export const AudioDeviceManager: React.FC<AudioDeviceManagerProps> = ({
  settings,
  onSettingsChange,
  onTestInput,
  onTestOutput,
  className,
}) => {
  const [inputDevices, setInputDevices] = useState<AudioDevice[]>([]);
  const [outputDevices, setOutputDevices] = useState<AudioDevice[]>([]);
  const [isEnumerating, setIsEnumerating] = useState(false);

  const enumerateDevices = async () => {
    setIsEnumerating(true);
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();

      const inputs = devices
        .filter(device => device.kind === 'audioinput')
        .map(device => ({
          deviceId: device.deviceId,
          label: device.label || 'Microphone',
          kind: device.kind,
          groupId: device.groupId,
        }));

      const outputs = devices
        .filter(device => device.kind === 'audiooutput')
        .map(device => ({
          deviceId: device.deviceId,
          label: device.label || 'Speaker',
          kind: device.kind,
          groupId: device.groupId,
        }));

      setInputDevices(inputs);
      setOutputDevices(outputs);
    } catch (error) {
      console.error('Failed to enumerate devices:', error);
    } finally {
      setIsEnumerating(false);
    }
  };

  useEffect(() => {
    enumerateDevices();
  }, []);

  const handleSettingChange = (key: keyof AudioSettings, value: any) => {
    onSettingsChange?.({ ...settings, [key]: value });
  };

  const getDeviceIcon = (device: AudioDevice) => {
    return device.kind === 'audioinput' ? <Mic className="w-4 h-4" /> : <Headphones className="w-4 h-4" />;
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Audio Device Manager
          </div>
          <Button onClick={enumerateDevices} disabled={isEnumerating} size="sm">
            {isEnumerating ? 'Scanning...' : 'Refresh'}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-3">
          <Label className="flex items-center gap-2">
            <Mic className="w-4 h-4" />
            Input Device
          </Label>
          <Select
            value={settings.inputDevice}
            onValueChange={(value) => handleSettingChange('inputDevice', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select input device" />
            </SelectTrigger>
            <SelectContent>
              {inputDevices.map((device) => (
                <SelectItem key={device.deviceId} value={device.deviceId}>
                  <div className="flex items-center gap-2">
                    {getDeviceIcon(device)}
                    {device.label}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {settings.inputDevice && (
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => onTestInput?.(settings.inputDevice!)}
                className="flex-1"
              >
                <TestTube className="w-4 h-4 mr-2" />
                Test Input
              </Button>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <Label className="flex items-center gap-2">
            <Headphones className="w-4 h-4" />
            Output Device
          </Label>
          <Select
            value={settings.outputDevice}
            onValueChange={(value) => handleSettingChange('outputDevice', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select output device" />
            </SelectTrigger>
            <SelectContent>
              {outputDevices.map((device) => (
                <SelectItem key={device.deviceId} value={device.deviceId}>
                  <div className="flex items-center gap-2">
                    {getDeviceIcon(device)}
                    {device.label}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {settings.outputDevice && (
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => onTestOutput?.(settings.outputDevice!)}
                className="flex-1"
              >
                <TestTube className="w-4 h-4 mr-2" />
                Test Output
              </Button>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-3">
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
                <SelectItem value="44100">44.1 kHz</SelectItem>
                <SelectItem value="48000">48 kHz</SelectItem>
                <SelectItem value="96000">96 kHz</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-3">
            <Label>Buffer Size</Label>
            <Select
              value={settings.bufferSize.toString()}
              onValueChange={(value) => handleSettingChange('bufferSize', parseInt(value))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="128">128 samples</SelectItem>
                <SelectItem value="256">256 samples</SelectItem>
                <SelectItem value="512">512 samples</SelectItem>
                <SelectItem value="1024">1024 samples</SelectItem>
                <SelectItem value="2048">2048 samples</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Input Gain</Label>
            <Badge variant="secondary">{settings.inputGain}%</Badge>
          </div>
          <Slider
            value={[settings.inputGain]}
            onValueChange={(value) => handleSettingChange('inputGain', value[0])}
            max={150}
            min={0}
            step={1}
            className="w-full"
          />
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Output Gain</Label>
            <Badge variant="secondary">{settings.outputGain}%</Badge>
          </div>
          <Slider
            value={[settings.outputGain]}
            onValueChange={(value) => handleSettingChange('outputGain', value[0])}
            max={150}
            min={0}
            step={1}
            className="w-full"
          />
        </div>
      </CardContent>
    </Card>
  );
};

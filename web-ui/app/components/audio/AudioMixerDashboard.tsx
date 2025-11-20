'use client';

import React, { useEffect, useState, useRef } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { AudioLevelMonitor } from './AudioLevelMonitor';
import './styles.css';
import { AudioWaveformDisplay } from './visualization/AudioWaveformDisplay';
import { SpectrumAnalyzer } from './visualization/SpectrumAnalyzer';
import { LEDVUMeter } from './visualization/LEDVUMeter';
import { ThreeDAudioVisualization } from './visualization/ThreeDAudioVisualization';
import { AudioRecordingControls } from './controls/AudioRecordingControls';
import { AudioPlaybackMixer } from './controls/AudioPlaybackMixer';
import { AudioEffects } from './effects/AudioEffects';
import { AudioDeviceManager } from './monitoring/AudioDeviceManager';
import { AudioMonitoring } from './monitoring/AudioMonitoring';
import {
  AudioLevelData,
  ChannelConfig,
  EffectConfig,
  AudioSettings,
  RecordingSettings,
  channelColors,
} from '@/lib/audio-utils';
import {
  Mic,
  Volume2,
  Waveform,
  Radio,
  Settings,
  Activity,
} from 'lucide-react';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';

export const AudioMixerDashboard: React.FC = () => {
  useKeyboardShortcuts({
    'ctrl+r': handleRecord,
    'ctrl+s': handleStop,
    'escape': handleStop,
  });

  function handleRecord() {
    if (!isRecording) {
      setIsRecording(true);
      setIsPaused(false);
      setRecordingTime(0);
    }
  }

  function handleStop() {
    setIsRecording(false);
    setIsPaused(false);
    setRecordingTime(0);
  }
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState<AudioLevelData>({
    rms: 0,
    peak: 0,
    db: -60,
  });
  const [frequencyData, setFrequencyData] = useState<Uint8Array>(new Uint8Array(0));
  const [audioBuffer, setAudioBuffer] = useState<Float32Array>(new Float32Array(0));
  const [channels, setChannels] = useState<ChannelConfig[]>([
    { id: '1', name: 'Channel 1', volume: 80, muted: false, solo: false, color: channelColors[0] },
    { id: '2', name: 'Channel 2', volume: 75, muted: false, solo: false, color: channelColors[1] },
  ]);
  const [effects, setEffects] = useState<EffectConfig>({
    noiseReduction: 0,
    echoCancellation: true,
    normalization: false,
    compression: {
      enabled: false,
      threshold: -20,
      ratio: 4,
      attack: 5,
      release: 50,
    },
  });
  const [audioSettings, setAudioSettings] = useState<AudioSettings>({
    sampleRate: 44100,
    bufferSize: 256,
    inputGain: 100,
    outputGain: 100,
    monitoringEnabled: true,
  });

  const initAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      audioContextRef.current = new AudioContext();
      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();

      analyserRef.current.fftSize = 2048;
      sourceRef.current.connect(analyserRef.current);

      const frequencyDataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      const audioBufferArray = new Float32Array(analyserRef.current.fftSize);

      const updateAudioData = () => {
        if (analyserRef.current) {
          analyserRef.current.getByteFrequencyData(frequencyDataArray);
          analyserRef.current.getFloatTimeDomainData(audioBufferArray);

          const rms = Math.sqrt(
            audioBufferArray.reduce((sum, val) => sum + val * val, 0) / audioBufferArray.length
          );
          const peak = Math.max(...audioBufferArray.map(val => Math.abs(val)));
          const db = 20 * Math.log10(Math.max(0.0001, rms));

          setAudioLevel({ rms, peak, db });
          setFrequencyData(frequencyDataArray);
          setAudioBuffer(audioBufferArray);
        }

        if (isRecording && !isPaused) {
          setRecordingTime(prev => prev + 0.1);
        }

        requestAnimationFrame(updateAudioData);
      };

      updateAudioData();
    } catch (error) {
      console.error('Failed to initialize audio:', error);
    }
  };

  useEffect(() => {
    initAudio();
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const handleRecord = () => {
    if (!isRecording) {
      setIsRecording(true);
      setIsPaused(false);
      setRecordingTime(0);
    }
  };

  const handlePause = () => {
    setIsPaused(!isPaused);
  };

  const handleStop = () => {
    setIsRecording(false);
    setIsPaused(false);
    setRecordingTime(0);
  };

  const handleChannelUpdate = (channelId: string, updates: Partial<ChannelConfig>) => {
    setChannels(channels.map(ch =>
      ch.id === channelId ? { ...ch, ...updates } : ch
    ));
  };

  const handleChannelAdd = () => {
    const newChannel: ChannelConfig = {
      id: Date.now().toString(),
      name: `Channel ${channels.length + 1}`,
      volume: 80,
      muted: false,
      solo: false,
      color: channelColors[channels.length % channelColors.length],
    };
    setChannels([...channels, newChannel]);
  };

  const handleChannelRemove = (channelId: string) => {
    setChannels(channels.filter(ch => ch.id !== channelId));
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-4xl font-bold flex items-center gap-3">
          <Volume2 className="w-10 h-10" />
          Audio/Visualization Mixer
        </h1>
      </div>

      <Tabs defaultValue="monitor" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="monitor">Monitor</TabsTrigger>
          <TabsTrigger value="waveform">Waveform</TabsTrigger>
          <TabsTrigger value="spectrum">Spectrum</TabsTrigger>
          <TabsTrigger value="3d">3D Visual</TabsTrigger>
          <TabsTrigger value="mixer">Mixer</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="monitor" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center mb-4">
                  <Mic className="w-8 h-8 mx-auto mb-2" />
                  <h3 className="text-lg font-semibold">Input Level</h3>
                </div>
                <AudioLevelMonitor
                  level={audioLevel}
                  isActive={isRecording || audioSettings.monitoringEnabled}
                  orientation="vertical"
                  size="lg"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center mb-4">
                  <Activity className="w-8 h-8 mx-auto mb-2" />
                  <h3 className="text-lg font-semibold">LED VU Meter</h3>
                </div>
                <div className="flex justify-center">
                  <LEDVUMeter
                    level={Math.max(0, (audioLevel.db + 60) / 60)}
                    orientation="vertical"
                    size="lg"
                  />
                </div>
              </CardContent>
            </Card>

            <AudioMonitoring
              latency={10 + Math.random() * 5}
              sampleRate={audioSettings.sampleRate}
              bufferSize={audioSettings.bufferSize}
              inputDeviceConnected={true}
              outputDeviceConnected={true}
              isMonitoring={audioSettings.monitoringEnabled}
              qualityScore={95 + Math.random() * 5}
            />
          </div>

          <Card>
            <CardContent className="pt-6">
              <h3 className="text-lg font-semibold mb-4">Recording Controls</h3>
              <AudioRecordingControls
                isRecording={isRecording}
                isPaused={isPaused}
                recordingTime={recordingTime}
                onRecord={handleRecord}
                onPause={handlePause}
                onStop={handleStop}
                onSettingsChange={(settings) => console.log('Recording settings:', settings)}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="waveform" className="space-y-6">
          <Card>
            <CardContent className="pt-6">
              <div className="mb-4">
                <Waveform className="w-8 h-8 inline-block mr-2" />
                <h3 className="text-2xl font-semibold inline-block">Real-time Waveform</h3>
              </div>
              <AudioWaveformDisplay
                buffer={audioBuffer}
                isRecording={isRecording}
                width={1200}
                height={300}
                showGrid={true}
                color="#3b82f6"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="spectrum" className="space-y-6">
          <Card>
            <CardContent className="pt-6">
              <div className="mb-4">
                <Radio className="w-8 h-8 inline-block mr-2" />
                <h3 className="text-2xl font-semibold inline-block">Frequency Spectrum</h3>
              </div>
              <SpectrumAnalyzer
                frequencyData={frequencyData}
                width={1200}
                height={400}
                barCount={64}
                gradient={true}
                showGrid={true}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="3d" className="space-y-6">
          <Card>
            <CardContent className="pt-6">
              <div className="mb-4">
                <Volume2 className="w-8 h-8 inline-block mr-2" />
                <h3 className="text-2xl font-semibold inline-block">3D Audio Visualization</h3>
              </div>
              <ThreeDAudioVisualization
                frequencyData={frequencyData}
                width={1200}
                height={600}
                color="#8b5cf6"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="mixer" className="space-y-6">
          <AudioPlaybackMixer
            channels={channels}
            onChannelUpdate={handleChannelUpdate}
            onChannelAdd={handleChannelAdd}
            onChannelRemove={handleChannelRemove}
          />

          <Card>
            <CardContent className="pt-6">
              <AudioEffects
                effects={effects}
                onEffectsChange={setEffects}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AudioDeviceManager
              settings={audioSettings}
              onSettingsChange={setAudioSettings}
              onTestInput={(deviceId) => console.log('Testing input:', deviceId)}
              onTestOutput={(deviceId) => console.log('Testing output:', deviceId)}
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

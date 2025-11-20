export interface AudioLevelData {
  rms: number;
  peak: number;
  db: number;
}

export interface AudioDevice {
  deviceId: string;
  label: string;
  kind: MediaDeviceKind;
  groupId: string;
}

export interface AudioSettings {
  sampleRate: number;
  bufferSize: number;
  inputDevice?: string;
  outputDevice?: string;
  inputGain: number;
  outputGain: number;
  monitoringEnabled: boolean;
}

export interface RecordingSettings {
  format: 'wav' | 'mp3' | 'flac';
  bitrate?: number;
  sampleRate: number;
  channels: number;
  maxLength?: number;
  autoGain: boolean;
}

export interface ChannelConfig {
  id: string;
  name: string;
  volume: number;
  muted: boolean;
  solo: boolean;
  color: string;
}

export interface EffectConfig {
  noiseReduction: number;
  echoCancellation: boolean;
  normalization: boolean;
  compression: {
    enabled: boolean;
    threshold: number;
    ratio: number;
    attack: number;
    release: number;
  };
}

export interface VisualizationConfig {
  type: 'vu-meter' | 'waveform' | 'spectrum' | 'oscilloscope' | '3d';
  theme: string;
  refreshRate: number;
  showGrid: boolean;
  showPeaks: boolean;
}

export const formatDecibels = (value: number): string => {
  return `${value > 0 ? '+' : ''}${value.toFixed(1)} dB`;
};

export const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

export const calculateRMS = (buffer: Float32Array): number => {
  let sum = 0;
  for (let i = 0; i < buffer.length; i++) {
    sum += buffer[i] * buffer[i];
  }
  return Math.sqrt(sum / buffer.length);
};

export const calculatePeak = (buffer: Float32Array): number => {
  let peak = 0;
  for (let i = 0; i < buffer.length; i++) {
    peak = Math.max(peak, Math.abs(buffer[i]));
  }
  return peak;
};

export const dbToLinear = (db: number): number => {
  return Math.pow(10, db / 20);
};

export const linearToDb = (linear: number): number => {
  return 20 * Math.log10(linear);
};

export const getColorForLevel = (db: number): string => {
  if (db > -6) return '#ef4444';
  if (db > -18) return '#f59e0b';
  return '#22c55e';
};

export const channelColors = [
  '#3b82f6',
  '#8b5cf6',
  '#ec4899',
  '#f59e0b',
  '#10b981',
  '#06b6d4',
  '#6366f1',
  '#f97316',
];

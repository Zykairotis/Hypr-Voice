"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Settings,
  Save,
  RotateCcw,
  Download,
  Upload,
  HardDrive,
  Volume2,
  Zap,
  Globe,
  Shield,
  Palette,
  Keyboard,
  FileAudio,
  Cloud,
  Database,
  Trash2
} from "lucide-react";
import { toast } from "sonner";

interface TTSSettings {
  audio: {
    sampleRate: number;
    bitRate: number;
    format: string;
    normalize: boolean;
    noiseReduction: boolean;
  };
  playback: {
    autoPlay: boolean;
    fadeIn: boolean;
    fadeOut: boolean;
    crossfade: boolean;
    crossfadeDuration: number;
    defaultVolume: number;
  };
  synthesis: {
    chunkSize: number;
    queueSize: number;
    concurrent: boolean;
    maxConcurrent: number;
    retryAttempts: number;
    timeout: number;
  };
  providers: {
    kokoro: {
      enabled: boolean;
      url: string;
      workers: number;
    };
    deepgram: {
      enabled: boolean;
      apiKey: string;
      endpoint: string;
    };
    elevenlabs: {
      enabled: boolean;
      apiKey: string;
      model: string;
    };
  };
  ui: {
    theme: string;
    visualization: boolean;
    showWaveform: boolean;
    showSpectrum: boolean;
    animations: boolean;
    compactMode: boolean;
  };
  shortcuts: {
    enabled: boolean;
    synthesize: string;
    play: string;
    pause: string;
    stop: string;
  };
  cache: {
    enabled: boolean;
    maxSize: number;
    ttl: number;
    location: string;
  };
}

export default function TTSAdvancedSettings() {
  const [settings, setSettings] = useState<TTSSettings>({
    audio: {
      sampleRate: 48000,
      bitRate: 128,
      format: "mp3",
      normalize: true,
      noiseReduction: false,
    },
    playback: {
      autoPlay: false,
      fadeIn: true,
      fadeOut: true,
      crossfade: false,
      crossfadeDuration: 3,
      defaultVolume: 1.0,
    },
    synthesis: {
      chunkSize: 1000,
      queueSize: 5,
      concurrent: true,
      maxConcurrent: 3,
      retryAttempts: 3,
      timeout: 30000,
    },
    providers: {
      kokoro: {
        enabled: true,
        url: "http://localhost:8880",
        workers: 2,
      },
      deepgram: {
        enabled: false,
        apiKey: "",
        endpoint: "https://api.deepgram.com",
      },
      elevenlabs: {
        enabled: false,
        apiKey: "",
        model: "eleven_turbo_v2_5",
      },
    },
    ui: {
      theme: "system",
      visualization: true,
      showWaveform: true,
      showSpectrum: false,
      animations: true,
      compactMode: false,
    },
    shortcuts: {
      enabled: true,
      synthesize: "Ctrl+Enter",
      play: "Space",
      pause: "Ctrl+Space",
      stop: "Escape",
    },
    cache: {
      enabled: true,
      maxSize: 1000,
      ttl: 3600,
      location: "./cache",
    },
  });

  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = () => {
    const saved = localStorage.getItem("tts-settings");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSettings({ ...settings, ...parsed });
      } catch (error) {
        console.error("Failed to load settings:", error);
      }
    }
  };

  const saveSettings = () => {
    localStorage.setItem("tts-settings", JSON.stringify(settings));
    setHasChanges(false);
    toast.success("Settings saved successfully");
  };

  const resetSettings = () => {
    if (confirm("Are you sure you want to reset all settings to defaults? This cannot be undone.")) {
      localStorage.removeItem("tts-settings");
      window.location.reload();
    }
  };

  const exportSettings = () => {
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "tts-settings.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Settings exported");
  };

  const importSettings = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const imported = JSON.parse(e.target?.result as string);
        setSettings({ ...settings, ...imported });
        setHasChanges(true);
        toast.success("Settings imported. Don't forget to save!");
      } catch (error) {
        toast.error("Invalid settings file");
      }
    };
    reader.readAsText(file);
  };

  const clearCache = () => {
    if (confirm("Are you sure you want to clear the TTS cache?")) {
      localStorage.removeItem("tts-audio-files");
      localStorage.removeItem("tts-audio-library");
      localStorage.removeItem("tts-job-history");
      toast.success("Cache cleared");
    }
  };

  const updateSettings = (path: string, value: any) => {
    setSettings((prev) => {
      const newSettings = { ...prev };
      const keys = path.split(".");
      let current: any = newSettings;

      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }

      current[keys[keys.length - 1]] = value;
      return newSettings;
    });
    setHasChanges(true);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Settings className="w-6 h-6 text-purple-400" />
            Advanced Settings
          </h2>
          <p className="text-muted-foreground mt-1">
            Configure TTS system parameters and preferences
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportSettings}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" onClick={() => document.getElementById("import-settings")?.click()}>
            <Upload className="w-4 h-4 mr-2" />
            Import
          </Button>
          <input
            id="import-settings"
            type="file"
            accept=".json"
            onChange={importSettings}
            className="hidden"
          />
          <Button variant="outline" onClick={resetSettings}>
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>
          <Button onClick={saveSettings} disabled={!hasChanges}>
            <Save className="w-4 h-4 mr-2" />
            Save
          </Button>
        </div>
      </div>

      {hasChanges && (
        <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <div className="flex items-center gap-2 text-yellow-400">
            <Shield className="w-4 h-4" />
            <span className="font-medium">Unsaved Changes</span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            You have unsaved changes. Don't forget to save your settings.
          </p>
        </div>
      )}

      {/* Audio Settings */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Volume2 className="w-5 h-5" />
            Audio Settings
          </CardTitle>
          <CardDescription>
            Configure audio output quality and format
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Sample Rate: {settings.audio.sampleRate} Hz</Label>
              <Select
                value={settings.audio.sampleRate.toString()}
                onValueChange={(value) => updateSettings("audio.sampleRate", parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="22050">22050 Hz</SelectItem>
                  <SelectItem value="44100">44100 Hz</SelectItem>
                  <SelectItem value="48000">48000 Hz</SelectItem>
                  <SelectItem value="96000">96000 Hz</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Bit Rate: {settings.audio.bitRate} kbps</Label>
              <Slider
                value={[settings.audio.bitRate]}
                onValueChange={(value) => updateSettings("audio.bitRate", value[0])}
                min={64}
                max={320}
                step={64}
              />
            </div>

            <div className="space-y-2">
              <Label>Output Format</Label>
              <Select
                value={settings.audio.format}
                onValueChange={(value) => updateSettings("audio.format", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mp3">MP3</SelectItem>
                  <SelectItem value="wav">WAV</SelectItem>
                  <SelectItem value="ogg">OGG</SelectItem>
                  <SelectItem value="flac">FLAC</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Normalize Audio</Label>
                <Switch
                  checked={settings.audio.normalize}
                  onCheckedChange={(checked) => updateSettings("audio.normalize", checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Noise Reduction</Label>
                <Switch
                  checked={settings.audio.noiseReduction}
                  onCheckedChange={(checked) => updateSettings("audio.noiseReduction", checked)}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Playback Settings */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileAudio className="w-5 h-5" />
            Playback Settings
          </CardTitle>
          <CardDescription>
            Configure audio playback behavior
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Auto-play on Synthesis</Label>
                <Switch
                  checked={settings.playback.autoPlay}
                  onCheckedChange={(checked) => updateSettings("playback.autoPlay", checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Fade In</Label>
                <Switch
                  checked={settings.playback.fadeIn}
                  onCheckedChange={(checked) => updateSettings("playback.fadeIn", checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Fade Out</Label>
                <Switch
                  checked={settings.playback.fadeOut}
                  onCheckedChange={(checked) => updateSettings("playback.fadeOut", checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Crossfade</Label>
                <Switch
                  checked={settings.playback.crossfade}
                  onCheckedChange={(checked) => updateSettings("playback.crossfade", checked)}
                />
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Crossfade Duration: {settings.playback.crossfadeDuration}s</Label>
                <Slider
                  value={[settings.playback.crossfadeDuration]}
                  onValueChange={(value) => updateSettings("playback.crossfadeDuration", value[0])}
                  min={1}
                  max={10}
                  step={1}
                  disabled={!settings.playback.crossfade}
                />
              </div>

              <div className="space-y-2">
                <Label>Default Volume: {Math.round(settings.playback.defaultVolume * 100)}%</Label>
                <Slider
                  value={[settings.playback.defaultVolume]}
                  onValueChange={(value) => updateSettings("playback.defaultVolume", value[0])}
                  min={0}
                  max={1}
                  step={0.1}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Synthesis Settings */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Synthesis Settings
          </CardTitle>
          <CardDescription>
            Configure TTS synthesis behavior and performance
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Chunk Size: {settings.synthesis.chunkSize} characters</Label>
                <Slider
                  value={[settings.synthesis.chunkSize]}
                  onValueChange={(value) => updateSettings("synthesis.chunkSize", value[0])}
                  min={100}
                  max={5000}
                  step={100}
                />
              </div>

              <div className="space-y-2">
                <Label>Queue Size: {settings.synthesis.queueSize}</Label>
                <Slider
                  value={[settings.synthesis.queueSize]}
                  onValueChange={(value) => updateSettings("synthesis.queueSize", value[0])}
                  min={1}
                  max={20}
                  step={1}
                />
              </div>

              <div className="space-y-2">
                <Label>Max Concurrent: {settings.synthesis.maxConcurrent}</Label>
                <Slider
                  value={[settings.synthesis.maxConcurrent]}
                  onValueChange={(value) => updateSettings("synthesis.maxConcurrent", value[0])}
                  min={1}
                  max={10}
                  step={1}
                />
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Enable Concurrency</Label>
                <Switch
                  checked={settings.synthesis.concurrent}
                  onCheckedChange={(checked) => updateSettings("synthesis.concurrent", checked)}
                />
              </div>

              <div className="space-y-2">
                <Label>Retry Attempts: {settings.synthesis.retryAttempts}</Label>
                <Slider
                  value={[settings.synthesis.retryAttempts]}
                  onValueChange={(value) => updateSettings("synthesis.retryAttempts", value[0])}
                  min={0}
                  max={10}
                  step={1}
                />
              </div>

              <div className="space-y-2">
                <Label>Timeout: {settings.synthesis.timeout / 1000}s</Label>
                <Slider
                  value={[settings.synthesis.timeout]}
                  onValueChange={(value) => updateSettings("synthesis.timeout", value[0])}
                  min={5000}
                  max={120000}
                  step={5000}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Provider Settings */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5" />
            Provider Configuration
          </CardTitle>
          <CardDescription>
            Configure TTS provider endpoints and credentials
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Kokoro */}
          <div className="space-y-3 p-4 rounded-lg bg-muted/50">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Kokoro TTS</h3>
              <Switch
                checked={settings.providers.kokoro.enabled}
                onCheckedChange={(checked) => updateSettings("providers.kokoro.enabled", checked)}
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Server URL</Label>
                <Input
                  value={settings.providers.kokoro.url}
                  onChange={(e) => updateSettings("providers.kokoro.url", e.target.value)}
                  placeholder="http://localhost:8880"
                />
              </div>
              <div className="space-y-2">
                <Label>Workers: {settings.providers.kokoro.workers}</Label>
                <Slider
                  value={[settings.providers.kokoro.workers]}
                  onValueChange={(value) => updateSettings("providers.kokoro.workers", value[0])}
                  min={1}
                  max={8}
                  step={1}
                />
              </div>
            </div>
          </div>

          {/* Deepgram */}
          <div className="space-y-3 p-4 rounded-lg bg-muted/50">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Deepgram</h3>
              <Switch
                checked={settings.providers.deepgram.enabled}
                onCheckedChange={(checked) => updateSettings("providers.deepgram.enabled", checked)}
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>API Key</Label>
                <Input
                  type="password"
                  value={settings.providers.deepgram.apiKey}
                  onChange={(e) => updateSettings("providers.deepgram.apiKey", e.target.value)}
                  placeholder="••••••••••••••••"
                />
              </div>
              <div className="space-y-2">
                <Label>Endpoint</Label>
                <Input
                  value={settings.providers.deepgram.endpoint}
                  onChange={(e) => updateSettings("providers.deepgram.endpoint", e.target.value)}
                  placeholder="https://api.deepgram.com"
                />
              </div>
            </div>
          </div>

          {/* ElevenLabs */}
          <div className="space-y-3 p-4 rounded-lg bg-muted/50">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">ElevenLabs</h3>
              <Switch
                checked={settings.providers.elevenlabs.enabled}
                onCheckedChange={(checked) => updateSettings("providers.elevenlabs.enabled", checked)}
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>API Key</Label>
                <Input
                  type="password"
                  value={settings.providers.elevenlabs.apiKey}
                  onChange={(e) => updateSettings("providers.elevenlabs.apiKey", e.target.value)}
                  placeholder="••••••••••••••••"
                />
              </div>
              <div className="space-y-2">
                <Label>Model</Label>
                <Select
                  value={settings.providers.elevenlabs.model}
                  onValueChange={(value) => updateSettings("providers.elevenlabs.model", value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="eleven_turbo_v2_5">Eleven Turbo v2.5</SelectItem>
                    <SelectItem value="eleven_flash_v2_5">Eleven Flash v2.5</SelectItem>
                    <SelectItem value="eleven_multilingual_v2">Eleven Multilingual v2</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* UI Settings */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="w-5 h-5" />
            User Interface
          </CardTitle>
          <CardDescription>
            Customize the TTS control panel appearance and behavior
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Theme</Label>
                <Select
                  value={settings.ui.theme}
                  onValueChange={(value) => updateSettings("ui.theme", value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="system">System</SelectItem>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Audio Visualization</Label>
                  <Switch
                    checked={settings.ui.visualization}
                    onCheckedChange={(checked) => updateSettings("ui.visualization", checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Show Waveform</Label>
                  <Switch
                    checked={settings.ui.showWaveform}
                    onCheckedChange={(checked) => updateSettings("ui.showWaveform", checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Show Spectrum</Label>
                  <Switch
                    checked={settings.ui.showSpectrum}
                    onCheckedChange={(checked) => updateSettings("ui.showSpectrum", checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Animations</Label>
                  <Switch
                    checked={settings.ui.animations}
                    onCheckedChange={(checked) => updateSettings("ui.animations", checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Compact Mode</Label>
                  <Switch
                    checked={settings.ui.compactMode}
                    onCheckedChange={(checked) => updateSettings("ui.compactMode", checked)}
                  />
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold flex items-center gap-2">
                <Keyboard className="w-4 h-4" />
                Keyboard Shortcuts
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Enable Shortcuts</Label>
                  <Switch
                    checked={settings.shortcuts.enabled}
                    onCheckedChange={(checked) => updateSettings("shortcuts.enabled", checked)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Synthesize</Label>
                  <Input
                    value={settings.shortcuts.synthesize}
                    onChange={(e) => updateSettings("shortcuts.synthesize", e.target.value)}
                    disabled={!settings.shortcuts.enabled}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Play/Pause</Label>
                  <Input
                    value={settings.shortcuts.play}
                    onChange={(e) => updateSettings("shortcuts.play", e.target.value)}
                    disabled={!settings.shortcuts.enabled}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Stop</Label>
                  <Input
                    value={settings.shortcuts.stop}
                    onChange={(e) => updateSettings("shortcuts.stop", e.target.value)}
                    disabled={!settings.shortcuts.enabled}
                  />
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cache Settings */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Cache Management
          </CardTitle>
          <CardDescription>
            Configure audio file caching for faster playback
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Enable Cache</Label>
                <Switch
                  checked={settings.cache.enabled}
                  onCheckedChange={(checked) => updateSettings("cache.enabled", checked)}
                />
              </div>
              <div className="space-y-2">
                <Label>Max Size: {settings.cache.maxSize} MB</Label>
                <Slider
                  value={[settings.cache.maxSize]}
                  onValueChange={(value) => updateSettings("cache.maxSize", value[0])}
                  min={50}
                  max={10000}
                  step={50}
                />
              </div>
              <div className="space-y-2">
                <Label>TTL: {settings.cache.ttl / 3600} hours</Label>
                <Slider
                  value={[settings.cache.ttl]}
                  onValueChange={(value) => updateSettings("cache.ttl", value[0])}
                  min={3600}
                  max={86400}
                  step={3600}
                />
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Cache Location</Label>
                <Input
                  value={settings.cache.location}
                  onChange={(e) => updateSettings("cache.location", e.target.value)}
                  placeholder="./cache"
                />
              </div>

              <Button variant="destructive" onClick={clearCache} className="w-full">
                <Trash2 className="w-4 h-4 mr-2" />
                Clear Cache
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

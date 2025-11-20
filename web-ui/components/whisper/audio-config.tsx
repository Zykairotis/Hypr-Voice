"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Save, RefreshCw, Mic, Volume2 } from "lucide-react";
import { toast } from "sonner";

interface AudioDevice {
  name: string;
  index: number;
  channels: number;
  sampleRate: number;
}

export default function AudioConfig() {
  const [devices, setDevices] = useState<AudioDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState("");
  const [sampleRate, setSampleRate] = useState(16000);
  const [channels, setChannels] = useState(1);
  const [bufferSize, setBufferSize] = useState(1024);
  const [saveRecordings, setSaveRecordings] = useState(false);
  const [autoCleanup, setAutoCleanup] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorCount, setErrorCount] = useState(0);

  useEffect(() => {
    loadAudioConfig();
    fetchAudioDevices();
  }, []);

  const loadAudioConfig = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/config/audio", {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const config = await response.json();
        setSelectedDevice(config.input_device || "");
        setSampleRate(config.sample_rate || 16000);
        setChannels(config.channels || 1);
        setBufferSize(config.buffer_size || 1024);
        setSaveRecordings(config.save_recordings || false);
        setAutoCleanup(config.auto_cleanup?.enabled || false);
        setErrorCount(0);
      }
    } catch (error) {
      // Only log occasionally to avoid console spam
      if (errorCount === 0) {
        console.warn("Backend not available on port 8934. Using default audio configuration. Run './start-ui.sh' to start the backend.");
      }
      setErrorCount(prev => prev + 1);
    }
  };

  const fetchAudioDevices = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/audio/devices", {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const data = await response.json();
        setDevices(data?.devices || []);
        setErrorCount(0);
      }
    } catch (error) {
      // Only log once to avoid console spam
      if (errorCount === 0) {
        console.warn("Backend not available. Using mock audio devices for UI preview.");
      }
      setErrorCount(prev => prev + 1);
      // Fallback to mock data for UI development
      setDevices([
        { name: "GA102 High Definition Audio Controller", index: 0, channels: 2, sampleRate: 48000 },
        { name: "Default PulseAudio Input", index: 1, channels: 2, sampleRate: 44100 },
      ]);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const config = {
        input_device: selectedDevice,
        sample_rate: sampleRate,
        channels: channels,
        buffer_size: bufferSize,
        save_recordings: saveRecordings,
        auto_cleanup: {
          enabled: autoCleanup,
          days_to_keep: 7
        }
      };

      const response = await fetch("http://localhost:8934/api/config/audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        toast.success("Audio configuration saved successfully");
      } else {
        toast.error("Failed to save configuration");
      }
    } catch (error) {
      toast.error("Error saving configuration");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Audio Device Selection */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="device" className="text-base font-semibold flex items-center gap-2">
            <Mic className="w-4 h-4" />
            Input Device
          </Label>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchAudioDevices}
            className="glass-hover"
          >
            <RefreshCw className="w-3 h-3 mr-2" />
            Refresh
          </Button>
        </div>
        <Select value={selectedDevice} onValueChange={setSelectedDevice}>
          <SelectTrigger id="device" className="glass">
            <SelectValue placeholder="Select audio input device" />
          </SelectTrigger>
          <SelectContent className="glass border-border/50">
            {devices.map((device) => (
              <SelectItem key={device.index} value={device.name}>
                <div className="flex items-center justify-between gap-4">
                  <span>{device.name}</span>
                  <Badge variant="outline" className="text-xs">
                    {device.channels}ch @ {device.sampleRate}Hz
                  </Badge>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-sm text-muted-foreground">
          Select the audio input device for voice recording
        </p>
      </div>

      <Separator className="bg-border/50" />

      {/* Sample Rate */}
      <div className="space-y-3">
        <Label htmlFor="sampleRate" className="text-base font-semibold flex items-center gap-2">
          <Volume2 className="w-4 h-4" />
          Sample Rate
        </Label>
        <div className="flex items-center gap-4">
          <Slider
            id="sampleRate"
            value={[sampleRate]}
            onValueChange={([value]) => setSampleRate(value)}
            min={8000}
            max={48000}
            step={8000}
            className="flex-1"
          />
          <Badge variant="outline" className="w-24 justify-center glass">
            {sampleRate} Hz
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Audio sample rate (16000 Hz recommended for Whisper)
        </p>
      </div>

      {/* Channels */}
      <div className="space-y-3">
        <Label className="text-base font-semibold">Channels</Label>
        <div className="flex gap-3">
          <Button
            variant={channels === 1 ? "default" : "outline"}
            onClick={() => setChannels(1)}
            className={channels === 1 ? "glow" : "glass-hover"}
          >
            Mono
          </Button>
          <Button
            variant={channels === 2 ? "default" : "outline"}
            onClick={() => setChannels(2)}
            className={channels === 2 ? "glow" : "glass-hover"}
          >
            Stereo
          </Button>
        </div>
        <p className="text-sm text-muted-foreground">
          Mono recommended for voice transcription
        </p>
      </div>

      <Separator className="bg-border/50" />

      {/* Buffer Size */}
      <div className="space-y-3">
        <Label htmlFor="bufferSize" className="text-base font-semibold">
          Buffer Size
        </Label>
        <div className="flex items-center gap-4">
          <Slider
            id="bufferSize"
            value={[bufferSize]}
            onValueChange={([value]) => setBufferSize(value)}
            min={512}
            max={4096}
            step={512}
            className="flex-1"
          />
          <Badge variant="outline" className="w-24 justify-center glass">
            {bufferSize}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Audio buffer size in samples (lower = less latency, higher = more stable)
        </p>
      </div>

      <Separator className="bg-border/50" />

      {/* Recording Options */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">Recording Options</Label>
        
        <div className="flex items-center justify-between p-4 rounded-lg glass-hover border border-border/50">
          <div className="space-y-0.5">
            <Label htmlFor="saveRecordings" className="cursor-pointer">
              Save Recordings
            </Label>
            <p className="text-sm text-muted-foreground">
              Save audio recordings to disk
            </p>
          </div>
          <Switch
            id="saveRecordings"
            checked={saveRecordings}
            onCheckedChange={setSaveRecordings}
          />
        </div>

        <div className="flex items-center justify-between p-4 rounded-lg glass-hover border border-border/50">
          <div className="space-y-0.5">
            <Label htmlFor="autoCleanup" className="cursor-pointer">
              Auto Cleanup
            </Label>
            <p className="text-sm text-muted-foreground">
              Automatically delete old recordings (7 days)
            </p>
          </div>
          <Switch
            id="autoCleanup"
            checked={autoCleanup}
            onCheckedChange={setAutoCleanup}
            disabled={!saveRecordings}
          />
        </div>
      </div>

      {/* Save Button */}
      <div className="pt-4">
        <Button
          onClick={handleSave}
          disabled={isLoading}
          className="w-full glow-hover"
          size="lg"
        >
          <Save className="w-4 h-4 mr-2" />
          {isLoading ? "Saving..." : "Save Audio Configuration"}
        </Button>
      </div>
    </div>
  );
}


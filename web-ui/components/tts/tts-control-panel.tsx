"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  Play,
  Pause,
  Volume2,
  Mic2,
  Settings,
  BarChart3,
  Sparkles,
  PauseCircle,
  RotateCcw,
  Download,
  TrendingUp
} from "lucide-react";
import { toast } from "sonner";

// Types
interface TTSProvider {
  id: string;
  name: string;
  type: "local" | "cloud";
  description: string;
  status: "active" | "inactive" | "error";
  voices: string[];
  usage: {
    requests: number;
    characters: number;
    monthly: string;
  };
  quality: "standard" | "high" | "ultra";
}

interface VoiceSettings {
  speed: number;
  pitch: number;
  volume: number;
  quality: "standard" | "high" | "ultra";
}

interface AudioVisualizationData {
  frequency: number[];
  waveform: number[];
}

// Mock providers data
const mockProviders: TTSProvider[] = [
  {
    id: "kokoro",
    name: "Kokoro TTS",
    type: "local",
    description: "Fast, offline text-to-speech",
    status: "active",
    voices: ["af_bella", "af_sky", "am_adam", "bm_george", "af_nicole", "am_michael"],
    usage: {
      requests: 1247,
      characters: 89234,
      monthly: "47K chars left"
    },
    quality: "high"
  },
  {
    id: "deepgram",
    name: "Deepgram TTS",
    type: "cloud",
    description: "Premium neural voices",
    status: "active",
    voices: ["asteria", "luna", "orion", "zeus", "athena", "hermes"],
    usage: {
      requests: 892,
      characters: 156743,
      monthly: "312K chars"
    },
    quality: "ultra"
  },
  {
    id: "elevenlabs",
    name: "ElevenLabs",
    type: "cloud",
    description: "AI-powered voice cloning",
    status: "inactive",
    voices: ["rachel", "drew", "clyde", "paul", "domi", "dave"],
    usage: {
      requests: 0,
      characters: 0,
      monthly: "Not configured"
    },
    quality: "ultra"
  }
];

export default function TTSControlPanel() {
  // State
  const [selectedProvider, setSelectedProvider] = useState("kokoro");
  const [selectedVoice, setSelectedVoice] = useState("af_bella");
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettings>({
    speed: 1.0,
    pitch: 1.0,
    volume: 0.8,
    quality: "high"
  });
  const [testText, setTestText] = useState("Hello! This is a test of the text-to-speech system. How does it sound?");
  const [isPlaying, setIsPlaying] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [audioVisualizationData, setAudioVisualizationData] = useState<AudioVisualizationData>({
    frequency: Array(32).fill(0),
    waveform: Array(64).fill(0)
  });
  const [providers] = useState<TTSProvider[]>(mockProviders);
  const [enableVisualization, setEnableVisualization] = useState(true);

  const animationFrameRef = useRef<number>();
  const audioRef = useRef<HTMLAudioElement>(null);

  // Get current provider
  const currentProvider = providers.find(p => p.id === selectedProvider);

  // Generate mock audio visualization data
  useEffect(() => {
    if (!enableVisualization) return;

    const generateVisualization = () => {
      setAudioVisualizationData({
        frequency: Array(32).fill(0).map(() => Math.random() * 100),
        waveform: Array(64).fill(0).map(() => Math.random() * 100)
      });
      animationFrameRef.current = requestAnimationFrame(generateVisualization);
    };

    generateVisualization();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [enableVisualization, isPlaying]);

  // Handle provider change
  const handleProviderChange = (providerId: string) => {
    setSelectedProvider(providerId);
    const provider = providers.find(p => p.id === providerId);
    if (provider && provider.voices.length > 0) {
      setSelectedVoice(provider.voices[0]);
    }
    toast.info(`Switched to ${provider?.name}`);
  };

  // Handle voice preview
  const handleVoicePreview = async () => {
    setIsGenerating(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      setIsPlaying(true);
      toast.success("Playing voice preview");

      // Simulate playback duration
      setTimeout(() => {
        setIsPlaying(false);
        toast.info("Preview completed");
      }, 3000);
    } catch (error) {
      toast.error("Failed to generate voice preview");
      setIsGenerating(false);
    }
  };

  // Handle test playback
  const handleTestPlayback = async () => {
    if (!testText.trim()) {
      toast.error("Please enter test text");
      return;
    }

    setIsGenerating(true);
    try {
      // Simulate TTS API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      setIsPlaying(true);
      toast.success("Playing test audio");

      // Update usage statistics
      const updatedProviders = providers.map(p => {
        if (p.id === selectedProvider) {
          return {
            ...p,
            usage: {
              ...p.usage,
              requests: p.usage.requests + 1,
              characters: p.usage.characters + testText.length
            }
          };
        }
        return p;
      });

      setTimeout(() => {
        setIsPlaying(false);
        setIsGenerating(false);
        toast.info("Test playback completed");
      }, 5000);
    } catch (error) {
      toast.error("Failed to generate speech");
      setIsGenerating(false);
    }
  };

  // Format number with K/M suffix
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + "M";
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + "K";
    }
    return num.toString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">TTS Control Panel</h2>
          <p className="text-sm text-muted-foreground">
            Configure and test text-to-speech providers
          </p>
        </div>
        <Badge variant="outline" className="glass px-3 py-1">
          <Sparkles className="w-3 h-3 mr-1" />
          Ready
        </Badge>
      </div>

      {/* Provider Selection Grid */}
      <div className="space-y-4">
        <Label className="text-base font-semibold flex items-center gap-2">
          <Mic2 className="w-4 h-4" />
          TTS Providers
        </Label>
        <div className="grid gap-3">
          {providers.map((provider) => (
            <Card
              key={provider.id}
              className={`glass-hover border-border/50 cursor-pointer transition-all ${
                selectedProvider === provider.id
                  ? "border-primary/50 bg-primary/5 glow"
                  : ""
              }`}
              onClick={() => handleProviderChange(provider.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <div className={`p-2 rounded-lg border ${
                      provider.status === 'active'
                        ? 'bg-green-500/10 border-green-500/20'
                        : provider.status === 'error'
                        ? 'bg-red-500/10 border-red-500/20'
                        : 'bg-yellow-500/10 border-yellow-500/20'
                    }`}>
                      <Mic2 className={`w-5 h-5 ${
                        provider.status === 'active'
                          ? 'text-green-500'
                          : provider.status === 'error'
                          ? 'text-red-500'
                          : 'text-yellow-500'
                      }`} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold">{provider.name}</span>
                        <Badge
                          variant="outline"
                          className={`text-xs ${
                            provider.type === 'local' ? 'glass' : ''
                          }`}
                        >
                          {provider.type === 'local' ? 'Local' : 'Cloud'}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={`text-xs ${
                            provider.quality === 'ultra' ? 'text-purple-400 border-purple-400/30' :
                            provider.quality === 'high' ? 'text-blue-400 border-blue-400/30' :
                            'text-gray-400 border-gray-400/30'
                          }`}
                        >
                          {provider.quality}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        {provider.description}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>{formatNumber(provider.usage.requests)} requests</span>
                        <span>{formatNumber(provider.usage.characters)} chars</span>
                        <span>{provider.usage.monthly}</span>
                      </div>
                    </div>
                  </div>
                  {selectedProvider === provider.id && (
                    <div className="flex flex-col items-end gap-2">
                      <Sparkles className="w-5 h-5 text-primary" />
                      <Badge
                        variant={provider.status === 'active' ? 'default' : 'secondary'}
                        className="text-xs"
                      >
                        {provider.status}
                      </Badge>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <Separator className="bg-border/50" />

      {/* Voice Selection */}
      <div className="space-y-3">
        <Label className="text-base font-semibold">Voice</Label>
        <Select value={selectedVoice} onValueChange={setSelectedVoice}>
          <SelectTrigger className="glass">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="glass border-border/50">
            {currentProvider?.voices.map((voice) => (
              <SelectItem key={voice} value={voice}>
                {voice.split('_').map(word =>
                  word.charAt(0).toUpperCase() + word.slice(1)
                ).join(' ')}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Voice Settings */}
      <div className="space-y-4">
        <Label className="text-base font-semibold flex items-center gap-2">
          <Settings className="w-4 h-4" />
          Voice Settings
        </Label>

        <Card className="glass border-border/30">
          <CardContent className="p-4 space-y-4">
            {/* Speed */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="speed">Speed</Label>
                <Badge variant="outline" className="glass">
                  {voiceSettings.speed.toFixed(2)}x
                </Badge>
              </div>
              <Slider
                id="speed"
                value={[voiceSettings.speed]}
                onValueChange={([value]) =>
                  setVoiceSettings(prev => ({ ...prev, speed: value }))
                }
                min={0.5}
                max={2.0}
                step={0.05}
              />
            </div>

            {/* Pitch */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="pitch">Pitch</Label>
                <Badge variant="outline" className="glass">
                  {voiceSettings.pitch.toFixed(2)}
                </Badge>
              </div>
              <Slider
                id="pitch"
                value={[voiceSettings.pitch]}
                onValueChange={([value]) =>
                  setVoiceSettings(prev => ({ ...prev, pitch: value }))
                }
                min={0.5}
                max={2.0}
                step={0.05}
              />
            </div>

            {/* Volume */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="volume">Volume</Label>
                <Badge variant="outline" className="glass">
                  {Math.round(voiceSettings.volume * 100)}%
                </Badge>
              </div>
              <Slider
                id="volume"
                value={[voiceSettings.volume]}
                onValueChange={([value]) =>
                  setVoiceSettings(prev => ({ ...prev, volume: value }))
                }
                min={0}
                max={1}
                step={0.01}
              />
            </div>

            {/* Quality */}
            <div className="space-y-2">
              <Label className="text-sm">Audio Quality</Label>
              <div className="flex gap-2">
                {(["standard", "high", "ultra"] as const).map((quality) => (
                  <Button
                    key={quality}
                    variant={voiceSettings.quality === quality ? "default" : "outline"}
                    size="sm"
                    onClick={() =>
                      setVoiceSettings(prev => ({ ...prev, quality }))
                    }
                    className={voiceSettings.quality === quality ? "glow" : "glass-hover"}
                  >
                    {quality}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Audio Visualization */}
      {enableVisualization && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-base font-semibold flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Audio Visualization
            </Label>
            <Switch
              checked={enableVisualization}
              onCheckedChange={setEnableVisualization}
            />
          </div>

          <Card className="glass border-border/30 overflow-hidden">
            <CardContent className="p-4">
              <div className="space-y-2">
                {/* Frequency bars */}
                <div className="flex items-end gap-1 h-16">
                  {audioVisualizationData.frequency.map((value, index) => (
                    <div
                      key={`freq-${index}`}
                      className="bg-gradient-to-t from-primary/80 to-primary/30 rounded-t"
                      style={{
                        height: `${value}%`,
                        width: `${100 / audioVisualizationData.frequency.length}%`,
                        transition: 'height 0.1s ease-out'
                      }}
                    />
                  ))}
                </div>

                {/* Waveform */}
                <div className="flex items-center gap-1 h-8">
                  {audioVisualizationData.waveform.map((value, index) => (
                    <div
                      key={`wave-${index}`}
                      className="bg-primary/40 rounded"
                      style={{
                        height: `${Math.abs(value - 50)}%`,
                        width: `${100 / audioVisualizationData.waveform.length}%`,
                        transition: 'height 0.05s ease-out'
                      }}
                    />
                  ))}
                </div>
              </div>

              {isPlaying && (
                <div className="mt-2 flex items-center justify-center gap-2 text-sm text-muted-foreground">
                  <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                  <span>Playing...</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Test Text Input */}
      <div className="space-y-3">
        <Label className="text-base font-semibold">Test Text</Label>
        <Textarea
          value={testText}
          onChange={(e) => setTestText(e.target.value)}
          placeholder="Enter text to test TTS..."
          className="glass min-h-[100px] resize-none"
          maxLength={500}
        />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{testText.length}/500 characters</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTestText("")}
            className="h-auto p-0 text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className="w-3 h-3 mr-1" />
            Clear
          </Button>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button
          onClick={handleVoicePreview}
          disabled={isGenerating || isPlaying}
          variant="outline"
          className="flex-1 glass-hover"
        >
          {isGenerating ? (
            <div className="w-4 h-4 mr-2 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          ) : (
            <Play className="w-4 h-4 mr-2" />
          )}
          Voice Preview
        </Button>

        <Button
          onClick={handleTestPlayback}
          disabled={isGenerating || isPlaying || !testText.trim()}
          className="flex-1 glow-hover"
        >
          {isGenerating ? (
            <div className="w-4 h-4 mr-2 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          ) : isPlaying ? (
            <PauseCircle className="w-4 h-4 mr-2" />
          ) : (
            <Volume2 className="w-4 h-4 mr-2" />
          )}
          Test Speech
        </Button>
      </div>

      {/* Usage Statistics */}
      <div className="space-y-3">
        <Label className="text-base font-semibold flex items-center gap-2">
          <TrendingUp className="w-4 h-4" />
          Usage Statistics
        </Label>

        <div className="grid gap-3">
          {providers.map((provider) => (
            <Card
              key={provider.id}
              className={`glass border-border/30 ${
                provider.id === selectedProvider ? 'border-primary/30' : ''
              }`}
            >
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center justify-between">
                  <span>{provider.name}</span>
                  <Badge variant="outline" className="glass text-xs">
                    {provider.usage.requests} requests
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Characters</span>
                    <span className="font-mono">{formatNumber(provider.usage.characters)}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Monthly Limit</span>
                    <span className="font-mono">{provider.usage.monthly}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Quality</span>
                    <Badge
                      variant="outline"
                      className={`text-xs ${
                        provider.quality === 'ultra' ? 'text-purple-400 border-purple-400/30' :
                        provider.quality === 'high' ? 'text-blue-400 border-blue-400/30' :
                        'text-gray-400 border-gray-400/30'
                      }`}
                    >
                      {provider.quality}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

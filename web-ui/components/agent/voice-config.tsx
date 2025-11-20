"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Card } from "@/components/ui/card";
import { Save, Mic2, Volume2, Sparkles } from "lucide-react";
import { toast } from "sonner";

export default function VoiceConfig() {
  const [provider, setProvider] = useState("kokoro");
  const [fallbackProvider, setFallbackProvider] = useState("deepgram");
  const [autoFallback, setAutoFallback] = useState(true);
  const [selectedVoice, setSelectedVoice] = useState("af_bella");
  const [preset, setPreset] = useState("professional");
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);
  const [isLoading, setIsLoading] = useState(false);
  const [errorCount, setErrorCount] = useState(0);

  const providers = [
    { value: "kokoro", label: "Kokoro TTS", badge: "Local", description: "Free, offline" },
    { value: "elevenlabs", label: "ElevenLabs", badge: "Cloud", description: "Premium quality" },
    { value: "deepgram", label: "Deepgram", badge: "Cloud", description: "Fast & natural" },
  ];

  const voices = {
    kokoro: [
      { value: "af_bella", label: "Bella (Female)" },
      { value: "af_sky", label: "Sky (Female)" },
      { value: "am_adam", label: "Adam (Male)" },
      { value: "bm_george", label: "George (Male)" },
    ],
    elevenlabs: [
      { value: "rachel", label: "Rachel" },
      { value: "bella", label: "Bella" },
      { value: "adam", label: "Adam" },
      { value: "antoni", label: "Antoni" },
    ],
    deepgram: [
      { value: "asteria", label: "Asteria" },
      { value: "luna", label: "Luna" },
      { value: "orion", label: "Orion" },
      { value: "zeus", label: "Zeus" },
    ],
  };

  const presets = [
    { value: "professional", label: "Professional", icon: "💼" },
    { value: "friendly", label: "Friendly", icon: "😊" },
    { value: "technical", label: "Technical", icon: "🔧" },
    { value: "narrator", label: "Narrator", icon: "📖" },
  ];

  useEffect(() => {
    loadVoiceConfig();
  }, []);

  const loadVoiceConfig = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/config/voice", {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const config = await response.json();
        setProvider(config.default_provider || "kokoro");
        setFallbackProvider(config.fallback_provider || "deepgram");
        setAutoFallback(config.auto_fallback ?? true);
        setSelectedVoice(config.voice || "af_bella");
        setPreset(config.preset || "professional");
        setErrorCount(0);
      }
    } catch (error) {
      // Only log once to avoid console spam
      if (errorCount === 0) {
        console.warn("Backend not available. Using default voice configuration.");
      }
      setErrorCount(prev => prev + 1);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const config = {
        default_provider: provider,
        fallback_provider: fallbackProvider,
        auto_fallback: autoFallback,
        voice: selectedVoice,
        preset: preset,
        speed: speed,
        pitch: pitch,
      };

      const response = await fetch("http://localhost:8934/api/config/voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        toast.success("Voice configuration saved successfully");
      } else {
        toast.error("Failed to save configuration");
      }
    } catch (error) {
      toast.error("Error saving configuration");
    } finally {
      setIsLoading(false);
    }
  };

  const testVoice = async () => {
    toast.info("Testing voice synthesis...");
    try {
      const response = await fetch("http://localhost:8934/api/voice/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: "Hello, this is a test of the voice synthesis system.",
          provider: provider,
          voice: selectedVoice,
        }),
      });

      if (response.ok) {
        toast.success("Voice test completed");
      } else {
        toast.error("Voice test failed");
      }
    } catch (error) {
      toast.error("Error testing voice");
    }
  };

  return (
    <div className="space-y-6">
      {/* Provider Selection */}
      <div className="space-y-3">
        <Label htmlFor="provider" className="text-base font-semibold flex items-center gap-2">
          <Volume2 className="w-4 h-4" />
          Voice Provider
        </Label>
        <div className="grid gap-3">
          {providers.map((p) => (
            <Card
              key={p.value}
              className={`glass-hover border-border/50 p-4 cursor-pointer transition-all ${
                provider === p.value ? "border-primary/50 bg-primary/5 glow" : ""
              }`}
              onClick={() => setProvider(p.value)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
                    <Mic2 className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{p.label}</span>
                      <Badge variant="outline" className="text-xs">
                        {p.badge}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{p.description}</p>
                  </div>
                </div>
                {provider === p.value && (
                  <Sparkles className="w-5 h-5 text-primary" />
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>

      <Separator className="bg-border/50" />

      {/* Voice Selection */}
      <div className="space-y-3">
        <Label htmlFor="voice" className="text-base font-semibold">
          Voice
        </Label>
        <Select value={selectedVoice} onValueChange={setSelectedVoice}>
          <SelectTrigger id="voice" className="glass">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="glass border-border/50">
            {voices[provider as keyof typeof voices]?.map((voice) => (
              <SelectItem key={voice.value} value={voice.value}>
                {voice.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Preset Selection */}
      <div className="space-y-3">
        <Label className="text-base font-semibold">Voice Preset</Label>
        <div className="grid grid-cols-2 gap-3">
          {presets.map((p) => (
            <Button
              key={p.value}
              variant={preset === p.value ? "default" : "outline"}
              onClick={() => setPreset(p.value)}
              className={preset === p.value ? "glow" : "glass-hover"}
            >
              <span className="mr-2">{p.icon}</span>
              {p.label}
            </Button>
          ))}
        </div>
      </div>

      <Separator className="bg-border/50" />

      {/* Advanced Settings */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">Advanced Settings</Label>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label htmlFor="speed">Speed</Label>
            <Badge variant="outline" className="glass">{speed.toFixed(2)}x</Badge>
          </div>
          <Slider
            id="speed"
            value={[speed]}
            onValueChange={([value]) => setSpeed(value)}
            min={0.5}
            max={2.0}
            step={0.05}
          />
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label htmlFor="pitch">Pitch</Label>
            <Badge variant="outline" className="glass">{pitch.toFixed(2)}</Badge>
          </div>
          <Slider
            id="pitch"
            value={[pitch]}
            onValueChange={([value]) => setPitch(value)}
            min={0.5}
            max={2.0}
            step={0.05}
          />
        </div>

        <div className="flex items-center justify-between p-4 rounded-lg glass-hover border border-border/50">
          <div className="space-y-0.5">
            <Label htmlFor="autoFallback" className="cursor-pointer">
              Auto Fallback
            </Label>
            <p className="text-sm text-muted-foreground">
              Automatically switch to fallback provider on error
            </p>
          </div>
          <Switch
            id="autoFallback"
            checked={autoFallback}
            onCheckedChange={setAutoFallback}
          />
        </div>

        {autoFallback && (
          <div className="space-y-3 pl-4 border-l-2 border-primary/20">
            <Label htmlFor="fallback">Fallback Provider</Label>
            <Select value={fallbackProvider} onValueChange={setFallbackProvider}>
              <SelectTrigger id="fallback" className="glass">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="glass border-border/50">
                {providers
                  .filter((p) => p.value !== provider)
                  .map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4">
        <Button
          onClick={testVoice}
          variant="outline"
          className="flex-1 glass-hover"
        >
          <Volume2 className="w-4 h-4 mr-2" />
          Test Voice
        </Button>
        <Button
          onClick={handleSave}
          disabled={isLoading}
          className="flex-1 glow-hover"
        >
          <Save className="w-4 h-4 mr-2" />
          {isLoading ? "Saving..." : "Save Configuration"}
        </Button>
      </div>
    </div>
  );
}


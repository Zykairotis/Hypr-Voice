"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  Settings,
  Mic2,
  Play,
  Volume2,
  Brain,
  History,
  Radio,
  Sparkles,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { toast } from "sonner";

import TTSProviderSelector from "./tts-provider-selector";
import TTSVoiceSelector from "./tts-voice-selector";
import TTSSynthesizer from "./tts-synthesizer";
import TTSAudioPlayer from "./tts-audio-player";
import TTSAgentIntegration from "./tts-agent-integration";
import TTSAudioLibrary from "./tts-audio-library";
import TTSLiveStream from "./tts-live-stream";
import TTSAdvancedSettings from "./tts-advanced-settings";

interface TTSControlPanelProps {
  onStatusChange?: (status: "online" | "offline" | "error") => void;
}

export default function TTSControlPanel({ onStatusChange }: TTSControlPanelProps) {
  const [activeTab, setActiveTab] = useState("synthesize");
  const [status, setStatus] = useState<"online" | "offline" | "error">("offline");
  const [ttsProvider, setTtsProvider] = useState("kokoro");
  const [ttsVoice, setTtsVoice] = useState("af_bella");
  const [isLoading, setIsLoading] = useState(false);

  // Check TTS service status on mount
  useEffect(() => {
    checkTTSStatus();
    const interval = setInterval(checkTTSStatus, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const checkTTSStatus = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/tts/status", {
        method: "GET",
      });

      if (response.ok) {
        const data = await response.json();
        setStatus(data.status || "offline");
        onStatusChange?.(data.status || "offline");
      } else {
        setStatus("error");
        onStatusChange?.("error");
      }
    } catch (error) {
      setStatus("offline");
      onStatusChange?.("offline");
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case "online":
        return (
          <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Online
          </Badge>
        );
      case "error":
        return (
          <Badge className="bg-red-500/20 text-red-400 border-red-500/50">
            <AlertCircle className="w-3 h-3 mr-1" />
            Error
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-muted-foreground">
            <AlertCircle className="w-3 h-3 mr-1" />
            Offline
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="glass glass-hover border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20">
                <Mic2 className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <CardTitle className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  TTS Control Panel
                </CardTitle>
                <CardDescription>
                  Professional text-to-speech synthesis with multiple providers
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-sm text-muted-foreground mb-1">Status</div>
                {getStatusBadge()}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-yellow-400" />
              <span className="text-muted-foreground">3 TTS Providers</span>
            </div>
            <div className="flex items-center gap-2">
              <Volume2 className="w-4 h-4 text-blue-400" />
              <span className="text-muted-foreground">High-Quality Audio</span>
            </div>
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-purple-400" />
              <span className="text-muted-foreground">Agent Integration</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-7 glass">
          <TabsTrigger value="synthesize" className="flex items-center gap-2">
            <Play className="w-4 h-4" />
            Synthesize
          </TabsTrigger>
          <TabsTrigger value="voices" className="flex items-center gap-2">
            <Mic2 className="w-4 h-4" />
            Voices
          </TabsTrigger>
          <TabsTrigger value="player" className="flex items-center gap-2">
            <Volume2 className="w-4 h-4" />
            Player
          </TabsTrigger>
          <TabsTrigger value="agents" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Agents
          </TabsTrigger>
          <TabsTrigger value="library" className="flex items-center gap-2">
            <History className="w-4 h-4" />
            Library
          </TabsTrigger>
          <TabsTrigger value="live" className="flex items-center gap-2">
            <Radio className="w-4 h-4" />
            Live Stream
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="synthesize" className="space-y-6">
          <Card className="glass glass-hover border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Play className="w-5 h-5" />
                Text-to-Speech Synthesis
              </CardTitle>
              <CardDescription>
                Convert text to speech with real-time preview and controls
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TTSSynthesizer
                provider={ttsProvider}
                voice={ttsVoice}
                onProviderChange={setTtsProvider}
                onVoiceChange={setTtsVoice}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="voices" className="space-y-6">
          <div className="grid gap-6">
            <Card className="glass glass-hover border-border/50">
              <CardHeader>
                <CardTitle>TTS Provider Selection</CardTitle>
                <CardDescription>
                  Choose and configure your preferred TTS provider
                </CardDescription>
              </CardHeader>
              <CardContent>
                <TTSProviderSelector
                  selectedProvider={ttsProvider}
                  onProviderChange={setTtsProvider}
                />
              </CardContent>
            </Card>

            <Card className="glass glass-hover border-border/50">
              <CardHeader>
                <CardTitle>Voice Selection</CardTitle>
                <CardDescription>
                  Browse and test available voices for each provider
                </CardDescription>
              </CardHeader>
              <CardContent>
                <TTSVoiceSelector
                  provider={ttsProvider}
                  selectedVoice={ttsVoice}
                  onVoiceChange={setTtsVoice}
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="player" className="space-y-6">
          <Card className="glass glass-hover border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Volume2 className="w-5 h-5" />
                Audio Player
              </CardTitle>
              <CardDescription>
                Advanced audio playback with visualization and controls
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TTSAudioPlayer />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="agents" className="space-y-6">
          <Card className="glass glass-hover border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5" />
                Agent Integration
              </CardTitle>
              <CardDescription>
                Configure TTS for individual agents with custom settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TTSAgentIntegration />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="library" className="space-y-6">
          <Card className="glass glass-hover border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="w-5 h-5" />
                Audio Library
              </CardTitle>
              <CardDescription>
                Manage your synthesized audio history and favorites
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TTSAudioLibrary />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="live" className="space-y-6">
          <Card className="glass glass-hover border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Radio className="w-5 h-5" />
                Live TTS Streaming
              </CardTitle>
              <CardDescription>
                Real-time TTS synthesis with WebSocket integration
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TTSLiveStream />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card className="glass glass-hover border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Advanced Settings
              </CardTitle>
              <CardDescription>
                Configure audio quality, parameters, and preferences
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TTSAdvancedSettings />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Radio,
  Play,
  Pause,
  Square,
  Activity,
  Zap,
  Wifi,
  WifiOff,
  Volume2,
  RadioIcon,
  MessageSquare,
  Send,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock
} from "lucide-react";
import { toast } from "sonner";

interface StreamEvent {
  id: string;
  timestamp: Date;
  type: "started" | "progress" | "chunk" | "completed" | "error";
  status: "pending" | "processing" | "success" | "failed";
  message: string;
  data?: any;
}

interface StreamSession {
  id: string;
  status: "active" | "completed" | "stopped";
  provider: string;
  voice: string;
  text: string;
  startTime: Date;
  endTime?: Date;
  events: StreamEvent[];
  chunks: number;
  duration?: number;
}

export default function TTSLiveStream() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentSession, setCurrentSession] = useState<StreamSession | null>(null);
  const [streamText, setStreamText] = useState("");
  const [provider, setProvider] = useState("kokoro");
  const [voice, setVoice] = useState("af_bella");
  const [wsConnected, setWsConnected] = useState(false);
  const [currentChunk, setCurrentChunk] = useState(0);
  const [totalChunks, setTotalChunks] = useState(0);
  const [sessionHistory, setSessionHistory] = useState<StreamSession[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const eventLogRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Load session history
    const saved = localStorage.getItem("tts-stream-history");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSessionHistory(parsed.map((session: any) => ({
          ...session,
          startTime: new Date(session.startTime),
          endTime: session.endTime ? new Date(session.endTime) : undefined,
          events: session.events.map((event: any) => ({
            ...event,
            timestamp: new Date(event.timestamp)
          }))
        })));
      } catch (error) {
        console.error("Failed to load stream history:", error);
      }
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    // Auto-scroll event log
    if (eventLogRef.current) {
      eventLogRef.current.scrollTop = eventLogRef.current.scrollHeight;
    }
  }, [currentSession?.events]);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket("ws://localhost:8934/api/tts/stream");

      ws.onopen = () => {
        setWsConnected(true);
        toast.success("WebSocket connected");
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleStreamMessage(data);
      };

      ws.onclose = () => {
        setWsConnected(false);
        toast.info("WebSocket disconnected");
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        toast.error("WebSocket connection error");
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Failed to connect WebSocket:", error);
      toast.error("Failed to connect to stream");
    }
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const handleStreamMessage = (data: any) => {
    if (!currentSession) return;

    const newEvent: StreamEvent = {
      id: `event_${Date.now()}`,
      timestamp: new Date(),
      type: data.type,
      status: data.status,
      message: data.message,
      data: data
    };

    setCurrentSession(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        events: [...prev.events, newEvent],
        chunks: data.chunkIndex ? data.chunkIndex + 1 : prev.chunks
      };
    });

    setCurrentChunk(data.chunkIndex || 0);
    setTotalChunks(data.totalChunks || 0);

    // Handle specific event types
    if (data.type === "completed") {
      setIsStreaming(false);
      toast.success("Stream synthesis completed");

      const completedSession = {
        ...currentSession,
        status: "completed" as const,
        endTime: new Date(),
        events: [...currentSession.events, newEvent]
      };

      const updatedHistory = [completedSession, ...sessionHistory.slice(0, 49)];
      setSessionHistory(updatedHistory);
      localStorage.setItem("tts-stream-history", JSON.stringify(updatedHistory));
    }

    if (data.type === "error") {
      setIsStreaming(false);
      toast.error(`Stream error: ${data.message}`);
    }
  };

  const startStreaming = async () => {
    if (!streamText.trim()) {
      toast.error("Please enter text to synthesize");
      return;
    }

    connectWebSocket();

    const session: StreamSession = {
      id: `stream_${Date.now()}`,
      status: "active",
      provider,
      voice,
      text: streamText,
      startTime: new Date(),
      events: [],
      chunks: 0
    };

    setCurrentSession(session);
    setIsStreaming(true);
    setCurrentChunk(0);

    try {
      const response = await fetch("http://localhost:8934/api/tts/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: streamText,
          provider,
          voice,
          stream: true
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to start streaming");
      }

      toast.success("Streaming synthesis started");
    } catch (error) {
      toast.error("Failed to start streaming");
      setIsStreaming(false);
      setCurrentSession(null);
    }
  };

  const stopStreaming = () => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ action: "stop" }));
    }

    setIsStreaming(false);

    if (currentSession) {
      const stoppedSession = {
        ...currentSession,
        status: "stopped" as const,
        endTime: new Date()
      };
      setCurrentSession(stoppedSession);
      const updatedHistory = [stoppedSession, ...sessionHistory.slice(0, 49)];
      setSessionHistory(updatedHistory);
      localStorage.setItem("tts-stream-history", JSON.stringify(updatedHistory));
    }

    disconnectWebSocket();
    toast.info("Streaming stopped");
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString();
  };

  const getEventIcon = (type: StreamEvent["type"]) => {
    switch (type) {
      case "started":
        return <Play className="w-4 h-4 text-green-400" />;
      case "progress":
        return <Activity className="w-4 h-4 text-blue-400" />;
      case "chunk":
        return <Zap className="w-4 h-4 text-purple-400" />;
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <Card className="glass border-border/50">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20">
                <RadioIcon className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Live TTS Streaming</h2>
                <p className="text-sm text-muted-foreground">
                  Real-time text-to-speech with chunked streaming
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge
                className={wsConnected ? "bg-green-500/20 text-green-400 border-green-500/50" : "bg-red-500/20 text-red-400 border-red-500/50"}
              >
                {wsConnected ? (
                  <>
                    <Wifi className="w-3 h-3 mr-1" />
                    Connected
                  </>
                ) : (
                  <>
                    <WifiOff className="w-3 h-3 mr-1" />
                    Disconnected
                  </>
                )}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Streaming Controls */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Send className="w-5 h-5" />
            Stream Configuration
          </CardTitle>
          <CardDescription>
            Configure and start a live TTS streaming session
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Provider</label>
              <Select value={provider} onValueChange={setProvider}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="kokoro">Kokoro (Local)</SelectItem>
                  <SelectItem value="deepgram">Deepgram (Cloud)</SelectItem>
                  <SelectItem value="elevenlabs">ElevenLabs (Cloud)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Voice</label>
              <Select value={voice} onValueChange={setVoice}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="af_bella">Bella (Female)</SelectItem>
                  <SelectItem value="af_sky">Sky (Female)</SelectItem>
                  <SelectItem value="am_adam">Adam (Male)</SelectItem>
                  <SelectItem value="am_michael">Michael (Male)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Text to Stream</label>
            <Textarea
              placeholder="Enter text for streaming synthesis..."
              value={streamText}
              onChange={(e) => setStreamText(e.target.value)}
              className="min-h-[100px] resize-none"
              disabled={isStreaming}
            />
            <div className="text-sm text-muted-foreground">
              {streamText.length} characters
            </div>
          </div>

          <div className="flex gap-2">
            {!isStreaming ? (
              <Button onClick={startStreaming} className="flex-1">
                <Play className="w-4 h-4 mr-2" />
                Start Streaming
              </Button>
            ) : (
              <Button onClick={stopStreaming} variant="destructive" className="flex-1">
                <Square className="w-4 h-4 mr-2" />
                Stop Streaming
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Current Stream */}
      {currentSession && (
        <Card className="glass border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-400" />
                  Active Stream
                </CardTitle>
                <CardDescription>
                  Stream ID: {currentSession.id}
                </CardDescription>
              </div>
              <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">
                {currentSession.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Progress */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-purple-400" />
                  Streaming Progress
                </span>
                <span>
                  {currentChunk} / {totalChunks} chunks
                </span>
              </div>
              {totalChunks > 0 && (
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(currentChunk / totalChunks) * 100}%` }}
                  />
                </div>
              )}
            </div>

            {/* Stream Info */}
            <div className="grid gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Provider:</span>
                <Badge variant="outline">{currentSession.provider}</Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Voice:</span>
                <span>{currentSession.voice}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Duration:</span>
                <span>
                  {Math.floor((Date.now() - currentSession.startTime.getTime()) / 1000)}s
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Chunks:</span>
                <span>{currentSession.chunks}</span>
              </div>
            </div>

            {/* Event Log */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <MessageSquare className="w-4 h-4" />
                Event Log
              </div>
              <div
                ref={eventLogRef}
                className="max-h-64 overflow-y-auto space-y-2 p-3 rounded-lg bg-muted/30"
              >
                {currentSession.events.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-start gap-2 text-sm"
                  >
                    {getEventIcon(event.type)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground text-xs">
                          {formatTimestamp(event.timestamp)}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {event.type}
                        </Badge>
                      </div>
                      <div className="text-xs mt-1">{event.message}</div>
                    </div>
                  </div>
                ))}
                {currentSession.events.length === 0 && (
                  <div className="text-center text-muted-foreground text-sm py-4">
                    No events yet. Stream events will appear here.
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Session History */}
      {sessionHistory.length > 0 && (
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Session History
            </CardTitle>
            <CardDescription>
              Previous streaming sessions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {sessionHistory.slice(0, 10).map((session) => (
                <div
                  key={session.id}
                  className="p-3 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          variant={session.status === "completed" ? "default" : "outline"}
                          className="text-xs"
                        >
                          {session.status}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {session.provider}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {formatTimestamp(session.startTime)}
                        </span>
                      </div>
                      <div className="text-sm font-medium truncate">
                        {session.text.substring(0, 80)}
                        {session.text.length > 80 && "..."}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1">
                        <span>{session.chunks} chunks</span>
                        {session.endTime && (
                          <span>
                            Duration: {Math.floor((session.endTime.getTime() - session.startTime.getTime()) / 1000)}s
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

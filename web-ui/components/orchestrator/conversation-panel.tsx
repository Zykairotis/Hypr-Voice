"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  MessageSquare, Send, Mic, MicOff, Volume2, VolumeX,
  User, Bot, Loader2, Play, RefreshCw, Zap, Clock, Brain, Copy
} from "lucide-react";
import { endpoints } from "@/lib/endpoints";
import { streamingFetch, useOrchestratorWebSocket, OrchestratorEvent } from "@/lib/orchestrator-websocket";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  agent_type?: string;
  audio_file?: string;
  routing?: {
    agent: string;
    confidence: number;
    reasoning: string;
  };
  metrics?: {
    ttft_ms?: number;
    total_tokens?: number;
  };
}

interface Conversation {
  id: string;
  created_at: string;
  title?: string;
  messages: Message[];
}

interface ConversationPanelProps {
  orchestratorOnline: boolean;
}

const AGENT_COLORS: Record<string, string> = {
  "general-conversation": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  "code-worker": "bg-blue-500/20 text-blue-400 border-blue-500/30",
  "research-worker": "bg-purple-500/20 text-purple-400 border-purple-500/30",
  "shell-worker": "bg-orange-500/20 text-orange-400 border-orange-500/30",
  "voice-worker": "bg-pink-500/20 text-pink-400 border-pink-500/30",
};

export default function ConversationPanel({ orchestratorOnline }: ConversationPanelProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [currentRouting, setCurrentRouting] = useState<Message["routing"] | null>(null);
  const [currentMetrics, setCurrentMetrics] = useState<Message["metrics"] | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [ttsStatus, setTtsStatus] = useState<"idle" | "connecting" | "connected" | "playing">("idle");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const { isConnected: wsConnected, subscribe } = useOrchestratorWebSocket();

  useEffect(() => {
    if (orchestratorOnline) {
      fetchConversations();
    }
  }, [orchestratorOnline]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentConversation?.messages, streamingContent]);

  useEffect(() => {
    const unsubAgent = subscribe("agent_activity", (event: OrchestratorEvent) => {
      console.log("[WS] Agent activity:", event);
    });

    const unsubRouting = subscribe("routing", (event: OrchestratorEvent) => {
      if (event.data) {
        setCurrentRouting({
          agent: event.data.agent,
          confidence: event.data.confidence,
          reasoning: event.data.reasoning,
        });
      }
    });

    return () => {
      unsubAgent();
      unsubRouting();
    };
  }, [subscribe]);

  const fetchConversations = async () => {
    try {
      const response = await fetch(endpoints.direct.voice.conversations);
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);
      }
    } catch (error) {
      console.error("Failed to fetch conversations:", error);
    }
  };

  const createConversation = async () => {
    try {
      const response = await fetch(endpoints.direct.voice.conversations, {
        method: "POST",
      });
      if (response.ok) {
        const conv = await response.json();
        setConversations(prev => [conv, ...prev]);
        setCurrentConversation(conv);
      }
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  };

  const sendMessageStreaming = useCallback(async () => {
    if (!input.trim() || isLoading || !orchestratorOnline) return;

    const userInput = input.trim();
    setInput("");
    setIsLoading(true);
    setIsStreaming(true);
    setStreamingContent("");
    setCurrentRouting(null);
    setCurrentMetrics(null);

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: userInput,
      timestamp: new Date().toISOString(),
    };

    setCurrentConversation(prev => {
      if (!prev) {
        return {
          id: "temp",
          created_at: new Date().toISOString(),
          title: userInput.slice(0, 50),
          messages: [userMessage],
        };
      }
      return {
        ...prev,
        messages: [...prev.messages, userMessage],
      };
    });

    let fullContent = "";
    let conversationId = currentConversation?.id;
    let agentType = "";
    let routing: Message["routing"] | undefined;
    let metrics: Message["metrics"] = {};

    try {
      await streamingFetch(
        endpoints.direct.voice.processStreaming,
        {
          text: userInput,
          conversation_id: conversationId,
          auto_play: autoSpeak,
        },
        (token) => {
          fullContent += token;
          setStreamingContent(fullContent);
        },
        (event) => {
          switch (event.type) {
            case "routing":
              agentType = event.data?.agent || event.agent || "";
              routing = {
                agent: agentType,
                confidence: event.data?.confidence ?? event.confidence ?? 0,
                reasoning: event.data?.reasoning || event.reasoning || "",
              };
              setCurrentRouting(routing);
              break;
            case "user_message":
              conversationId = event.conversation_id || conversationId;
              break;
            case "first_token":
              metrics.ttft_ms = event.data?.ttft_ms || event.ttft_ms;
              setCurrentMetrics({ ...metrics });
              break;
            case "tts_connecting":
              setTtsStatus("connecting");
              break;
            case "tts_connected":
              setTtsStatus("connected");
              break;
            case "audio_playing":
              setTtsStatus("playing");
              setIsSpeaking(true);
              break;
            case "audio_complete":
              setTtsStatus("idle");
              setIsSpeaking(false);
              break;
            case "complete":
              metrics.total_tokens = event.data?.token_count || event.token_count;
              break;
          }
        }
      );

      const assistantMessage: Message = {
        id: Date.now().toString() + "_assistant",
        role: "assistant",
        content: fullContent,
        timestamp: new Date().toISOString(),
        agent_type: agentType,
        routing,
        metrics,
      };

      setCurrentConversation(prev => {
        if (!prev) return null;
        return {
          ...prev,
          id: conversationId || prev.id,
          messages: [...prev.messages, assistantMessage],
        };
      });

    } catch (error) {
      console.error("Streaming error:", error);
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      setStreamingContent("");
      setCurrentRouting(null);
      setCurrentMetrics(null);
      setTtsStatus("idle");
    }
  }, [input, isLoading, orchestratorOnline, currentConversation?.id, autoSpeak]);

  const playAudio = async (audioFile: string) => {
    if (audioRef.current) {
      try {
        setIsSpeaking(true);
        audioRef.current.src = audioFile;
        await audioRef.current.play();
      } catch (error) {
        console.error("Failed to play audio:", error);
        setIsSpeaking(false);
      }
    }
  };

  const copyConversation = () => {
    if (!currentConversation?.messages.length) return;

    const conversationText = currentConversation.messages
      .map((msg) => {
        const speaker = msg.role === "user" ? "You" : msg.agent_type || "Assistant";
        const timestamp = new Date(msg.timestamp).toLocaleString();
        return `[${timestamp}] ${speaker}:\n${msg.content}`;
      })
      .join("\n\n");

    navigator.clipboard.writeText(conversationText).then(() => {
      // Optionally, you could add a toast notification here
      console.log("Conversation copied to clipboard");
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessageStreaming();
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card className="glass glass-hover border-border/50">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500/20 to-green-500/20 border border-emerald-500/30">
                <MessageSquare className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <CardTitle className="flex items-center gap-2 flex-wrap">
                  Voice Conversation
                  {wsConnected && (
                    <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/30 text-xs">
                      <Zap className="w-3 h-3 mr-1" />
                      Live
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription className="text-xs sm:text-sm">
                  Real-time streaming with Cerebras routing
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoSpeak(!autoSpeak)}
                className={`transition-colors ${autoSpeak ? "text-emerald-400 border-emerald-400/50" : "text-gray-400"}`}
              >
                {autoSpeak ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={copyConversation}
                disabled={!currentConversation?.messages.length}
                title="Copy conversation"
              >
                <Copy className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={createConversation}
                disabled={!orchestratorOnline}
              >
                <RefreshCw className="w-4 h-4 sm:mr-1" />
                <span className="hidden sm:inline">New</span>
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Messages */}
      <Card className="glass glass-hover border-border/50 min-h-[300px] sm:min-h-[400px] max-h-[60vh] flex flex-col">
        <CardContent className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-4">
          {!currentConversation?.messages?.length && !isStreaming ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-8">
              <MessageSquare className="w-10 h-10 sm:w-12 sm:h-12 text-gray-500 mb-4" />
              <p className="text-gray-400 mb-2 text-sm sm:text-base">No messages yet</p>
              <p className="text-xs sm:text-sm text-gray-500 px-4">
                Start a conversation by typing below
              </p>
            </div>
          ) : (
            <>
              {currentConversation?.messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  onPlayAudio={playAudio}
                />
              ))}
              
              {/* Streaming message */}
              {isStreaming && (
                <div className="flex gap-2 sm:gap-3 justify-start animate-in fade-in-0 slide-in-from-bottom-2">
                  <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-violet-500/20 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-violet-400" />
                  </div>
                  <div className="max-w-[85%] sm:max-w-[80%] rounded-2xl px-3 sm:px-4 py-2 sm:py-3 bg-white/5 border border-white/10">
                    {currentRouting && (
                      <div className="flex flex-wrap items-center gap-2 mb-2 pb-2 border-b border-white/10">
                        <Badge variant="outline" className={`text-xs ${AGENT_COLORS[currentRouting.agent] || "bg-gray-500/20 text-gray-400"}`}>
                          <Brain className="w-3 h-3 mr-1" />
                          {currentRouting.agent}
                        </Badge>
                        {currentMetrics?.ttft_ms && (
                          <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30 text-xs">
                            <Clock className="w-3 h-3 mr-1" />
                            {currentMetrics.ttft_ms}ms
                          </Badge>
                        )}
                        {ttsStatus !== "idle" && (
                          <Badge variant="outline" className="bg-pink-500/10 text-pink-400 border-pink-500/30 text-xs">
                            <Volume2 className="w-3 h-3 mr-1 animate-pulse" />
                            {ttsStatus}
                          </Badge>
                        )}
                      </div>
                    )}
                    <p className="text-xs sm:text-sm text-white/90 whitespace-pre-wrap">
                      {streamingContent}
                      <span className="inline-block w-2 h-4 bg-violet-400 animate-pulse ml-0.5" />
                    </p>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </CardContent>

        {/* Input */}
        <div className="p-3 sm:p-4 border-t border-white/10">
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={orchestratorOnline ? "Type a message..." : "Orchestrator offline..."}
              disabled={!orchestratorOnline || isLoading}
              className="min-h-[50px] sm:min-h-[60px] max-h-[100px] sm:max-h-[120px] resize-none bg-white/5 border-white/10 text-sm"
            />
            <div className="flex flex-col gap-2">
              <Button
                onClick={sendMessageStreaming}
                disabled={!input.trim() || isLoading || !orchestratorOnline}
                className="bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-600 hover:to-green-600 h-8 sm:h-10 px-3 sm:px-4"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
              <Button
                variant="outline"
                disabled={!orchestratorOnline}
                className={`h-8 sm:h-10 px-3 sm:px-4 ${isSpeaking ? "text-emerald-400 border-emerald-400" : ""}`}
              >
                {isSpeaking ? (
                  <Volume2 className="w-4 h-4 animate-pulse" />
                ) : (
                  <Mic className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </Card>

      <audio 
        ref={audioRef} 
        className="hidden" 
        onEnded={() => setIsSpeaking(false)}
        onError={() => setIsSpeaking(false)}
      />
    </div>
  );
}

function MessageBubble({ 
  message, 
  onPlayAudio 
}: { 
  message: Message; 
  onPlayAudio: (file: string) => void;
}) {
  const isUser = message.role === "user";
  
  return (
    <div className={`flex gap-2 sm:gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-violet-500/20 flex items-center justify-center flex-shrink-0">
          <Bot className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-violet-400" />
        </div>
      )}
      <div
        className={`max-w-[85%] sm:max-w-[80%] rounded-2xl px-3 sm:px-4 py-2 sm:py-3 ${
          isUser
            ? "bg-blue-500/20 border border-blue-500/30"
            : "bg-white/5 border border-white/10"
        }`}
      >
        <p className="text-xs sm:text-sm text-white/90 whitespace-pre-wrap">
          {message.content}
        </p>
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 mt-2">
          {message.agent_type && (
            <Badge 
              variant="outline" 
              className={`text-xs ${AGENT_COLORS[message.agent_type] || "bg-gray-500/20 text-gray-400"}`}
            >
              {message.agent_type}
            </Badge>
          )}
          {message.routing && (
            <Badge 
              variant="outline" 
              className="bg-yellow-500/10 text-yellow-400 border-yellow-500/30 text-xs"
              title={message.routing.reasoning}
            >
              {Math.round(message.routing.confidence * 100)}%
            </Badge>
          )}
          {message.metrics?.ttft_ms && (
            <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30 text-xs">
              <Clock className="w-2.5 h-2.5 mr-0.5" />
              {message.metrics.ttft_ms}ms
            </Badge>
          )}
          {message.audio_file && (
            <Button
              variant="ghost"
              size="sm"
              className="h-5 sm:h-6 px-1.5 sm:px-2"
              onClick={() => onPlayAudio(message.audio_file!)}
            >
              <Play className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
            </Button>
          )}
          <span className="text-xs text-gray-500 ml-auto">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
      {isUser && (
        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
          <User className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-blue-400" />
        </div>
      )}
    </div>
  );
}

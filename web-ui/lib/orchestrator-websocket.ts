"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { endpoints } from "./endpoints";

export interface OrchestratorEvent {
  type: string;
  data?: any;
  timestamp?: string;
  agent_type?: string;
  session_id?: string;
  conversation_id?: string;
}

export interface StreamingToken {
  content: string;
  token_count: number;
}

export interface RoutingInfo {
  agent: string;
  confidence: number;
  reasoning: string;
}

export interface AgentSession {
  session_id: string;
  agent_type: string;
  status: string;
  created_at: string;
  last_activity?: string;
  query?: string;
  parent_session?: string;
}

type EventHandler = (event: OrchestratorEvent) => void;

class OrchestratorWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private listeners: Map<string, Set<EventHandler>> = new Map();
  private isConnecting = false;
  private url: string;

  constructor(url?: string) {
    this.url = url || endpoints.ws.orchestrator;
  }

  connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return Promise.resolve();
    }

    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log("[Orchestrator WS] Connected");
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.emit("connection", { status: "connected" });
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch {
            console.warn("[Orchestrator WS] Failed to parse message:", event.data);
          }
        };

        this.ws.onerror = (error) => {
          console.error("[Orchestrator WS] Error:", error);
          this.isConnecting = false;
          this.emit("error", { error });
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log("[Orchestrator WS] Disconnected", event.code, event.reason);
          this.isConnecting = false;
          this.stopHeartbeat();
          this.emit("connection", { status: "disconnected" });
          this.attemptReconnect();
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }
  }

  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn("[Orchestrator WS] Cannot send - not connected");
    }
  }

  subscribe(topic: string): void {
    this.send({ type: "subscribe", topic });
  }

  on(event: string, handler: EventHandler): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(handler);

    return () => {
      this.listeners.get(event)?.delete(handler);
    };
  }

  private emit(event: string, data: any): void {
    this.listeners.get(event)?.forEach((handler) => handler(data));
    this.listeners.get("*")?.forEach((handler) => handler({ type: event, ...data }));
  }

  private handleMessage(data: any): void {
    const eventType = data.type || "unknown";
    this.emit(eventType, data);

    if (data.event_type) {
      this.emit(data.event_type, data);
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: "ping", timestamp: Date.now() });
      }
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1), 10000);
      console.log(`[Orchestrator WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

      setTimeout(() => {
        this.connect().catch(() => {});
      }, delay);
    } else {
      console.error("[Orchestrator WS] Max reconnect attempts reached");
      this.emit("reconnect_failed", {});
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

let wsService: OrchestratorWebSocketService | null = null;

export function getOrchestratorWS(): OrchestratorWebSocketService {
  if (!wsService) {
    wsService = new OrchestratorWebSocketService();
  }
  return wsService;
}

export function useOrchestratorWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<OrchestratorEvent | null>(null);
  const serviceRef = useRef<OrchestratorWebSocketService | null>(null);

  useEffect(() => {
    serviceRef.current = getOrchestratorWS();

    const handleConnection = (data: any) => {
      setIsConnected(data.status === "connected");
    };

    const handleAnyEvent = (event: OrchestratorEvent) => {
      setLastEvent(event);
    };

    const unsubConnection = serviceRef.current.on("connection", handleConnection);
    const unsubAll = serviceRef.current.on("*", handleAnyEvent);

    serviceRef.current.connect().catch(console.error);

    return () => {
      unsubConnection();
      unsubAll();
    };
  }, []);

  const subscribe = useCallback((event: string, handler: EventHandler) => {
    return serviceRef.current?.on(event, handler) || (() => {});
  }, []);

  const send = useCallback((message: any) => {
    serviceRef.current?.send(message);
  }, []);

  return {
    isConnected,
    lastEvent,
    subscribe,
    send,
    connect: () => serviceRef.current?.connect(),
    disconnect: () => serviceRef.current?.disconnect(),
  };
}

export async function streamingFetch(
  url: string,
  body: any,
  onToken: (token: string) => void,
  onEvent?: (event: OrchestratorEvent) => void
): Promise<void> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          
          if (data.type === "token" && data.content) {
            onToken(data.content);
          }
          
          if (onEvent) {
            onEvent(data);
          }
        } catch {
          // Skip malformed JSON
        }
      }
    }
  }
}

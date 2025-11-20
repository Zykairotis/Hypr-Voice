"use client";

import { useEffect, useRef, useState, useCallback } from "react";

export type EventType =
  | "agent_created"
  | "agent_started"
  | "agent_output"
  | "agent_error"
  | "agent_completed"
  | "tool_execution"
  | "mcp_event"
  | "skill_executed"
  | "voice_synthesis"
  | "system_metrics"
  | "alert_triggered"
  | "connection_status";

export interface MonitoringEvent {
  id: string;
  type: EventType;
  timestamp: number;
  source: string;
  data: any;
  severity?: "info" | "warning" | "error" | "critical";
  agentId?: string;
  correlationId?: string;
}

export interface SystemMetrics {
  timestamp: number;
  cpu: number;
  memory: number;
  activeAgents: number;
  websocketConnections: number;
  requestsPerSecond: number;
  averageResponseTime: number;
  errorRate: number;
}

export interface AlertRule {
  id: string;
  name: string;
  condition: string;
  threshold: number;
  severity: "info" | "warning" | "error" | "critical";
  enabled: boolean;
  cooldown: number;
  lastTriggered?: number;
}

export interface WebSocketMessage {
  event: MonitoringEvent;
  metrics?: SystemMetrics;
  alert?: {
    ruleId: string;
    message: string;
    severity: string;
    timestamp: number;
  };
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private clientId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private eventBuffer: MonitoringEvent[] = [];
  private maxBufferSize = 1000;
  private isConnecting = false;

  constructor(clientId?: string) {
    this.clientId = clientId || `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  connect(url?: string): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return Promise.resolve();
    }

    this.isConnecting = true;
    const wsUrl = url || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/${this.clientId}`;

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log("WebSocket connected");
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.emit("connection", { status: "connected", clientId: this.clientId });
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);

            if (message.event) {
              this.addEvent(message.event);
            }

            if (message.metrics) {
              this.emit("metrics", message.metrics);
            }

            if (message.alert) {
              this.emit("alert", message.alert);
            }
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        };

        this.ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          this.isConnecting = false;
          this.emit("error", error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log("WebSocket disconnected");
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
      this.ws.close();
      this.ws = null;
    }
    this.emit("connection", { status: "disconnected" });
  }

  send(event: Omit<MonitoringEvent, "id" | "timestamp">): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ event }));
    }
  }

  on(event: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);

    return () => {
      this.listeners.get(event)?.delete(callback);
    };
  }

  private emit(event: string, data: any): void {
    this.listeners.get(event)?.forEach(callback => callback(data));
  }

  private addEvent(event: MonitoringEvent): void {
    this.eventBuffer.push(event);
    if (this.eventBuffer.length > this.maxBufferSize) {
      this.eventBuffer.shift();
    }
    this.emit("event", event);
  }

  getEvents(limit = 100): MonitoringEvent[] {
    return this.eventBuffer.slice(-limit);
  }

  getEventsByType(type: EventType, limit = 100): MonitoringEvent[] {
    return this.eventBuffer
      .filter(e => e.type === type)
      .slice(-limit);
  }

  clearEvents(): void {
    this.eventBuffer = [];
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: "heartbeat", source: "monitor", data: { timestamp: Date.now() } });
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
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

      setTimeout(() => {
        this.connect().catch(() => {
          // Reconnection attempt failed
        });
      }, delay);
    }
  }

  getClientId(): string {
    return this.clientId;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

let wsService: WebSocketService | null = null;

export function useWebSocket(clientId?: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<MonitoringEvent[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const serviceRef = useRef<WebSocketService | null>(null);

  useEffect(() => {
    if (!wsService) {
      wsService = new WebSocketService(clientId);
    }
    serviceRef.current = wsService;

    const handleConnection = (status: any) => {
      setIsConnected(status.status === "connected");
    };

    const handleEvent = (event: MonitoringEvent) => {
      setEvents(prev => [...prev.slice(-999), event]);
    };

    const handleMetrics = (newMetrics: SystemMetrics) => {
      setMetrics(newMetrics);
    };

    const handleAlert = (alert: any) => {
      setAlerts(prev => [...prev.slice(-49), alert]);
      if (alert.severity === "critical" || alert.severity === "error") {
        playAlertSound(alert.severity);
      }
    };

    const unsubscribeConnection = wsService.on("connection", handleConnection);
    const unsubscribeEvent = wsService.on("event", handleEvent);
    const unsubscribeMetrics = wsService.on("metrics", handleMetrics);
    const unsubscribeAlert = wsService.on("alert", handleAlert);

    wsService.connect().catch(console.error);

    return () => {
      unsubscribeConnection();
      unsubscribeEvent();
      unsubscribeMetrics();
      unsubscribeAlert();
    };
  }, [clientId]);

  const connect = useCallback(() => {
    return serviceRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    serviceRef.current?.disconnect();
  }, []);

  const send = useCallback((event: Omit<MonitoringEvent, "id" | "timestamp">) => {
    serviceRef.current?.send(event);
  }, []);

  return {
    isConnected,
    events,
    metrics,
    alerts,
    connect,
    disconnect,
    send,
    getEvents: () => serviceRef.current?.getEvents() || [],
    clearEvents: () => serviceRef.current?.clearEvents(),
    getClientId: () => serviceRef.current?.getClientId() || "",
  };
}

function playAlertSound(severity: string): void {
  if (typeof window === "undefined") return;

  const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();

  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);

  const frequencies = {
    critical: [800, 1000, 1200],
    error: [600, 800],
    warning: [400, 600],
    info: [400]
  };

  const freqs = frequencies[severity as keyof typeof frequencies] || frequencies.info;
  let currentFreqIndex = 0;

  oscillator.frequency.setValueAtTime(freqs[currentFreqIndex], audioContext.currentTime);
  gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);

  oscillator.start();

  const interval = setInterval(() => {
    currentFreqIndex = (currentFreqIndex + 1) % freqs.length;
    oscillator.frequency.setValueAtTime(freqs[currentFreqIndex], audioContext.currentTime);
  }, 200);

  setTimeout(() => {
    clearInterval(interval);
    oscillator.stop();
    audioContext.close();
  }, 1000);
}

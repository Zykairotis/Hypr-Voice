import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketMessage, VoiceState, ServerStatus, LogEntry, Session, PerformanceMetrics } from '@/types';

interface UseWebSocketOptions {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export function useWebSocket({
  url,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setConnectionStatus('connected');
        setReconnectAttempts(0);
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          message.timestamp = new Date(message.timestamp);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setConnectionStatus('disconnected');
        onDisconnect?.();

        if (shouldReconnectRef.current && !event.wasClean && reconnectAttempts < maxReconnectAttempts) {
          setReconnectAttempts(prev => prev + 1);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        setConnectionStatus('error');
        onError?.(error);
      };

    } catch (error) {
      setConnectionStatus('error');
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [url, reconnectInterval, maxReconnectAttempts, reconnectAttempts, onConnect, onDisconnect, onError]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    reconnectAttempts,
    connect,
    disconnect,
    send,
  };
}

export function useVoiceState(url: string) {
  const [voiceState, setVoiceState] = useState<VoiceState>({
    isRecording: false,
    isActive: false,
    isProcessing: false,
    audioLevel: 0,
    f9Pressed: false,
    f10Pressed: false,
  });

  const { lastMessage } = useWebSocket({
    url,
    onMessage: (message) => {
      if (message.type === 'voice_state') {
        setVoiceState(message.data);
      }
    },
  });

  return voiceState;
}

export function useServerStatus(url: string) {
  const [serverStatus, setServerStatus] = useState<ServerStatus>({
    running: false,
  });

  const { lastMessage } = useWebSocket({
    url,
    onMessage: (message) => {
      if (message.type === 'server_status') {
        setServerStatus(message.data);
      }
    },
  });

  return serverStatus;
}

export function useLogs(url: string, maxEntries = 1000) {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const { lastMessage } = useWebSocket({
    url,
    onMessage: (message) => {
      if (message.type === 'log') {
        setLogs(prev => {
          const newLogs = [message.data, ...prev];
          return newLogs.slice(0, maxEntries);
        });
      }
    },
  });

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  return { logs, clearLogs };
}

export function useSessions(url: string) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);

  const { lastMessage } = useWebSocket({
    url,
    onMessage: (message) => {
      if (message.type === 'session') {
        const sessionData = message.data;

        if (sessionData.status === 'active') {
          setCurrentSession(sessionData);
        } else {
          setCurrentSession(null);
        }

        setSessions(prev => {
          const existingIndex = prev.findIndex(s => s.id === sessionData.id);
          if (existingIndex >= 0) {
            const updated = [...prev];
            updated[existingIndex] = sessionData;
            return updated.sort((a, b) => new Date(b.startTime).getTime() - new Date(a.startTime).getTime());
          } else {
            return [sessionData, ...prev].sort((a, b) => new Date(b.startTime).getTime() - new Date(a.startTime).getTime());
          }
        });
      }
    },
  });

  return { sessions, currentSession };
}

export function usePerformanceMetrics(url: string) {
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([]);
  const [currentMetrics, setCurrentMetrics] = useState<PerformanceMetrics | null>(null);

  const { lastMessage } = useWebSocket({
    url,
    onMessage: (message) => {
      if (message.type === 'metrics') {
        const metricData = message.data;
        setCurrentMetrics(metricData);

        setMetrics(prev => {
          const newMetrics = [metricData, ...prev.slice(0, 59)]; // Keep last 60 data points (1 hour at 1-minute intervals)
          return newMetrics;
        });
      }
    },
  });

  return { metrics, currentMetrics };
}
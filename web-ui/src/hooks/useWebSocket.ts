import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketMessage, PerformanceMetrics } from '../types/logViewer';

interface UseWebSocketOptions {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  sendMessage: (message: any) => void;
  reconnect: () => void;
  disconnect: () => void;
  metrics: PerformanceMetrics;
}

export const useWebSocket = ({
  url,
  reconnectInterval = 3000,
  maxReconnectAttempts = 10,
  onMessage,
  onConnect,
  onDisconnect,
  onError
}: UseWebSocketOptions): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    totalEntries: 0,
    entriesPerSecond: 0,
    memoryUsage: 0,
    averageProcessingTime: 0,
    connectionStatus: 'disconnected',
    lastUpdate: new Date()
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const messageBufferRef = useRef<WebSocketMessage[]>([]);
  const lastMetricsUpdateRef = useRef<number>(Date.now());
  const entriesCountRef = useRef<number>(0);

  const updateMetrics = useCallback(() => {
    const now = Date.now();
    const timeDiff = (now - lastMetricsUpdateRef.current) / 1000; // in seconds

    if (timeDiff >= 1) { // Update every second
      const entriesPerSecond = entriesCountRef.current / timeDiff;

      setMetrics(prev => ({
        ...prev,
        entriesPerSecond,
        connectionStatus: wsRef.current?.readyState === WebSocket.OPEN ? 'connected' : 'disconnected',
        lastUpdate: new Date(),
        memoryUsage: performance.memory ? performance.memory.usedJSHeapSize : 0
      }));

      entriesCountRef.current = 0;
      lastMetricsUpdateRef.current = now;
    }
  }, []);

  const processMessage = useCallback((rawMessage: string) => {
    try {
      const message: WebSocketMessage = JSON.parse(rawMessage);

      // Update entry count for metrics
      if (message.type === 'log') {
        entriesCountRef.current++;
        setMetrics(prev => ({
          ...prev,
          totalEntries: prev.totalEntries + 1
        }));
      }

      // Handle metrics updates from server
      if (message.type === 'metrics') {
        setMetrics(prev => ({
          ...prev,
          ...message.data,
          connectionStatus: 'connected',
          lastUpdate: new Date()
        }));
      }

      // Update performance metrics
      updateMetrics();

      // Buffer message for processing
      messageBufferRef.current.push(message);

      // Limit buffer size to prevent memory issues
      if (messageBufferRef.current.length > 1000) {
        messageBufferRef.current = messageBufferRef.current.slice(-500);
      }

      // Call user callback
      if (onMessage) {
        onMessage(message);
      }
    } catch (err) {
      console.error('Failed to process WebSocket message:', err);
      setError('Failed to process message');
    }
  }, [onMessage, updateMetrics]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectAttemptsRef.current = 0;

        // Request initial data
        ws.send(JSON.stringify({
          type: 'subscribe',
          data: {
            sources: ['agent.log', 'server.log', 'client.log']
          }
        }));

        if (onConnect) {
          onConnect();
        }
      };

      ws.onmessage = (event) => {
        processMessage(event.data);
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setIsConnecting(false);

        if (onDisconnect) {
          onDisconnect();
        }

        // Attempt to reconnect if not explicitly closed
        if (!event.wasClean && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          setMetrics(prev => ({
            ...prev,
            connectionStatus: 'reconnecting'
          }));

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setError('Maximum reconnection attempts reached');
          setMetrics(prev => ({
            ...prev,
            connectionStatus: 'error'
          }));
        }
      };

      ws.onerror = (event) => {
        setIsConnecting(false);
        setError('WebSocket connection error');

        if (onError) {
          onError(event);
        }

        setMetrics(prev => ({
          ...prev,
          connectionStatus: 'error'
        }));
      };

    } catch (err) {
      setIsConnecting(false);
      setError(`Failed to create WebSocket connection: ${err}`);
    }
  }, [url, reconnectInterval, maxReconnectAttempts, onConnect, onDisconnect, onError, processMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
      } catch (err) {
        setError('Failed to send message');
      }
    } else {
      setError('WebSocket is not connected');
    }
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(connect, 100);
  }, [disconnect, connect]);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Periodic metrics update
  useEffect(() => {
    const interval = setInterval(updateMetrics, 1000);
    return () => clearInterval(interval);
  }, [updateMetrics]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    isConnected,
    isConnecting,
    error,
    sendMessage,
    reconnect,
    disconnect,
    metrics
  };
};

// Hook for getting buffered messages
export const useWebSocketBuffer = (wsHook: UseWebSocketReturn) => {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);

  const consumeMessages = useCallback(() => {
    const newMessages = Array.from(messageBufferRef.current);
    messageBufferRef.current = [];
    setMessages(prev => [...prev, ...newMessages]);
    return newMessages;
  }, []);

  const clearBuffer = useCallback(() => {
    messageBufferRef.current = [];
    setMessages([]);
  }, []);

  return {
    messages,
    consumeMessages,
    clearBuffer
  };
};
// WebSocket hook for real-time agent monitoring

'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { AgentEvent, EventType } from './types';

interface UseWebSocketOptions {
  onEvent?: (event: AgentEvent) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  subscribedAgents?: string[];
}

export function useAgentWebSocket(options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const clientIdRef = useRef<string>(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  const { onEvent, onConnect, onDisconnect, onError, subscribedAgents = [] } = options;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');

    try {
      const wsUrl = `ws://localhost:8922/ws/${clientIdRef.current}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        onConnect?.();

        // Subscribe to all requested agents
        subscribedAgents.forEach(agentId => {
          subscribeToAgent(agentId);
        });
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'pong') {
            return;
          }

          if (data.type === 'subscribed') {
            console.log(`Subscribed to agent: ${data.agent_id}`);
            return;
          }

          // Treat as agent event
          if (data.event_type && data.agent_id) {
            const agentEvent: AgentEvent = {
              event_type: data.event_type as EventType,
              agent_id: data.agent_id,
              timestamp: data.timestamp,
              data: data.data || {},
            };

            onEvent?.(agentEvent);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
        onError?.(error);
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setConnectionStatus('disconnected');
        onDisconnect?.();

        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          if (wsRef.current?.readyState !== WebSocket.OPEN) {
            connect();
          }
        }, 3000);
      };
    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setConnectionStatus('error');
    }
  }, [onConnect, onDisconnect, onError, subscribedAgents, onEvent]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const subscribeToAgent = useCallback((agentId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        agent_id: agentId,
      }));
    }
  }, []);

  const unsubscribeFromAgent = useCallback((agentId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        agent_id: agentId,
      }));
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const ping = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Update subscriptions when subscribedAgents changes
  useEffect(() => {
    if (isConnected && subscribedAgents.length > 0) {
      subscribedAgents.forEach(agentId => {
        subscribeToAgent(agentId);
      });
    }
  }, [isConnected, subscribedAgents, subscribeToAgent]);

  return {
    isConnected,
    connectionStatus,
    clientId: clientIdRef.current,
    connect,
    disconnect,
    subscribeToAgent,
    unsubscribeFromAgent,
    sendMessage,
    ping,
  };
}

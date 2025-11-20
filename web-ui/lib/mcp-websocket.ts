// MCP Server WebSocket Manager
import { useMCPStore } from "./mcp-store";

export class MCPWebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 5000;
  private isConnecting = false;

  constructor(private url: string = "ws://localhost:8933/mcp") {}

  connect() {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log("MCP WebSocket connected");
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.send({ type: "subscribe", channels: ["server-status", "metrics", "logs"] });
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      this.ws.onclose = () => {
        console.log("MCP WebSocket disconnected");
        this.isConnecting = false;
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error("MCP WebSocket error:", error);
        this.isConnecting = false;
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      this.isConnecting = false;
      this.attemptReconnect();
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnecting = false;
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket is not connected");
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    this.reconnectAttempts++;
    console.log(
      `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
    );

    setTimeout(() => {
      this.connect();
    }, this.reconnectInterval * this.reconnectAttempts);
  }

  private handleMessage(message: any) {
    const { updateMetrics, updateHealth, addLog } = useMCPStore.getState();

    switch (message.type) {
      case "server-status":
        // Update server status
        if (message.serverId && message.status) {
          useMCPStore.getState().updateServer(message.serverId, {
            status: message.status,
            lastHeartbeat: new Date(),
          });
        }
        break;

      case "metrics":
        // Update server metrics
        if (message.serverId && message.metrics) {
          updateMetrics(message.serverId, message.metrics);
        }
        break;

      case "health":
        // Update health check results
        if (message.serverId && message.health) {
          updateHealth(message.serverId, message.health);
        }
        break;

      case "log":
        // Add log entry
        if (message.serverId && message.log) {
          addLog(message.serverId, message.log);
        }
        break;

      case "server-started":
        if (message.serverId) {
          useMCPStore.getState().updateServer(message.serverId, {
            status: "online",
            lastStarted: new Date(),
          });
        }
        break;

      case "server-stopped":
        if (message.serverId) {
          useMCPStore.getState().updateServer(message.serverId, {
            status: "offline",
          });
        }
        break;

      case "server-error":
        if (message.serverId && message.error) {
          useMCPStore.getState().updateServer(message.serverId, {
            status: "error",
          });
          addLog(message.serverId, {
            id: Date.now().toString(),
            serverId: message.serverId,
            timestamp: new Date(),
            level: "error",
            message: message.error,
          });
        }
        break;

      default:
        console.log("Unknown message type:", message.type);
    }
  }

  // Request server status update
  requestServerStatus(serverId: string) {
    this.send({ type: "request-status", serverId });
  }

  // Subscribe to server-specific updates
  subscribeServer(serverId: string) {
    this.send({ type: "subscribe-server", serverId });
  }

  // Unsubscribe from server-specific updates
  unsubscribeServer(serverId: string) {
    this.send({ type: "unsubscribe-server", serverId });
  }

  // Send command to server
  sendCommand(serverId: string, command: string, args?: any) {
    this.send({
      type: "command",
      serverId,
      command,
      args,
    });
  }
}

// Singleton instance
let mcpWebSocket: MCPWebSocketManager | null = null;

export const getMCPWebSocket = () => {
  if (!mcpWebSocket) {
    mcpWebSocket = new MCPWebSocketManager();
  }
  return mcpWebSocket;
};

// React hook for using MCP WebSocket
export const useMCPWebSocket = () => {
  const manager = getMCPWebSocket();

  return {
    connect: manager.connect.bind(manager),
    disconnect: manager.disconnect.bind(manager),
    send: manager.send.bind(manager),
    requestServerStatus: manager.requestServerStatus.bind(manager),
    subscribeServer: manager.subscribeServer.bind(manager),
    unsubscribeServer: manager.unsubscribeServer.bind(manager),
    sendCommand: manager.sendCommand.bind(manager),
  };
};

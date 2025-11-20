# Real-time Activity Monitor

A comprehensive real-time system monitoring solution with WebSocket streaming for the Hypr-Voice application.

## Features

### 1. Live Event Stream
- **Real-time event display** showing agent_created, agent_started, agent_output, agent_error, agent_completed, tool_execution, mcp_event, skill_executed, voice_synthesis, and more
- **Event filtering and search** by type, source, severity, or agent ID
- **Event categorization and tagging** with visual indicators
- **Event history and replay** with export functionality (JSON)

### 2. System Metrics Dashboard
- **CPU and memory usage** tracking
- **Active agents count** monitoring
- **WebSocket connections** status
- **Request throughput** metrics
- **Response time** tracking
- **Resource distribution** visualization

### 3. Agent Activity Visualization
- **Agent execution timeline** showing lifecycle events
- **Agent state transitions** (idle, running, completed, error)
- **Task completion tracking** with output/error counts
- **Agent detail view** with full event history
- **Agent statistics** (tasks, outputs, errors, duration)

### 4. Log Management
- **Centralized log viewer** with filtering
- **Log filtering** by level (debug, info, warning, error, critical)
- **Search functionality** across all log entries
- **Export capability** (JSON format)
- **Log statistics** by severity

### 5. Performance Monitoring
- **Response time graphs** with trend analysis
- **Success/error rates** tracking
- **Throughput metrics** visualization
- **Bottleneck identification** with alerts
- **Interactive charts** using Recharts library
- **Real-time metric updates**

### 6. Alerts & Notifications
- **Real-time error alerts** with sound notifications
- **Performance threshold alerts** (CPU, memory, error rate)
- **Custom alert rules** engine
- **Alert management** (enable/disable, configure)
- **Notification history** with severity levels
- **Test alerts** for validation

### 7. Activity Timeline
- **Chronological event view** with visual timeline
- **Zoom and filter** by time range (1h, 6h, 24h, all)
- **Event correlation** with relationship mapping
- **Session-based grouping** with gap detection
- **Export functionality** for analysis
- **Interactive playback** with controls

### 8. Data Export
- **Export activity data** (JSON, CSV formats)
- **Generate activity reports** with statistics
- **Scheduled reports** capability
- **Integration ready** for external tools

## WebSocket Events

The monitor listens to the following event types via WebSocket:

### Agent Events
- `agent_created` - New agent spawned
- `agent_started` - Agent begins execution
- `agent_output` - Agent produces output
- `agent_error` - Agent encounters error
- `agent_completed` - Agent finishes successfully

### System Events
- `tool_execution` - Tool/utility execution
- `mcp_event` - MCP (Model Context Protocol) events
- `skill_executed` - Skill execution events
- `voice_synthesis` - Voice synthesis operations
- `system_metrics` - Periodic system metrics
- `alert_triggered` - Alert conditions met
- `connection_status` - Connection state changes

## Architecture

### Components Structure

```
app/components/monitor/
├── MonitorDashboard.tsx      # Main dashboard component
├── EventStream.tsx           # Live event stream display
├── AgentActivity.tsx         # Agent monitoring
├── alerts/
│   └── AlertCenter.tsx       # Alert management
├── charts/
│   └── PerformanceCharts.tsx # Performance visualization
├── logs/
│   └── LogViewer.tsx         # Log management
├── metrics/
│   ├── SystemMetrics.tsx     # System metrics
│   └── MetricsHistory.tsx    # Floating metrics widget
└── timeline/
    └── ActivityTimeline.tsx  # Activity timeline view
```

### WebSocket Service

The `lib/websocket.ts` module provides:
- **WebSocket connection management** with auto-reconnect
- **Event buffering** (up to 1000 events)
- **Real-time data streaming** to all components
- **Client identification** with unique IDs
- **Heartbeat mechanism** for connection health
- **Event filtering** and querying
- **Sound notifications** for critical alerts

## Usage

### Basic Setup

```tsx
import { useWebSocket } from "lib/websocket";

function MyComponent() {
  const { isConnected, events, metrics, alerts } = useWebSocket();

  return (
    <div>
      <p>Connection: {isConnected ? "Connected" : "Disconnected"}</p>
      <p>Active Agents: {metrics?.activeAgents}</p>
    </div>
  );
}
```

### Accessing the Monitor

Navigate to the **Monitor** tab in the main application. The monitor is integrated into the existing dashboard with:
- Status indicator in the header
- Full-screen monitoring interface
- Floating metrics widget
- Keyboard-accessible controls

## Configuration

### Alert Rules

Default alert rules include:
- High CPU Usage (>80%)
- Critical CPU Usage (>95%)
- High Memory Usage (>85%)
- Error Rate Spike (>10%)

### WebSocket Endpoint

WebSocket URL: `ws://localhost:8933/ws/{client_id}`

Auto-generated client ID format: `client_{timestamp}_{random}`

### Event Buffer

- Maximum events: 1000
- Auto-cleanup: Oldest events removed
- Export available at any time

## Data Models

### MonitoringEvent
```typescript
{
  id: string;
  type: EventType;
  timestamp: number;
  source: string;
  data: any;
  severity?: "info" | "warning" | "error" | "critical";
  agentId?: string;
  correlationId?: string;
}
```

### SystemMetrics
```typescript
{
  timestamp: number;
  cpu: number;
  memory: number;
  activeAgents: number;
  websocketConnections: number;
  requestsPerSecond: number;
  averageResponseTime: number;
  errorRate: number;
}
```

### AlertRule
```typescript
{
  id: string;
  name: string;
  condition: string;
  threshold: number;
  severity: "info" | "warning" | "error" | "critical";
  enabled: boolean;
  cooldown: number;
  lastTriggered?: number;
}
```

## Technical Details

### Dependencies
- Next.js 16.0.1
- React 19.2.0
- Framer Motion (animations)
- Recharts (charts)
- Lucide React (icons)
- Radix UI (UI primitives)

### Performance Optimizations
- Event batching to prevent UI thrashing
- Lazy loading of components
- Memoization of expensive calculations
- Efficient re-rendering with React hooks
- Debounced search and filtering

### Browser Compatibility
- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- WebSocket API required

## Development

### Adding New Event Types

1. Add to `EventType` union in `lib/websocket.ts`
2. Add icon/color mapping in components
3. Update filters as needed

### Creating Custom Charts

Use the Recharts library:

```tsx
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="time" />
    <YAxis />
    <Tooltip />
    <Line type="monotone" dataKey="value" stroke="#3b82f6" />
  </LineChart>
</ResponsiveContainer>
```

## Troubleshooting

### WebSocket Connection Issues
- Check server is running on correct port
- Verify firewall allows WebSocket connections
- Check browser console for errors
- Test with different browsers

### Missing Events
- Ensure event types are in the union
- Check WebSocket connection status
- Verify event data format
- Check event buffer size

### Performance Issues
- Reduce event buffer size if needed
- Implement event filtering
- Check for memory leaks in components
- Monitor DOM node count

## API Integration

The monitor expects a WebSocket server that sends JSON messages:

```json
{
  "event": {
    "id": "evt_123",
    "type": "agent_created",
    "timestamp": 1234567890,
    "source": "agent_manager",
    "data": { "agentId": "agent_1" },
    "severity": "info"
  },
  "metrics": {
    "timestamp": 1234567890,
    "cpu": 45.2,
    "memory": 62.1,
    "activeAgents": 5,
    "websocketConnections": 1,
    "requestsPerSecond": 12.5,
    "averageResponseTime": 85,
    "errorRate": 0.5
  },
  "alert": {
    "ruleId": "rule_1",
    "message": "High CPU usage detected",
    "severity": "warning",
    "timestamp": 1234567890
  }
}
```

## License

Part of the Hypr-Voice project.

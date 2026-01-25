# MCP Servers Management Interface

A comprehensive Model Context Protocol (MCP) server management system built for Hypr-Voice.

## Features

### 🖥️ MCP Server Dashboard
- **Real-time Monitoring**: Track server status, health, and performance metrics
- **Quick Actions**: Start, stop, restart, and test servers with one click
- **Search & Filter**: Find servers by category, status, or name
- **Bulk Operations**: Manage multiple servers simultaneously

### ⚙️ Server Configuration
- **Visual Editor**: Intuitive UI for configuring server parameters
- **Connection Settings**: Set host, port, timeout, and retry parameters
- **Authentication**: Secure API key and token management with encryption
- **Environment Variables**: Configure server environment
- **Capabilities**: Define server capabilities (read, write, search, etc.)

### 📊 Analytics Dashboard
- **Performance Metrics**: Request volume, response times, error rates
- **Usage Statistics**: Track popular servers and categories
- **Uptime Monitoring**: Server availability and health scores
- **Visual Charts**: Interactive graphs and heatmaps
- **Export Data**: Download analytics reports

### 🏪 MCP Server Store
- **Community Servers**: Browse verified MCP servers
- **One-Click Install**: Install servers directly from the store
- **Ratings & Reviews**: Community-driven quality assessment
- **Categories**: Filter by server type (filesystem, web, database, etc.)
- **Verified Publishers**: Trust indicators for quality servers

### 🔧 Custom Server Builder
- **Code Editor**: Built-in editor with syntax highlighting
- **Templates**: Start from proven templates (Basic, Filesystem)
- **Live Testing**: Test servers before deploying
- **Export/Import**: Share custom servers with others
- **Version Control**: Track server iterations

### 🤝 Agent-MCP Integration
- **Server Assignment**: Connect servers to specific agents
- **Usage Tracking**: Monitor agent-server interactions
- **Assignment Matrix**: Visual overview of agent-server relationships
- **Performance Metrics**: Per-agent usage statistics

### 💓 Health Monitoring
- **Real-time Health Checks**: Continuous monitoring of server health
- **Automatic Alerts**: Notifications for degraded performance
- **Health Scores**: Composite health metrics
- **Check Details**: Granular health check results

## Architecture

### Client-Side
- **Framework**: Next.js 16 with React 19
- **State Management**: Zustand for client-side state
- **WebSocket**: Real-time updates for server status
- **UI Components**: Radix UI primitives with custom styling
- **Animations**: Framer Motion for smooth transitions

### API Routes
- **Server Management**: `/api/mcp/servers`
- **Server Store**: `/api/mcp/store/servers`
- **Analytics**: `/api/mcp/analytics`
- **Real-time Updates**: WebSocket on port 8933

### Data Types
```typescript
interface MCPServerConfig {
  id: string;
  name: string;
  category: MCPServerCategory;
  status: MCPServerStatus;
  command: string;
  args?: string[];
  enabled: boolean;
  capabilities: ServerCapability[];
  // ... more fields
}
```

## Usage

### Accessing the MCP Dashboard
Navigate to `/mcp` or select "MCP Servers" from the main navigation dock.

### Managing Servers

1. **Add a Server**:
   - Click "Add Server" in the header
   - Configure basic settings
   - Test the connection
   - Save and start

2. **Monitor Servers**:
   - View real-time status in the dashboard
   - Check health metrics and performance
   - Review logs and error reports

3. **Configure Servers**:
   - Click on a server card to edit
   - Modify connection settings
   - Update authentication
   - Adjust advanced options

4. **Install from Store**:
   - Browse available servers
   - Read reviews and ratings
   - One-click install
   - Automatic configuration

### Building Custom Servers

1. **Create New Server**:
   - Navigate to "Builder" tab
   - Select a template
   - Customize server code
   - Test functionality

2. **Deploy Server**:
   - Export configuration
   - Add to local servers
   - Assign to agents
   - Monitor performance

## API Reference

### Server Operations

#### Start Server
```bash
POST /api/mcp/servers/{id}/start
```

#### Stop Server
```bash
POST /api/mcp/servers/{id}/stop
```

#### Restart Server
```bash
POST /api/mcp/servers/{id}/restart
```

#### Test Server
```bash
POST /api/mcp/servers/{id}/test
```

### Store Operations

#### List Servers
```bash
GET /api/mcp/store/servers
```

#### Install Server
```bash
POST /api/mcp/store/install/{serverId}
```

### Analytics

#### Get Analytics
```bash
GET /api/mcp/analytics
```

## WebSocket Events

### Client → Server
- `subscribe`: Subscribe to updates
- `request-status`: Request server status
- `command`: Send command to server

### Server → Client
- `server-status`: Server status update
- `metrics`: Performance metrics
- `health`: Health check results
- `log`: Log entries
- `server-started`: Server started notification
- `server-stopped`: Server stopped notification
- `server-error`: Error notification

## Configuration

### Environment Variables
```bash
MCP_WEBSOCKET_PORT=8933
MCP_STORE_URL=https://store.mcp.com
MCP_ENCRYPTION_KEY=your-encryption-key
```

### Server Configuration Example
```json
{
  "id": "filesystem-1",
  "name": "Filesystem Server",
  "category": "filesystem",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/workspace"],
  "enabled": true,
  "autoStart": true,
  "capabilities": ["read", "write", "delete"],
  "timeout": 30,
  "retryAttempts": 3
}
```

## Security

- **API Key Encryption**: Sensitive credentials are encrypted at rest
- **Secure Communication**: WebSocket connections over TLS
- **Authentication**: Support for API keys, bearer tokens, and OAuth
- **Access Control**: Server-level permissions and agent assignments

## Development

### Adding a New Server Category
1. Update `MCPServerCategory` type in `/types/mcp.ts`
2. Add category to filter dropdowns
3. Update server store categories
4. Add icon and styling

### Creating a New UI Component
```typescript
// Example: /app/components/mcp/feature/NewComponent.tsx
export default function NewComponent() {
  const { servers } = useMCPStore();
  // Component implementation
}
```

## Troubleshooting

### Server Won't Start
1. Check command and args are correct
2. Verify dependencies are installed
3. Review server logs
4. Test connection manually

### WebSocket Connection Failed
1. Verify WebSocket server is running
2. Check port 8933 is accessible
3. Review firewall settings
4. Enable debug logging

### Performance Issues
1. Monitor resource usage
2. Check health check intervals
3. Review error rates
4. Optimize server configuration

## Future Enhancements

- [ ] Kubernetes deployment support
- [ ] Server clustering and load balancing
- [ ] Advanced monitoring with Prometheus
- [ ] Automated server updates
- [ ] Multi-tenant support
- [ ] Server marketplace

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any improvements.

## License

This project is licensed under the MIT License.

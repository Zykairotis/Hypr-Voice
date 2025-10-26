# Hypr-Voice Port Configuration

This document outlines the port configuration for the Hypr-Voice web UI and API services.

## Service Ports

### Web UI (Next.js)
- **Port**: `8345`
- **URL**: `http://localhost:8345`
- **Purpose**: Main web interface for controlling and monitoring Hypr-Voice

### API Bridge (FastAPI)
- **Port**: `8435`
- **URL**: `http://localhost:8435`
- **Purpose**: HTTP to Unix socket bridge for Hypr-Voice control
- **Documentation**: `http://localhost:8435/docs`

### WebSocket Endpoints
- **URL**: `ws://localhost:8435/api/logs/stream`
- **Purpose**: Real-time log streaming and status updates

## Configuration Files

### API Bridge Configuration
- **File**: `src/api/config.yaml`
- **Setting**: `server.port: 8435`

### Web UI Configuration
- **File**: `web-ui/.env.sample`
- **Settings**:
  - `NEXT_PUBLIC_WS_URL=ws://localhost:8435`
  - `NEXT_PUBLIC_API_BASE_URL=http://localhost:8435`

### Package Scripts
- **File**: `web-ui/package.json`
- **Scripts**:
  - `"dev": "next dev -p 8345"`
  - `"start": "next start -p 8345"`

## Startup Scripts

### Individual Services

#### API Bridge
```bash
# Start API bridge on port 8435
./scripts/start_bridge.sh

# Development mode
./scripts/start_bridge.sh --dev
```

#### Web UI
```bash
# Navigate to web UI directory
cd web-ui

# Start web UI on port 8345
npm run dev

# Production mode
npm run build && npm start
```

### Combined Startup

#### All Services
```bash
# Start both API bridge and web UI
./scripts/start_web_ui.sh start

# Stop both services
./scripts/start_web_ui.sh stop

# Restart both services
./scripts/start_web_ui.sh restart

# Check status
./scripts/start_web_ui.sh status

# View logs
./scripts/start_web_ui.sh logs

# Install dependencies
./scripts/start_web_ui.sh install
```

## Environment Setup

### Local Development
1. Copy environment configuration:
   ```bash
   cp web-ui/.env.sample web-ui/.env.local
   ```

2. Update `.env.local` if needed (defaults are correct for the specified ports)

### Port Conflicts
If you experience port conflicts, you can:

1. **Check what's using the ports**:
   ```bash
   lsof -i :8345  # Web UI port
   lsof -i :8435  # API Bridge port
   ```

2. **Stop conflicting services**:
   ```bash
   ./scripts/start_web_ui.sh stop
   ```

3. **Kill processes manually** (if needed):
   ```bash
   kill -9 $(lsof -t -i:8345)  # Web UI
   kill -9 $(lsof -t -i:8435)  # API Bridge
   ```

## Access URLs

After starting the services:

| Service              | URL                            | Description                           |
|---------------------|--------------------------------|---------------------------------------|
| Web UI              | http://localhost:8345          | Main control interface                |
| API Bridge          | http://localhost:8435          | REST API for Hypr-Voice control       |
| API Documentation   | http://localhost:8435/docs     | Interactive API documentation          |
| WebSocket Logs      | ws://localhost:8435/api/logs/stream | Real-time log streaming           |

## Service Dependencies

The Web UI depends on the API Bridge service:
1. API Bridge must be running first
2. Web UI connects to API Bridge for all functionality
3. WebSocket connections provide real-time updates

## Troubleshooting

### Common Issues

1. **Port already in use**:
   - Stop existing services with `./scripts/start_web_ui.sh stop`
   - Check for other processes using the ports
   - Kill conflicting processes if needed

2. **API Bridge not responding**:
   - Check API logs: `tail -f /tmp/hypr-voice-api.log`
   - Verify Hypr-Voice is installed and accessible
   - Check Unix socket permissions: `/tmp/hypr-voice.sock`

3. **Web UI not loading**:
   - Check Web UI logs: `tail -f /tmp/hypr-voice-webui.log`
   - Verify API Bridge is running and accessible
   - Check network connectivity to localhost

4. **WebSocket connection failed**:
   - Verify API Bridge is running on port 8435
   - Check firewall settings
   - Verify WebSocket endpoint is accessible

### Log Locations

- **API Bridge Logs**: `/tmp/hypr-voice-api.log`
- **Web UI Logs**: `/tmp/hypr-voice-webui.log`
- **Hypr-Voice Logs**: `/tmp/hypr-voice-logs/agent.log`

### Health Checks

1. **API Bridge Health**:
   ```bash
   curl http://localhost:8435/api/health
   ```

2. **Web UI Health**:
   - Open http://localhost:8345 in browser
   - Check for connection status indicators

## Security Considerations

- Services bind to `0.0.0.0` (all interfaces) by default
- For production, consider restricting to localhost
- API endpoints currently have no authentication
- WebSocket connections are unencrypted (local only)

## Port Customization

If you need to use different ports:

1. Update `src/api/config.yaml` (API Bridge port)
2. Update `web-ui/package.json` (Web UI port)
3. Update `web-ui/.env.sample` (API URL references)
4. Update scripts and documentation
5. Restart services with new configuration
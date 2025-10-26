# Hypr-Voice Web UI Architecture

## System Overview

This document outlines the complete web UI architecture for Hypr-Voice, providing a modern web-based interface for managing voice transcription services with real-time monitoring, configuration management, and session analytics.

## Current System Analysis

### Existing Architecture
- **Core System**: Python-based voice transcription using Whisper
- **Communication**: Unix socket interface for internal communication
- **Configuration**: YAML-based configuration system
- **Audio Processing**: Real-time audio recording and transcription
- **Context Engine**: AI-enhanced text processing with multiple LLM providers
- **Application Profiles**: Context-aware behavior for different applications

### Key Integration Points
1. **Whisper Server**: FastAPI-based transcription service with WebSocket support
2. **Unix Socket Interface**: Internal communication between components
3. **Configuration System**: YAML files in `hypr-voice/config/`
4. **Audio Pipeline**: Real-time audio processing and VAD
5. **Context Engine**: LLM integration for text enhancement

## Proposed Web UI Architecture

### 1. High-Level System Architecture (C4 Model)

#### Level 1 - System Context
```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Browser                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Dashboard  │  │ Config UI   │  │  Log Viewer │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                           │ HTTPS/WSS
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Web UI Gateway                             │
│                   (Next.js + TypeScript)                        │
└─────────────────────────────────────────────────────────────────┘
                           │ HTTP/WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Bridge                                 │
│                   (FastAPI Service)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ HTTP Routes  │  │ WebSocket   │  │   Unix      │           │
│  │             │  │ Streaming   │  │  Socket     │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                           │ Unix Socket
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Hypr-Voice Core                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ Whisper     │  │   Context   │  │    Audio    │           │
│  │   Server    │  │   Engine    │  │   Pipeline  │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

#### Level 2 - Container Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                      Web UI Container                           │
│                   (Next.js Application)                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Frontend App                            ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         ││
│  │  │ Dashboard   │ │ Config      │ │ Sessions    │         ││
│  │  │ Component   │ │ Manager     │ │ Monitor     │         ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘         ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         ││
│  │  │ Voice       │ │ Server      │ │ System      │         ││
│  │  │ Visualizer  │ │ Control     │ │ Metrics     │         ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Bridge Container                         │
│                   (FastAPI Service)                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                HTTP API Server                             ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         ││
│  │  │   Auth      │ │   CORS      │ │   Rate      │         ││
│  │  │ Middleware  │ │ Middleware  │ │  Limiting   │         ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘         ││
│  │  ┌─────────────────────────────────────────────────────────┐│
│  │  │              WebSocket Server                          ││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     ││
│  │  │  │ Log Stream  │ │ Status      │ │ Metrics     │     ││
│  │  │  │   Service   │ │ Streamer    │ │ Streamer    │     ││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘     ││
│  │  └─────────────────────────────────────────────────────────┘│
│  │  ┌─────────────────────────────────────────────────────────┐│
│  │  │              Unix Socket Bridge                        ││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     ││
│  │  │  │   Config    │ │   Process   │ │   Health    │     ││
│  │  │  │  Manager    │ │ Controller  │ │ Monitor     │     ││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘     ││
│  │  └─────────────────────────────────────────────────────────┘│
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 2. Component Architecture

#### Frontend Components (Next.js + ShadCN UI)

```
src/
├── components/
│   ├── ui/                    # ShadCN UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── tabs.tsx
│   │   ├── switch.tsx
│   │   ├── badge.tsx
│   │   ├── progress.tsx
│   │   └── table.tsx
│   ├── layout/
│   │   ├── header.tsx
│   │   ├── sidebar.tsx
│   │   ├── footer.tsx
│   │   └── main-layout.tsx
│   ├── dashboard/
│   │   ├── system-status.tsx
│   │   ├── server-controls.tsx
│   │   ├── voice-activity.tsx
│   │   └── quick-stats.tsx
│   ├── configuration/
│   │   ├── config-editor.tsx
│   │   ├── audio-settings.tsx
│   │   ├── llm-providers.tsx
│   │   ├── app-profiles.tsx
│   │   └── validation-panel.tsx
│   ├── sessions/
│   │   ├── session-list.tsx
│   │   ├── session-details.tsx
│   │   ├── transcription-view.tsx
│   │   └── performance-metrics.tsx
│   ├── logs/
│   │   ├── log-viewer.tsx
│   │   ├── log-filter.tsx
│   │   └── real-time-stream.tsx
│   └── common/
│       ├── loading-spinner.tsx
│       ├── error-boundary.tsx
│       ├── websocket-client.tsx
│       └── api-client.tsx
├── pages/
│   ├── index.tsx              # Dashboard
│   ├── configuration.tsx
│   ├── sessions.tsx
│   ├── logs.tsx
│   └── api/
│       ├── auth/
│       ├── config/
│       ├── server/
│       └── websocket/
├── hooks/
│   ├── use-websocket.ts
│   ├── use-server-status.ts
│   ├── use-config.ts
│   └── use-sessions.ts
├── types/
│   ├── api.ts
│   ├── config.ts
│   ├── session.ts
│   └── server.ts
└── utils/
    ├── api-client.ts
    ├── websocket-client.ts
    ├── validation.ts
    └── formatting.ts
```

#### API Bridge Components (FastAPI)

```
api_bridge/
├── main.py                    # FastAPI application entry
├── routers/
│   ├── auth.py               # Authentication endpoints
│   ├── server.py             # Server control endpoints
│   ├── config.py             # Configuration management
│   ├── sessions.py           # Session data and metrics
│   ├── logs.py               # Log access and streaming
│   └── websocket.py          # WebSocket endpoints
├── middleware/
│   ├── auth.py               # JWT authentication
│   ├── cors.py               # CORS configuration
│   ├── rate_limit.py         # Rate limiting
│   └── logging.py            # Request logging
├── services/
│   ├── unix_socket_client.py # Unix socket communication
│   ├── config_manager.py     # Configuration management
│   ├── log_streamer.py       # Real-time log streaming
│   ├── process_controller.py # Process management
│   └── health_monitor.py     # Health monitoring
├── models/
│   ├── auth.py               # Authentication models
│   ├── config.py             # Configuration models
│   ├── server.py             # Server status models
│   ├── session.py            # Session data models
│   └── response.py           # Common response models
├── utils/
│   ├── security.py           # Security utilities
│   ├── validation.py         # Data validation
│   ├── socket_client.py      # Unix socket client
│   └── file_manager.py       # File operations
└── config/
    ├── settings.py           # API bridge settings
    └── logging_config.py     # Logging configuration
```

### 3. Data Flow Architecture

#### Request Flow
```
1. User Action (Web UI)
   ↓
2. HTTP Request (Next.js)
   ↓
3. API Bridge (FastAPI)
   ↓
4. Unix Socket Communication
   ↓
5. Hypr-Voice Core
   ↓
6. Response Back Through Chain
```

#### Real-time Data Flow
```
1. Hypr-Voice Core Event
   ↓
2. Unix Socket Message
   ↓
3. API Bridge WebSocket Handler
   ↓
4. WebSocket Broadcast
   ↓
5. Frontend WebSocket Client
   ↓
6. UI Update (React State)
```

### 4. API Specifications

#### REST API Endpoints

**Authentication**
```
POST   /api/auth/login          # User authentication
POST   /api/auth/refresh        # Token refresh
DELETE /api/auth/logout         # Logout
```

**Server Control**
```
GET    /api/server/status       # Server status
POST   /api/server/start        # Start server
POST   /api/server/stop         # Stop server
POST   /api/server/restart      # Restart server
GET    /api/server/metrics      # Performance metrics
GET    /api/server/health       # Health check
```

**Configuration Management**
```
GET    /api/config/list         # List config files
GET    /api/config/{file}       # Get specific config
PUT    /api/config/{file}       # Update config
POST   /api/config/validate     # Validate configuration
GET    /api/config/schemas      # Configuration schemas
```

**Session Management**
```
GET    /api/sessions            # List sessions
GET    /api/sessions/{id}       # Session details
GET    /api/sessions/{id}/transcript # Transcript data
DELETE /api/sessions/{id}       # Delete session
GET    /api/sessions/stats      # Session statistics
```

**Log Management**
```
GET    /api/logs                # Get log entries
GET    /api/logs/stream         # Stream logs (SSE)
GET    /api/logs/search         # Search logs
GET    /api/logs/levels         # Available log levels
```

#### WebSocket Events

**Server Status Updates**
```typescript
{
  type: 'server_status',
  data: {
    status: 'running' | 'stopped' | 'error',
    uptime: number,
    cpu_usage: number,
    memory_usage: number,
    active_sessions: number
  }
}
```

**Real-time Logs**
```typescript
{
  type: 'log_entry',
  data: {
    timestamp: string,
    level: 'info' | 'warn' | 'error' | 'debug',
    component: string,
    message: string,
    metadata?: object
  }
}
```

**Voice Activity**
```typescript
{
  type: 'voice_activity',
  data: {
    is_recording: boolean,
    audio_level: number,
    duration: number,
    mode: 'raw' | 'enhanced'
  }
}
```

**Session Updates**
```typescript
{
  type: 'session_update',
  data: {
    session_id: string,
    status: 'active' | 'completed' | 'error',
    transcript?: string,
    duration: number,
    metadata?: object
  }
}
```

### 5. Component Integration Details

#### F9/F10 Mode Switching
```typescript
interface ModeControlProps {
  currentMode: 'raw' | 'enhanced';
  onModeChange: (mode: 'raw' | 'enhanced') => void;
  disabled?: boolean;
}

// Component handles keyboard shortcuts and API calls
const ModeControl: React.FC<ModeControlProps> = ({
  currentMode,
  onModeChange,
  disabled
}) => {
  // WebSocket listener for mode changes
  // API integration for mode persistence
  // Keyboard event handlers for F9/F10
};
```

#### Server Status Dashboard
```typescript
interface ServerStatus {
  status: 'running' | 'stopped' | 'error' | 'starting';
  uptime: number;
  cpu_usage: number;
  memory_usage: number;
  active_sessions: number;
  last_error?: string;
}

const ServerStatusCard: React.FC = () => {
  const [status, setStatus] = useState<ServerStatus>();
  const ws = useWebSocket();

  // Real-time status updates via WebSocket
  // Server control buttons (start/stop/restart)
  // Status indicators and metrics
};
```

#### Configuration Editor
```typescript
interface ConfigEditorProps {
  configFile: string;
  schema: JSONSchema;
  initialConfig: object;
  onSave: (config: object) => void;
}

const ConfigEditor: React.FC<ConfigEditorProps> = ({
  configFile,
  schema,
  initialConfig,
  onSave
}) => {
  // YAML validation
  // Real-time validation feedback
  // Auto-save functionality
  // Schema-based form generation
};
```

### 6. Technology Stack

#### Frontend
- **Framework**: Next.js 14 (React 18)
- **UI Library**: ShadCN UI (Tailwind CSS + Radix UI)
- **Language**: TypeScript
- **State Management**: React Query + Zustand
- **WebSocket Client**: Socket.io-client
- **HTTP Client**: Axios
- **Form Handling**: React Hook Form + Zod
- **Charts**: Recharts
- **Icons**: Lucide React

#### Backend (API Bridge)
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Authentication**: JWT + OAuth2
- **WebSocket**: FastAPI WebSocket
- **Data Validation**: Pydantic
- **Async Support**: asyncio
- **Unix Socket**: socket library
- **Configuration**: Pydantic Settings

#### Integration Layer
- **Unix Socket**: Native Python socket interface
- **Process Management**: subprocess + psutil
- **File Watching**: watchdog
- **Configuration**: PyYAML
- **Logging**: structlog + loguru

### 7. Security Considerations

#### Authentication & Authorization
- JWT-based authentication with refresh tokens
- Role-based access control (admin, user, readonly)
- Session management with secure cookies
- CSRF protection for state-changing operations

#### API Security
- Rate limiting on all endpoints
- Input validation and sanitization
- SQL injection prevention (though using file-based config)
- File access restrictions to config directories

#### WebSocket Security
- Authentication token validation for WebSocket connections
- Message size limits
- Connection rate limiting
- Secure WebSocket (WSS) in production

### 8. Performance Optimization

#### Frontend Optimization
- Code splitting by route and component
- Lazy loading for heavy components
- Image optimization and serving
- Service worker for offline capability
- Virtual scrolling for large lists

#### Backend Optimization
- Async/await patterns for non-blocking operations
- Connection pooling for Unix socket connections
- Caching for configuration and status data
- Efficient WebSocket message batching
- Background task processing for file operations

### 9. Error Handling & Recovery

#### Frontend Error Handling
- Error boundaries for component errors
- Global error handling with toast notifications
- Automatic retry mechanisms for failed requests
- Graceful degradation for WebSocket disconnections
- Offline mode support

#### Backend Error Handling
- Comprehensive exception handling
- Structured error responses
- Automatic recovery from Unix socket disconnections
- Health check endpoints for monitoring
- Graceful shutdown handling

### 10. Development & Deployment

#### Development Setup
```bash
# Frontend development
cd web-ui
npm install
npm run dev

# API Bridge development
cd api_bridge
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Production Deployment
- Docker containerization for both frontend and API bridge
- Nginx reverse proxy for static file serving
- Systemd service for API bridge
- SSL/TLS termination
- Log aggregation and monitoring

### 11. Migration Strategy

#### Phase 1: API Bridge Development
1. Create FastAPI service with Unix socket bridge
2. Implement basic server control endpoints
3. Add configuration management API
4. Create WebSocket streaming for logs and status

#### Phase 2: Frontend Development
1. Set up Next.js project with ShadCN UI
2. Implement core dashboard components
3. Add configuration management interface
4. Integrate real-time features

#### Phase 3: Integration & Testing
1. End-to-end integration testing
2. Performance optimization
3. Security audit
4. Documentation completion

#### Phase 4: Deployment & Migration
1. Gradual rollout with feature flags
2. Backward compatibility maintenance
3. User training and documentation
4. Monitoring and feedback collection

This architecture provides a solid foundation for extending Hypr-Voice with modern web capabilities while maintaining integration with the existing Unix socket-based system.
# React Component Architecture & TypeScript Types

## Component Structure

### Overview

The Hypr-Voice web UI uses Next.js 14 with TypeScript, organized in a clean hierarchical structure with ShadCN UI components. The architecture follows React best practices with proper separation of concerns, type safety, and reusability.

### File Structure

```
src/
├── components/
│   ├── ui/                           # ShadCN UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── tabs.tsx
│   │   ├── switch.tsx
│   │   ├── badge.tsx
│   │   ├── progress.tsx
│   │   ├── table.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── textarea.tsx
│   │   ├── toast.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── accordion.tsx
│   │   ├── alert.tsx
│   │   ├── separator.tsx
│   │   ├── label.tsx
│   │   ├── checkbox.tsx
│   │   ├── radio-group.tsx
│   │   ├── slider.tsx
│   │   └── index.ts
│   ├── layout/
│   │   ├── app-header.tsx
│   │   ├── app-sidebar.tsx
│   │   ├── app-footer.tsx
│   │   ├── main-layout.tsx
│   │   ├── navigation.tsx
│   │   ├── breadcrumb.tsx
│   │   └── index.ts
│   ├── dashboard/
│   │   ├── system-status-card.tsx
│   │   ├── server-controls.tsx
│   │   ├── voice-activity-monitor.tsx
│   │   ├── quick-stats.tsx
│   │   ├── recent-sessions.tsx
│   │   ├── system-metrics.tsx
│   │   ├── mode-switcher.tsx
│   │   └── index.ts
│   ├── configuration/
│   │   ├── config-editor.tsx
│   │   ├── audio-settings-panel.tsx
│   │   ├── llm-providers-panel.tsx
│   │   ├── app-profiles-panel.tsx
│   │   ├── validation-panel.tsx
│   │   ├── config-file-list.tsx
│   │   ├── schema-based-form.tsx
│   │   └── index.ts
│   ├── sessions/
│   │   ├── session-list.tsx
│   │   ├── session-details.tsx
│   │   ├── session-player.tsx
│   │   ├── transcription-view.tsx
│   │   ├── session-metrics.tsx
│   │   ├── session-filters.tsx
│   │   └── index.ts
│   ├── logs/
│   │   ├── log-viewer.tsx
│   │   ├── log-filter.tsx
│   │   ├── real-time-log-stream.tsx
│   │   ├── log-export.tsx
│   │   └── index.ts
│   ├── forms/
│   │   ├── server-control-form.tsx
│   │   ├── config-upload-form.tsx
│   │   ├── search-form.tsx
│   │   └── index.ts
│   ├── charts/
│   │   ├── audio-level-chart.tsx
│   │   ├── performance-metrics-chart.tsx
│   │   ├── session-usage-chart.tsx
│   │   └── index.ts
│   └── common/
│       ├── loading-spinner.tsx
│       ├── error-boundary.tsx
│       ├── websocket-client.tsx
│       ├── api-client.tsx
│       ├── confirmation-dialog.tsx
│       ├── status-indicator.tsx
│       ├── keyboard-shortcuts.tsx
│       └── index.ts
├── pages/
│   ├── _app.tsx
│   ├── _document.tsx
│   ├── index.tsx                      # Dashboard
│   ├── configuration.tsx
│   ├── sessions/
│   │   ├── index.tsx
│   │   └── [id].tsx
│   ├── logs.tsx
│   ├── settings.tsx
│   └── api/
│       ├── auth/
│       │   ├── login.ts
│       │   └── refresh.ts
│       ├── config/
│       │   ├── [filename].ts
│       │   └── validate.ts
│       ├── server/
│       │   ├── status.ts
│       │   ├── start.ts
│       │   ├── stop.ts
│       │   └── restart.ts
│       ├── sessions/
│       │   ├── index.ts
│       │   └── [id].ts
│       └── logs/
│           ├── index.ts
│           └── search.ts
├── hooks/
│   ├── use-websocket.ts
│   ├── use-server-status.ts
│   ├── use-config.ts
│   ├── use-sessions.ts
│   ├── use-logs.ts
│   ├── use-auth.ts
│   ├── use-keyboard-shortcuts.ts
│   ├── use-local-storage.ts
│   ├── use-debounce.ts
│   └── use-polling.ts
├── types/
│   ├── api.ts
│   ├── config.ts
│   ├── session.ts
│   ├── server.ts
│   ├── log.ts
│   ├── auth.ts
│   └── websocket.ts
├── stores/
│   ├── auth-store.ts
│   ├── server-store.ts
│   ├── config-store.ts
│   ├── session-store.ts
│   └── ui-store.ts
├── utils/
│   ├── api-client.ts
│   ├── websocket-client.ts
│   ├── validation.ts
│   ├── formatting.ts
│   ├── date-utils.ts
│   ├── file-utils.ts
│   ├── keyboard-shortcuts.ts
│   └── constants.ts
├── styles/
│   ├── globals.css
│   └── components.css
└── lib/
    ├── utils.ts
    ├── validations.ts
    └── api-helpers.ts
```

## TypeScript Type Definitions

### Core API Types

```typescript
// src/types/api.ts

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: ApiError;
  message?: string;
  timestamp: string;
  request_id?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
  request_id?: string;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  offset?: number;
}

export interface PaginationResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface SearchParams {
  query?: string;
  filters?: Record<string, any>;
  sort?: {
    field: string;
    direction: 'asc' | 'desc';
  };
}
```

### Authentication Types

```typescript
// src/types/auth.ts

export interface User {
  id: string;
  username: string;
  role: UserRole;
  permissions: Permission[];
  created_at: string;
  last_login?: string;
}

export type UserRole = 'admin' | 'user' | 'readonly';

export type Permission = 'read' | 'write' | 'admin' | 'config' | 'server_control';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface JwtPayload {
  sub: string;
  username: string;
  role: UserRole;
  permissions: Permission[];
  iat: number;
  exp: number;
  jti: string;
}
```

### Server Status Types

```typescript
// src/types/server.ts

export type ServerStatus = 'running' | 'stopped' | 'error' | 'starting' | 'restarting';

export interface ServerStatusResponse {
  status: ServerStatus;
  uptime: number;
  cpu_usage: number;
  memory_usage: number;
  active_sessions: number;
  total_sessions: number;
  whisper_model: string;
  audio_device: string;
  current_mode: TranscriptionMode;
  last_activity: string;
  errors: string[];
}

export interface ServerMetrics {
  system: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    network_io: {
      bytes_sent: number;
      bytes_received: number;
    };
  };
  transcription: {
    total_transcriptions: number;
    average_latency: number;
    success_rate: number;
    error_rate: number;
  };
  audio: {
    sample_rate: number;
    channels: number;
    buffer_size: number;
    input_level: number;
  };
  sessions: {
    active_count: number;
    total_duration: number;
    average_session_length: number;
  };
}

export interface ServerControlRequest {
  config_overrides?: Record<string, any>;
}

export interface ServerControlResponse {
  message: string;
  task_id: string;
  estimated_time?: number;
}

export type TranscriptionMode = 'raw' | 'enhanced';
```

### Configuration Types

```typescript
// src/types/config.ts

export interface ConfigFile {
  name: string;
  path: string;
  description: string;
  last_modified: string;
  size: number;
}

export interface ConfigResponse {
  filename: string;
  content: string;
  schema: JSONSchema;
  metadata: {
    last_modified: string;
    checksum: string;
    version: string;
  };
}

export interface ConfigUpdateRequest {
  content: string;
  backup?: boolean;
  validate?: boolean;
}

export interface ConfigUpdateResponse {
  success: boolean;
  message: string;
  backup_created?: string;
  validation: ConfigValidation;
  requires_restart: boolean;
}

export interface ConfigValidation {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  suggestions: string[];
}

export interface ValidationError {
  path: string;
  message: string;
  value: any;
}

export interface ValidationWarning {
  path: string;
  message: string;
  value: any;
}

export interface JSONSchema {
  type: string;
  properties: Record<string, any>;
  required?: string[];
  additionalProperties?: boolean;
}

export interface ConfigValidationRequest {
  filename: string;
  content: string;
}
```

### Session Types

```typescript
// src/types/session.ts

export type SessionStatus = 'active' | 'completed' | 'error' | 'cancelled';

export interface Session {
  id: string;
  status: SessionStatus;
  start_time: string;
  end_time?: string;
  duration?: number;
  mode: TranscriptionMode;
  application: ApplicationInfo;
  transcript?: string;
  confidence?: number;
  enhanced_text?: string;
  metadata: SessionMetadata;
}

export interface ApplicationInfo {
  name: string;
  class: string;
  window_title: string;
  process_id?: number;
}

export interface SessionMetadata {
  whisper_model: string;
  llm_provider?: string;
  audio_device: string;
  sample_rate: number;
  channels: number;
  format: string;
  file_path?: string;
}

export interface SessionDetails extends Session {
  audio: AudioInfo;
  transcription?: TranscriptionInfo;
  enhancement?: EnhancementInfo;
  events: SessionEvent[];
}

export interface AudioInfo {
  device: string;
  sample_rate: number;
  channels: number;
  format: string;
  file_path: string;
  duration: number;
  size: number;
}

export interface TranscriptionInfo {
  raw_text: string;
  confidence: number;
  language: string;
  processing_time: number;
  word_count: number;
}

export interface EnhancementInfo {
  provider: string;
  model: string;
  enhanced_text: string;
  processing_time: number;
  changes_made: number;
}

export interface SessionEvent {
  timestamp: string;
  type: SessionEventType;
  details: Record<string, any>;
}

export type SessionEventType =
  | 'recording_started'
  | 'recording_stopped'
  | 'transcription_started'
  | 'transcription_completed'
  | 'enhancement_started'
  | 'enhancement_completed'
  | 'error'
  | 'cancelled';

export interface SessionStats {
  total_sessions: number;
  total_duration: number;
  average_session_length: number;
  success_rate: number;
  modes: Record<TranscriptionMode, number>;
  applications: ApplicationUsage[];
  daily_usage: DailyUsage[];
  performance: SessionPerformance;
}

export interface ApplicationUsage {
  name: string;
  count: number;
  percentage: number;
}

export interface DailyUsage {
  date: string;
  sessions: number;
  duration: number;
}

export interface SessionPerformance {
  average_latency: number;
  average_confidence: number;
  error_rate: number;
}

export interface SessionFilters {
  status?: SessionStatus;
  mode?: TranscriptionMode;
  application?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}
```

### Log Types

```typescript
// src/types/log.ts

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  component: string;
  message: string;
  metadata?: Record<string, any>;
}

export interface LogListResponse {
  logs: LogEntry[];
  pagination: {
    limit: number;
    offset: number;
    total: number;
  };
  filters: LogFilters;
}

export interface LogFilters {
  level?: LogLevel;
  component?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
}

export interface LogSearchRequest {
  query: string;
  level?: LogLevel[];
  components?: string[];
  date_from?: string;
  date_to?: string;
  limit?: number;
}

export interface LogSearchResponse {
  results: LogEntry[];
  total: number;
  search_time: number;
}
```

### WebSocket Types

```typescript
// src/types/websocket.ts

export interface WebSocketMessage {
  type: WebSocketMessageType;
  timestamp: string;
  data: any;
  id?: string;
}

export type WebSocketMessageType =
  | 'server_status_change'
  | 'voice_activity'
  | 'transcription_progress'
  | 'log_entry'
  | 'config_change'
  | 'session_created'
  | 'session_completed'
  | 'error_notification'
  | 'pong'
  | 'subscription_ack';

export interface ServerStatusChangeMessage {
  type: 'server_status_change';
  timestamp: string;
  data: {
    status: ServerStatus;
    uptime: number;
    cpu_usage: number;
    memory_usage: number;
    active_sessions: number;
  };
}

export interface VoiceActivityMessage {
  type: 'voice_activity';
  timestamp: string;
  data: {
    is_recording: boolean;
    audio_level: number;
    duration: number;
    mode: TranscriptionMode;
    peak_level: number;
    rms_level: number;
  };
}

export interface TranscriptionProgressMessage {
  type: 'transcription_progress';
  timestamp: string;
  data: {
    session_id: string;
    status: SessionStatus;
    progress: number;
    partial_text?: string;
    confidence?: number;
    estimated_time_remaining?: number;
  };
}

export interface LogEntryMessage {
  type: 'log_entry';
  timestamp: string;
  data: LogEntry;
}

export interface ConfigChangeMessage {
  type: 'config_change';
  timestamp: string;
  data: {
    filename: string;
    changes: ConfigChange[];
    requires_restart: boolean;
    applied_by: string;
  };
}

export interface ConfigChange {
  path: string;
  old_value: any;
  new_value: any;
}

export interface SessionCreatedMessage {
  type: 'session_created';
  timestamp: string;
  data: {
    session_id: string;
    application: string;
    mode: TranscriptionMode;
    audio_device: string;
  };
}

export interface SessionCompletedMessage {
  type: 'session_completed';
  timestamp: string;
  data: {
    session_id: string;
    duration: number;
    transcript: string;
    confidence: number;
    enhanced_text?: string;
    processing_time: number;
  };
}

export interface ErrorNotificationMessage {
  type: 'error_notification';
  timestamp: string;
  data: {
    error_code: string;
    message: string;
    severity: 'critical' | 'error' | 'warning';
    component: string;
    recoverable: boolean;
    suggested_action?: string;
  };
}

export interface WebSocketSubscription {
  events: WebSocketMessageType[];
  filters?: Record<string, any>;
}
```

## Component Implementations

### Dashboard Components

```typescript
// src/components/dashboard/system-status-card.tsx

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { ServerStatusResponse } from '@/types/server';
import { useServerStatus } from '@/hooks/use-server-status';

interface SystemStatusCardProps {
  className?: string;
}

export const SystemStatusCard: React.FC<SystemStatusCardProps> = ({
  className
}) => {
  const { status, isLoading, startServer, stopServer, restartServer } = useServerStatus();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'stopped': return 'bg-red-500';
      case 'starting': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">System Status</CardTitle>
        <div className={`w-3 h-3 rounded-full ${getStatusColor(status.status)}`} />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">Status</span>
            <Badge variant={status.status === 'running' ? 'default' : 'destructive'}>
              {status.status}
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">Uptime</span>
            <span className="text-sm font-medium">{formatUptime(status.uptime)}</span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">CPU Usage</span>
              <span className="text-sm font-medium">{status.cpu_usage.toFixed(1)}%</span>
            </div>
            <Progress value={status.cpu_usage} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Memory Usage</span>
              <span className="text-sm font-medium">{status.memory_usage.toFixed(1)} MB</span>
            </div>
            <Progress
              value={(status.memory_usage / 1024) * 100}
              className="h-2"
            />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">Active Sessions</span>
            <span className="text-sm font-medium">{status.active_sessions}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">Current Mode</span>
            <Badge variant="outline">{status.current_mode}</Badge>
          </div>

          <div className="flex space-x-2 pt-2">
            {status.status === 'running' ? (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={restartServer}
                  disabled={isLoading}
                >
                  Restart
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={stopServer}
                  disabled={isLoading}
                >
                  Stop
                </Button>
              </>
            ) : (
              <Button
                size="sm"
                onClick={startServer}
                disabled={isLoading}
              >
                Start
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
```

### Configuration Editor Component

```typescript
// src/components/configuration/config-editor.tsx

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ConfigResponse, ConfigValidation } from '@/types/config';
import { useConfig } from '@/hooks/use-config';

interface ConfigEditorProps {
  filename: string;
  onSave?: (filename: string, content: string) => void;
}

export const ConfigEditor: React.FC<ConfigEditorProps> = ({
  filename,
  onSave
}) => {
  const {
    config,
    validation,
    isLoading,
    updateConfig,
    validateConfig
  } = useConfig(filename);

  const [content, setContent] = useState('');
  const [isValid, setIsValid] = useState(true);
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    if (config?.content) {
      setContent(config.content);
    }
  }, [config]);

  useEffect(() => {
    if (validation) {
      setIsValid(validation.valid);
    }
  }, [validation]);

  const handleContentChange = (value: string) => {
    setContent(value);
    setIsDirty(true);

    // Debounced validation
    const timer = setTimeout(() => {
      validateConfig(filename, value);
    }, 500);

    return () => clearTimeout(timer);
  };

  const handleSave = async () => {
    try {
      await updateConfig(filename, content, true);
      setIsDirty(false);
      onSave?.(filename, content);
    } catch (error) {
      console.error('Failed to save config:', error);
    }
  };

  const handleReset = () => {
    if (config?.content) {
      setContent(config.content);
      setIsDirty(false);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Loading configuration...</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse">
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{filename}</CardTitle>
          <div className="flex items-center space-x-2">
            {isDirty && (
              <Badge variant="outline">Modified</Badge>
            )}
            {validation && (
              <Badge variant={validation.valid ? 'default' : 'destructive'}>
                {validation.valid ? 'Valid' : 'Invalid'}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="editor" className="w-full">
          <TabsList>
            <TabsTrigger value="editor">Editor</TabsTrigger>
            <TabsTrigger value="validation">Validation</TabsTrigger>
            <TabsTrigger value="schema">Schema</TabsTrigger>
          </TabsList>

          <TabsContent value="editor" className="space-y-4">
            <div className="relative">
              <Textarea
                value={content}
                onChange={(e) => handleContentChange(e.target.value)}
                className="min-h-[400px] font-mono text-sm"
                placeholder="Enter YAML configuration..."
              />
              {isDirty && (
                <div className="absolute top-2 right-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleReset}
                  >
                    Reset
                  </Button>
                </div>
              )}
            </div>

            <div className="flex justify-end space-x-2">
              <Button
                onClick={handleSave}
                disabled={!isDirty || !isValid}
              >
                Save Changes
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="validation" className="space-y-4">
            {validation && (
              <>
                {validation.errors.length > 0 && (
                  <Alert variant="destructive">
                    <AlertDescription>
                      <div className="space-y-2">
                        <strong>Validation Errors:</strong>
                        <ul className="list-disc list-inside space-y-1">
                          {validation.errors.map((error, index) => (
                            <li key={index} className="text-sm">
                              <code className="bg-gray-100 px-1 rounded">
                                {error.path}
                              </code>: {error.message}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                {validation.warnings.length > 0 && (
                  <Alert>
                    <AlertDescription>
                      <div className="space-y-2">
                        <strong>Warnings:</strong>
                        <ul className="list-disc list-inside space-y-1">
                          {validation.warnings.map((warning, index) => (
                            <li key={index} className="text-sm">
                              <code className="bg-gray-100 px-1 rounded">
                                {warning.path}
                              </code>: {warning.message}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                {validation.suggestions.length > 0 && (
                  <Alert>
                    <AlertDescription>
                      <div className="space-y-2">
                        <strong>Suggestions:</strong>
                        <ul className="list-disc list-inside space-y-1">
                          {validation.suggestions.map((suggestion, index) => (
                            <li key={index} className="text-sm">
                              {suggestion}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
              </>
            )}
          </TabsContent>

          <TabsContent value="schema" className="space-y-4">
            {config?.schema && (
              <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto">
                {JSON.stringify(config.schema, null, 2)}
              </pre>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
```

### WebSocket Client Hook

```typescript
// src/hooks/use-websocket.ts

import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '@/stores/auth-store';
import {
  WebSocketMessage,
  WebSocketMessageType,
  ServerStatusChangeMessage,
  VoiceActivityMessage,
  TranscriptionProgressMessage,
  LogEntryMessage
} from '@/types/websocket';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  lastMessage: WebSocketMessage | null;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectDelay = 1000
  } = options;

  const { token } = useAuthStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const currentReconnectAttempts = useRef(0);

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    lastMessage: null
  });

  const [subscriptions, setSubscriptions] = useState<Set<WebSocketMessageType>>(new Set());
  const messageHandlers = useRef<Map<WebSocketMessageType, Function[]>>(new Map());

  const connect = useCallback(() => {
    if (!token) {
      console.warn('Cannot connect WebSocket: No authentication token');
      return;
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setState(prev => ({
        ...prev,
        isConnected: true,
        isConnecting: false,
        error: null
      }));
      currentReconnectAttempts.current = 0;

      // Resubscribe to events
      if (subscriptions.size > 0) {
        subscribe(Array.from(subscriptions));
      }
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        setState(prev => ({ ...prev, lastMessage: message }));

        // Route message to handlers
        const handlers = messageHandlers.current.get(message.type) || [];
        handlers.forEach(handler => handler(message.data));
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      setState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false
      }));

      // Auto-reconnect if not explicitly closed
      if (event.code !== 1000 && currentReconnectAttempts.current < reconnectAttempts) {
        const delay = reconnectDelay * Math.pow(2, currentReconnectAttempts.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          currentReconnectAttempts.current++;
          connect();
        }, delay);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setState(prev => ({
        ...prev,
        error: 'WebSocket connection error'
      }));
    };
  }, [token, reconnectAttempts, reconnectDelay, subscriptions]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false
    }));
  }, []);

  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  }, []);

  const subscribe = useCallback((eventTypes: WebSocketMessageType[]) => {
    const newSubscriptions = new Set(subscriptions);
    eventTypes.forEach(type => newSubscriptions.add(type));
    setSubscriptions(newSubscriptions);

    send({
      type: 'subscribe',
      events: Array.from(newSubscriptions)
    });
  }, [subscriptions, send]);

  const unsubscribe = useCallback((eventTypes: WebSocketMessageType[]) => {
    const newSubscriptions = new Set(subscriptions);
    eventTypes.forEach(type => newSubscriptions.delete(type));
    setSubscriptions(newSubscriptions);

    send({
      type: 'unsubscribe',
      events: eventTypes
    });
  }, [subscriptions, send]);

  const addMessageHandler = useCallback((
    messageType: WebSocketMessageType,
    handler: (data: any) => void
  ) => {
    const handlers = messageHandlers.current.get(messageType) || [];
    handlers.push(handler);
    messageHandlers.current.set(messageType, handlers);

    // Return cleanup function
    return () => {
      const currentHandlers = messageHandlers.current.get(messageType) || [];
      const index = currentHandlers.indexOf(handler);
      if (index > -1) {
        currentHandlers.splice(index, 1);
        messageHandlers.current.set(messageType, currentHandlers);
      }
    };
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, token, connect, disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    send,
    subscribe,
    unsubscribe,
    addMessageHandler,
    subscriptions: Array.from(subscriptions)
  };
};

// Specific hooks for different message types
export const useServerStatusWebSocket = () => {
  const [serverStatus, setServerStatus] = useState(null);
  const ws = useWebSocket();

  useEffect(() => {
    const unsubscribe = ws.addMessageHandler('server_status_change', (data) => {
      setServerStatus(data);
    });

    ws.subscribe(['server_status_change']);

    return unsubscribe;
  }, [ws]);

  return serverStatus;
};

export const useVoiceActivityWebSocket = () => {
  const [voiceActivity, setVoiceActivity] = useState(null);
  const ws = useWebSocket();

  useEffect(() => {
    const unsubscribe = ws.addMessageHandler('voice_activity', (data) => {
      setVoiceActivity(data);
    });

    ws.subscribe(['voice_activity']);

    return unsubscribe;
  }, [ws]);

  return voiceActivity;
};

export const useTranscriptionProgressWebSocket = () => {
  const [progress, setProgress] = useState(null);
  const ws = useWebSocket();

  useEffect(() => {
    const unsubscribe = ws.addMessageHandler('transcription_progress', (data) => {
      setProgress(data);
    });

    ws.subscribe(['transcription_progress']);

    return unsubscribe;
  }, [ws]);

  return progress;
};
```

### API Client Hook

```typescript
// src/hooks/use-api-client.ts

import { useState, useEffect, useCallback } from 'react';
import { ApiResponse } from '@/types/api';
import { useAuthStore } from '@/stores/auth-store';

interface UseApiClientOptions<T> {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: any) => void;
}

interface ApiState<T> {
  data: T | null;
  isLoading: boolean;
  error: any;
  lastUpdated: Date | null;
}

export const useApiClient = <T = any>(
  endpoint: string,
  options: UseApiClientOptions<T> = {}
) => {
  const { immediate = false, onSuccess, onError } = options;
  const { token, refreshAccessToken } = useAuthStore();

  const [state, setState] = useState<ApiState<T>>({
    data: null,
    isLoading: false,
    error: null,
    lastUpdated: null
  });

  const execute = useCallback(async (
    url: string = endpoint,
    fetchOptions: RequestInit = {}
  ): Promise<T | null> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          ...fetchOptions.headers,
        },
      });

      if (response.status === 401) {
        // Token expired, try to refresh
        const refreshSuccess = await refreshAccessToken();
        if (refreshSuccess) {
          // Retry the request with new token
          return execute(url, fetchOptions);
        } else {
          throw new Error('Authentication failed');
        }
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: ApiResponse<T> = await response.json();

      if (result.success && result.data) {
        setState(prev => ({
          ...prev,
          data: result.data,
          isLoading: false,
          lastUpdated: new Date()
        }));

        onSuccess?.(result.data);
        return result.data;
      } else {
        throw new Error(result.error?.message || 'API request failed');
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error,
        isLoading: false
      }));

      onError?.(error);
      return null;
    }
  }, [endpoint, token, refreshAccessToken, onSuccess, onError]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute]);

  const reset = useCallback(() => {
    setState({
      data: null,
      isLoading: false,
      error: null,
      lastUpdated: null
    });
  }, []);

  return {
    ...state,
    execute,
    reset
  };
};

// Generic GET hook
export const useApiGet = <T>(
  endpoint: string,
  options?: UseApiClientOptions<T>
) => {
  return useApiClient<T>(endpoint, { ...options, immediate: true });
};

// Generic POST hook
export const useApiPost = <T>(
  endpoint: string,
  options?: UseApiClientOptions<T>
) => {
  const { execute, ...state } = useApiClient<T>(endpoint, options);

  const post = useCallback(async (data: any) => {
    return execute(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }, [execute, endpoint]);

  return {
    ...state,
    execute: post
  };
};

// Generic PUT hook
export const useApiPut = <T>(
  endpoint: string,
  options?: UseApiClientOptions<T>
) => {
  const { execute, ...state } = useApiClient<T>(endpoint, options);

  const put = useCallback(async (data: any) => {
    return execute(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }, [execute, endpoint]);

  return {
    ...state,
    execute: put
  };
};

// Generic DELETE hook
export const useApiDelete = <T>(
  endpoint: string,
  options?: UseApiClientOptions<T>
) => {
  const { execute, ...state } = useApiClient<T>(endpoint, options);

  const del = useCallback(async () => {
    return execute(endpoint, {
      method: 'DELETE'
    });
  }, [execute, endpoint]);

  return {
    ...state,
    execute: del
  };
};
```

This comprehensive component architecture provides a solid foundation for the Hypr-Voice web UI with proper TypeScript typing, real-time WebSocket integration, and a clean component hierarchy using ShadCN UI components.
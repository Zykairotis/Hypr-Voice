import React, { useState } from 'react';
import { LogViewer, LogLevel, LogViewerConfig } from './index';
import './App.css';

// Mock WebSocket server for demo
const createMockWebSocket = () => {
  const mockLogs = [
    { level: 'INFO', source: 'agent.log', message: 'Hypr-Voice agent started successfully', timestamp: new Date() },
    { level: 'DEBUG', source: 'server.log', message: 'WebSocket server listening on port 8080', timestamp: new Date() },
    { level: 'INFO', source: 'client.log', message: 'Client connected to log stream', timestamp: new Date() },
    { level: 'WARN', source: 'agent.log', message: 'High memory usage detected: 85%', timestamp: new Date() },
    { level: 'ERROR', source: 'server.log', message: 'Failed to connect to database: Connection timeout', timestamp: new Date() },
    { level: 'INFO', source: 'agent.log', message: 'Processing audio input: sample_rate=44100, channels=2', timestamp: new Date() },
    { level: 'DEBUG', source: 'client.log', message: 'Sent transcript request: session_id=abc123', timestamp: new Date() },
    { level: 'INFO', source: 'agent.log', message: 'Transcription completed: length=1.2s, confidence=0.94', timestamp: new Date() },
    { level: 'WARN', source: 'server.log', message: 'Rate limit approaching: 95% of requests used', timestamp: new Date() },
    { level: 'ERROR', source: 'client.log', message: 'Network error: Failed to fetch transcript', timestamp: new Date() },
    { level: 'FATAL', source: 'agent.log', message: 'Critical error: Whisper model failed to load', timestamp: new Date() },
    { level: 'INFO', source: 'server.log', message: 'Restarting agent service...', timestamp: new Date() }
  ];

  let interval: NodeJS.Timeout;

  const startStreaming = () => {
    let index = 0;
    interval = setInterval(() => {
      const log = mockLogs[index % mockLogs.length];
      log.timestamp = new Date();

      // Simulate random log generation
      if (Math.random() > 0.7) {
        window.dispatchEvent(new CustomEvent('mock-log', {
          detail: {
            type: 'log',
            data: {
              log: `[${log.timestamp.toISOString()}] [${log.level}] [${log.source}] ${log.message}`,
              source: log.source
            },
            timestamp: log.timestamp
          }
        }));
      }
      index++;
    }, 2000);
  };

  const stopStreaming = () => {
    if (interval) {
      clearInterval(interval);
    }
  };

  return { startStreaming, stopStreaming };
};

const App: React.FC = () => {
  const [config, setConfig] = useState<LogViewerConfig>({
    maxEntries: 10000,
    bufferSize: 500,
    updateInterval: 100,
    autoScroll: true,
    theme: 'auto',
    timeZone: 'UTC',
    timestampFormat: 'ISO',
    enableVirtualScrolling: true,
    enablePerformanceMetrics: true
  });

  const [websocketUrl] = useState('ws://localhost:8080/api/logs/stream');
  const mockWebSocket = createMockWebSocket();

  React.useEffect(() => {
    // Start mock log streaming for demo
    mockWebSocket.startStreaming();

    return () => {
      mockWebSocket.stopStreaming();
    };
  }, []);

  const handleEntryClick = (entry: any) => {
    console.log('Log entry clicked:', entry);
  };

  const handleBookmarkAdd = (bookmark: any) => {
    console.log('Bookmark added:', bookmark);
  };

  const handleBookmarkRemove = (bookmarkId: string) => {
    console.log('Bookmark removed:', bookmarkId);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Hypr-Voice Log Viewer Demo</h1>
        <div className="app-controls">
          <label>
            Theme:
            <select
              value={config.theme}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                theme: e.target.value as 'light' | 'dark' | 'auto'
              }))}
            >
              <option value="auto">Auto</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </label>
          <label>
            Virtual Scrolling:
            <input
              type="checkbox"
              checked={config.enableVirtualScrolling}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                enableVirtualScrolling: e.target.checked
              }))}
            />
          </label>
        </div>
      </header>

      <main className="app-main">
        <LogViewer
          websocketUrl={websocketUrl}
          config={config}
          height="calc(100vh - 80px)"
          onEntryClick={handleEntryClick}
          onBookmarkAdd={handleBookmarkAdd}
          onBookmarkRemove={handleBookmarkRemove}
          className="demo-log-viewer"
        />
      </main>

      <footer className="app-footer">
        <p>
          Advanced Real-time Log Viewer for Hypr-Voice • Built with React & TypeScript
        </p>
        <div className="demo-info">
          <span>⚡ Mock WebSocket Active</span>
          <span>📊 Performance Metrics Enabled</span>
          <span>🔍 Search & Filters Available</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
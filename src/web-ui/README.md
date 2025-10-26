# Hypr-Voice Log Viewer

An advanced real-time log viewer component built with React and TypeScript for the Hypr-Voice project. Features WebSocket streaming, virtual scrolling, search, filtering, and export capabilities.

## ✨ Features

### Core Functionality
- **Real-time log streaming** via WebSocket connection
- **Multiple log sources** support (agent.log, server.log, client.log)
- **Virtual scrolling** for handling 10,000+ log entries efficiently
- **Memory management** with bounded buffers and automatic cleanup
- **Responsive design** for mobile and desktop

### Advanced Features
- **Search functionality** with regex support and search history
- **Advanced filtering** by log level, source, time range, and session
- **Export functionality** (JSON, CSV, plain text)
- **Bookmark system** with annotations and tags
- **Performance metrics** visualization and monitoring
- **Dark/light theme** support with automatic detection
- **Accessibility** with proper ARIA labels and keyboard navigation

### Technical Features
- **TypeScript** for type safety and better development experience
- **Modular architecture** with reusable components
- **Optimized performance** with virtual scrolling and efficient rendering
- **Real-time updates** with batching and debouncing
- **Error handling** and graceful degradation
- **Cross-browser compatibility** and modern web standards

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/hypr-voice/hypr-voice-log-viewer.git
cd hypr-voice-log-viewer/web-ui

# Install dependencies
npm install

# Start development server
npm run dev
```

### Basic Usage

```tsx
import React from 'react';
import { LogViewer } from './src';

function App() {
  return (
    <LogViewer
      websocketUrl="ws://localhost:8080/api/logs/stream"
      height="600px"
      config={{
        maxEntries: 10000,
        autoScroll: true,
        theme: 'auto',
        enableVirtualScrolling: true
      }}
      onEntryClick={(entry) => console.log('Entry clicked:', entry)}
    />
  );
}
```

## 📋 API Reference

### LogViewer Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `websocketUrl` | `string` | `ws://localhost:8080/api/logs/stream` | WebSocket endpoint for log streaming |
| `config` | `Partial<LogViewerConfig>` | `DEFAULT_CONFIG` | Configuration options |
| `height` | `string \| number` | `'600px'` | Height of the log viewer |
| `onEntryClick` | `(entry: LogEntry) => void` | `undefined` | Callback when log entry is clicked |
| `onBookmarkAdd` | `(bookmark: Bookmark) => void` | `undefined` | Callback when bookmark is added |
| `onBookmarkRemove` | `(bookmarkId: string) => void` | `undefined` | Callback when bookmark is removed |

### Configuration Options

```typescript
interface LogViewerConfig {
  maxEntries: number;           // Maximum entries to keep in memory
  bufferSize: number;           // Buffer size for WebSocket
  updateInterval: number;       // Update interval in milliseconds
  autoScroll: boolean;          // Enable auto-scrolling
  theme: 'light' | 'dark' | 'auto';
  timeZone: string;             // Timezone for timestamps
  timestampFormat: string;      // Timestamp format
  enableVirtualScrolling: boolean;  // Enable virtual scrolling
  enablePerformanceMetrics: boolean; // Show performance metrics
}
```

### Log Entry Structure

```typescript
interface LogEntry {
  id: string;                   // Unique identifier
  timestamp: Date;             // Log timestamp
  level: LogLevel;             // Log level (DEBUG, INFO, WARN, ERROR, FATAL)
  source: string;              // Log source (agent.log, server.log, etc.)
  message: string;             // Log message
  metadata?: Record<string, any>; // Additional metadata
  raw?: string;                // Raw log line
  sessionId?: string;          // Session identifier
  bookmarked?: boolean;        // Whether entry is bookmarked
  annotations?: string[];      // User annotations
}
```

## 🔧 Advanced Usage

### Custom Log Parsing

```tsx
import { LogParser } from './src';

// Parse a single log entry
const entry = LogParser.parse('[2024-01-01 12:00:00] [INFO] [agent] Started', 'agent.log');

// Parse multiple log entries
const entries = LogParser.parseBatch(logLines, 'server.log');

// Extract session ID from entry
const sessionId = LogParser.extractSessionId(entry);
```

### Advanced Filtering

```tsx
import { LogFilterManager } from './src';

// Create custom filter
const filter = {
  levels: [LogLevel.ERROR, LogLevel.FATAL],
  sources: ['agent.log'],
  searchQuery: '/connection.*failed/i',
  startTime: new Date('2024-01-01'),
  endTime: new Date('2024-01-02')
};

// Apply filter to entries
const filtered = LogFilterManager.filterEntries(entries, filter);

// Get statistics
const stats = LogFilterManager.getLevelStats(entries);
const sources = LogFilterManager.getUniqueSources(entries);
```

### Export Functionality

```tsx
import { LogExporter } from './src';

// Export to JSON
const jsonData = await LogExporter.exportToJSON(entries, {
  format: 'json',
  includeMetadata: true,
  levels: [LogLevel.ERROR, LogLevel.WARN]
});

// Export and download file
await LogExporter.exportAndDownload(entries, {
  format: 'csv',
  includeMetadata: false
}, 'csv');
```

## 🎨 Theming

The log viewer supports automatic theme detection and manual theme switching:

```tsx
// Auto theme (based on system preference)
<LogViewer config={{ theme: 'auto' }} />

// Force light theme
<LogViewer config={{ theme: 'light' }} />

// Force dark theme
<LogViewer config={{ theme: 'dark' }} />
```

### Custom CSS Variables

You can customize the appearance using CSS variables:

```css
.log-viewer {
  --background-color: #ffffff;
  --text-color: #333333;
  --border-color: #e0e0e0;
  --primary-color: #007bff;
  --success-color: #28a745;
  --warning-color: #ffc107;
  --error-color: #dc3545;
}
```

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Space` | Pause/Resume log streaming |
| `Ctrl+F` | Open search panel |
| `Ctrl+B` | Bookmark selected entry |
| `Ctrl+E` | Open export dialog |
| `Escape` | Close panels/dialogs |
| `↑/↓` | Navigate search history |

## 📱 Responsive Design

The log viewer is fully responsive and works on:

- **Desktop** (1200px+): Full feature set with all panels visible
- **Tablet** (768px-1199px): Optimized layout with collapsible panels
- **Mobile** (480px-767px): Touch-friendly interface with bottom panels
- **Small Mobile** (<480px): Compact layout with essential features

## 🧪 Testing

```bash
# Run tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui
```

## 🔧 Development

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Type check
npm run typecheck

# Format code
npm run format
```

## 📊 Performance

The log viewer is optimized for performance:

- **Virtual scrolling** handles 10,000+ entries without performance degradation
- **Memory management** with bounded buffers prevents memory leaks
- **Efficient rendering** with React.memo and useMemo optimizations
- **Debounced updates** reduce unnecessary re-renders
- **Lazy loading** for panels and dialogs

### Performance Metrics

- **Initial load**: <100ms
- **Scroll performance**: 60 FPS with 10,000 entries
- **Memory usage**: <50MB with 10,000 entries
- **WebSocket latency**: <10ms for real-time updates

## 🔌 WebSocket Integration

The log viewer connects to a WebSocket endpoint for real-time log streaming:

### Message Format

```json
{
  "type": "log",
  "data": {
    "log": "[2024-01-01 12:00:00] [INFO] [agent] Message",
    "source": "agent.log"
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Supported Message Types

- `log`: New log entry
- `metrics`: Performance metrics
- `status`: Connection status
- `error`: Error message

## 🛠️ Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- 📧 Email: support@hypr-voice.com
- 💬 Discord: [Hypr-Voice Discord](https://discord.gg/hypr-voice)
- 🐛 Issues: [GitHub Issues](https://github.com/hypr-voice/hypr-voice-log-viewer/issues)
- 📖 Documentation: [Wiki](https://github.com/hypr-voice/hypr-voice-log-viewer/wiki)

## 🙏 Acknowledgments

- React team for the amazing UI library
- TypeScript team for type safety
- Vite team for the build tool
- Hypr-Voice community for feedback and contributions
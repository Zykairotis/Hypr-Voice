# Hypr-Voice Web UI

A comprehensive Next.js web interface for controlling and monitoring the Hypr-Voice system. Built with TypeScript, Tailwind CSS, and ShadCN UI components.

## Features

### 🎯 Core Functionality
- **Real-time Dashboard**: Monitor voice activity, server status, and system performance
- **Voice Control Panel**: Interactive controls for F9/F10 key monitoring and recording
- **Server Management**: Start, stop, and restart Hypr-Voice server with status monitoring
- **Live Log Viewer**: Real-time log streaming with filtering and search capabilities
- **Session Monitoring**: Track voice transcription sessions with detailed analytics
- **Configuration Editor**: YAML-based configuration editing with real-time validation

### 🎨 User Interface
- **Responsive Design**: Mobile-first design that works on all screen sizes
- **Dark/Light Theme**: System theme support with manual override options
- **Accessibility**: WCAG compliant with keyboard navigation and screen reader support
- **Real-time Updates**: WebSocket connections for live data synchronization
- **Interactive Charts**: Performance metrics visualization with Recharts

### ⚡ Technical Features
- **TypeScript**: Full type safety throughout the application
- **Component Architecture**: Modular, reusable React components
- **Error Handling**: Comprehensive error boundaries and graceful degradation
- **Performance**: Optimized loading states and virtual scrolling for large datasets
- **Security**: Input validation and XSS protection

## Port Configuration

**Default Ports:**
- **Web UI**: `http://localhost:8345`
- **API Bridge**: `http://localhost:8435`
- **API Documentation**: `http://localhost:8435/docs`

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Hypr-Voice backend server running
- API Bridge service running on port 8435

### Installation

1. Navigate to the web-ui directory:
```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice-main/web-ui
```

2. Install dependencies:
```bash
npm install
```

3. Copy environment configuration:
```bash
cp .env.sample .env.local
```

4. Start the development server:
```bash
npm run dev
```

5. Open [http://localhost:8345](http://localhost:8345) in your browser.

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── config/            # Configuration page
│   ├── logs/              # Logs page
│   ├── sessions/          # Sessions page
│   ├── settings/          # Settings page
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Dashboard page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── ui/               # ShadCN UI components
│   ├── error-boundary.tsx
│   ├── voice-control-panel.tsx
│   ├── server-control-panel.tsx
│   ├── log-viewer.tsx
│   ├── performance-chart.tsx
│   ├── session-overview.tsx
│   ├── session-details.tsx
│   ├── config-editor.tsx
│   └── navigation.tsx
├── hooks/                 # Custom React hooks
│   └── use-websocket.ts
├── lib/                   # Utility functions
│   ├── utils.ts
│   └── validations.ts
├── types/                 # TypeScript type definitions
│   └── index.ts
└── utils/                 # Helper utilities
```

## Configuration

### Environment Variables

Key environment variables (see `.env.sample`):

- `NEXT_PUBLIC_WS_URL`: WebSocket server URL
- `NEXT_PUBLIC_API_BASE_URL`: REST API base URL
- `NEXT_PUBLIC_DEBUG`: Enable debug mode
- `NEXT_PUBLIC_LOG_LEVEL`: Default log level

### WebSocket Integration

The application connects to the Hypr-Voice WebSocket server for real-time updates:

```typescript
// Example WebSocket hook usage
const { isConnected, lastMessage, send } = useWebSocket({
  url: 'ws://localhost:8765',
  onMessage: (message) => {
    console.log('Received:', message);
  }
});
```

### Theme Configuration

The application supports light, dark, and system themes:

```typescript
// Settings persistence
const [settings, setSettings] = useState<AppSettings>({
  theme: 'system', // 'light' | 'dark' | 'system'
  language: 'en',
  autoStart: false,
  notifications: true,
  logLevel: 'info',
  refreshInterval: 5000,
  maxLogEntries: 1000,
});
```

## Components

### VoiceControlPanel
Main control interface for voice recording with F9/F10 key monitoring, audio level visualization, and server controls.

### ServerControlPanel
Server management interface with start/stop controls, resource usage monitoring, and status indicators.

### LogViewer
Real-time log viewer with filtering, search, export capabilities, and virtual scrolling for performance.

### SessionOverview
Session analytics dashboard with productivity metrics, application usage tracking, and historical data visualization.

### ConfigEditor
YAML configuration editor with real-time validation, syntax highlighting, and import/export functionality.

## Development

### Code Style

- TypeScript with strict type checking
- ESLint with Next.js configuration
- Prettier for code formatting
- Conventional commits for version control

### Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

### Linting

```bash
# Run ESLint
npm run lint

# Fix linting issues
npm run lint:fix

# Type checking
npm run typecheck
```

## Deployment

### Docker

```dockerfile
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS builder
WORKDIR /app
COPY . .
RUN npm ci
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
COPY --from=base /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

CMD ["npm", "start"]
```

### Static Export

```bash
# Build static version
npm run build

# Export static files
npm run export
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow the existing code style and patterns
- Add TypeScript types for all new components
- Include error handling and loading states
- Test on multiple screen sizes
- Update documentation for new features

## Performance

### Optimization Techniques

- **Virtual Scrolling**: For large log lists and data tables
- **Debouncing**: For search and filter inputs
- **Memoization**: For expensive computations
- **Code Splitting**: Lazy loading of components
- **Image Optimization**: Next.js Image component usage

### Monitoring

The application includes built-in performance monitoring:

```typescript
// Performance metrics hook
const { metrics, currentMetrics } = usePerformanceMetrics(wsUrl);
```

## Security

### Best Practices

- **Input Validation**: All user inputs are validated
- **XSS Protection**: Content Security Policy headers
- **API Security**: Proper error handling without information leakage
- **Dependency Updates**: Regular security updates

### Environment Variables

Never commit sensitive information to version control. Use `.env.local` for development secrets.

## Troubleshooting

### Common Issues

**WebSocket Connection Failed**
- Check if Hypr-Voice server is running on port 8765
- Verify WebSocket URL in environment variables
- Check browser console for connection errors

**Build Errors**
- Clear Next.js cache: `rm -rf .next`
- Delete node_modules and reinstall: `rm -rf node_modules package-lock.json && npm install`
- Check for TypeScript errors with `npm run typecheck`

**Performance Issues**
- Check for memory leaks in WebSocket connections
- Monitor bundle size with `npm run analyze`
- Use React DevTools Profiler for component performance

## License

This project is licensed under the MIT License - see the parent project LICENSE file for details.

## Files Created

This web UI includes the following key files:

### Core Application Files:
- `/src/app/layout.tsx` - Root layout with navigation
- `/src/app/page.tsx` - Main dashboard page
- `/src/app/config/page.tsx` - Configuration management
- `/src/app/logs/page.tsx` - Log viewing interface
- `/src/app/sessions/page.tsx` - Session monitoring
- `/src/app/settings/page.tsx` - Application settings

### Components:
- `/src/components/voice-control-panel.tsx` - Voice recording controls
- `/src/components/server-control-panel.tsx` - Server management
- `/src/components/log-viewer.tsx` - Real-time log display
- `/src/components/performance-chart.tsx` - Metrics visualization
- `/src/components/session-overview.tsx` - Session analytics
- `/src/components/config-editor.tsx` - YAML configuration editor
- `/src/components/navigation.tsx` - Main navigation
- `/src/components/error-boundary.tsx` - Error handling

### Hooks and Utilities:
- `/src/hooks/use-websocket.ts` - WebSocket management
- `/src/lib/utils.ts` - Utility functions
- `/src/lib/validations.ts` - Input validation
- `/src/types/index.ts` - TypeScript type definitions

### Configuration:
- `package.json` - Dependencies and scripts
- `tailwind.config.ts` - Tailwind CSS configuration
- `tsconfig.json` - TypeScript configuration
- `next.config.js` - Next.js configuration

The web UI is now ready for development and can be extended with additional features as needed!
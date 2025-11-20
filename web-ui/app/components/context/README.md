# Context Manager Components

This directory contains React components for the Hypr-Whisper Context Manager system.

## Components

### Core Components

- **ContextDashboard.tsx** - Main dashboard with all context features
- **ShellHistoryManager.tsx** - Shell command history viewer and manager
- **ClipboardManager.tsx** - Clipboard history viewer with privacy controls
- **ApplicationDetector.tsx** - Real-time application detection and tracking

### Visualization

- **ContextTimeline.tsx** - Chronological timeline of context events
- Displays commands, clipboard entries, and window changes
- Includes activity analysis and peak hour visualization

### Analytics

- **ContextAnalyticsPanel.tsx** - Advanced analytics and insights
- Keyword frequency analysis
- Command pattern recognition
- Application usage statistics
- Context effectiveness scoring

### Widgets

- **ContextWidget.tsx** - Compact widget for embedding in other pages
- Quick context overview
- Context strength indicator
- Direct link to full dashboard

### Hooks

- **useContextData.ts** - Main hook for context data management
- Handles API calls, WebSocket updates, filtering, and state management

## Usage

### Basic Dashboard

```typescript
import { ContextDashboard } from '@/app/components/context';

export default function ContextPage() {
  return (
    <div className="container mx-auto py-6">
      <ContextDashboard />
    </div>
  );
}
```

### Using Individual Components

```typescript
import {
  ShellHistoryManager,
  ClipboardManager,
  ApplicationDetector
} from '@/app/components/context';

export function MyComponent() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <ShellHistoryManager
        commands={commands}
        statistics={stats}
        onSearch={handleSearch}
      />
      <ClipboardManager
        entries={entries}
        statistics={clipboardStats}
        onCopy={handleCopy}
      />
      <ApplicationDetector
        activeWindow={window}
        usageStats={appStats}
        history={history}
      />
    </div>
  );
}
```

### Using the Widget

```typescript
import { ContextWidget } from '@/app/components/context/widgets/ContextWidget';

export function Dashboard() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <ContextWidget />
      {/* Other widgets */}
    </div>
  );
}
```

### Custom Hook Usage

```typescript
import { useContextData } from '@/app/components/context';

function MyComponent() {
  const {
    data,
    loading,
    error,
    updateFilters,
    clearContext,
    exportContext
  } = useContextData();

  // Use context data
  return (
    <div>
      {loading && <div>Loading...</div>}
      {error && <div>Error: {error}</div>}
      {data && (
        <div>
          <h2>Context Strength: {data.contextStrength}%</h2>
          {/* Render context data */}
        </div>
      )}
    </div>
  );
}
```

## API Routes

### Context Data
- `GET /api/context/data` - Fetch context data
- `POST /api/context/clear` - Clear context data

### Analytics
- `GET /api/context/analytics` - Fetch analytics data

### Export
- `GET /api/context/export` - Export context data

### Integration
- `GET /api/context/integration` - Get integration status
- `POST /api/context/integration` - Perform integration actions

## Types

### ShellCommand
```typescript
interface ShellCommand {
  id: string;
  command: string;
  timestamp: number;
  category?: string;
  tags?: string[];
}
```

### ClipboardEntry
```typescript
interface ClipboardEntry {
  id: string;
  content: string;
  timestamp: number;
  type: 'text' | 'code' | 'url' | 'file' | 'other';
  category?: string;
}
```

### ActiveWindow
```typescript
interface ActiveWindow {
  class: string;
  title: string;
  pid: number;
  category: string;
  timestamp: number;
}
```

### ContextData
```typescript
interface ContextData {
  shell: {
    commands: ShellCommand[];
    statistics: {
      totalCommands: number;
      uniqueCommands: number;
      mostUsedCommands: Array<{ command: string; count: number }>;
      commandCategories: Record<string, number>;
    };
  };
  clipboard: {
    entries: ClipboardEntry[];
    statistics: {
      totalEntries: number;
      contentTypes: Record<string, number>;
    };
  };
  applications: {
    activeWindow: ActiveWindow | null;
    usageStats: ApplicationStats[];
    history: ActiveWindow[];
  };
}
```

## Features

### Real-Time Updates
- WebSocket connection for live context updates
- Automatic reconnection handling
- Throttled updates to prevent performance issues

### Privacy Controls
- Automatic detection of sensitive information
- Configurable privacy mode
- Mask sensitive data in UI

### Search & Filter
- Full-text search across all context data
- Filter by category, time range, application
- Debounced search for performance

### Analytics
- Keyword frequency analysis
- Command pattern recognition
- Application usage statistics
- Context effectiveness scoring

### Export
- Export context data in JSON format
- Downloadable reports
- Selective export options

## Styling

All components use:
- Tailwind CSS for styling
- Radix UI primitives
- Lucide React icons
- Framer Motion for animations
- CSS variables for theming

## Dependencies

- React 19+
- Next.js 16+
- TypeScript 5+
- Radix UI
- Framer Motion
- Lucide React
- Tailwind CSS v4

## Testing

```bash
# Run tests
npm run test context

# Run with coverage
npm run test:coverage context

# Run specific test file
npm test -- ContextDashboard.test.tsx
```

## Performance

### Optimization Strategies
- Lazy loading of components
- Debounced search inputs
- Virtualized lists for large datasets
- Memoization of expensive calculations
- Efficient re-rendering with React.memo

### Best Practices
- Use ScrollArea for large lists
- Implement pagination for extensive data
- Cache API responses
- Use Web Workers for heavy computations

## Accessibility

All components:
- Support keyboard navigation
- Include ARIA labels
- Maintain proper focus management
- Are screen reader friendly
- Follow WCAG guidelines

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

When adding new components:

1. Follow TypeScript best practices
2. Include proper type definitions
3. Add JSDoc comments
4. Write unit tests
5. Update this README
6. Follow existing code style

## License

MIT License - see project root for details

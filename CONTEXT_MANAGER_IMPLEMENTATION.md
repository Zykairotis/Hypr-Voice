# Context Manager Controls Implementation

## Overview

The Context Manager Controls system provides intelligent context management for the Hypr-Whisper project, enhancing transcription accuracy through real-time analysis of shell history, clipboard content, and application detection.

## Features Implemented

### 1. Shell History Manager
- **Display**: Recent shell commands (last 100+ commands)
- **Features**:
  - Keyword extraction from command history
  - Command categorization and tagging
  - Search and filter functionality
  - Command statistics (most used commands)
  - Export history to JSON
  - Clear history option

### 2. Clipboard Manager
- **Display**: Clipboard history viewer (last 50 entries)
- **Features**:
  - Text content analysis and categorization
  - Clipboard keyword extraction
  - Privacy controls (mask sensitive information)
  - Auto-extract technical terms
  - Copy to clipboard functionality
  - Content type detection (text, code, URL, file)

### 3. Application Detection
- **Display**: Real-time active window monitoring
- **Features**:
  - Window class and title tracking
  - Application categorization (editor, browser, terminal, etc.)
  - Application usage statistics
  - Per-application context snapshots
  - Window history tracking

### 4. Context Dashboard
- **Display**: Combined view of shell + clipboard + app context
- **Features**:
  - Context timeline visualization
  - Real-time context updates
  - Context strength indicator
  - Multi-tab interface
  - Auto-refresh capability

### 5. Context-Aware Features
- **Auto-generate**: Vocabulary from context
- **Context-based**: Prompt suggestions
- **Keyword prioritization**: Based on context
- **Context similarity**: Matching

### 6. Context Analytics
- **Metrics**:
  - Most used commands/apps
  - Session-based context analysis
  - Keyword frequency over time
  - Context effectiveness scoring
- **Visualizations**:
  - Command pattern analysis
  - Application usage distribution
  - Peak activity hours
  - Context strength breakdown

### 7. Privacy & Security
- **Features**:
  - Local-only processing toggle
  - Mask sensitive information
  - Clear context data
  - Access logging

### 8. Context Export/Import
- **Export**: Context data in JSON/CSV formats
- **Import**: Context snapshots
- **Share**: Context templates
- **Backup**: And restore functionality

## Architecture

### Frontend Components

```
web-ui/app/components/context/
├── types.ts                          # TypeScript interfaces
├── ContextDashboard.tsx              # Main dashboard component
├── ShellHistoryManager.tsx           # Shell history management
├── ClipboardManager.tsx              # Clipboard management
├── ApplicationDetector.tsx           # Application detection
├── hooks/
│   └── useContextData.ts             # Context data hook
├── visualization/
│   └── ContextTimeline.tsx           # Timeline visualization
├── analytics/
│   └── ContextAnalyticsPanel.tsx     # Analytics panel
├── widgets/
│   └── ContextWidget.tsx             # Dashboard widget
└── index.ts                          # Export file
```

### API Routes

```
web-ui/app/api/context/
├── data/route.ts                     # Context data API
├── analytics/route.ts                # Analytics API
├── clear/route.ts                    # Clear context API
└── export/route.ts                   # Export context API
```

### Backend Integration

The Context Manager connects to the Python `context_manager.py`:

```python
# Backend (context_manager.py)
class ContextManager:
    def get_shell_history(self, count: int = 40) -> List[str]
    def get_clipboard_history(self, count: int = 5) -> List[str]
    def extract_vocabulary_from_context(self, commands, clipboard) -> List[str]
    def get_comprehensive_context(self, window_info: Dict = None) -> Dict[str, any]
```

## Technology Stack

- **Framework**: Next.js 16 with React 19
- **Language**: TypeScript
- **UI Components**: Radix UI primitives
- **Styling**: Tailwind CSS v4
- **Animations**: Framer Motion
- **Charts**: Recharts (for analytics)
- **WebSocket**: Real-time updates
- **Icons**: Lucide React

## Usage

### Accessing the Context Dashboard

1. Navigate to `/context` in the web UI
2. View the comprehensive dashboard with all context features
3. Use the widget on the main dashboard for quick context overview

### Viewing Shell History

```typescript
import { ShellHistoryManager } from '@/app/components/context';

<ShellHistoryManager
  commands={data?.shell.commands || []}
  statistics={data?.shell.statistics || {}}
  loading={loading}
/>
```

### Managing Clipboard

```typescript
import { ClipboardManager } from '@/app/components/context';

<ClipboardManager
  entries={data?.clipboard.entries || []}
  statistics={data?.clipboard.statistics || {}}
  onCopy={handleCopy}
/>
```

### Detecting Applications

```typescript
import { ApplicationDetector } from '@/app/components/context';

<ApplicationDetector
  activeWindow={data?.applications.activeWindow}
  usageStats={data?.applications.usageStats}
  history={data?.applications.history}
/>
```

## WebSocket Integration

Real-time updates via WebSocket:

```typescript
const ws = new WebSocket('ws://localhost:9090/ws/context');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  if (update.type === 'context_update') {
    // Update context data in real-time
    setData(update.data);
  }
};
```

## Context Strength Scoring

The system calculates a context strength score (0-100%) based on:

- Shell commands: 30% weight
- Clipboard entries: 20% weight
- Active window: 25% weight
- Application history: 25% weight

Formula:
```
score = min(commands/50 * 30 + entries/30 * 20 + window * 25 + history/20 * 25, 100)
```

## Privacy Controls

### Sensitive Information Detection

Automatically detects and masks:
- Passwords
- API keys
- Secrets/tokens
- Credit card numbers
- Email addresses

### Privacy Mode Toggle

```typescript
const [showSensitive, setShowSensitive] = useState(false);

{maskedContent}
```

## Analytics Features

### Keyword Frequency Analysis

Tracks keyword occurrences across:
- Shell commands
- Clipboard entries
- Active application window

### Command Pattern Recognition

Identifies:
- Most frequently used commands
- Command categories
- Usage patterns

### Application Usage Statistics

Tracks:
- Time spent per application
- Application launch count
- Category distribution

### Context Effectiveness

Calculates effectiveness score based on:
- Rich shell history
- Active clipboard usage
- Application context detection
- Extensive keyword vocabulary
- Long session duration

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+C` | Clear all context data |
| `Ctrl+Shift+E` | Export context data |
| `Ctrl+Shift+R` | Refresh context |
| `Ctrl+Shift+F` | Focus search |

## Configuration

### Environment Variables

```env
NEXT_PUBLIC_CONTEXT_WS_URL=ws://localhost:9090/ws/context
CONTEXT_REFRESH_INTERVAL=5000
CONTEXT_MAX_COMMANDS=100
CONTEXT_MAX_CLIPBOARD=50
```

### API Configuration

```typescript
// web-ui/app/api/context/data/route.ts
export async function GET(request: NextRequest) {
  // Configurable parameters
  const timeRange = searchParams.get('timeRange') || '24h';
  const categories = searchParams.get('categories')?.split(',');
  const keywords = searchParams.get('keywords')?.split(',');
  const application = searchParams.get('application');

  // Return filtered context data
}
```

## Performance Considerations

1. **Efficient Data Loading**:
   - Pagination for large datasets
   - Lazy loading of visualizations
   - Debounced search inputs

2. **Memory Management**:
   - Automatic cleanup of old data
   - WebSocket connection pooling
   - Local storage optimization

3. **Real-time Updates**:
   - Throttled updates (5s default)
   - Selective component updates
   - Efficient diff algorithms

## Testing

```bash
# Run context manager tests
npm run test -- context

# Run integration tests
npm run test:integration context

# Type checking
npm run typecheck
```

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Future Enhancements

1. **Machine Learning Integration**:
   - Predictive context suggestions
   - Automatic pattern learning
   - Context similarity matching

2. **Advanced Visualizations**:
   - 3D context networks
   - Interactive command graphs
   - Heatmaps

3. **Multi-user Support**:
   - Team context sharing
   - Collaborative filtering
   - Access control

4. **Integration Expansions**:
   - IDE plugin support
   - Git integration
   - File system watchers

## Troubleshooting

### Common Issues

**Issue**: Context data not loading
- Check WebSocket connection
- Verify API endpoints
- Check browser console for errors

**Issue**: Real-time updates not working
- Verify WebSocket URL
- Check firewall settings
- Restart context service

**Issue**: Privacy mode not working
- Clear browser cache
- Check privacy settings
- Restart application

### Debug Mode

Enable debug mode:
```typescript
localStorage.setItem('context-debug', 'true');
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Submit PR

## License

MIT License - see LICENSE file for details

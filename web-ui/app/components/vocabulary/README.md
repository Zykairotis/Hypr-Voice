# Vocabulary Management Interface

A comprehensive vocabulary management system for Hypr-Voice that dramatically improves transcription accuracy through intelligent keyword management and context-aware vocabulary enhancement.

## Features

### 1. Vocabulary Dashboard
- Overview of all loaded vocabularies
- Current active vocabulary display
- Total keyword count and statistics
- Vocabulary switching controls
- Real-time updates via WebSocket

### 2. Application-Specific Vocabulary
- Detect and display current active application
- Show matched vocabulary for current app
- Manual vocabulary selection override
- Application window class detection
- Support for multiple window managers (Hyprland, X11)

### 3. Vocabulary Editor
- Add/edit/remove keywords
- Keyword categories management
- Bulk import/export vocabulary (CSV, JSON, YAML)
- Drag-and-drop keyword organization
- Search and filter functionality
- Validation and error checking

### 4. Context-Aware Vocabulary
- Display shell history extracted keywords
- Clipboard history integration
- Context keyword prioritization
- Real-time context updates
- Automatic keyword extraction from:
  - Shell commands
  - Clipboard entries
  - Active window information

### 5. Global Vocabulary Settings
- Technical terms management
- Programming keywords
- Common corrections database
- Priority and weighting settings
- Context extraction configuration
- Fuzzy match threshold adjustment

### 6. Vocabulary Statistics
- Keyword usage frequency
- Match accuracy statistics
- Transcription improvement metrics
- Performance analytics
- Visual charts and graphs
- Trend analysis

### 7. Live Vocabulary Monitoring
- Real-time keyword updates
- Active vocabulary changes
- Keyword matching visualization
- Vocabulary effectiveness scoring
- WebSocket-powered live feed
- Performance metrics dashboard

### 8. Vocabulary Presets
- Pre-built vocabularies for common apps
- Import/export custom vocabularies
- Vocabulary templates
- Backup and restore functionality
- Community sharing (planned)
- Built-in template library

## Architecture

### Component Structure
```
web-ui/app/components/vocabulary/
├── dashboard/
│   └── VocabularyDashboard.tsx
├── application/
│   └── ApplicationVocabulary.tsx
├── editor/
│   └── VocabularyEditor.tsx
├── context/
│   └── ContextAwareVocabulary.tsx
├── settings/
│   └── GlobalVocabularySettings.tsx
├── statistics/
│   └── VocabularyStatistics.tsx
├── monitoring/
│   └── LiveVocabularyMonitor.tsx
├── presets/
│   └── VocabularyPresets.tsx
├── visualization/
│   └── WordCloud.tsx
└── index.ts
```

### API Endpoints
```
/api/vocabulary
  GET    - List all vocabularies
  POST   - Create new vocabulary

/api/vocabulary/[id]
  GET    - Get vocabulary details
  PATCH  - Update vocabulary
  DELETE - Delete vocabulary

/api/vocabulary/statistics
  GET    - Get vocabulary statistics

/api/vocabulary/context
  GET    - Get context data

/api/vocabulary/application
  GET    - Get current application context

/api/vocabulary/update
  POST   - Force vocabulary update

/api/vocabulary/presets
  GET    - List all presets
  POST   - Create new preset

/api/vocabulary/[id]/validate
  GET    - Validate vocabulary
```

## Usage

### Basic Setup
1. Navigate to `/vocabulary` in the web UI
2. The system will automatically connect to the vocabulary manager
3. View the dashboard for an overview of all vocabularies

### Managing Vocabularies
1. **View Dashboard**: See statistics and overview
2. **Edit Vocabulary**: Use the Editor tab to modify keywords
3. **Import/Export**: Bulk operations for managing large vocabularies
4. **Create Presets**: Save vocabularies as reusable templates

### Application-Specific Configuration
1. Go to the **Application** tab
2. Click "Detect App" to find the current application
3. Select or create vocabulary for that application
4. Click "Apply Vocabulary" to activate

### Context-Aware Enhancement
1. Navigate to the **Context** tab
2. View extracted keywords from:
   - Shell history
   - Clipboard entries
   - Active window
3. Keywords are automatically added to active vocabulary

### Monitoring and Analytics
1. **Live Tab**: Monitor real-time updates
2. **Statistics Tab**: View detailed analytics
3. Track keyword effectiveness and usage patterns

## Key Features

### Real-Time Updates
- WebSocket connection for live updates
- Automatic vocabulary switching
- Real-time keyword matching visualization
- Live statistics updates

### Smart Context Extraction
- Shell command analysis
- Clipboard integration
- Window information parsing
- CamelCase splitting
- Technical term identification

### Intelligent Matching
- Direct keyword matching
- Fuzzy matching with configurable threshold
- Priority-based keyword selection
- Automatic post-processing corrections

### Comprehensive Statistics
- Usage frequency tracking
- Accuracy rate monitoring
- Performance metrics
- Visual analytics with charts

## Integration with Backend

### Vocabulary Manager
The interface integrates with `src/Hypr-Whisper/vocabulary_manager.py`:
- Loads vocabulary configurations
- Manages keyword extraction
- Handles application detection
- Provides statistics

### Context Manager
Works with `src/Hypr-Whisper/context_manager.py`:
- Extracts keywords from shell history
- Monitors clipboard changes
- Analyzes window context

## WebSocket Events

### Client → Server
- `vocabulary_change` - Vocabulary was modified
- `keyword_match` - Keyword was matched
- `application_switch` - Application changed

### Server → Client
- `vocabulary_change` - Vocabulary updated
- `keyword_match` - Match detected
- `application_switch` - App switch detected
- `stats_update` - Statistics updated
- `context_update` - Context changed

## Keyboard Shortcuts

- `Ctrl/Cmd + N` - Add new word
- `Ctrl/Cmd + I` - Import vocabulary
- `Ctrl/Cmd + E` - Export vocabulary
- `Ctrl/Cmd + R` - Refresh data
- `Ctrl/Cmd + /` - Focus search

## Best Practices

### Vocabulary Organization
1. Use clear, descriptive category names
2. Group related keywords together
3. Set appropriate priorities
4. Regular cleanup of unused terms

### Application-Specific Vocabularies
1. Create dedicated vocabulary per application
2. Use window class patterns for auto-detection
3. Include relevant technical terms
4. Test with real usage

### Context Extraction
1. Keep shell history active
2. Use descriptive variable names
3. Include technical terms in commands
4. Monitor extracted keywords regularly

### Performance Optimization
1. Limit active vocabulary size (~50-100 keywords)
2. Use priority to rank keywords
3. Regular cleanup of low-usage terms
4. Monitor accuracy metrics

## Troubleshooting

### WebSocket Connection Issues
- Check network connectivity
- Verify WebSocket server is running
- Check browser console for errors
- Refresh the page

### Vocabulary Not Loading
- Verify YAML files are valid
- Check file permissions
- Review error logs
- Validate syntax

### Application Detection Fails
- Ensure window manager integration
- Check Hyprland/wlroots compatibility
- Verify window class detection
- Test with different applications

### Context Extraction Issues
- Enable shell history
- Install required tools (cliphist, wl-paste)
- Check history file permissions
- Verify clipboard access

## Future Enhancements

1. **Machine Learning Integration**
   - Automatic keyword ranking
   - Predictive vocabulary switching
   - Usage pattern learning

2. **Community Features**
   - Shared vocabulary templates
   - Rating and reviews
   - Collaborative editing

3. **Advanced Analytics**
   - Detailed performance metrics
   - Custom report generation
   - Historical data analysis

4. **Enhanced Visualization**
   - Interactive word clouds
   - Network graphs
   - 3D visualizations

5. **Mobile Support**
   - Responsive design
   - Touch-optimized controls
   - Mobile-specific features

## API Reference

See `/api/vocabulary/docs` for detailed API documentation.

## Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Submit pull request

## License

MIT License - see LICENSE file for details.

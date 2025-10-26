// Main entry point for the LogViewer component
export { LogViewer } from './components/LogViewer/LogViewer';
export type {
  LogEntry,
  LogLevel,
  LogFilter,
  LogViewerConfig,
  PerformanceMetrics,
  Bookmark,
  LogExportOptions,
  WebSocketMessage,
  VirtualScrollItem,
  LogViewerState
} from './types/logViewer';

export { LogParser } from './utils/logParser';
export { LogFilterManager } from './utils/logFilter';
export { LogExporter } from './utils/logExporter';
export { useWebSocket } from './hooks/useWebSocket';
export { useVirtualScroll } from './hooks/useVirtualScroll';

// Export all sub-components for advanced usage
export { LogEntryComponent } from './components/LogViewer/LogEntry';
export { LogControls } from './components/LogViewer/LogControls';
export { LogFilters } from './components/LogViewer/LogFilters';
export { PerformancePanel } from './components/LogViewer/PerformancePanel';
export { ExportDialog } from './components/LogViewer/ExportDialog';
export { SearchPanel } from './components/LogViewer/SearchPanel';
export { BookmarkPanel } from './components/LogViewer/BookmarkPanel';

// Export styles for import
import './components/LogViewer/LogViewer.css';
import './components/LogViewer/LogEntry.css';
import './components/LogViewer/LogControls.css';
import './components/LogViewer/LogFilters.css';
import './components/LogViewer/PerformancePanel.css';
import './components/LogViewer/ExportDialog.css';
import './components/LogViewer/SearchPanel.css';
import './components/LogViewer/BookmarkPanel.css';
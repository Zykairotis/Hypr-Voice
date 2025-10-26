import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { LogEntry, LogLevel, LogViewerConfig, LogFilter, PerformanceMetrics, Bookmark, LogExportOptions } from '../../types/logViewer';
import { LogParser } from '../../utils/logParser';
import { LogFilterManager } from '../../utils/logFilter';
import { LogExporter } from '../../utils/logExporter';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useVirtualScroll, useDynamicItemHeight } from '../../hooks/useVirtualScroll';
import { LogEntryComponent } from './LogEntry';
import { LogControls } from './LogControls';
import { LogFilters } from './LogFilters';
import { PerformancePanel } from './PerformancePanel';
import { ExportDialog } from './ExportDialog';
import { SearchPanel } from './SearchPanel';
import { BookmarkPanel } from './BookmarkPanel';

import './LogViewer.css';

const DEFAULT_CONFIG: LogViewerConfig = {
  maxEntries: 10000,
  bufferSize: 500,
  updateInterval: 100,
  autoScroll: true,
  theme: 'auto',
  timeZone: 'UTC',
  timestampFormat: 'ISO',
  enableVirtualScrolling: true,
  enablePerformanceMetrics: true
};

interface LogViewerProps {
  websocketUrl?: string;
  config?: Partial<LogViewerConfig>;
  className?: string;
  height?: string | number;
  onEntryClick?: (entry: LogEntry) => void;
  onBookmarkAdd?: (bookmark: Bookmark) => void;
  onBookmarkRemove?: (bookmarkId: string) => void;
}

export const LogViewer: React.FC<LogViewerProps> = ({
  websocketUrl = 'ws://localhost:8080/api/logs/stream',
  config = {},
  className = '',
  height = '600px',
  onEntryClick,
  onBookmarkAdd,
  onBookmarkRemove
}) => {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [filteredEntries, setFilteredEntries] = useState<LogEntry[]>([]);
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [configState, setConfigState] = useState<LogViewerConfig>({ ...DEFAULT_CONFIG, ...config });
  const [filter, setFilter] = useState<LogFilter>({
    levels: Object.values(LogLevel),
    sources: [],
    searchQuery: ''
  });
  const [selectedEntry, setSelectedEntry] = useState<LogEntry | undefined>();
  const [isPaused, setIsPaused] = useState(false);
  const [isAutoScrolling, setIsAutoScrolling] = useState(configState.autoScroll);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showSearchPanel, setShowSearchPanel] = useState(false);
  const [showBookmarkPanel, setShowBookmarkPanel] = useState(false);
  const [showPerformancePanel, setShowPerformancePanel] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // WebSocket connection
  const {
    isConnected,
    isConnecting,
    error: wsError,
    sendMessage,
    metrics
  } = useWebSocket({
    url: websocketUrl,
    onMessage: (message) => {
      if (message.type === 'log' && !isPaused) {
        const newEntry = LogParser.parse(message.data.log, message.data.source);
        setEntries(prev => {
          const updated = [...prev, newEntry];
          // Keep only the latest maxEntries
          if (updated.length > configState.maxEntries) {
            return updated.slice(-configState.maxEntries);
          }
          return updated;
        });
      }
    },
    onConnect: () => {
      // Request historical logs
      sendMessage({
        type: 'history',
        data: {
          limit: configState.bufferSize,
          sources: ['agent.log', 'server.log', 'client.log']
        }
      });
    }
  });

  // Virtual scrolling
  const { measureItem } = useDynamicItemHeight();
  const {
    virtualItems,
    totalSize,
    scrollToIndex,
    containerRef: virtualContainerRef,
    isScrolling,
    startIndex,
    endIndex
  } = useVirtualScroll({
    items: filteredEntries,
    containerHeight: typeof height === 'number' ? height : 600,
    itemHeight: (index, item) => {
      const messageLines = Math.ceil(item.message.length / 100);
      const baseHeight = 32 + (messageLines * 16);
      return measureItem(item, item.message) || baseHeight;
    },
    overscan: 10,
    enabled: configState.enableVirtualScrolling
  });

  // Apply filters
  useEffect(() => {
    const filtered = LogFilterManager.filterEntries(entries, filter);
    setFilteredEntries(filtered);
  }, [entries, filter]);

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (isAutoScrolling && !isScrolling && filteredEntries.length > 0) {
      scrollToIndex(filteredEntries.length - 1);
    }
  }, [filteredEntries.length, isAutoScrolling, isScrolling, scrollToIndex]);

  // Handle entry selection
  const handleEntryClick = useCallback((entry: LogEntry) => {
    setSelectedEntry(entry);
    onEntryClick?.(entry);
  }, [onEntryClick]);

  // Handle bookmarking
  const handleBookmarkAdd = useCallback((entry: LogEntry, note?: string, tags: string[] = []) => {
    const bookmark: Bookmark = {
      id: `bookmark-${Date.now()}`,
      logId: entry.id,
      timestamp: new Date(),
      note,
      tags
    };

    setBookmarks(prev => [...prev, bookmark]);
    setEntries(prev => prev.map(e =>
      e.id === entry.id ? { ...e, bookmarked: true } : e
    ));

    onBookmarkAdd?.(bookmark);
  }, [onBookmarkAdd]);

  const handleBookmarkRemove = useCallback((bookmarkId: string) => {
    const bookmark = bookmarks.find(b => b.id === bookmarkId);
    if (bookmark) {
      setBookmarks(prev => prev.filter(b => b.id !== bookmarkId));
      setEntries(prev => prev.map(e =>
        e.id === bookmark.logId ? { ...e, bookmarked: false } : e
      ));
      onBookmarkRemove?.(bookmarkId);
    }
  }, [bookmarks, onBookmarkRemove]);

  // Handle search
  const handleSearch = useCallback((query: string) => {
    setFilter(prev => ({ ...prev, searchQuery: query }));
  }, []);

  // Handle filter changes
  const handleFilterChange = useCallback((newFilter: Partial<LogFilter>) => {
    setFilter(prev => ({ ...prev, ...newFilter }));
  }, []);

  // Handle export
  const handleExport = useCallback(async (options: LogExportOptions) => {
    await LogExporter.exportAndDownload(filteredEntries, options, options.format);
    setShowExportDialog(false);
  }, [filteredEntries]);

  // Handle pause/resume
  const handlePauseResume = useCallback(() => {
    setIsPaused(prev => !prev);
  }, []);

  // Handle clear logs
  const handleClearLogs = useCallback(() => {
    setEntries([]);
    setFilteredEntries([]);
    setSelectedEntry(undefined);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement) return;

      switch (event.key) {
        case ' ':
          event.preventDefault();
          handlePauseResume();
          break;
        case 'f':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            setShowSearchPanel(true);
            setTimeout(() => searchInputRef.current?.focus(), 100);
          }
          break;
        case 'b':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            if (selectedEntry) {
              handleBookmarkAdd(selectedEntry);
            }
          }
          break;
        case 'e':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            setShowExportDialog(true);
          }
          break;
        case 'Escape':
          setShowSearchPanel(false);
          setShowExportDialog(false);
          setSelectedEntry(undefined);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handlePauseResume, selectedEntry, handleBookmarkAdd]);

  // Calculate statistics
  const stats = useMemo(() => {
    const levelStats = LogFilterManager.getLevelStats(filteredEntries);
    const sourceStats = LogFilterManager.getSourceStats(filteredEntries);
    const uniqueSources = LogFilterManager.getUniqueSources(filteredEntries);
    const uniqueSessions = LogFilterManager.getUniqueSessions(filteredEntries);

    return {
      totalEntries: filteredEntries.length,
      levelStats,
      sourceStats,
      uniqueSources,
      uniqueSessions
    };
  }, [filteredEntries]);

  return (
    <div
      ref={containerRef}
      className={`log-viewer ${className}`}
      style={{ height }}
      data-theme={configState.theme}
    >
      {/* Header with controls */}
      <div className="log-viewer-header">
        <div className="log-viewer-title">
          <h2>Hypr-Voice Logs</h2>
          <div className="connection-status">
            <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`} />
            {isConnected ? 'Connected' : isConnecting ? 'Connecting...' : 'Disconnected'}
          </div>
        </div>

        <LogControls
          isPaused={isPaused}
          isAutoScrolling={isAutoScrolling}
          onPauseResume={handlePauseResume}
          onToggleAutoScroll={setIsAutoScrolling}
          onClearLogs={handleClearLogs}
          onExport={() => setShowExportDialog(true)}
          onSearch={() => setShowSearchPanel(true)}
          onBookmarks={() => setShowBookmarkPanel(true)}
          onPerformance={() => setShowPerformancePanel(true)}
          stats={stats}
        />
      </div>

      {/* Filter bar */}
      <LogFilters
        filter={filter}
        onFilterChange={handleFilterChange}
        availableSources={stats.uniqueSources}
        availableLevels={Object.values(LogLevel)}
      />

      {/* Main content area */}
      <div className="log-viewer-content">
        {/* Search panel */}
        {showSearchPanel && (
          <SearchPanel
            query={filter.searchQuery || ''}
            onQueryChange={handleSearch}
            onClose={() => setShowSearchPanel(false)}
            inputRef={searchInputRef}
          />
        )}

        {/* Performance panel */}
        {showPerformancePanel && (
          <PerformancePanel
            metrics={metrics}
            stats={stats}
            onClose={() => setShowPerformancePanel(false)}
          />
        )}

        {/* Bookmark panel */}
        {showBookmarkPanel && (
          <BookmarkPanel
            bookmarks={bookmarks}
            entries={entries}
            onBookmarkRemove={handleBookmarkRemove}
            onBookmarkClick={(bookmark) => {
              const entry = entries.find(e => e.id === bookmark.logId);
              if (entry) {
                const index = filteredEntries.findIndex(e => e.id === entry.id);
                if (index !== -1) {
                  scrollToIndex(index, 'center');
                  setSelectedEntry(entry);
                }
              }
            }}
            onClose={() => setShowBookmarkPanel(false)}
          />
        )}

        {/* Virtual scroll container */}
        <div
          ref={virtualContainerRef}
          className="log-entries-container"
          onScroll={undefined} // VirtualScroll hook handles this
          role="log"
          aria-label="Log entries"
          aria-live="polite"
        >
          <div style={{ height: totalSize, position: 'relative' }}>
            {virtualItems.map((virtualItem) => (
              <LogEntryComponent
                key={virtualItem.entry.id}
                entry={virtualItem.entry}
                isSelected={selectedEntry?.id === virtualItem.entry.id}
                isHighlighted={filter.searchQuery ?
                  LogFilterManager.createSearchRegex(filter.searchQuery).test(virtualItem.entry.message) :
                  false
                }
                searchRegex={filter.searchQuery ? LogFilterManager.createSearchRegex(filter.searchQuery) : undefined}
                onClick={handleEntryClick}
                onBookmark={handleBookmarkAdd}
                onRemoveBookmark={() => {
                  const bookmark = bookmarks.find(b => b.logId === virtualItem.entry.id);
                  if (bookmark) {
                    handleBookmarkRemove(bookmark.id);
                  }
                }}
                style={{
                  position: 'absolute',
                  top: virtualItem.offset,
                  width: '100%',
                  height: virtualItem.height
                }}
              />
            ))}
          </div>
        </div>

        {/* Selected entry details */}
        {selectedEntry && (
          <div className="log-entry-details">
            <div className="details-header">
              <h3>Entry Details</h3>
              <button
                className="close-button"
                onClick={() => setSelectedEntry(undefined)}
                aria-label="Close details"
              >
                ×
              </button>
            </div>
            <div className="details-content">
              <div className="detail-row">
                <label>Timestamp:</label>
                <span>{selectedEntry.timestamp.toISOString()}</span>
              </div>
              <div className="detail-row">
                <label>Level:</label>
                <span className={`level-${LogLevel[selectedEntry.level].toLowerCase()}`}>
                  {LogLevel[selectedEntry.level]}
                </span>
              </div>
              <div className="detail-row">
                <label>Source:</label>
                <span>{selectedEntry.source}</span>
              </div>
              <div className="detail-row">
                <label>Message:</label>
                <pre>{selectedEntry.message}</pre>
              </div>
              {selectedEntry.metadata && (
                <div className="detail-row">
                  <label>Metadata:</label>
                  <pre>{JSON.stringify(selectedEntry.metadata, null, 2)}</pre>
                </div>
              )}
              <div className="detail-actions">
                <button
                  onClick={() => handleBookmarkAdd(selectedEntry)}
                  disabled={selectedEntry.bookmarked}
                >
                  {selectedEntry.bookmarked ? 'Bookmarked' : 'Add Bookmark'}
                </button>
                <button onClick={() => {
                  navigator.clipboard.writeText(selectedEntry.raw || selectedEntry.message);
                }}>
                  Copy Raw
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Export dialog */}
      {showExportDialog && (
        <ExportDialog
          totalEntries={filteredEntries.length}
          onExport={handleExport}
          onClose={() => setShowExportDialog(false)}
        />
      )}

      {/* Error display */}
      {wsError && (
        <div className="log-viewer-error">
          <strong>Connection Error:</strong> {wsError}
        </div>
      )}

      {/* Measurement container for dynamic heights */}
      <div ref={useDynamicItemHeight().measurementContainerRef} style={{ position: 'absolute', visibility: 'hidden' }} />
    </div>
  );
};

export default LogViewer;
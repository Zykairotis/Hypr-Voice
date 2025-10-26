import React, { memo } from 'react';
import { LogEntry, LogLevel } from '../../types/logViewer';
import './LogEntry.css';

interface LogEntryComponentProps {
  entry: LogEntry;
  isSelected: boolean;
  isHighlighted: boolean;
  searchRegex?: RegExp;
  onClick: (entry: LogEntry) => void;
  onBookmark: (entry: LogEntry, note?: string) => void;
  onRemoveBookmark: () => void;
  style?: React.CSSProperties;
}

const LogEntryComponent: React.FC<LogEntryComponentProps> = memo(({
  entry,
  isSelected,
  isHighlighted,
  searchRegex,
  onClick,
  onBookmark,
  onRemoveBookmark,
  style
}) => {
  const handleClick = (e: React.MouseEvent) => {
    if (e.target instanceof HTMLButtonElement) return; // Don't trigger on button clicks
    onClick(entry);
  };

  const handleBookmark = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (entry.bookmarked) {
      onRemoveBookmark();
    } else {
      onBookmark(entry);
    }
  };

  const formatTimestamp = (timestamp: Date): string => {
    return timestamp.toISOString().replace('T', ' ').replace('Z', '');
  };

  const getLevelIcon = (level: LogLevel): string => {
    switch (level) {
      case LogLevel.DEBUG: return '🔍';
      case LogLevel.INFO: return 'ℹ️';
      case LogLevel.WARN: return '⚠️';
      case LogLevel.ERROR: return '❌';
      case LogLevel.FATAL: return '💀';
      default: return '📝';
    }
  };

  const highlightText = (text: string, regex: RegExp): React.ReactNode => {
    if (!regex) return text;

    const parts = text.split(regex);
    return parts.map((part, index) => {
      if (regex.test(part)) {
        return <mark key={index} className="search-highlight">{part}</mark>;
      }
      return part;
    });
  };

  const renderMessage = (): React.ReactNode => {
    if (searchRegex) {
      return highlightText(entry.message, searchRegex);
    }
    return entry.message;
  };

  return (
    <div
      className={`log-entry ${isSelected ? 'selected' : ''} ${isHighlighted ? 'highlighted' : ''} level-${LogLevel[entry.level].toLowerCase()}`}
      style={style}
      onClick={handleClick}
      role="article"
      tabIndex={0}
      aria-label={`Log entry: ${LogLevel[entry.level]} from ${entry.source} at ${formatTimestamp(entry.timestamp)}`}
      aria-selected={isSelected}
    >
      <div className="log-entry-header">
        <span className="log-timestamp" title={entry.timestamp.toISOString()}>
          {formatTimestamp(entry.timestamp)}
        </span>
        <span className="log-level" title={`Level: ${LogLevel[entry.level]}`}>
          {getLevelIcon(entry.level)} {LogLevel[entry.level]}
        </span>
        <span className="log-source" title={`Source: ${entry.source}`}>
          {entry.source}
        </span>
        {entry.sessionId && (
          <span className="log-session" title={`Session: ${entry.sessionId}`}>
            📱 {entry.sessionId.substring(0, 8)}...
          </span>
        )}
        <div className="log-actions">
          {entry.annotations && entry.annotations.length > 0 && (
            <span className="log-annotations" title={`Annotations: ${entry.annotations.join(', ')}`}>
              📝 {entry.annotations.length}
            </span>
          )}
          <button
            className={`bookmark-button ${entry.bookmarked ? 'bookmarked' : ''}`}
            onClick={handleBookmark}
            title={entry.bookmarked ? 'Remove bookmark' : 'Add bookmark'}
            aria-label={entry.bookmarked ? 'Remove bookmark' : 'Add bookmark'}
          >
            {entry.bookmarked ? '⭐' : '☆'}
          </button>
        </div>
      </div>

      <div className="log-message">
        {renderMessage()}
      </div>

      {entry.metadata && Object.keys(entry.metadata).length > 0 && (
        <details className="log-metadata">
          <summary>Metadata ({Object.keys(entry.metadata).length} items)</summary>
          <pre>{JSON.stringify(entry.metadata, null, 2)}</pre>
        </details>
      )}

      {entry.annotations && entry.annotations.length > 0 && (
        <div className="log-annotations-list">
          {entry.annotations.map((annotation, index) => (
            <div key={index} className="annotation">
              📝 {annotation}
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

LogEntryComponent.displayName = 'LogEntryComponent';

export { LogEntryComponent };
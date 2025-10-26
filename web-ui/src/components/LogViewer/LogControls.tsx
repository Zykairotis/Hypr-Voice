import React, { useCallback } from 'react';
import { LogLevel } from '../../types/logViewer';
import './LogControls.css';

interface LogControlsProps {
  isPaused: boolean;
  isAutoScrolling: boolean;
  onPauseResume: () => void;
  onToggleAutoScroll: (enabled: boolean) => void;
  onClearLogs: () => void;
  onExport: () => void;
  onSearch: () => void;
  onBookmarks: () => void;
  onPerformance: () => void;
  stats: {
    totalEntries: number;
    levelStats: Record<LogLevel, number>;
    sourceStats: Record<string, number>;
    uniqueSources: string[];
    uniqueSessions: string[];
  };
}

export const LogControls: React.FC<LogControlsProps> = ({
  isPaused,
  isAutoScrolling,
  onPauseResume,
  onToggleAutoScroll,
  onClearLogs,
  onExport,
  onSearch,
  onBookmarks,
  onPerformance,
  stats
}) => {
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onPauseResume();
    }
  }, [onPauseResume]);

  const getLevelColor = (level: LogLevel): string => {
    switch (level) {
      case LogLevel.DEBUG: return '#6c757d';
      case LogLevel.INFO: return '#007bff';
      case LogLevel.WARN: return '#ffc107';
      case LogLevel.ERROR: return '#dc3545';
      case LogLevel.FATAL: return '#6f42c1';
      default: return '#6c757d';
    }
  };

  const getLevelPercentage = (count: number): string => {
    if (stats.totalEntries === 0) return '0';
    return ((count / stats.totalEntries) * 100).toFixed(1);
  };

  return (
    <div className="log-controls">
      {/* Control buttons */}
      <div className="control-buttons">
        <button
          className={`control-button ${isPaused ? 'paused' : 'playing'}`}
          onClick={onPauseResume}
          onKeyDown={handleKeyDown}
          title={isPaused ? 'Resume (Space)' : 'Pause (Space)'}
          aria-label={isPaused ? 'Resume logging' : 'Pause logging'}
        >
          {isPaused ? '▶️' : '⏸️'}
        </button>

        <button
          className={`control-button ${isAutoScrolling ? 'active' : ''}`}
          onClick={() => onToggleAutoScroll(!isAutoScrolling)}
          title={isAutoScrolling ? 'Disable auto-scroll' : 'Enable auto-scroll'}
          aria-label={isAutoScrolling ? 'Disable auto-scroll' : 'Enable auto-scroll'}
        >
          ⬇️
        </button>

        <button
          className="control-button"
          onClick={onSearch}
          title="Search (Ctrl+F)"
          aria-label="Search logs"
        >
          🔍
        </button>

        <button
          className="control-button"
          onClick={onBookmarks}
          title="Bookmarks (Ctrl+B)"
          aria-label="View bookmarks"
        >
          ⭐
        </button>

        <button
          className="control-button"
          onClick={onPerformance}
          title="Performance metrics"
          aria-label="View performance metrics"
        >
          📊
        </button>

        <button
          className="control-button"
          onClick={onExport}
          title="Export (Ctrl+E)"
          aria-label="Export logs"
        >
          💾
        </button>

        <button
          className="control-button danger"
          onClick={onClearLogs}
          title="Clear all logs"
          aria-label="Clear logs"
        >
          🗑️
        </button>
      </div>

      {/* Statistics */}
      <div className="log-stats">
        <div className="stat-item">
          <span className="stat-label">Total:</span>
          <span className="stat-value">{stats.totalEntries.toLocaleString()}</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Sources:</span>
          <span className="stat-value">{stats.uniqueSources.length}</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Sessions:</span>
          <span className="stat-value">{stats.uniqueSessions.length}</span>
        </div>
      </div>

      {/* Level distribution */}
      <div className="level-distribution">
        {Object.entries(stats.levelStats).map(([level, count]) => {
          const levelNum = Number(level) as LogLevel;
          const percentage = getLevelPercentage(count);
          const color = getLevelColor(levelNum);

          return (
            <div key={level} className="level-stat">
              <span
                className="level-indicator"
                style={{ backgroundColor: color }}
                title={`${LogLevel[levelNum]}: ${count} entries (${percentage}%)`}
              />
              <span className="level-count">{count}</span>
            </div>
          );
        })}
      </div>

      {/* Quick filters */}
      <div className="quick-filters">
        <button
          className="quick-filter"
          onClick={() => console.log('Filter errors')} // This would connect to parent
          title="Show only errors and above"
        >
          ❌ Errors ({stats.levelStats[LogLevel.ERROR] + stats.levelStats[LogLevel.FATAL]})
        </button>

        <button
          className="quick-filter"
          onClick={() => console.log('Filter warnings')} // This would connect to parent
          title="Show only warnings and above"
        >
          ⚠️ Warnings+ ({stats.levelStats[LogLevel.WARN] + stats.levelStats[LogLevel.ERROR] + stats.levelStats[LogLevel.FATAL]})
        </button>
      </div>

      {/* Real-time indicators */}
      <div className="real-time-indicators">
        <div className="indicator">
          <span className="indicator-dot live" />
          <span className="indicator-text">Live</span>
        </div>

        {isPaused && (
          <div className="indicator paused">
            <span className="indicator-dot paused" />
            <span className="indicator-text">Paused</span>
          </div>
        )}

        {isAutoScrolling && (
          <div className="indicator">
            <span className="indicator-dot auto-scroll" />
            <span className="indicator-text">Auto-scroll</span>
          </div>
        )}
      </div>
    </div>
  );
};
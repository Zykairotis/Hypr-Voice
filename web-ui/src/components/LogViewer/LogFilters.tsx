import React, { useState, useCallback, useMemo } from 'react';
import { LogFilter, LogLevel } from '../../types/logViewer';
import { LogFilterManager } from '../../utils/logFilter';
import './LogFilters.css';

interface LogFiltersProps {
  filter: LogFilter;
  onFilterChange: (filter: Partial<LogFilter>) => void;
  availableSources: string[];
  availableLevels: LogLevel[];
}

export const LogFilters: React.FC<LogFiltersProps> = ({
  filter,
  onFilterChange,
  availableSources,
  availableLevels
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: filter.startTime ? filter.startTime.toISOString().slice(0, 16) : '',
    end: filter.endTime ? filter.endTime.toISOString().slice(0, 16) : ''
  });

  const levelLabels = {
    [LogLevel.DEBUG]: 'Debug',
    [LogLevel.INFO]: 'Info',
    [LogLevel.WARN]: 'Warning',
    [LogLevel.ERROR]: 'Error',
    [LogLevel.FATAL]: 'Fatal'
  };

  const handleLevelToggle = useCallback((level: LogLevel) => {
    const newLevels = filter.levels.includes(level)
      ? filter.levels.filter(l => l !== level)
      : [...filter.levels, level];

    onFilterChange({ levels: newLevels });
  }, [filter.levels, onFilterChange]);

  const handleSourceToggle = useCallback((source: string) => {
    const newSources = filter.sources.includes(source)
      ? filter.sources.filter(s => s !== source)
      : [...filter.sources, source];

    onFilterChange({ sources: newSources });
  }, [filter.sources, onFilterChange]);

  const handleDateRangeChange = useCallback((type: 'start' | 'end', value: string) => {
    const newDateRange = { ...dateRange, [type]: value };
    setDateRange(newDateRange);

    if (value) {
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        onFilterChange({
          [type === 'start' ? 'startTime' : 'endTime']: date
        });
      }
    } else {
      onFilterChange({
        [type === 'start' ? 'startTime' : 'endTime']: undefined
      });
    }
  }, [dateRange, onFilterChange]);

  const handleClearFilters = useCallback(() => {
    onFilterChange({
      levels: availableLevels,
      sources: [],
      searchQuery: '',
      startTime: undefined,
      endTime: undefined,
      sessionId: undefined
    });
    setDateRange({ start: '', end: '' });
  }, [availableLevels, onFilterChange]);

  const hasActiveFilters = useMemo(() => {
    return (
      filter.levels.length < availableLevels.length ||
      filter.sources.length > 0 ||
      filter.searchQuery ||
      filter.startTime ||
      filter.endTime ||
      filter.sessionId
    );
  }, [filter, availableLevels.length]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filter.levels.length < availableLevels.length) count++;
    if (filter.sources.length > 0) count++;
    if (filter.searchQuery) count++;
    if (filter.startTime || filter.endTime) count++;
    if (filter.sessionId) count++;
    return count;
  }, [filter, availableLevels.length]);

  return (
    <div className="log-filters">
      <div className="filter-header">
        <h3>Filters</h3>
        {hasActiveFilters && (
          <span className="active-filter-count">
            {activeFilterCount} active
          </span>
        )}
        <div className="filter-actions">
          <button
            className="toggle-advanced"
            onClick={() => setShowAdvanced(!showAdvanced)}
            aria-expanded={showAdvanced}
            aria-label="Toggle advanced filters"
          >
            {showAdvanced ? '▼' : '▶'} Advanced
          </button>
          {hasActiveFilters && (
            <button
              className="clear-filters"
              onClick={handleClearFilters}
              aria-label="Clear all filters"
            >
              ✕ Clear All
            </button>
          )}
        </div>
      </div>

      <div className="filter-content">
        {/* Log Level Filters */}
        <div className="filter-group">
          <label className="filter-label">Log Levels</label>
          <div className="level-filters">
            {availableLevels.map(level => (
              <label key={level} className="level-filter">
                <input
                  type="checkbox"
                  checked={filter.levels.includes(level)}
                  onChange={() => handleLevelToggle(level)}
                  aria-label={`Toggle ${levelLabels[level]} logs`}
                />
                <span className={`level-indicator level-${LogLevel[level].toLowerCase()}`}>
                  {levelLabels[level]}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Source Filters */}
        {availableSources.length > 0 && (
          <div className="filter-group">
            <label className="filter-label">Sources</label>
            <div className="source-filters">
              {availableSources.slice(0, showAdvanced ? undefined : 5).map(source => (
                <label key={source} className="source-filter">
                  <input
                    type="checkbox"
                    checked={filter.sources.includes(source)}
                    onChange={() => handleSourceToggle(source)}
                    aria-label={`Toggle ${source} logs`}
                  />
                  <span className="source-name">{source}</span>
                </label>
              ))}
              {!showAdvanced && availableSources.length > 5 && (
                <span className="more-sources">
                  +{availableSources.length - 5} more...
                </span>
              )}
            </div>
          </div>
        )}

        {/* Advanced Filters */}
        {showAdvanced && (
          <div className="advanced-filters">
            {/* Time Range */}
            <div className="filter-group">
              <label className="filter-label">Time Range</label>
              <div className="time-range-filters">
                <div className="time-input">
                  <label htmlFor="start-time">From:</label>
                  <input
                    id="start-time"
                    type="datetime-local"
                    value={dateRange.start}
                    onChange={(e) => handleDateRangeChange('start', e.target.value)}
                    aria-label="Start time filter"
                  />
                </div>
                <div className="time-input">
                  <label htmlFor="end-time">To:</label>
                  <input
                    id="end-time"
                    type="datetime-local"
                    value={dateRange.end}
                    onChange={(e) => handleDateRangeChange('end', e.target.value)}
                    aria-label="End time filter"
                  />
                </div>
              </div>
            </div>

            {/* Session ID */}
            <div className="filter-group">
              <label className="filter-label" htmlFor="session-id">Session ID</label>
              <input
                id="session-id"
                type="text"
                placeholder="Filter by session ID..."
                value={filter.sessionId || ''}
                onChange={(e) => onFilterChange({ sessionId: e.target.value || undefined })}
                aria-label="Session ID filter"
              />
            </div>

            {/* Additional source filters (if hidden in basic view) */}
            {!showAdvanced && availableSources.length > 5 && (
              <div className="filter-group">
                <label className="filter-label">All Sources</label>
                <div className="source-filters">
                  {availableSources.map(source => (
                    <label key={source} className="source-filter">
                      <input
                        type="checkbox"
                        checked={filter.sources.includes(source)}
                        onChange={() => handleSourceToggle(source)}
                      />
                      <span className="source-name">{source}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Quick Presets */}
        <div className="filter-presets">
          <label className="filter-label">Quick Presets</label>
          <div className="preset-buttons">
            <button
              className="preset-button"
              onClick={() => onFilterChange({
                levels: [LogLevel.ERROR, LogLevel.FATAL]
              })}
              aria-label="Show only errors and fatal logs"
            >
              🚨 Errors Only
            </button>
            <button
              className="preset-button"
              onClick={() => onFilterChange({
                levels: [LogLevel.WARN, LogLevel.ERROR, LogLevel.FATAL]
              })}
              aria-label="Show warnings and above"
            >
              ⚠️ Warnings+
            </button>
            <button
              className="preset-button"
              onClick={() => onFilterChange({
                levels: [LogLevel.DEBUG]
              })}
              aria-label="Show only debug logs"
            >
              🔍 Debug Only
            </button>
            <button
              className="preset-button"
              onClick={() => {
                const now = new Date();
                const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
                onFilterChange({
                  startTime: oneHourAgo,
                  endTime: now
                });
                setDateRange({
                  start: oneHourAgo.toISOString().slice(0, 16),
                  end: now.toISOString().slice(0, 16)
                });
              }}
              aria-label="Show last hour"
            >
              🕐 Last Hour
            </button>
            <button
              className="preset-button"
              onClick={() => {
                const now = new Date();
                const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                onFilterChange({
                  startTime: oneDayAgo,
                  endTime: now
                });
                setDateRange({
                  start: oneDayAgo.toISOString().slice(0, 16),
                  end: now.toISOString().slice(0, 16)
                });
              }}
              aria-label="Show last 24 hours"
            >
              📅 Last 24h
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
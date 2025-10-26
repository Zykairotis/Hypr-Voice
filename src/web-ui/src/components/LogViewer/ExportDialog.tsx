import React, { useState, useCallback, useRef } from 'react';
import { LogExportOptions, LogLevel } from '../../types/logViewer';
import './ExportDialog.css';

interface ExportDialogProps {
  totalEntries: number;
  onExport: (options: LogExportOptions) => void;
  onClose: () => void;
}

export const ExportDialog: React.FC<ExportDialogProps> = ({
  totalEntries,
  onExport,
  onClose
}) => {
  const [format, setFormat] = useState<'json' | 'csv' | 'txt'>('json');
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [useDateRange, setUseDateRange] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: '',
    end: ''
  });
  const [selectedLevels, setSelectedLevels] = useState<LogLevel[]>(Object.values(LogLevel));
  const [isExporting, setIsExporting] = useState(false);

  const dialogRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  }, [onClose]);

  const handleLevelToggle = useCallback((level: LogLevel) => {
    setSelectedLevels(prev =>
      prev.includes(level)
        ? prev.filter(l => l !== level)
        : [...prev, level]
    );
  }, []);

  const handleExport = useCallback(async () => {
    if (selectedLevels.length === 0) {
      alert('Please select at least one log level to export.');
      return;
    }

    setIsExporting(true);

    const options: LogExportOptions = {
      format,
      includeMetadata,
      levels: selectedLevels,
      sources: [], // Export all sources
      ...(useDateRange && dateRange.start && dateRange.end ? {
        dateRange: {
          start: new Date(dateRange.start),
          end: new Date(dateRange.end)
        }
      } : {})
    };

    try {
      await onExport(options);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  }, [format, includeMetadata, selectedLevels, useDateRange, dateRange, onExport]);

  const getFormatDescription = (format: string): string => {
    switch (format) {
      case 'json':
        return 'Structured data with full metadata, ideal for programmatic processing';
      case 'csv':
        return 'Tabular format suitable for spreadsheet applications';
      case 'txt':
        return 'Human-readable plain text format';
      default:
        return '';
    }
  };

  const getFileExtension = (format: string): string => {
    switch (format) {
      case 'json': return '.json';
      case 'csv': return '.csv';
      case 'txt': return '.txt';
      default: return '.log';
    }
  };

  const levelLabels = {
    [LogLevel.DEBUG]: 'Debug',
    [LogLevel.INFO]: 'Info',
    [LogLevel.WARN]: 'Warning',
    [LogLevel.ERROR]: 'Error',
    [LogLevel.FATAL]: 'Fatal'
  };

  // Calculate estimated entries based on filters
  const estimatedEntries = useDateRange && dateRange.start && dateRange.end
    ? Math.floor(totalEntries * 0.3) // Rough estimate
    : totalEntries;

  return (
    <div className="export-dialog-overlay" onClick={onClose}>
      <div
        ref={dialogRef}
        className="export-dialog"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
        role="dialog"
        aria-modal="true"
        aria-labelledby="export-dialog-title"
      >
        <div className="dialog-header">
          <h2 id="export-dialog-title">Export Logs</h2>
          <button
            className="close-button"
            onClick={onClose}
            aria-label="Close export dialog"
          >
            ×
          </button>
        </div>

        <div className="dialog-content">
          {/* Total entries info */}
          <div className="export-info">
            <div className="info-item">
              <span className="info-label">Total entries available:</span>
              <span className="info-value">{totalEntries.toLocaleString()}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Estimated entries to export:</span>
              <span className="info-value">{estimatedEntries.toLocaleString()}</span>
            </div>
          </div>

          {/* Format selection */}
          <div className="form-group">
            <label className="form-label" htmlFor="export-format">
              Export Format
            </label>
            <div className="format-options">
              {(['json', 'csv', 'txt'] as const).map(fmt => (
                <label key={fmt} className="format-option">
                  <input
                    id={`format-${fmt}`}
                    type="radio"
                    name="format"
                    value={fmt}
                    checked={format === fmt}
                    onChange={(e) => setFormat(e.target.value as 'json' | 'csv' | 'txt')}
                  />
                  <div className="format-details">
                    <span className="format-name">{fmt.toUpperCase()}</span>
                    <span className="format-description">{getFormatDescription(fmt)}</span>
                    <span className="format-extension">File extension: {getFileExtension(fmt)}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Log level selection */}
          <div className="form-group">
            <label className="form-label">
              Log Levels to Export
              <span className="selected-count">
                ({selectedLevels.length} of {Object.values(LogLevel).length} selected)
              </span>
            </label>
            <div className="level-options">
              {Object.entries(levelLabels).map(([level, label]) => (
                <label key={level} className="level-option">
                  <input
                    type="checkbox"
                    checked={selectedLevels.includes(Number(level) as LogLevel)}
                    onChange={() => handleLevelToggle(Number(level) as LogLevel)}
                  />
                  <span className="level-name">{label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Metadata option */}
          <div className="form-group">
            <label className="form-label">
              <input
                type="checkbox"
                checked={includeMetadata}
                onChange={(e) => setIncludeMetadata(e.target.checked)}
              />
              Include metadata and additional fields
            </label>
            <p className="form-help">
              Includes structured metadata, session IDs, and other additional information
            </p>
          </div>

          {/* Date range option */}
          <div className="form-group">
            <label className="form-label">
              <input
                type="checkbox"
                checked={useDateRange}
                onChange={(e) => setUseDateRange(e.target.checked)}
              />
              Export specific date range
            </label>
            {useDateRange && (
              <div className="date-range-inputs">
                <div className="date-input">
                  <label htmlFor="start-date">From:</label>
                  <input
                    id="start-date"
                    type="datetime-local"
                    value={dateRange.start}
                    onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                  />
                </div>
                <div className="date-input">
                  <label htmlFor="end-date">To:</label>
                  <input
                    id="end-date"
                    type="datetime-local"
                    value={dateRange.end}
                    onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Export summary */}
          <div className="export-summary">
            <h3>Export Summary</h3>
            <ul>
              <li>Format: {format.toUpperCase()}</li>
              <li>Include metadata: {includeMetadata ? 'Yes' : 'No'}</li>
              <li>Log levels: {selectedLevels.map(l => levelLabels[l]).join(', ')}</li>
              {useDateRange && dateRange.start && dateRange.end && (
                <li>
                  Date range: {new Date(dateRange.start).toLocaleString()} - {new Date(dateRange.end).toLocaleString()}
                </li>
              )}
              <li>Estimated file size: ~{(estimatedEntries * 0.5).toFixed(0)} KB</li>
            </ul>
          </div>
        </div>

        <div className="dialog-actions">
          <button
            className="cancel-button"
            onClick={onClose}
            disabled={isExporting}
          >
            Cancel
          </button>
          <button
            className="export-button"
            onClick={handleExport}
            disabled={isExporting || selectedLevels.length === 0}
          >
            {isExporting ? 'Exporting...' : `Export as ${format.toUpperCase()}`}
          </button>
        </div>
      </div>
    </div>
  );
};
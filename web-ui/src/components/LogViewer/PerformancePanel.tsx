import React, { useEffect, useRef } from 'react';
import { PerformanceMetrics } from '../../types/logViewer';
import './PerformancePanel.css';

interface PerformancePanelProps {
  metrics: PerformanceMetrics;
  stats: {
    totalEntries: number;
    levelStats: Record<string, number>;
    sourceStats: Record<string, number>;
    uniqueSources: string[];
    uniqueSessions: string[];
  };
  onClose: () => void;
}

export const PerformancePanel: React.FC<PerformancePanelProps> = ({
  metrics,
  stats,
  onClose
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  // Draw performance chart
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const drawChart = () => {
      const width = canvas.width;
      const height = canvas.height;
      const padding = 40;

      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Draw axes
      ctx.strokeStyle = '#e0e0e0';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padding, padding);
      ctx.lineTo(padding, height - padding);
      ctx.lineTo(width - padding, height - padding);
      ctx.stroke();

      // Draw grid lines
      ctx.strokeStyle = '#f0f0f0';
      for (let i = 0; i <= 10; i++) {
        const y = padding + (height - 2 * padding) * i / 10;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();

        // Y-axis labels
        ctx.fillStyle = '#666';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        const value = Math.round((100 - i * 10) * metrics.entriesPerSecond / 100);
        ctx.fillText(value.toString(), padding - 5, y + 3);
      }

      // Draw performance line (simplified sine wave for demo)
      ctx.strokeStyle = '#007bff';
      ctx.lineWidth = 2;
      ctx.beginPath();

      const points = 50;
      for (let i = 0; i <= points; i++) {
        const x = padding + (width - 2 * padding) * i / points;
        const value = metrics.entriesPerSecond * (0.5 + 0.5 * Math.sin(i / 5));
        const y = height - padding - (height - 2 * padding) * value / Math.max(metrics.entriesPerSecond * 1.5, 10);

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Draw current value
      const currentX = width - padding;
      const currentValue = metrics.entriesPerSecond;
      const currentY = height - padding - (height - 2 * padding) * currentValue / Math.max(metrics.entriesPerSecond * 1.5, 10);

      ctx.fillStyle = '#007bff';
      ctx.beginPath();
      ctx.arc(currentX, currentY, 4, 0, Math.PI * 2);
      ctx.fill();

      animationRef.current = requestAnimationFrame(drawChart);
    };

    drawChart();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [metrics]);

  const formatMemoryUsage = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  const getConnectionStatusColor = (status: string): string => {
    switch (status) {
      case 'connected': return '#28a745';
      case 'disconnected': return '#6c757d';
      case 'reconnecting': return '#ffc107';
      case 'error': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getConnectionStatusText = (status: string): string => {
    switch (status) {
      case 'connected': return 'Connected';
      case 'disconnected': return 'Disconnected';
      case 'reconnecting': return 'Reconnecting...';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  return (
    <div className="performance-panel">
      <div className="panel-header">
        <h2>Performance Metrics</h2>
        <button className="close-button" onClick={onClose} aria-label="Close performance panel">
          ×
        </button>
      </div>

      <div className="panel-content">
        {/* Connection Status */}
        <div className="metric-card">
          <h3>Connection Status</h3>
          <div className="status-indicator">
            <span
              className="status-dot"
              style={{ backgroundColor: getConnectionStatusColor(metrics.connectionStatus) }}
            />
            <span className="status-text">
              {getConnectionStatusText(metrics.connectionStatus)}
            </span>
          </div>
          <div className="status-details">
            Last update: {metrics.lastUpdate.toLocaleTimeString()}
          </div>
        </div>

        {/* Throughput Metrics */}
        <div className="metric-card">
          <h3>Throughput</h3>
          <div className="metric-grid">
            <div className="metric-item">
              <div className="metric-value">{metrics.entriesPerSecond.toFixed(1)}</div>
              <div className="metric-label">Entries/Second</div>
            </div>
            <div className="metric-item">
              <div className="metric-value">{metrics.totalEntries.toLocaleString()}</div>
              <div className="metric-label">Total Entries</div>
            </div>
          </div>
        </div>

        {/* Performance Chart */}
        <div className="metric-card">
          <h3>Entries Rate</h3>
          <canvas
            ref={canvasRef}
            width={400}
            height={200}
            className="performance-chart"
            aria-label="Performance chart showing entries per second over time"
          />
        </div>

        {/* Memory Usage */}
        <div className="metric-card">
          <h3>Memory Usage</h3>
          <div className="metric-item">
            <div className="metric-value">{formatMemoryUsage(metrics.memoryUsage)}</div>
            <div className="metric-label">Heap Used</div>
          </div>
        </div>

        {/* Processing Time */}
        <div className="metric-card">
          <h3>Processing</h3>
          <div className="metric-item">
            <div className="metric-value">{metrics.averageProcessingTime.toFixed(2)}ms</div>
            <div className="metric-label">Average Processing Time</div>
          </div>
        </div>

        {/* Log Distribution */}
        <div className="metric-card">
          <h3>Log Distribution</h3>
          <div className="distribution-chart">
            {Object.entries(stats.levelStats).map(([level, count]) => {
              const percentage = stats.totalEntries > 0 ? (count / stats.totalEntries) * 100 : 0;
              const colors = {
                '0': '#6c757d', // DEBUG
                '1': '#007bff', // INFO
                '2': '#ffc107', // WARN
                '3': '#dc3545', // ERROR
                '4': '#6f42c1'  // FATAL
              };

              return (
                <div key={level} className="distribution-item">
                  <div className="distribution-bar">
                    <div
                      className="distribution-fill"
                      style={{
                        width: `${percentage}%`,
                        backgroundColor: colors[level] || '#6c757d'
                      }}
                    />
                  </div>
                  <div className="distribution-label">
                    <span className="level-name">{level}</span>
                    <span className="level-count">{count} ({percentage.toFixed(1)}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Source Statistics */}
        <div className="metric-card">
          <h3>Source Statistics</h3>
          <div className="source-stats">
            {Object.entries(stats.sourceStats)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5)
              .map(([source, count]) => {
                const percentage = stats.totalEntries > 0 ? (count / stats.totalEntries) * 100 : 0;
                return (
                  <div key={source} className="source-stat">
                    <span className="source-name">{source}</span>
                    <span className="source-count">{count} ({percentage.toFixed(1)}%)</span>
                  </div>
                );
              })}
          </div>
        </div>

        {/* System Information */}
        <div className="metric-card">
          <h3>System Information</h3>
          <div className="system-info">
            <div className="info-item">
              <span className="info-label">Unique Sources:</span>
              <span className="info-value">{stats.uniqueSources.length}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Active Sessions:</span>
              <span className="info-value">{stats.uniqueSessions.length}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Browser:</span>
              <span className="info-value">{navigator.userAgent.split(' ')[0]}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Page Load:</span>
              <span className="info-value">
                {performance.timing ?
                  `${((performance.timing.loadEventEnd - performance.timing.navigationStart) / 1000).toFixed(2)}s` :
                  'N/A'
                }
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
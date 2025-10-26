import { LogEntry, LogExportOptions, LogLevel } from '../types/logViewer';

export class LogExporter {
  static async exportToJSON(entries: LogEntry[], options: LogExportOptions): Promise<string> {
    const filteredEntries = this.filterEntries(entries, options);

    const exportData = {
      metadata: {
        exportedAt: new Date().toISOString(),
        totalEntries: filteredEntries.length,
        dateRange: options.dateRange,
        levels: options.levels,
        sources: options.sources,
        includeMetadata: options.includeMetadata
      },
      entries: filteredEntries.map(entry => {
        const baseEntry = {
          id: entry.id,
          timestamp: entry.timestamp.toISOString(),
          level: LogLevel[entry.level],
          source: entry.source,
          message: entry.message,
          sessionId: entry.sessionId,
          bookmarked: entry.bookmarked,
          annotations: entry.annotations
        };

        if (options.includeMetadata && entry.metadata) {
          return { ...baseEntry, metadata: entry.metadata };
        }

        return baseEntry;
      })
    };

    return JSON.stringify(exportData, null, 2);
  }

  static async exportToCSV(entries: LogEntry[], options: LogExportOptions): Promise<string> {
    const filteredEntries = this.filterEntries(entries, options);

    const headers = [
      'Timestamp',
      'Level',
      'Source',
      'Message',
      'Session ID',
      'Bookmarked',
      'Annotations'
    ];

    if (options.includeMetadata) {
      headers.push('Metadata');
    }

    const csvRows = [headers.join(',')];

    for (const entry of filteredEntries) {
      const row = [
        this.escapeCsvValue(entry.timestamp.toISOString()),
        this.escapeCsvValue(LogLevel[entry.level]),
        this.escapeCsvValue(entry.source),
        this.escapeCsvValue(entry.message),
        this.escapeCsvValue(entry.sessionId || ''),
        this.escapeCsvValue(entry.bookmarked ? 'true' : 'false'),
        this.escapeCsvValue(entry.annotations?.join('; ') || '')
      ];

      if (options.includeMetadata) {
        row.push(this.escapeCsvValue(JSON.stringify(entry.metadata || {})));
      }

      csvRows.push(row.join(','));
    }

    return csvRows.join('\n');
  }

  static async exportToText(entries: LogEntry[], options: LogExportOptions): Promise<string> {
    const filteredEntries = this.filterEntries(entries, options);

    const lines: string[] = [];

    // Add header
    lines.push('='.repeat(80));
    lines.push('HYPR-VOICE LOG EXPORT');
    lines.push('='.repeat(80));
    lines.push(`Exported at: ${new Date().toISOString()}`);
    lines.push(`Total entries: ${filteredEntries.length}`);

    if (options.dateRange) {
      lines.push(`Date range: ${options.dateRange.start.toISOString()} to ${options.dateRange.end.toISOString()}`);
    }

    if (options.levels && options.levels.length > 0) {
      lines.push(`Levels: ${options.levels.map(l => LogLevel[l]).join(', ')}`);
    }

    if (options.sources && options.sources.length > 0) {
      lines.push(`Sources: ${options.sources.join(', ')}`);
    }

    lines.push('-'.repeat(80));
    lines.push('');

    // Add log entries
    for (const entry of filteredEntries) {
      const timestamp = entry.timestamp.toISOString();
      const level = LogLevel[entry.level].padEnd(5);
      const source = entry.source.padEnd(15);

      lines.push(`[${timestamp}] [${level}] [${source}] ${entry.message}`);

      if (entry.sessionId) {
        lines.push(`  Session: ${entry.sessionId}`);
      }

      if (options.includeMetadata && entry.metadata) {
        lines.push('  Metadata:');
        for (const [key, value] of Object.entries(entry.metadata)) {
          lines.push(`    ${key}: ${JSON.stringify(value)}`);
        }
      }

      if (entry.annotations && entry.annotations.length > 0) {
        lines.push(`  Annotations: ${entry.annotations.join('; ')}`);
      }

      if (entry.bookmarked) {
        lines.push('  ⭐ Bookmarked');
      }

      lines.push('');
    }

    return lines.join('\n');
  }

  static downloadFile(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  }

  static async exportAndDownload(
    entries: LogEntry[],
    options: LogExportOptions,
    format: 'json' | 'csv' | 'txt'
  ): Promise<void> {
    let content: string;
    let filename: string;
    let mimeType: string;

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

    switch (format) {
      case 'json':
        content = await this.exportToJSON(entries, options);
        filename = `hypr-voice-logs-${timestamp}.json`;
        mimeType = 'application/json';
        break;

      case 'csv':
        content = await this.exportToCSV(entries, options);
        filename = `hypr-voice-logs-${timestamp}.csv`;
        mimeType = 'text/csv';
        break;

      case 'txt':
        content = await this.exportToText(entries, options);
        filename = `hypr-voice-logs-${timestamp}.txt`;
        mimeType = 'text/plain';
        break;

      default:
        throw new Error(`Unsupported export format: ${format}`);
    }

    this.downloadFile(content, filename, mimeType);
  }

  private static filterEntries(entries: LogEntry[], options: LogExportOptions): LogEntry[] {
    let filtered = [...entries];

    // Apply date range filter
    if (options.dateRange) {
      filtered = filtered.filter(entry =>
        entry.timestamp >= options.dateRange!.start &&
        entry.timestamp <= options.dateRange!.end
      );
    }

    // Apply level filter
    if (options.levels && options.levels.length > 0) {
      filtered = filtered.filter(entry => options.levels!.includes(entry.level));
    }

    // Apply source filter
    if (options.sources && options.sources.length > 0) {
      filtered = filtered.filter(entry => options.sources!.includes(entry.source));
    }

    return filtered;
  }

  private static escapeCsvValue(value: string): string {
    if (value.includes(',') || value.includes('"') || value.includes('\n')) {
      return `"${value.replace(/"/g, '""')}"`;
    }
    return value;
  }

  static generateReport(entries: LogEntry[]): string {
    const totalEntries = entries.length;
    const levelCounts = {
      [LogLevel.DEBUG]: 0,
      [LogLevel.INFO]: 0,
      [LogLevel.WARN]: 0,
      [LogLevel.ERROR]: 0,
      [LogLevel.FATAL]: 0
    };

    const sourceCounts: Record<string, number> = {};
    const sessionCounts: Record<string, number> = {};

    let earliestTimestamp: Date | null = null;
    let latestTimestamp: Date | null = null;

    for (const entry of entries) {
      // Count levels
      levelCounts[entry.level]++;

      // Count sources
      sourceCounts[entry.source] = (sourceCounts[entry.source] || 0) + 1;

      // Count sessions
      if (entry.sessionId) {
        sessionCounts[entry.sessionId] = (sessionCounts[entry.sessionId] || 0) + 1;
      }

      // Track time range
      if (!earliestTimestamp || entry.timestamp < earliestTimestamp) {
        earliestTimestamp = entry.timestamp;
      }
      if (!latestTimestamp || entry.timestamp > latestTimestamp) {
        latestTimestamp = entry.timestamp;
      }
    }

    const report = [
      '# HYPR-VOICE LOG ANALYSIS REPORT',
      `Generated at: ${new Date().toISOString()}`,
      '',
      '## SUMMARY',
      `- Total Entries: ${totalEntries}`,
      `- Time Range: ${earliestTimestamp?.toISOString() || 'N/A'} to ${latestTimestamp?.toISOString() || 'N/A'}`,
      `- Unique Sources: ${Object.keys(sourceCounts).length}`,
      `- Unique Sessions: ${Object.keys(sessionCounts).length}`,
      '',
      '## LOG LEVELS',
      ...Object.entries(levelCounts).map(([level, count]) =>
        `- ${LogLevel[Number(level)]}: ${count} (${((count / totalEntries) * 100).toFixed(1)}%)`
      ),
      '',
      '## TOP SOURCES',
      ...Object.entries(sourceCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10)
        .map(([source, count]) =>
          `- ${source}: ${count} (${((count / totalEntries) * 100).toFixed(1)}%)`
        ),
      '',
      '## TOP SESSIONS',
      ...Object.entries(sessionCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10)
        .map(([session, count]) =>
          `- ${session}: ${count} entries`
        )
    ].join('\n');

    return report;
  }
}
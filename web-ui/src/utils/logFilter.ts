import { LogEntry, LogFilter, LogLevel } from '../types/logViewer';

export class LogFilterManager {
  static filterEntries(entries: LogEntry[], filter: LogFilter): LogEntry[] {
    return entries.filter(entry => this.matchesFilter(entry, filter));
  }

  static matchesFilter(entry: LogEntry, filter: LogFilter): boolean {
    // Level filtering
    if (filter.levels.length > 0 && !filter.levels.includes(entry.level)) {
      return false;
    }

    // Source filtering
    if (filter.sources.length > 0 && !filter.sources.includes(entry.source)) {
      return false;
    }

    // Search query filtering
    if (filter.searchQuery) {
      const searchRegex = this.createSearchRegex(filter.searchQuery);
      if (!searchRegex.test(entry.message) &&
          !searchRegex.test(entry.source) &&
          !(entry.raw && searchRegex.test(entry.raw))) {
        return false;
      }
    }

    // Time range filtering
    if (filter.startTime && entry.timestamp < filter.startTime) {
      return false;
    }

    if (filter.endTime && entry.timestamp > filter.endTime) {
      return false;
    }

    // Session filtering
    if (filter.sessionId && entry.sessionId !== filter.sessionId) {
      return false;
    }

    return true;
  }

  static createSearchRegex(query: string): RegExp {
    try {
      // Check if the query is a valid regex
      if (query.startsWith('/') && query.endsWith('/')) {
        const pattern = query.slice(1, -1);
        return new RegExp(pattern, 'i');
      }

      // Check for regex flags
      const regexMatch = query.match(/^\/(.+)\/([gimsuy]*)$/);
      if (regexMatch) {
        const [, pattern, flags] = regexMatch;
        return new RegExp(pattern, flags);
      }

      // Treat as simple text search (case-insensitive)
      const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return new RegExp(escaped, 'i');
    } catch (error) {
      // Fallback to literal string search
      const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return new RegExp(escaped, 'i');
    }
  }

  static getUniqueSources(entries: LogEntry[]): string[] {
    const sources = new Set<string>();
    entries.forEach(entry => sources.add(entry.source));
    return Array.from(sources).sort();
  }

  static getUniqueSessions(entries: LogEntry[]): string[] {
    const sessions = new Set<string>();
    entries.forEach(entry => {
      if (entry.sessionId) {
        sessions.add(entry.sessionId);
      }
    });
    return Array.from(sessions).sort();
  }

  static getTimeRange(entries: LogEntry[]): { start?: Date; end?: Date } {
    if (entries.length === 0) {
      return {};
    }

    const timestamps = entries.map(e => e.timestamp.getTime());
    return {
      start: new Date(Math.min(...timestamps)),
      end: new Date(Math.max(...timestamps))
    };
  }

  static getLevelStats(entries: LogEntry[]): Record<LogLevel, number> {
    const stats = {
      [LogLevel.DEBUG]: 0,
      [LogLevel.INFO]: 0,
      [LogLevel.WARN]: 0,
      [LogLevel.ERROR]: 0,
      [LogLevel.FATAL]: 0
    };

    entries.forEach(entry => {
      stats[entry.level]++;
    });

    return stats;
  }

  static getSourceStats(entries: LogEntry[]): Record<string, number> {
    const stats: Record<string, number> = {};

    entries.forEach(entry => {
      stats[entry.source] = (stats[entry.source] || 0) + 1;
    });

    return stats;
  }

  static getHourlyDistribution(entries: LogEntry[]): Record<number, number> {
    const distribution: Record<number, number> = {};

    // Initialize all hours to 0
    for (let i = 0; i < 24; i++) {
      distribution[i] = 0;
    }

    entries.forEach(entry => {
      const hour = entry.timestamp.getHours();
      distribution[hour]++;
    });

    return distribution;
  }

  static searchWithHighlight(
    entries: LogEntry[],
    query: string,
    highlightTag: string = 'mark'
  ): Array<{ entry: LogEntry; highlightedMessage: string }> {
    const regex = this.createSearchRegex(query);

    return entries.map(entry => {
      const highlightedMessage = entry.message.replace(
        regex,
        (match) => `<${highlightTag}>${match}</${highlightTag}>`
      );

      return {
        entry,
        highlightedMessage
      };
    });
  }

  static createAdvancedFilter(options: {
    levels?: LogLevel[];
    sources?: string[];
    searchQuery?: string;
    startTime?: Date;
    endTime?: Date;
    sessionId?: string;
    hasMetadata?: boolean;
    bookmarked?: boolean;
    hasAnnotations?: boolean;
  }): LogFilter {
    return {
      levels: options.levels ?? Object.values(LogLevel),
      sources: options.sources ?? [],
      searchQuery: options.searchQuery,
      startTime: options.startTime,
      endTime: options.endTime,
      sessionId: options.sessionId
    };
  }

  static applyAdvancedFilters(
    entries: LogEntry[],
    filters: {
      levels?: LogLevel[];
      sources?: string[];
      searchQuery?: string;
      startTime?: Date;
      endTime?: Date;
      sessionId?: string;
      hasMetadata?: boolean;
      bookmarked?: boolean;
      hasAnnotations?: boolean;
    }
  ): LogEntry[] {
    return entries.filter(entry => {
      // Basic filter criteria
      if (filters.levels && !filters.levels.includes(entry.level)) {
        return false;
      }

      if (filters.sources && !filters.sources.includes(entry.source)) {
        return false;
      }

      if (filters.searchQuery) {
        const regex = this.createSearchRegex(filters.searchQuery);
        if (!regex.test(entry.message) && !regex.test(entry.source)) {
          return false;
        }
      }

      if (filters.startTime && entry.timestamp < filters.startTime) {
        return false;
      }

      if (filters.endTime && entry.timestamp > filters.endTime) {
        return false;
      }

      if (filters.sessionId && entry.sessionId !== filters.sessionId) {
        return false;
      }

      // Advanced filter criteria
      if (filters.hasMetadata && !entry.metadata) {
        return false;
      }

      if (filters.bookmarked && !entry.bookmarked) {
        return false;
      }

      if (filters.hasAnnotations && (!entry.annotations || entry.annotations.length === 0)) {
        return false;
      }

      return true;
    });
  }
}
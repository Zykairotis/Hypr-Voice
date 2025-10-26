import { LogEntry, LogLevel } from '../types/logViewer';

export class LogParser {
  private static readonly LOG_LEVEL_MAP: Record<string, LogLevel> = {
    'DEBUG': LogLevel.DEBUG,
    'INFO': LogLevel.INFO,
    'WARN': LogLevel.WARN,
    'WARNING': LogLevel.WARN,
    'ERROR': LogLevel.ERROR,
    'FATAL': LogLevel.FATAL,
    'CRITICAL': LogLevel.FATAL
  };

  private static readonly LOG_PATTERNS = [
    // JSON format: {"timestamp": "...", "level": "INFO", "message": "..."}
    {
      regex: /^\s*(\{.*\})\s*$/,
      parser: this.parseJSONLog.bind(this)
    },
    // Standard log format: [2024-01-01 12:00:00] [INFO] [source] message
    {
      regex: /^\s*\[?(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?)\]?\s*\[?(\w+)\]?\s*\[?([^\]]+)\]?\s*(.*)$/,
      parser: this.parseStandardLog.bind(this)
    },
    // Simple format: 2024-01-01 12:00:00 INFO source message
    {
      regex: /^\s*(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?)\s+(\w+)\s+(\w+)\s+(.*)$/,
      parser: this.parseSimpleLog.bind(this)
    },
    // Just level and message: INFO message
    {
      regex: /^\s*(\w+)\s+(.*)$/,
      parser: this.parseBasicLog.bind(this)
    }
  ];

  static parse(rawLog: string, source: string = 'unknown'): LogEntry {
    const trimmed = rawLog.trim();

    for (const pattern of this.LOG_PATTERNS) {
      const match = trimmed.match(pattern.regex);
      if (match) {
        try {
          return pattern.parser(match, trimmed, source);
        } catch (error) {
          console.warn('Failed to parse log with pattern:', error);
          continue;
        }
      }
    }

    // Fallback: treat entire line as message with INFO level
    return this.createFallbackEntry(trimmed, source);
  }

  private static parseJSONLog(match: RegExpMatchArray, raw: string, source: string): LogEntry {
    const jsonStr = match[1];
    const data = JSON.parse(jsonStr);

    const timestamp = this.parseTimestamp(data.timestamp || data.time || Date.now());
    const level = this.parseLogLevel(data.level || data.severity || 'INFO');
    const message = data.message || data.msg || '';
    const metadata = { ...data };
    delete metadata.timestamp;
    delete metadata.time;
    delete metadata.level;
    delete metadata.severity;
    delete metadata.message;
    delete metadata.msg;

    return {
      id: this.generateId(),
      timestamp,
      level,
      source: data.source || source,
      message,
      metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
      raw,
      sessionId: data.sessionId
    };
  }

  private static parseStandardLog(match: RegExpMatchArray, raw: string, source: string): LogEntry {
    const [, timestampStr, levelStr, sourceStr, message] = match;

    return {
      id: this.generateId(),
      timestamp: this.parseTimestamp(timestampStr),
      level: this.parseLogLevel(levelStr),
      source: sourceStr || source,
      message,
      raw
    };
  }

  private static parseSimpleLog(match: RegExpMatchArray, raw: string, source: string): LogEntry {
    const [, timestampStr, levelStr, sourceStr, message] = match;

    return {
      id: this.generateId(),
      timestamp: this.parseTimestamp(timestampStr),
      level: this.parseLogLevel(levelStr),
      source: sourceStr || source,
      message,
      raw
    };
  }

  private static parseBasicLog(match: RegExpMatchArray, raw: string, source: string): LogEntry {
    const [, levelStr, message] = match;

    return {
      id: this.generateId(),
      timestamp: new Date(),
      level: this.parseLogLevel(levelStr),
      source,
      message,
      raw
    };
  }

  private static createFallbackEntry(message: string, source: string): LogEntry {
    return {
      id: this.generateId(),
      timestamp: new Date(),
      level: LogLevel.INFO,
      source,
      message,
      raw: message
    };
  }

  private static parseTimestamp(timestamp: string | number): Date {
    if (typeof timestamp === 'number') {
      return new Date(timestamp);
    }

    // Try parsing as ISO string
    const isoDate = new Date(timestamp);
    if (!isNaN(isoDate.getTime())) {
      return isoDate;
    }

    // Try parsing common formats
    const formats = [
      /^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2}):(\d{2})(?:\.(\d{3}))?(Z|[+-]\d{2}:\d{2})?$/,
      /^(\d{2})\/(\d{2})\/(\d{4})\s+(\d{2}):(\d{2}):(\d{2})$/
    ];

    for (const format of formats) {
      const match = timestamp.match(format);
      if (match) {
        try {
          return new Date(timestamp);
        } catch {
          continue;
        }
      }
    }

    // Fallback to current time
    return new Date();
  }

  private static parseLogLevel(level: string): LogLevel {
    const upperLevel = level.toUpperCase();
    return this.LOG_LEVEL_MAP[upperLevel] ?? LogLevel.INFO;
  }

  private static generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  static parseBatch(logs: string[], source: string = 'unknown'): LogEntry[] {
    return logs.map(log => this.parse(log, source));
  }

  static isValidJSONLog(line: string): boolean {
    const trimmed = line.trim();
    if (!trimmed.startsWith('{') || !trimmed.endsWith('}')) {
      return false;
    }

    try {
      const parsed = JSON.parse(trimmed);
      return parsed && typeof parsed === 'object';
    } catch {
      return false;
    }
  }

  static extractSessionId(log: LogEntry): string | undefined {
    // Try to extract session ID from metadata or message
    if (log.metadata?.sessionId) {
      return log.metadata.sessionId;
    }

    // Look for session ID patterns in the message
    const sessionPatterns = [
      /session[_-]?id[:\s]+([a-f0-9-]+)/i,
      /session[:\s]+([a-f0-9-]+)/i,
      /\[([a-f0-9-]{8,})\]/,
    ];

    for (const pattern of sessionPatterns) {
      const match = log.message.match(pattern);
      if (match) {
        return match[1];
      }
    }

    return undefined;
  }

  static groupBySession(entries: LogEntry[]): Map<string, LogEntry[]> {
    const sessions = new Map<string, LogEntry[]>();

    for (const entry of entries) {
      const sessionId = entry.sessionId || this.extractSessionId(entry) || 'default';

      if (!sessions.has(sessionId)) {
        sessions.set(sessionId, []);
      }

      sessions.get(sessionId)!.push(entry);
    }

    return sessions;
  }
}
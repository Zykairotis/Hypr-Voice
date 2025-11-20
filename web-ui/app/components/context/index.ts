export { ContextDashboard } from './ContextDashboard';
export { ShellHistoryManager } from './ShellHistoryManager';
export { ClipboardManager } from './ClipboardManager';
export { ApplicationDetector } from './ApplicationDetector';
export { ContextTimeline } from './visualization/ContextTimeline';
export { ContextAnalyticsPanel } from './analytics/ContextAnalyticsPanel';
export { useContextData } from './hooks/useContextData';

export type {
  ShellCommand,
  ClipboardEntry,
  ActiveWindow,
  ApplicationStats,
  ContextData,
  ContextFilter,
  ContextTimelineEvent,
  ContextAnalytics,
  ContextState,
} from './types';

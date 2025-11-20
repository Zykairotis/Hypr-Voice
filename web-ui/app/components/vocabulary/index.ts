'use client';

// Main vocabulary management interface
export { VocabularyDashboard } from './dashboard/VocabularyDashboard';
export { ApplicationVocabulary } from './application/ApplicationVocabulary';
export { VocabularyEditor } from './editor/VocabularyEditor';
export { ContextAwareVocabulary } from './context/ContextAwareVocabulary';
export { GlobalVocabularySettings } from './settings/GlobalVocabularySettings';
export { VocabularyStatistics } from './statistics/VocabularyStatistics';
export { LiveVocabularyMonitor } from './monitoring/LiveVocabularyMonitor';
export { VocabularyPresets } from './presets/VocabularyPresets';
export { WordCloud, VocabularyGraph } from './visualization/WordCloud';

// Types
export type {
  VocabularyWord,
  VocabularyCategory,
  VocabularyConfig,
  ApplicationContext,
  ContextData,
  VocabularyStatistics,
  VocabularyPreset,
  VocabularyMatch,
  LiveUpdate,
  VocabularyFilter,
  VocabularyEditorState,
  VocabularyAction,
  KeywordEffectiveness,
} from '@/lib/vocabulary/types';

// API and utilities
export { vocabularyAPI } from '@/lib/vocabulary/api';
export { vocabularyWS } from '@/lib/vocabulary/websocket';

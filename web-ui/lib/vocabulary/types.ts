// Vocabulary Management Types
export interface VocabularyWord {
  id: string;
  word: string;
  category: string;
  priority: number;
  weight: number;
  corrections?: string[];
  metadata?: Record<string, any>;
}

export interface VocabularyCategory {
  id: string;
  name: string;
  description?: string;
  words: VocabularyWord[];
  color?: string;
}

export interface VocabularyConfig {
  name: string;
  description: string;
  keywords: Record<string, string[] | Record<string, string[]>>;
  applications: {
    window_classes?: string[];
    patterns?: string[];
    title_patterns?: string[];
  };
  prompts: {
    initial?: string;
    context?: string;
  };
  priority: number;
}

export interface ApplicationContext {
  class: string;
  title: string;
  windowClass?: string;
  keywords: string[];
  matchedVocabulary?: string;
}

export interface ContextData {
  vocabulary: string[];
  context: {
    shell: {
      recent_commands: string[];
      command_count: number;
      unique_commands: number;
      timestamp: number;
    };
    clipboard: {
      recent_entries: string[];
      entry_count: number;
      timestamp: number;
    };
    window?: {
      application: string;
      title: string;
      metadata: Record<string, any>;
      timestamp: number;
    };
  };
}

export interface VocabularyStatistics {
  totalVocabularies: number;
  currentVocabulary?: string;
  currentApplication?: string;
  activeKeywords: number;
  vocabularies: Record<string, {
    name: string;
    description: string;
    totalKeywords: number;
  }>;
  usageStats?: {
    mostUsed: Array<{ word: string; count: number }>;
    accuracyRate: number;
    totalCorrections: number;
  };
}

export interface VocabularyPreset {
  id: string;
  name: string;
  description: string;
  category: string;
  vocabulary: VocabularyConfig;
  tags: string[];
  createdAt: number;
  isBuiltIn: boolean;
}

export interface VocabularyMatch {
  word: string;
  match: string;
  confidence: number;
  type: 'exact' | 'fuzzy';
  category?: string;
}

export interface LiveUpdate {
  type: 'vocabulary_change' | 'keyword_match' | 'application_switch' | 'stats_update';
  payload: any;
  timestamp: number;
}

export interface VocabularyFilter {
  category?: string;
  search?: string;
  minPriority?: number;
  hasCorrections?: boolean;
  sortBy?: 'word' | 'priority' | 'category' | 'usage';
  sortOrder?: 'asc' | 'desc';
}

export interface VocabularyEditorState {
  selectedVocabulary: string;
  selectedCategory?: string;
  selectedWords: Set<string>;
  isEditing: boolean;
  filter: VocabularyFilter;
  viewMode: 'grid' | 'list' | 'cloud';
}

export interface VocabularyAction {
  type: 'ADD_WORD' | 'REMOVE_WORD' | 'UPDATE_WORD' | 'BULK_IMPORT' | 'EXPORT' | 'CLEAR';
  payload: any;
  vocabularyId?: string;
}

export interface KeywordEffectiveness {
  word: string;
  category: string;
  matches: number;
  corrections: number;
  accuracy: number;
  lastUsed?: number;
  trend: 'up' | 'down' | 'stable';
}

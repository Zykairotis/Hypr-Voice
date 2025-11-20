// React hooks for vocabulary management
import { useState, useEffect, useCallback } from 'react';
import { vocabularyAPI } from './api';
import { vocabularyWS } from './websocket';
import {
  VocabularyConfig,
  VocabularyStatistics,
  ContextData,
  ApplicationContext,
  VocabularyWord,
  LiveUpdate,
} from './types';

export function useVocabularies() {
  const [vocabularies, setVocabularies] = useState<VocabularyConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadVocabularies = useCallback(async () => {
    try {
      setLoading(true);
      const data = await vocabularyAPI.getVocabularies();
      setVocabularies(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadVocabularies();

    // Listen for vocabulary changes
    vocabularyWS.on('vocabulary_change', loadVocabularies);

    return () => {
      vocabularyWS.off('vocabulary_change', loadVocabularies);
    };
  }, [loadVocabularies]);

  return { vocabularies, loading, error, reload: loadVocabularies };
}

export function useVocabularyStats() {
  const [stats, setStats] = useState<VocabularyStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadStats = useCallback(async () => {
    try {
      setLoading(true);
      const data = await vocabularyAPI.getStatistics();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStats();

    // Listen for stats updates
    vocabularyWS.on('stats_update', (update) => {
      setStats(update.payload);
    });

    return () => {
      vocabularyWS.off('stats_update', () => {});
    };
  }, [loadStats]);

  return { stats, loading, error, reload: loadStats };
}

export function useApplicationContext() {
  const [context, setContext] = useState<ApplicationContext | null>(null);
  const [loading, setLoading] = useState(true);

  const detectApplication = useCallback(async () => {
    try {
      setLoading(true);
      const data = await vocabularyAPI.getApplicationContext();
      setContext(data);
    } catch (error) {
      console.error('Failed to detect application:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    detectApplication();

    // Listen for application changes
    vocabularyWS.on('application_switch', (update) => {
      setContext(update.payload);
    });

    return () => {
      vocabularyWS.off('application_switch', () => {});
    };
  }, [detectApplication]);

  return { context, loading, detectApplication };
}

export function useVocabularyUpdates() {
  const [updates, setUpdates] = useState<LiveUpdate[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const handleUpdate = (update: LiveUpdate) => {
      setUpdates((prev) => [update, ...prev.slice(0, 99)]);
    };

    vocabularyWS.on('connect', () => setIsConnected(true));
    vocabularyWS.on('disconnect', () => setIsConnected(false));

    vocabularyWS.on('vocabulary_change', handleUpdate);
    vocabularyWS.on('keyword_match', handleUpdate);
    vocabularyWS.on('application_switch', handleUpdate);
    vocabularyWS.on('stats_update', handleUpdate);

    return () => {
      vocabularyWS.off('connect', () => setIsConnected(false));
      vocabularyWS.off('disconnect', () => setIsConnected(false));
      vocabularyWS.off('vocabulary_change', handleUpdate);
      vocabularyWS.off('keyword_match', handleUpdate);
      vocabularyWS.off('application_switch', handleUpdate);
      vocabularyWS.off('stats_update', handleUpdate);
    };
  }, []);

  const sendUpdate = useCallback((event: string, data: any) => {
    vocabularyWS.send(event, data);
  }, []);

  return { updates, isConnected, sendUpdate };
}

export function useContextData() {
  const [contextData, setContextData] = useState<ContextData | null>(null);
  const [loading, setLoading] = useState(true);

  const loadContext = useCallback(async () => {
    try {
      setLoading(true);
      const data = await vocabularyAPI.getCurrentContext();
      setContextData(data);
    } catch (error) {
      console.error('Failed to load context:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadContext();

    // Listen for context updates
    vocabularyWS.on('context_update', (update) => {
      setContextData(update.payload);
    });

    return () => {
      vocabularyWS.off('context_update', () => {});
    };
  }, [loadContext]);

  return { contextData, loading, reload: loadContext };
}

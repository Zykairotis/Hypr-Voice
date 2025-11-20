'use client';

import { useState, useEffect, useCallback } from 'react';
import { ContextData, ContextFilter, ContextState, ContextAnalytics } from '../types';

export function useContextData() {
  const [state, setState] = useState<ContextState>({
    data: null,
    loading: true,
    error: null,
    lastUpdate: 0,
    filters: {},
    realtimeEnabled: true,
  });

  const [analytics, setAnalytics] = useState<ContextAnalytics | null>(null);

  const fetchContextData = useCallback(async (filters?: ContextFilter) => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));

      const queryParams = new URLSearchParams();
      if (filters) {
        if (filters.timeRange) queryParams.append('timeRange', filters.timeRange);
        if (filters.categories?.length) queryParams.append('categories', filters.categories.join(','));
        if (filters.keywords?.length) queryParams.append('keywords', filters.keywords.join(','));
        if (filters.application) queryParams.append('application', filters.application);
      }

      const response = await fetch(`/api/context/data?${queryParams.toString()}`);
      if (!response.ok) {
        throw new Error('Failed to fetch context data');
      }

      const data: ContextData = await response.json();
      setState(prev => ({
        ...prev,
        data,
        loading: false,
        lastUpdate: Date.now(),
      }));

      // Fetch analytics
      const analyticsResponse = await fetch('/api/context/analytics');
      if (analyticsResponse.ok) {
        const analyticsData: ContextAnalytics = await analyticsResponse.json();
        setAnalytics(analyticsData);
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error',
        loading: false,
      }));
    }
  }, []);

  const updateFilters = useCallback((filters: ContextFilter) => {
    setState(prev => ({ ...prev, filters }));
    fetchContextData(filters);
  }, [fetchContextData]);

  const clearContext = useCallback(async () => {
    try {
      const response = await fetch('/api/context/clear', { method: 'POST' });
      if (response.ok) {
        fetchContextData(state.filters);
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to clear context',
      }));
    }
  }, [fetchContextData, state.filters]);

  const exportContext = useCallback(async (format: 'json' | 'csv' = 'json') => {
    try {
      const response = await fetch(`/api/context/export?format=${format}`);
      if (!response.ok) throw new Error('Failed to export context');

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `context-export-${Date.now()}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to export context',
      }));
    }
  }, []);

  // Real-time updates via WebSocket
  useEffect(() => {
    if (!state.realtimeEnabled) return;

    const ws = new WebSocket('ws://localhost:9090/ws/context');

    ws.onopen = () => {
      console.log('Context WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data);
        if (update.type === 'context_update') {
          setState(prev => ({
            ...prev,
            data: update.data,
            lastUpdate: Date.now(),
          }));
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Context WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Context WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, [state.realtimeEnabled]);

  // Initial load
  useEffect(() => {
    fetchContextData();
  }, [fetchContextData]);

  return {
    ...state,
    analytics,
    fetchContextData,
    updateFilters,
    clearContext,
    exportContext,
  };
}

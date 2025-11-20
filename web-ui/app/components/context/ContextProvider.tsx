'use client';

import React, { createContext, useContext, ReactNode } from 'react';
import { useContextData } from './hooks/useContextData';
import { ContextData, ContextFilter } from './types';

interface ContextContextType {
  data: ContextData | null;
  loading: boolean;
  error: string | null;
  lastUpdate: number;
  filters: ContextFilter;
  realtimeEnabled: boolean;
  analytics: any;
  fetchContextData: (filters?: ContextFilter) => Promise<void>;
  updateFilters: (filters: ContextFilter) => void;
  clearContext: () => Promise<void>;
  exportContext: (format: 'json' | 'csv') => Promise<void>;
}

const ContextContext = createContext<ContextContextType | null>(null);

export function ContextProvider({ children }: { children: ReactNode }) {
  const contextValue = useContextData();

  return (
    <ContextContext.Provider value={contextValue}>
      {children}
    </ContextContext.Provider>
  );
}

export function useContext() {
  const context = useContext(ContextContext);
  if (!context) {
    throw new Error('useContext must be used within a ContextProvider');
  }
  return context;
}

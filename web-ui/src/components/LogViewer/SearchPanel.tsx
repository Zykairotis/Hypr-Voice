import React, { useState, useCallback, useEffect, useRef } from 'react';
import './SearchPanel.css';

interface SearchPanelProps {
  query: string;
  onQueryChange: (query: string) => void;
  onClose: () => void;
  inputRef?: React.RefObject<HTMLInputElement>;
}

export const SearchPanel: React.FC<SearchPanelProps> = ({
  query,
  onQueryChange,
  onClose,
  inputRef: externalInputRef
}) => {
  const [localQuery, setLocalQuery] = useState(query);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [useRegex, setUseRegex] = useState(false);
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [wholeWord, setWholeWord] = useState(false);
  const [searchHistoryIndex, setSearchHistoryIndex] = useState(-1);

  const internalInputRef = useRef<HTMLInputElement>(null);
  const inputRef = externalInputRef || internalInputRef;
  const historyRef = useRef<HTMLDivElement>(null);

  // Load search history from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem('logViewer-searchHistory');
      if (saved) {
        setSearchHistory(JSON.parse(saved));
      }
    } catch (error) {
      console.warn('Failed to load search history:', error);
    }
  }, []);

  // Sync local query with prop
  useEffect(() => {
    setLocalQuery(query);
  }, [query]);

  // Focus input when panel opens
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [inputRef]);

  const handleQueryChange = useCallback((newQuery: string) => {
    setLocalQuery(newQuery);
    onQueryChange(newQuery);
    setSearchHistoryIndex(-1);

    if (newQuery.trim()) {
      setShowHistory(false);
    }
  }, [onQueryChange]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Enter':
        e.preventDefault();
        if (localQuery.trim()) {
          handleSearch();
        }
        break;
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
      case 'ArrowUp':
        e.preventDefault();
        if (showHistory && searchHistory.length > 0) {
          const newIndex = Math.min(searchHistoryIndex + 1, searchHistory.length - 1);
          setSearchHistoryIndex(newIndex);
          setLocalQuery(searchHistory[newIndex]);
        } else if (searchHistory.length > 0) {
          setShowHistory(true);
          setSearchHistoryIndex(0);
          setLocalQuery(searchHistory[0]);
        }
        break;
      case 'ArrowDown':
        e.preventDefault();
        if (showHistory) {
          const newIndex = Math.max(searchHistoryIndex - 1, -1);
          setSearchHistoryIndex(newIndex);
          if (newIndex >= 0) {
            setLocalQuery(searchHistory[newIndex]);
          } else {
            setLocalQuery(query);
          }
        }
        break;
    }
  }, [localQuery, showHistory, searchHistory, searchHistoryIndex, query, onClose]);

  const handleSearch = useCallback(() => {
    if (!localQuery.trim()) return;

    // Update search history
    const newHistory = [localQuery, ...searchHistory.filter(h => h !== localQuery)].slice(0, 20);
    setSearchHistory(newHistory);
    localStorage.setItem('logViewer-searchHistory', JSON.stringify(newHistory));

    onQueryChange(localQuery);
    setShowHistory(false);
  }, [localQuery, searchHistory, onQueryChange]);

  const clearHistory = useCallback(() => {
    setSearchHistory([]);
    localStorage.removeItem('logViewer-searchHistory');
    setShowHistory(false);
  }, []);

  const applyHistoryItem = useCallback((item: string) => {
    setLocalQuery(item);
    onQueryChange(item);
    setShowHistory(false);
    setSearchHistoryIndex(-1);
  }, [onQueryChange]);

  const buildSearchPattern = useCallback((query: string): string => {
    if (!useRegex) {
      // Escape regex special characters for literal search
      const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

          if (wholeWord) {
        return `\\b${escaped}\\b`;
          }
          return escaped;
        }

        // User provided regex, use as-is but wrap with word boundaries if needed
        if (wholeWord && !query.startsWith('\\b') && !query.endsWith('\\b')) {
          return `\\b${query}\\b`;
        }
        return query;
      }, [useRegex, wholeWord]);

      const getSearchDescription = useCallback((): string => {
        if (!localQuery.trim()) return 'Enter a search query';

        const parts = [];
        if (useRegex) parts.push('regex');
        if (caseSensitive) parts.push('case-sensitive');
        if (wholeWord) parts.push('whole word');

        const prefix = parts.length > 0 ? `${parts.join(', ')} search` : 'Search';
        return `${prefix} for "${localQuery}"`;
      }, [localQuery, useRegex, caseSensitive, wholeWord]);

      // Click outside to close history
      useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
          if (historyRef.current && !historyRef.current.contains(event.target as Node)) {
            if (!inputRef.current?.contains(event.target as Node)) {
              setShowHistory(false);
            }
          }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
      }, [inputRef]);

      return (
        <div className="search-panel">
          <div className="search-header">
            <h3>Search Logs</h3>
            <button
              className="close-button"
              onClick={onClose}
              aria-label="Close search panel"
            >
              ×
            </button>
          </div>

          <div className="search-content">
            <div className="search-input-wrapper">
              <div className="search-input-container">
                <input
                  ref={inputRef}
                  type="text"
                  className="search-input"
                  placeholder="Search logs... (use /regex/ for regex search)"
                  value={localQuery}
                  onChange={(e) => handleQueryChange(e.target.value)}
                  onKeyDown={handleKeyDown}
                  aria-label="Search logs"
                  aria-describedby="search-description"
                />
                <button
                  className="search-button"
                  onClick={handleSearch}
                  disabled={!localQuery.trim()}
                  aria-label="Perform search"
                >
                  🔍
                </button>
              </div>

              {/* Search history dropdown */}
              {showHistory && searchHistory.length > 0 && (
                <div ref={historyRef} className="search-history">
                  <div className="history-header">
                    <span>Recent Searches</span>
                    <button
                      className="clear-history-button"
                      onClick={clearHistory}
                      aria-label="Clear search history"
                    >
                      Clear
                    </button>
                  </div>
                  <div className="history-items">
                    {searchHistory.map((item, index) => (
                      <button
                        key={index}
                        className={`history-item ${index === searchHistoryIndex ? 'selected' : ''}`}
                        onClick={() => applyHistoryItem(item)}
                        onMouseEnter={() => setSearchHistoryIndex(index)}
                      >
                        {item}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Search options */}
            <div className="search-options">
              <label className="search-option">
                <input
                  type="checkbox"
                  checked={useRegex}
                  onChange={(e) => setUseRegex(e.target.checked)}
                />
                <span>Regular Expression</span>
              </label>
              <label className="search-option">
                <input
                  type="checkbox"
                  checked={caseSensitive}
                  onChange={(e) => setCaseSensitive(e.target.checked)}
                />
                <span>Case Sensitive</span>
              </label>
              <label className="search-option">
                <input
                  type="checkbox"
                  checked={wholeWord}
                  onChange={(e) => setWholeWord(e.target.checked)}
                />
                <span>Whole Word</span>
              </label>
            </div>

            {/* Search description */}
            <div id="search-description" className="search-description">
              {getSearchDescription()}
            </div>

            {/* Search tips */}
            <div className="search-tips">
              <h4>Search Tips:</h4>
              <ul>
                <li><kbd>Enter</kbd> - Perform search</li>
                <li><kbd>Escape</kbd> - Close search</li>
                <li><kbd>↑/↓</kbd> - Navigate history</li>
                <li><code>/pattern/flags</code> - Use regular expressions</li>
                <li><code>text</code> - Plain text search</li>
                <li><code>field:value</code> - Field-specific search</li>
              </ul>
            </div>

            {/* Example searches */}
            <div className="search-examples">
              <h4>Example Searches:</h4>
              <div className="example-searches">
                <button
                  className="example-search"
                  onClick={() => handleQueryChange('ERROR')}
                >
                  ERROR
                </button>
                <button
                  className="example-search"
                  onClick={() => handleQueryChange('/\\[ERROR\\].*database/')}
                >
                  /[ERROR].*database/
                </button>
                <button
                  className="example-search"
                  onClick={() => handleQueryChange('session:')}
                >
                  session:
                </button>
                <button
                  className="example-search"
                  onClick={() => handleQueryChange('/timeout.*ms/gi')}
                >
                  /timeout.*ms/gi
                </button>
                <button
                  className="example-search"
                  onClick={() => handleQueryChange('"connection failed"')}
                >
                  "connection failed"
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    };
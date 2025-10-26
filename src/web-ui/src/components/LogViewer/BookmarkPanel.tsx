import React, { useState, useCallback, useMemo } from 'react';
import { Bookmark, LogEntry } from '../../types/logViewer';
import './BookmarkPanel.css';

interface BookmarkPanelProps {
  bookmarks: Bookmark[];
  entries: LogEntry[];
  onBookmarkRemove: (bookmarkId: string) => void;
  onBookmarkClick: (bookmark: Bookmark) => void;
  onClose: () => void;
}

export const BookmarkPanel: React.FC<BookmarkPanelProps> = ({
  bookmarks,
  entries,
  onBookmarkRemove,
  onBookmarkClick,
  onClose
}) => {
  const [sortBy, setSortBy] = useState<'timestamp' | 'source' | 'level'>('timestamp');
  const [filterTags, setFilterTags] = useState<string[]>([]);
  const [showAllTags, setShowAllTags] = useState(true);

  // Get unique tags from all bookmarks
  const allTags = useMemo(() => {
    const tags = new Set<string>();
    bookmarks.forEach(bookmark => {
      bookmark.tags.forEach(tag => tags.add(tag));
    });
    return Array.from(tags).sort();
  }, [bookmarks]);

  // Filter and sort bookmarks
  const filteredBookmarks = useMemo(() => {
    let filtered = bookmarks;

    // Filter by tags
    if (filterTags.length > 0 || !showAllTags) {
      filtered = filtered.filter(bookmark => {
        if (showAllTags && filterTags.length === 0) return true;
        return bookmark.tags.some(tag => filterTags.includes(tag));
      });
    }

    // Sort bookmarks
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'timestamp':
          return b.timestamp.getTime() - a.timestamp.getTime();
        case 'source':
          const aEntry = entries.find(e => e.id === a.logId);
          const bEntry = entries.find(e => e.id === b.logId);
          if (!aEntry || !bEntry) return 0;
          return aEntry.source.localeCompare(bEntry.source);
        case 'level':
          // This would require more complex logic to get log entries
          return 0;
        default:
          return 0;
      }
    });
  }, [bookmarks, entries, sortBy, filterTags, showAllTags]);

  const handleTagToggle = useCallback((tag: string) => {
    setFilterTags(prev =>
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  }, []);

  const handleBookmarkRemove = useCallback((bookmarkId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    if (window.confirm('Are you sure you want to remove this bookmark?')) {
      onBookmarkRemove(bookmarkId);
    }
  }, [onBookmarkRemove]);

  const handleExportBookmarks = useCallback(() => {
    const exportData = {
      exportedAt: new Date().toISOString(),
      totalBookmarks: bookmarks.length,
      bookmarks: bookmarks.map(bookmark => {
        const entry = entries.find(e => e.id === bookmark.logId);
        return {
          ...bookmark,
          logEntry: entry ? {
            timestamp: entry.timestamp.toISOString(),
            level: entry.level,
            source: entry.source,
            message: entry.message
          } : null
        };
      })
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `hypr-voice-bookmarks-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [bookmarks, entries]);

  const formatTimestamp = (timestamp: Date): string => {
    return timestamp.toLocaleString();
  };

  const getEntryPreview = (entry: LogEntry): string => {
    const preview = entry.message.length > 100
      ? entry.message.substring(0, 100) + '...'
      : entry.message;
    return preview.replace(/\n/g, ' ');
  };

  return (
    <div className="bookmark-panel">
      <div className="panel-header">
        <h3>Bookmarks ({bookmarks.length})</h3>
        <div className="panel-actions">
          {bookmarks.length > 0 && (
            <button
              className="export-button"
              onClick={handleExportBookmarks}
              title="Export bookmarks"
              aria-label="Export bookmarks"
            >
              💾
            </button>
          )}
          <button
            className="close-button"
            onClick={onClose}
            aria-label="Close bookmark panel"
          >
            ×
          </button>
        </div>
      </div>

      <div className="panel-content">
        {bookmarks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">⭐</div>
            <h4>No bookmarks yet</h4>
            <p>Click the star icon on log entries to bookmark them for quick access.</p>
          </div>
        ) : (
          <>
            {/* Controls */}
            <div className="bookmark-controls">
              {/* Sort options */}
              <div className="sort-controls">
                <label htmlFor="sort-by">Sort by:</label>
                <select
                  id="sort-by"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'timestamp' | 'source' | 'level')}
                >
                  <option value="timestamp">Timestamp</option>
                  <option value="source">Source</option>
                  <option value="level">Log Level</option>
                </select>
              </div>

              {/* Filter by tags */}
              {allTags.length > 0 && (
                <div className="tag-filter">
                  <label>Filter by tags:</label>
                  <div className="tag-options">
                    <label className="tag-option">
                      <input
                        type="checkbox"
                        checked={showAllTags}
                        onChange={(e) => setShowAllTags(e.target.checked)}
                      />
                      <span>All</span>
                    </label>
                    {allTags.map(tag => (
                      <label key={tag} className="tag-option">
                        <input
                          type="checkbox"
                          checked={filterTags.includes(tag)}
                          onChange={() => handleTagToggle(tag)}
                        />
                        <span>{tag}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Bookmarks list */}
            <div className="bookmarks-list">
              {filteredBookmarks.length === 0 ? (
                <div className="no-results">
                  <p>No bookmarks match the current filters.</p>
                </div>
              ) : (
                filteredBookmarks.map(bookmark => {
                  const entry = entries.find(e => e.id === bookmark.logId);
                  if (!entry) return null;

                  return (
                    <div
                      key={bookmark.id}
                      className="bookmark-item"
                      onClick={() => onBookmarkClick(bookmark)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          onBookmarkClick(bookmark);
                        }
                      }}
                      aria-label={`Bookmark from ${entry.source} at ${formatTimestamp(bookmark.timestamp)}`}
                    >
                      <div className="bookmark-header">
                        <div className="bookmark-meta">
                          <span className="bookmark-source">{entry.source}</span>
                          <span className="bookmark-timestamp">
                            {formatTimestamp(bookmark.timestamp)}
                          </span>
                          <span className={`bookmark-level level-${entry.level}`}>
                            {entry.level}
                          </span>
                        </div>
                        <button
                          className="remove-bookmark-button"
                          onClick={(e) => handleBookmarkRemove(bookmark.id, e)}
                          title="Remove bookmark"
                          aria-label="Remove bookmark"
                        >
                          ×
                        </button>
                      </div>

                      <div className="bookmark-content">
                        <div className="bookmark-message">
                          {getEntryPreview(entry)}
                        </div>

                        {bookmark.note && (
                          <div className="bookmark-note">
                            <strong>Note:</strong> {bookmark.note}
                          </div>
                        )}

                        {bookmark.tags.length > 0 && (
                          <div className="bookmark-tags">
                            {bookmark.tags.map(tag => (
                              <span key={tag} className="bookmark-tag">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
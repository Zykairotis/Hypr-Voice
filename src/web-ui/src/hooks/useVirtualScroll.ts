import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { LogEntry, VirtualScrollItem } from '../types/logViewer';

interface UseVirtualScrollOptions {
  items: LogEntry[];
  containerHeight: number;
  itemHeight: number | ((index: number, item: LogEntry) => number);
  overscan?: number;
  enabled?: boolean;
}

interface UseVirtualScrollReturn {
  virtualItems: VirtualScrollItem[];
  totalSize: number;
  scrollToIndex: (index: number, align?: 'start' | 'center' | 'end') => void;
  scrollToOffset: (offset: number) => void;
  containerRef: React.RefObject<HTMLDivElement>;
  isScrolling: boolean;
  startIndex: number;
  endIndex: number;
}

export const useVirtualScroll = ({
  items,
  containerHeight,
  itemHeight,
  overscan = 5,
  enabled = true
}: UseVirtualScrollOptions): UseVirtualScrollReturn => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollOffset, setScrollOffset] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);
  const scrollTimeoutRef = useRef<NodeJS.Timeout>();

  // Calculate item heights
  const getItemHeight = useCallback((index: number, item: LogEntry): number => {
    if (typeof itemHeight === 'function') {
      return itemHeight(index, item);
    }
    return itemHeight;
  }, [itemHeight]);

  // Build index map for fast height lookup
  const heightMap = useMemo(() => {
    const map = new Map<number, number>();
    let totalHeight = 0;

    for (let i = 0; i < items.length; i++) {
      map.set(i, totalHeight);
      totalHeight += getItemHeight(i, items[i]);
    }

    return { map, totalHeight };
  }, [items, getItemHeight]);

  // Find item index from scroll offset using binary search
  const findItemIndex = useCallback((offset: number): number => {
    if (!enabled) return 0;

    const { map } = heightMap;
    let left = 0;
    let right = items.length - 1;

    while (left <= right) {
      const mid = Math.floor((left + right) / 2);
      const itemOffset = map.get(mid) ?? 0;
      const nextItemOffset = map.get(mid + 1) ?? heightMap.totalHeight;

      if (offset >= itemOffset && offset < nextItemOffset) {
        return mid;
      } else if (offset < itemOffset) {
        right = mid - 1;
      } else {
        left = mid + 1;
      }
    }

    return Math.max(0, Math.min(left, items.length - 1));
  }, [enabled, items.length, heightMap]);

  // Calculate visible range
  const visibleRange = useMemo(() => {
    if (!enabled) {
      return { start: 0, end: items.length - 1 };
    }

    const start = findItemIndex(scrollOffset);
    let end = start;
    let currentHeight = 0;

    // Find end index by adding heights until we exceed container height
    while (end < items.length && currentHeight < containerHeight) {
      currentHeight += getItemHeight(end, items[end]);
      end++;
    }

    return {
      start: Math.max(0, start - overscan),
      end: Math.min(items.length - 1, end + overscan)
    };
  }, [enabled, scrollOffset, containerHeight, findItemIndex, getItemHeight, items, overscan]);

  // Generate virtual items
  const virtualItems = useMemo((): VirtualScrollItem[] => {
    if (!enabled) {
      return items.map((entry, index) => ({
        index,
        entry,
        height: getItemHeight(index, entry),
        offset: 0
      }));
    }

    const { map } = heightMap;
    const result: VirtualScrollItem[] = [];

    for (let i = visibleRange.start; i <= visibleRange.end; i++) {
      if (i < items.length) {
        result.push({
          index: i,
          entry: items[i],
          height: getItemHeight(i, items[i]),
          offset: map.get(i) ?? 0
        });
      }
    }

    return result;
  }, [enabled, items, visibleRange, getItemHeight, heightMap]);

  // Handle scroll events
  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;

    const offset = containerRef.current.scrollTop;
    setScrollOffset(offset);
    setIsScrolling(true);

    // Clear existing timeout
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    // Set scrolling to false after scroll ends
    scrollTimeoutRef.current = setTimeout(() => {
      setIsScrolling(false);
    }, 150);
  }, []);

  // Scroll to specific index
  const scrollToIndex = useCallback((index: number, align: 'start' | 'center' | 'end' = 'start') => {
    if (!containerRef.current || !enabled) return;

    const { map, totalHeight } = heightMap;
    const itemOffset = map.get(Math.max(0, Math.min(index, items.length - 1))) ?? 0;
    const itemHeight = getItemHeight(index, items[index]);
    const containerHeight = containerRef.current.clientHeight;

    let scrollOffset: number;

    switch (align) {
      case 'center':
        scrollOffset = itemOffset - (containerHeight - itemHeight) / 2;
        break;
      case 'end':
        scrollOffset = itemOffset - containerHeight + itemHeight;
        break;
      case 'start':
      default:
        scrollOffset = itemOffset;
        break;
    }

    // Clamp to valid range
    scrollOffset = Math.max(0, Math.min(scrollOffset, totalHeight - containerHeight));
    containerRef.current.scrollTop = scrollOffset;
  }, [enabled, items, heightMap, getItemHeight]);

  // Scroll to specific offset
  const scrollToOffset = useCallback((offset: number) => {
    if (!containerRef.current || !enabled) return;

    const { totalHeight } = heightMap;
    const containerHeight = containerRef.current.clientHeight;
    const maxOffset = Math.max(0, totalHeight - containerHeight);
    const clampedOffset = Math.max(0, Math.min(offset, maxOffset));

    containerRef.current.scrollTop = clampedOffset;
  }, [enabled, heightMap]);

  // Update scroll offset when container height changes
  useEffect(() => {
    if (containerRef.current && enabled) {
      const currentOffset = containerRef.current.scrollTop;
      setScrollOffset(currentOffset);
    }
  }, [containerHeight, enabled]);

  // Auto-scroll to bottom when new items are added (if at bottom)
  useEffect(() => {
    if (enabled && containerRef.current && items.length > 0) {
      const { totalHeight } = heightMap;
      const containerHeight = containerRef.current.clientHeight;
      const maxOffset = Math.max(0, totalHeight - containerHeight);
      const currentOffset = containerRef.current.scrollTop;

      // If we're within 50px of the bottom, scroll to new bottom
      if (currentOffset >= maxOffset - 50) {
        containerRef.current.scrollTop = maxOffset;
      }
    }
  }, [enabled, items.length, heightMap]);

  // Cleanup scroll timeout
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  return {
    virtualItems,
    totalSize: enabled ? heightMap.totalHeight : items.length * (typeof itemHeight === 'number' ? itemHeight : 40),
    scrollToIndex,
    scrollToOffset,
    containerRef,
    isScrolling,
    startIndex: visibleRange.start,
    endIndex: visibleRange.end
  };
};

// Hook for dynamic item heights based on content
export const useDynamicItemHeight = () => {
  const itemHeightsRef = useRef<Map<string, number>>(new Map());
  const measurementContainerRef = useRef<HTMLDivElement>(null);

  const measureItem = useCallback((item: LogEntry, content: string): number => {
    if (!measurementContainerRef.current) return 40;

    const cacheKey = `${item.id}-${item.message.length}`;

    if (itemHeightsRef.current.has(cacheKey)) {
      return itemHeightsRef.current.get(cacheKey)!;
    }

    // Create temporary element for measurement
    const measureElement = document.createElement('div');
    measureElement.style.cssText = `
      position: absolute;
      visibility: hidden;
      width: 100%;
      padding: 8px 12px;
      font-family: monospace;
      font-size: 12px;
      line-height: 1.4;
      white-space: pre-wrap;
      word-wrap: break-word;
    `;

    measureElement.textContent = content;
    measurementContainerRef.current.appendChild(measureElement);

    const height = measureElement.offsetHeight;
    measurementContainerRef.current.removeChild(measureElement);

    // Cache the result
    itemHeightsRef.current.set(cacheKey, height);

    // Limit cache size
    if (itemHeightsRef.current.size > 1000) {
      const keys = Array.from(itemHeightsRef.current.keys());
      keys.slice(0, 500).forEach(key => itemHeightsRef.current.delete(key));
    }

    return Math.max(40, height); // Minimum height
  }, []);

  const clearCache = useCallback(() => {
    itemHeightsRef.current.clear();
  }, []);

  return {
    measureItem,
    clearCache,
    measurementContainerRef
  };
};
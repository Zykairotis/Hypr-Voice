interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class Cache {
  private storage: Map<string, CacheEntry<any>> = new Map();
  private maxSize: number;
  private cleanupInterval: number;

  constructor(maxSize: number = 100, cleanupInterval: number = 60000) {
    this.maxSize = maxSize;
    this.cleanupInterval = cleanupInterval;

    setInterval(() => {
      this.cleanup();
    }, this.cleanupInterval);
  }

  async get<T>(key: string): Promise<T | null> {
    const entry = this.storage.get(key);

    if (!entry) {
      return null;
    }

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.storage.delete(key);
      return null;
    }

    return entry.data;
  }

  async set<T>(key: string, data: T, ttl: number = 300000): Promise<void> {
    if (this.storage.size >= this.maxSize) {
      this.evictOldest();
    }

    this.storage.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  async delete(key: string): Promise<void> {
    this.storage.delete(key);
  }

  async clear(): Promise<void> {
    this.storage.clear();
  }

  async has(key: string): Promise<boolean> {
    const entry = this.storage.get(key);

    if (!entry) {
      return false;
    }

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.storage.delete(key);
      return false;
    }

    return true;
  }

  async getKeys(): Promise<string[]> {
    return Array.from(this.storage.keys());
  }

  private evictOldest(): void {
    let oldestKey: string | null = null;
    let oldestTimestamp = Date.now();

    for (const [key, entry] of this.storage.entries()) {
      if (entry.timestamp < oldestTimestamp) {
        oldestTimestamp = entry.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.storage.delete(oldestKey);
    }
  }

  private cleanup(): void {
    const now = Date.now();

    for (const [key, entry] of this.storage.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.storage.delete(key);
      }
    }
  }

  async getStats(): Promise<{
    size: number;
    maxSize: number;
    hitRate: number;
  }> {
    return {
      size: this.storage.size,
      maxSize: this.maxSize,
      hitRate: 0,
    };
  }
}

const globalCache = new Cache(200, 60000);

export const useCache = () => {
  return {
    get: <T>(key: string): Promise<T | null> => globalCache.get<T>(key),
    set: <T>(key: string, data: T, ttl?: number): Promise<void> => globalCache.set(key, data, ttl),
    delete: (key: string): Promise<void> => globalCache.delete(key),
    clear: (): Promise<void> => globalCache.clear(),
    has: (key: string): Promise<boolean> => globalCache.has(key),
    getKeys: (): Promise<string[]> => globalCache.getKeys(),
    getStats: (): Promise<ReturnType<Cache['getStats']>> => globalCache.getStats(),
  };
};

export { Cache };

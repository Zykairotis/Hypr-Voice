import { useState, useEffect, useCallback } from 'react';
import { useCache } from '../utils/cache';

interface AnalyticsData {
  systemMetrics: any[];
  agentMetrics: any[];
  ttsMetrics: any[];
  vocabularyMetrics: any[];
  historicalMetrics: any[];
  metricList: string[];
  benchmarks: any[];
  abTests: any[];
  alertRules: any[];
  alerts: any[];
  bottlenecks: any[];
  optimizationRecommendations: any[];
  avgResponseTime: number;
  criticalAlerts: number;
}

interface UseAnalyticsDataOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const useAnalyticsData = (options: UseAnalyticsDataOptions = {}) => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { autoRefresh = true, refreshInterval = 5000 } = options;

  const cache = useCache();

  const generateMockData = useCallback((): AnalyticsData => {
    const now = Date.now();
    const systemMetrics = Array.from({ length: 100 }, (_, i) => ({
      timestamp: now - (100 - i) * 60000,
      cpu: {
        overall: 30 + Math.random() * 40,
        perCore: Array.from({ length: 8 }, () => 20 + Math.random() * 60),
        processes: [
          { name: 'chrome', usage: 15 + Math.random() * 10 },
          { name: 'node', usage: 20 + Math.random() * 15 },
          { name: 'python', usage: 10 + Math.random() * 10 },
        ],
      },
      memory: {
        total: 16 * 1024 * 1024 * 1024,
        used: 8 * 1024 * 1024 * 1024 + Math.random() * 4 * 1024 * 1024 * 1024,
        free: 4 * 1024 * 1024 * 1024,
        swapTotal: 8 * 1024 * 1024 * 1024,
        swapUsed: Math.random() * 2 * 1024 * 1024 * 1024,
      },
      disk: {
        readSpeed: Math.random() * 100 * 1024 * 1024,
        writeSpeed: Math.random() * 80 * 1024 * 1024,
        ioTime: 5 + Math.random() * 10,
      },
      network: {
        bytesIn: Math.random() * 10 * 1024 * 1024,
        bytesOut: Math.random() * 5 * 1024 * 1024,
        packetsIn: Math.random() * 1000,
        packetsOut: Math.random() * 500,
      },
      gpu: {
        utilization: 30 + Math.random() * 40,
        memoryUsed: 2 * 1024 * 1024 * 1024,
        memoryTotal: 8 * 1024 * 1024 * 1024,
        temperature: 45 + Math.random() * 20,
      },
      temperature: {
        cpu: 35 + Math.random() * 25,
        gpu: 40 + Math.random() * 20,
        disk: [35, 38, 40],
      },
    }));

    const agentMetrics = Array.from({ length: 20 }, (_, i) => ({
      agentId: `agent-${i + 1}`,
      agentType: ['coder', 'reviewer', 'tester', 'researcher'][i % 4],
      timestamp: now - Math.random() * 3600000,
      responseTime: 200 + Math.random() * 800,
      tasksCompleted: Math.floor(Math.random() * 50),
      tasksSucceeded: 0,
      tasksFailed: 0,
      tokensUsed: Math.floor(Math.random() * 100000),
      efficiency: 60 + Math.random() * 35,
      status: ['idle', 'busy', 'error'][Math.floor(Math.random() * 3)] as any,
      subagents: i % 3 === 0 ? Array.from({ length: 3 }, (_, j) => ({
        id: `subagent-${i}-${j}`,
        performance: 70 + Math.random() * 25,
      })) : undefined,
    })).map(agent => ({
      ...agent,
      tasksSucceeded: agent.tasksCompleted - Math.floor(Math.random() * 5),
      tasksFailed: Math.floor(Math.random() * 5),
    }));

    const ttsMetrics = Array.from({ length: 50 }, (_, i) => ({
      id: `tts-${i + 1}`,
      timestamp: now - Math.random() * 3600000,
      provider: ['OpenAI', 'Azure', 'Google', 'AWS'][Math.floor(Math.random() * 4)],
      voice: `voice-${Math.floor(Math.random() * 5) + 1}`,
      textLength: Math.floor(Math.random() * 500) + 50,
      synthesisTime: 500 + Math.random() * 2000,
      audioGenerationTime: 200 + Math.random() * 1000,
      totalTime: 0,
      success: Math.random() > 0.05,
      quality: 60 + Math.random() * 40,
      cost: 0.1 + Math.random() * 0.5,
    })).map(m => ({ ...m, totalTime: m.synthesisTime + m.audioGenerationTime }));

    const vocabularyMetrics = Array.from({ length: 30 }, (_, i) => ({
      id: `vocab-${i + 1}`,
      timestamp: now - Math.random() * 3600000,
      application: ['Code Editor', 'Browser', 'Terminal', 'IDE'][Math.floor(Math.random() * 4)],
      category: ['Development', 'Web', 'System', 'Productivity'][Math.floor(Math.random() * 4)],
      keywordsMatched: Math.floor(Math.random() * 50) + 10,
      keywordsTotal: 50 + Math.floor(Math.random() * 20),
      matchAccuracy: 80 + Math.random() * 20,
      contextExtracted: Math.floor(Math.random() * 10) + 5,
      contextTotal: 15,
      switchingFrequency: Math.random() * 5,
      customizationImpact: 10 + Math.random() * 30,
      processingTime: 20 + Math.random() * 100,
      success: Math.random() > 0.05,
    }));

    const historicalMetrics = Array.from({ length: 200 }, (_, i) => ({
      timestamp: now - (200 - i) * 3600000,
      value: 50 + Math.random() * 30,
      metric: ['cpu_usage', 'memory_usage', 'response_time'][i % 3],
      metadata: { source: 'system' },
    }));

    const benchmarks = Array.from({ length: 5 }, (_, i) => ({
      id: `benchmark-${i + 1}`,
      name: `Benchmark ${i + 1}`,
      timestamp: now - Math.random() * 30 * 24 * 3600000,
      metrics: {
        throughput: 1000 + Math.random() * 500,
        latency: 50 + Math.random() * 20,
        accuracy: 90 + Math.random() * 10,
      },
      category: ['Performance', 'Accuracy', 'Scalability'][i % 3],
      configuration: {
        version: `v${i + 1}.0`,
        settings: 'default',
      },
      environment: ['production', 'staging'][i % 2],
    }));

    const abTests = Array.from({ length: 3 }, (_, i) => ({
      id: `abtest-${i + 1}`,
      name: `A/B Test ${i + 1}`,
      startDate: now - Math.random() * 14 * 24 * 3600000,
      endDate: Math.random() > 0.5 ? now - Math.random() * 7 * 24 * 3600000 : undefined,
      variantA: {
        name: 'Control',
        metrics: {
          conversion: 10 + Math.random() * 5,
          engagement: 50 + Math.random() * 20,
        },
      },
      variantB: {
        name: 'Variant',
        metrics: {
          conversion: 12 + Math.random() * 5,
          engagement: 55 + Math.random() * 20,
        },
      },
      status: ['running', 'completed', 'paused'][i % 3] as any,
      winner: i % 3 === 2 ? 'B' : i % 3 === 1 ? 'A' : 'inconclusive',
    }));

    const alertRules = Array.from({ length: 10 }, (_, i) => ({
      id: `rule-${i + 1}`,
      name: `Alert Rule ${i + 1}`,
      description: `Monitor ${['CPU', 'Memory', 'Response Time', 'Error Rate'][i % 4]} metrics`,
      metric: ['cpu_usage', 'memory_usage', 'response_time', 'error_rate'][i % 4],
      condition: 'greater_than' as const,
      threshold: [70, 75, 500, 5][i % 4],
      duration: 60,
      severity: ['info', 'warning', 'critical'][i % 3] as any,
      enabled: Math.random() > 0.2,
      actions: [{ type: 'email', target: 'admin@example.com', enabled: true }],
      tags: ['monitoring', 'production'],
    }));

    const alerts = Array.from({ length: 15 }, (_, i) => ({
      id: `alert-${i + 1}`,
      ruleId: `rule-${(i % 5) + 1}`,
      ruleName: `Alert Rule ${(i % 5) + 1}`,
      timestamp: now - Math.random() * 3600000,
      severity: ['info', 'warning', 'critical'][i % 3] as any,
      message: `Threshold exceeded for metric`,
      value: 50 + Math.random() * 50,
      acknowledged: Math.random() > 0.7,
      resolved: Math.random() > 0.8,
    }));

    const bottlenecks = Array.from({ length: 8 }, (_, i) => ({
      id: `bottleneck-${i + 1}`,
      type: ['cpu', 'memory', 'disk', 'network', 'database', 'api'][i % 6] as any,
      severity: ['low', 'medium', 'high', 'critical'][i % 4] as any,
      description: `Performance bottleneck detected in ${['CPU', 'Memory', 'Disk', 'Network', 'Database', 'API'][i % 6]} system`,
      impact: {
        performance: 20 + Math.random() * 30,
        throughput: 15 + Math.random() * 25,
        latency: 10 + Math.random() * 40,
      },
      affectedComponents: ['Component A', 'Component B'],
      recommendation: {
        priority: ['low', 'medium', 'high'][i % 3] as any,
        action: `Optimize ${['CPU usage', 'Memory allocation', 'Disk I/O', 'Network throughput', 'Database queries', 'API response'][i % 6]}`,
        expectedImprovement: '20-30% performance increase',
        effort: ['low', 'medium', 'high'][i % 3] as any,
        estimatedTime: ['1 day', '1 week', '2 weeks'][i % 3],
      },
    }));

    const optimizationRecommendations = Array.from({ length: 12 }, (_, i) => ({
      id: `rec-${i + 1}`,
      category: ['Performance', 'Scalability', 'Cost', 'Security'][i % 4],
      title: `Optimization ${i + 1}`,
      description: `Recommendation to improve ${['system performance', 'resource usage', 'cost efficiency', 'security posture'][i % 4]}`,
      currentState: 'Current implementation shows suboptimal performance',
      targetState: 'Optimized configuration with improved metrics',
      benefits: [
        '20% performance improvement',
        'Reduced resource consumption',
        'Better user experience',
      ],
      implementation: {
        steps: [
          'Analyze current configuration',
          'Implement optimization changes',
          'Test and validate improvements',
        ],
        complexity: ['low', 'medium', 'high'][i % 3] as any,
        resources: ['1 developer', '2 days', 'testing environment'],
        risks: ['Minimal', 'Medium', 'High'][i % 3] === 'Low' ? [] : ['Potential downtime', 'Data migration required'],
      },
      metrics: [
        { metric: 'Response Time', current: 500, target: 300, unit: 'ms' },
        { metric: 'Throughput', current: 1000, target: 1500, unit: 'req/s' },
      ],
    }));

    return {
      systemMetrics,
      agentMetrics,
      ttsMetrics,
      vocabularyMetrics,
      historicalMetrics,
      metricList: ['cpu_usage', 'memory_usage', 'response_time', 'error_rate', 'throughput'],
      benchmarks,
      abTests,
      alertRules,
      alerts,
      bottlenecks,
      optimizationRecommendations,
      avgResponseTime: 350,
      criticalAlerts: 3,
    };
  }, []);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const cacheKey = 'analytics-data';
      const cached = await cache.get(cacheKey);

      if (cached) {
        setData(cached);
        setLoading(false);
        return;
      }

      await new Promise((resolve) => setTimeout(resolve, 800));

      const mockData = generateMockData();

      await cache.set(cacheKey, mockData, 60000);

      setData(mockData);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch analytics data'));
      console.error('Error fetching analytics data:', err);
    } finally {
      setLoading(false);
    }
  }, [cache, generateMockData]);

  const refresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchData]);

  return {
    data,
    loading,
    error,
    refresh,
  };
};

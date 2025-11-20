import { MetricDataPoint } from './dataAggregator';

export interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number[];
    processes: Array<{ name: string; pid: number; usage: number }>;
  };
  memory: {
    total: number;
    used: number;
    free: number;
    buffers: number;
    cached: number;
    swapTotal: number;
    swapUsed: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
    io: {
      read: number;
      write: number;
    };
  };
  network: {
    bytesIn: number;
    bytesOut: number;
    packetsIn: number;
    packetsOut: number;
    errors: number;
  };
  gpu?: {
    utilization: number;
    memoryUsed: number;
    memoryTotal: number;
    temperature: number;
    powerUsage: number;
  };
  temperature: {
    cpu: number;
    gpu?: number;
    disk: number[];
  };
}

export interface AgentMetrics {
  agentId: string;
  type: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  metrics: {
    responseTime: number;
    tasksCompleted: number;
    tasksSucceeded: number;
    tasksFailed: number;
    tokensUsed: number;
    efficiency: number;
    errorRate: number;
    uptime: number;
  };
  resourceUsage: {
    cpu: number;
    memory: number;
  };
}

export interface TTSMetrics {
  requestId: string;
  provider: string;
  voice: string;
  textLength: number;
  synthesisTime: number;
  audioGenerationTime: number;
  totalTime: number;
  success: boolean;
  errorMessage?: string;
  quality?: number;
  cost: number;
  timestamp: number;
}

export interface VocabularyMetrics {
  requestId: string;
  application: string;
  category: string;
  context: string;
  keywordsMatched: number;
  keywordsTotal: number;
  matchAccuracy: number;
  contextExtracted: number;
  processingTime: number;
  success: boolean;
  timestamp: number;
}

class MetricsCollector {
  private static instance: MetricsCollector;
  private systemMetricsBuffer: MetricDataPoint[] = [];
  private agentMetricsBuffer: AgentMetrics[] = [];
  private ttsMetricsBuffer: TTSMetrics[] = [];
  private vocabularyMetricsBuffer: VocabularyMetrics[] = [];
  private readonly maxBufferSize = 10000;

  private constructor() {}

  public static getInstance(): MetricsCollector {
    if (!MetricsCollector.instance) {
      MetricsCollector.instance = new MetricsCollector();
    }
    return MetricsCollector.instance;
  }

  public async collectSystemMetrics(): Promise<SystemMetrics> {
    const mockMetrics: SystemMetrics = {
      cpu: {
        usage: 30 + Math.random() * 40,
        cores: Array.from({ length: 8 }, () => 20 + Math.random() * 60),
        processes: [
          { name: 'node', pid: 1234, usage: 15 + Math.random() * 10 },
          { name: 'chrome', pid: 5678, usage: 20 + Math.random() * 15 },
          { name: 'python', pid: 9012, usage: 10 + Math.random() * 10 },
          { name: 'docker', pid: 3456, usage: 5 + Math.random() * 5 },
        ],
      },
      memory: {
        total: 16 * 1024 * 1024 * 1024,
        used: 8 * 1024 * 1024 * 1024 + Math.random() * 4 * 1024 * 1024 * 1024,
        free: 4 * 1024 * 1024 * 1024,
        buffers: 512 * 1024 * 1024,
        cached: 1024 * 1024 * 1024,
        swapTotal: 8 * 1024 * 1024 * 1024,
        swapUsed: Math.random() * 2 * 1024 * 1024 * 1024,
      },
      disk: {
        total: 500 * 1024 * 1024 * 1024,
        used: 300 * 1024 * 1024 * 1024,
        free: 200 * 1024 * 1024 * 1024,
        io: {
          read: Math.random() * 100 * 1024 * 1024,
          write: Math.random() * 80 * 1024 * 1024,
        },
      },
      network: {
        bytesIn: Math.random() * 10 * 1024 * 1024,
        bytesOut: Math.random() * 5 * 1024 * 1024,
        packetsIn: Math.random() * 1000,
        packetsOut: Math.random() * 500,
        errors: Math.random() * 5,
      },
      gpu: {
        utilization: 30 + Math.random() * 40,
        memoryUsed: 2 * 1024 * 1024 * 1024,
        memoryTotal: 8 * 1024 * 1024 * 1024,
        temperature: 45 + Math.random() * 20,
        powerUsage: 50 + Math.random() * 100,
      },
      temperature: {
        cpu: 35 + Math.random() * 25,
        gpu: 40 + Math.random() * 20,
        disk: [35, 38, 40, 42],
      },
    };

    this.addToBuffer(
      this.systemMetricsBuffer,
      {
        timestamp: Date.now(),
        value: mockMetrics.cpu.usage,
        tags: { type: 'cpu', metric: 'usage' },
      },
      this.maxBufferSize
    );

    return mockMetrics;
  }

  public async collectAgentMetrics(): Promise<AgentMetrics[]> {
    const agents: AgentMetrics[] = Array.from({ length: 20 }, (_, i) => ({
      agentId: `agent-${i + 1}`,
      type: ['coder', 'reviewer', 'tester', 'researcher'][i % 4],
      status: ['idle', 'busy', 'error', 'offline'][Math.floor(Math.random() * 4)] as any,
      metrics: {
        responseTime: 200 + Math.random() * 800,
        tasksCompleted: Math.floor(Math.random() * 100),
        tasksSucceeded: 0,
        tasksFailed: Math.floor(Math.random() * 5),
        tokensUsed: Math.floor(Math.random() * 100000),
        efficiency: 60 + Math.random() * 35,
        errorRate: Math.random() * 5,
        uptime: Date.now() - Math.random() * 30 * 24 * 3600000,
      },
      resourceUsage: {
        cpu: Math.random() * 50,
        memory: Math.random() * 1024 * 1024 * 1024,
      },
    }));

    agents.forEach((agent) => {
      agent.metrics.tasksSucceeded = agent.metrics.tasksCompleted - agent.metrics.tasksFailed;
    });

    return agents;
  }

  public async collectTTSMetrics(): Promise<TTSMetrics[]> {
    const metrics: TTSMetrics[] = Array.from({ length: 50 }, (_, i) => {
      const synthesisTime = 500 + Math.random() * 2000;
      const audioGenerationTime = 200 + Math.random() * 1000;
      const totalTime = synthesisTime + audioGenerationTime;
      const textLength = Math.floor(Math.random() * 500) + 50;
      const success = Math.random() > 0.05;

      return {
        requestId: `tts-${i + 1}`,
        provider: ['OpenAI', 'Azure', 'Google', 'AWS'][Math.floor(Math.random() * 4)],
        voice: `voice-${Math.floor(Math.random() * 5) + 1}`,
        textLength,
        synthesisTime,
        audioGenerationTime,
        totalTime,
        success,
        errorMessage: success ? undefined : 'Synthesis failed',
        quality: success ? 60 + Math.random() * 40 : undefined,
        cost: 0.1 + Math.random() * 0.5,
        timestamp: Date.now() - Math.random() * 3600000,
      };
    });

    return metrics;
  }

  public async collectVocabularyMetrics(): Promise<VocabularyMetrics[]> {
    const metrics: VocabularyMetrics[] = Array.from({ length: 30 }, (_, i) => ({
      requestId: `vocab-${i + 1}`,
      application: ['Code Editor', 'Browser', 'Terminal', 'IDE'][Math.floor(Math.random() * 4)],
      category: ['Development', 'Web', 'System', 'Productivity'][Math.floor(Math.random() * 4)],
      context: 'Current application context',
      keywordsMatched: Math.floor(Math.random() * 50) + 10,
      keywordsTotal: 50 + Math.floor(Math.random() * 20),
      matchAccuracy: 80 + Math.random() * 20,
      contextExtracted: Math.floor(Math.random() * 10) + 5,
      processingTime: 20 + Math.random() * 100,
      success: Math.random() > 0.05,
      timestamp: Date.now() - Math.random() * 3600000,
    }));

    return metrics;
  }

  public getSystemMetricsBuffer(): MetricDataPoint[] {
    return [...this.systemMetricsBuffer];
  }

  public getAgentMetricsBuffer(): AgentMetrics[] {
    return [...this.agentMetricsBuffer];
  }

  public getTTSMetricsBuffer(): TTSMetrics[] {
    return [...this.ttsMetricsBuffer];
  }

  public getVocabularyMetricsBuffer(): VocabularyMetrics[] {
    return [...this.vocabularyMetricsBuffer];
  }

  public clearBuffers(): void {
    this.systemMetricsBuffer = [];
    this.agentMetricsBuffer = [];
    this.ttsMetricsBuffer = [];
    this.vocabularyMetricsBuffer = [];
  }

  public exportMetrics(format: 'json' | 'csv' | 'prometheus'): string {
    const data = {
      system: this.getSystemMetricsBuffer(),
      agents: this.getAgentMetricsBuffer(),
      tts: this.getTTSMetricsBuffer(),
      vocabulary: this.getVocabularyMetricsBuffer(),
      timestamp: Date.now(),
    };

    if (format === 'json') {
      return JSON.stringify(data, null, 2);
    }

    if (format === 'csv') {
      const rows = [
        'type,timestamp,metric,value,tags',
        ...this.systemMetricsBuffer.map((m) => {
          const tags = m.tags ? JSON.stringify(m.tags) : '';
          return `system,${m.timestamp},${m.tags?.metric || 'value'},${m.value},${tags}`;
        }),
      ];
      return rows.join('\n');
    }

    if (format === 'prometheus') {
      const lines = this.systemMetricsBuffer
        .map((m) => {
          const metricName = m.tags?.metric || 'value';
          const tags = Object.entries(m.tags || {})
            .map(([k, v]) => `${k}="${v}"`)
            .join(',');
          return `system_${metricName}{${tags}} ${m.value} ${m.timestamp}`;
        })
        .join('\n');
      return lines;
    }

    return '';
  }

  private addToBuffer<T>(buffer: T[], item: T, maxSize: number): void {
    buffer.push(item);
    if (buffer.length > maxSize) {
      buffer.shift();
    }
  }
}

export const metricsCollector = MetricsCollector.getInstance();

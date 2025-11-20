# Analytics Dashboard Components

Comprehensive performance analytics and system monitoring dashboard with advanced metrics and insights.

## Features

### 1. System Performance Metrics
- **CPU Usage**: Overall and per-core utilization monitoring
- **Memory Usage**: RAM, swap, buffers, and cache tracking
- **Disk I/O**: Read/write speeds and I/O time monitoring
- **Network**: Throughput, packets, and error tracking
- **GPU Utilization**: Memory usage, temperature, and power
- **Temperature**: CPU, GPU, and disk temperature monitoring

### 2. Agent Performance Analytics
- **Response Times**: Real-time and historical tracking
- **Task Completion**: Success/failure rates and volumes
- **Token Usage**: Per-agent and aggregate tracking
- **Efficiency Scores**: Performance metrics and comparisons
- **Subagent Performance**: Hierarchical agent monitoring

### 3. TTS Performance Tracking
- **Synthesis Speed**: Characters per second metrics
- **Audio Generation**: Processing time breakdown
- **Provider Comparison**: Performance across services
- **Quality Metrics**: Audio quality assessment
- **Cost Analysis**: Per-request and aggregate costs

### 4. Vocabulary Analytics
- **Match Accuracy**: Keyword matching effectiveness
- **Context Extraction**: Semantic analysis metrics
- **Application Performance**: Per-app statistics
- **Switching Frequency**: Vocabulary transition tracking
- **Customization Impact**: User adaptation metrics

### 5. Real-Time Dashboards
- **Live Widgets**: Auto-refreshing metric displays
- **Threshold Alerts**: Configurable warning/critical levels
- **Interactive Charts**: Real-time data visualization
- **WebSocket Streaming**: Live data updates

### 6. Historical Data Analysis
- **Time-Series Data**: Long-term trend analysis
- **Aggregations**: Minute, hour, day, week, month
- **Pattern Recognition**: Usage patterns and anomalies
- **Capacity Planning**: Growth projections and recommendations
- **Regression Detection**: Performance degradation alerts

### 7. Comparative Analytics
- **Benchmarking**: Before/after comparisons
- **A/B Testing**: Variant analysis and winners
- **Configuration Comparison**: Parameter impact analysis
- **Version Tracking**: Performance across releases

### 8. Custom Metrics & Alerts
- **Rule Engine**: Flexible alert condition definitions
- **Multiple Channels**: Email, SMS, Slack, webhooks
- **Alert History**: Complete audit trail
- **Acknowledgment Workflow**: Incident management

### 9. Performance Optimization
- **Bottleneck Identification**: Automatic detection
- **Recommendations**: Actionable improvement suggestions
- **Impact Analysis**: Before/after projections
- **Implementation Guides**: Step-by-step instructions

### 10. Export & Reporting
- **Multiple Formats**: PDF, CSV, JSON, HTML, XLSX
- **Custom Templates**: Executive, technical, detailed
- **Scheduled Reports**: Automated delivery
- **API Access**: Programmatic data retrieval

## Architecture

### Components Structure

```
analytics/
├── AnalyticsDashboard.tsx       # Main orchestration component
├── SystemPerformance.tsx        # System metrics visualization
├── AgentPerformance.tsx         # Agent analytics
├── TTSPerformance.tsx           # TTS metrics tracking
├── VocabularyAnalytics.tsx      # Vocabulary analysis
├── RealTimeDashboard.tsx        # Live monitoring
├── HistoricalAnalysis.tsx       # Time-series analysis
├── ComparativeAnalytics.tsx     # Benchmarking
├── AlertsEngine.tsx             # Alert management
├── PerformanceOptimization.tsx  # Optimization insights
├── ExportReports.tsx            # Report generation
├── hooks/
│   ├── useWebSocket.ts         # WebSocket integration
│   └── useAnalyticsData.ts     # Data fetching
└── utils/
    ├── cache.ts                # Caching layer
    ├── dataAggregator.ts       # Data processing
    ├── metricsCollector.ts     # Metrics gathering
    └── exportUtils.ts          # Export functions
```

### Data Flow

1. **Metrics Collection**: Real-time system and application metrics
2. **Data Aggregation**: Time-series processing and statistical analysis
3. **Caching**: In-memory cache for performance optimization
4. **Visualization**: Interactive charts and dashboards
5. **Alerting**: Threshold-based notification system
6. **Export**: Multiple format report generation

## Usage

### Basic Dashboard

```tsx
import { AnalyticsDashboard } from '@/components/analytics';

function App() {
  return <AnalyticsDashboard />;
}
```

### Individual Components

```tsx
import { SystemPerformance } from '@/components/analytics';

function SystemView() {
  return <SystemPerformance data={metricsData} realTime={true} />;
}
```

### Custom Metrics

```tsx
import { AlertsEngine } from '@/components/analytics';

<AlertsEngine
  rules={alertRules}
  alerts={activeAlerts}
  onRuleCreate={(rule) => createRule(rule)}
  onAlertAcknowledge={(id) => acknowledgeAlert(id)}
/>
```

## WebSocket Integration

The dashboard supports real-time updates via WebSocket:

```typescript
import { useWebSocket } from '@/components/analytics/hooks/useWebSocket';

const { isConnected, lastMessage } = useWebSocket('ws://localhost:8080/metrics', {
  onMessage: (message) => {
    // Handle real-time update
    updateMetrics(message.data);
  },
});
```

## Data Export

Export analytics data in multiple formats:

```typescript
import { exportReport } from '@/components/analytics/utils/exportUtils';

const result = await exportReport({
  format: 'pdf',
  metrics: ['cpu_usage', 'memory_usage'],
  dateRange: { start: startDate, end: endDate },
  includeCharts: true,
  template: 'executive',
}, data);
```

## Caching

Automatic caching for improved performance:

```typescript
import { useCache } from '@/components/analytics/utils/cache';

const cache = useCache();

await cache.set('metrics-key', data, 60000);
const cached = await cache.get('metrics-key');
```

## Browser Support

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- Modern mobile browsers

## Performance

- Initial load: < 2s
- Dashboard update: < 500ms
- Memory usage: < 100MB
- Real-time latency: < 100ms

## Dependencies

- React 18+
- Recharts for visualization
- WebSocket API
- Modern browser APIs (IntersectionObserver, etc.)

## License

Internal use - Hypr-Voice Project

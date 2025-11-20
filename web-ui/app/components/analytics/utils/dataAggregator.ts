export interface MetricDataPoint {
  timestamp: number;
  value: number;
  tags?: Record<string, string>;
}

export interface AggregationResult {
  timestamp: number;
  value: number;
  count: number;
  min: number;
  max: number;
  avg: number;
  p95?: number;
  p99?: number;
}

export const aggregateTimeSeries = (
  data: MetricDataPoint[],
  interval: number,
  method: 'avg' | 'sum' | 'min' | 'max' | 'count' | 'p95' | 'p99' = 'avg'
): AggregationResult[] => {
  const buckets = new Map<number, number[]>();

  data.forEach((point) => {
    const bucketKey = Math.floor(point.timestamp / interval) * interval;

    if (!buckets.has(bucketKey)) {
      buckets.set(bucketKey, []);
    }

    buckets.get(bucketKey)!.push(point.value);
  });

  const results: AggregationResult[] = [];

  for (const [timestamp, values] of buckets.entries()) {
    const sorted = [...values].sort((a, b) => a - b);
    const count = values.length;

    let value: number;
    switch (method) {
      case 'sum':
        value = values.reduce((sum, v) => sum + v, 0);
        break;
      case 'min':
        value = Math.min(...values);
        break;
      case 'max':
        value = Math.max(...values);
        break;
      case 'count':
        value = count;
        break;
      case 'p95':
        value = sorted[Math.floor(sorted.length * 0.95)] || 0;
        break;
      case 'p99':
        value = sorted[Math.floor(sorted.length * 0.99)] || 0;
        break;
      case 'avg':
      default:
        value = values.reduce((sum, v) => sum + v, 0) / count;
        break;
    }

    results.push({
      timestamp,
      value,
      count,
      min: sorted[0] || 0,
      max: sorted[sorted.length - 1] || 0,
      avg: values.reduce((sum, v) => sum + v, 0) / count,
      p95: sorted[Math.floor(sorted.length * 0.95)] || undefined,
      p99: sorted[Math.floor(sorted.length * 0.99)] || undefined,
    });
  }

  return results.sort((a, b) => a.timestamp - b.timestamp);
};

export const calculateMovingAverage = (
  data: MetricDataPoint[],
  windowSize: number
): MetricDataPoint[] => {
  const result: MetricDataPoint[] = [];

  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - windowSize + 1);
    const window = data.slice(start, i + 1);

    const avg = window.reduce((sum, point) => sum + point.value, 0) / window.length;

    result.push({
      timestamp: data[i].timestamp,
      value: avg,
      tags: data[i].tags,
    });
  }

  return result;
};

export const detectAnomalies = (
  data: MetricDataPoint[],
  threshold: number = 2
): MetricDataPoint[] => {
  const values = data.map((d) => d.value);
  const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
  const variance =
    values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
  const stdDev = Math.sqrt(variance);

  return data.filter((point) => {
    const zScore = Math.abs((point.value - mean) / stdDev);
    return zScore > threshold;
  });
};

export const calculatePercentile = (
  data: MetricDataPoint[],
  percentile: number
): number => {
  const sorted = [...data].sort((a, b) => a.value - b.value);
  const index = Math.ceil((percentile / 100) * sorted.length) - 1;
  return sorted[index]?.value || 0;
};

export const comparePeriods = (
  current: MetricDataPoint[],
  previous: MetricDataPoint[],
  metric: string
): {
  metric: string;
  currentAvg: number;
  previousAvg: number;
  change: number;
  changePercent: number;
} => {
  const currentAvg = current.reduce((sum, p) => sum + p.value, 0) / current.length;
  const previousAvg = previous.reduce((sum, p) => sum + p.value, 0) / previous.length;

  const change = currentAvg - previousAvg;
  const changePercent = ((change / previousAvg) * 100);

  return {
    metric,
    currentAvg,
    previousAvg,
    change,
    changePercent,
  };
};

export const groupByTag = (
  data: MetricDataPoint[],
  tagKey: string
): Record<string, MetricDataPoint[]> => {
  return data.reduce((groups, point) => {
    const tagValue = point.tags?.[tagKey] || 'unknown';

    if (!groups[tagValue]) {
      groups[tagValue] = [];
    }

    groups[tagValue].push(point);
    return groups;
  }, {} as Record<string, MetricDataPoint[]>);
};

export const calculateCorrelation = (
  series1: MetricDataPoint[],
  series2: MetricDataPoint[]
): number => {
  if (series1.length !== series2.length) {
    throw new Error('Series must have the same length');
  }

  const n = series1.length;
  const sum1 = series1.reduce((sum, p) => sum + p.value, 0);
  const sum2 = series2.reduce((sum, p) => sum + p.value, 0);
  const sum1Sq = series1.reduce((sum, p) => sum + p.value * p.value, 0);
  const sum2Sq = series2.reduce((sum, p) => sum + p.value * p.value, 0);
  const pSum = series1.reduce((sum, p, i) => sum + p.value * series2[i].value, 0);

  const num = pSum - (sum1 * sum2 / n);
  const den = Math.sqrt((sum1Sq - sum1 * sum1 / n) * (sum2Sq - sum2 * sum2 / n));

  return den === 0 ? 0 : num / den;
};

export const resampleData = (
  data: MetricDataPoint[],
  targetInterval: number,
  method: 'avg' | 'sum' | 'interpolate' = 'avg'
): MetricDataPoint[] => {
  if (data.length === 0) return [];

  const startTime = Math.floor(data[0].timestamp / targetInterval) * targetInterval;
  const endTime = Math.ceil(data[data.length - 1].timestamp / targetInterval) * targetInterval;

  const result: MetricDataPoint[] = [];
  let dataIndex = 0;

  for (let timestamp = startTime; timestamp <= endTime; timestamp += targetInterval) {
    const pointsInInterval: MetricDataPoint[] = [];

    while (
      dataIndex < data.length &&
      data[dataIndex].timestamp < timestamp + targetInterval
    ) {
      if (data[dataIndex].timestamp >= timestamp) {
        pointsInInterval.push(data[dataIndex]);
      }
      dataIndex++;
    }

    let value: number;

    switch (method) {
      case 'sum':
        value = pointsInInterval.reduce((sum, p) => sum + p.value, 0);
        break;
      case 'interpolate':
        if (pointsInInterval.length === 0) {
          value = dataIndex > 0 ? data[dataIndex - 1].value : 0;
        } else if (pointsInInterval.length === 1) {
          value = pointsInInterval[0].value;
        } else {
          value =
            pointsInInterval.reduce((sum, p) => sum + p.value, 0) / pointsInInterval.length;
        }
        break;
      case 'avg':
      default:
        value =
          pointsInInterval.length > 0
            ? pointsInInterval.reduce((sum, p) => sum + p.value, 0) /
              pointsInInterval.length
            : 0;
        break;
    }

    result.push({
      timestamp,
      value,
    });
  }

  return result;
};

export const calculateTrend = (data: MetricDataPoint[]): {
  slope: number;
  intercept: number;
  correlation: number;
  direction: 'increasing' | 'decreasing' | 'stable';
} => {
  if (data.length < 2) {
    return { slope: 0, intercept: 0, correlation: 0, direction: 'stable' };
  }

  const n = data.length;
  const sumX = data.reduce((sum, _, i) => sum + i, 0);
  const sumY = data.reduce((sum, p) => sum + p.value, 0);
  const sumXY = data.reduce((sum, p, i) => sum + p.value * i, 0);
  const sumX2 = data.reduce((sum, _, i) => sum + i * i, 0);

  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  const correlation = calculateCorrelation(
    data,
    data.map((_, i) => ({ timestamp: 0, value: i }))
  );

  const direction =
    Math.abs(slope) < 0.1
      ? 'stable'
      : slope > 0
      ? 'increasing'
      : 'decreasing';

  return { slope, intercept, correlation, direction };
};

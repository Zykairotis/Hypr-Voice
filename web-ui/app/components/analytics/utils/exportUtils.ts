import { MetricDataPoint } from './dataAggregator';

export interface ExportOptions {
  format: 'json' | 'csv' | 'xlsx' | 'pdf' | 'html';
  metrics: string[];
  dateRange: {
    start: Date;
    end: Date;
  };
  includeCharts: boolean;
  includeStatistics: boolean;
  template: 'executive' | 'technical' | 'detailed' | 'summary';
}

export interface ExportResult {
  success: boolean;
  fileName: string;
  mimeType: string;
  data: string | Blob;
  size: number;
  downloadUrl?: string;
}

export const exportToJSON = (
  data: any[],
  fileName: string = `export-${Date.now()}.json`
): ExportResult => {
  try {
    const jsonData = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    return {
      success: true,
      fileName,
      mimeType: 'application/json',
      data: blob,
      size: blob.size,
      downloadUrl: url,
    };
  } catch (error) {
    return {
      success: false,
      fileName,
      mimeType: 'application/json',
      data: '',
      size: 0,
    };
  }
};

export const exportToCSV = (
  data: any[],
  fileName: string = `export-${Date.now()}.csv`
): ExportResult => {
  try {
    if (!data || data.length === 0) {
      throw new Error('No data to export');
    }

    const headers = Object.keys(data[0]);
    const csvRows = [
      headers.join(','),
      ...data.map((row) =>
        headers
          .map((header) => {
            const value = row[header];
            if (typeof value === 'object' && value !== null) {
              return `"${JSON.stringify(value).replace(/"/g, '""')}"`;
            }
            return `"${String(value).replace(/"/g, '""')}"`;
          })
          .join(',')
      ),
    ];

    const csvData = csvRows.join('\n');
    const blob = new Blob([csvData], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);

    return {
      success: true,
      fileName,
      mimeType: 'text/csv',
      data: blob,
      size: blob.size,
      downloadUrl: url,
    };
  } catch (error) {
    return {
      success: false,
      fileName,
      mimeType: 'text/csv',
      data: '',
      size: 0,
    };
  }
};

export const exportToHTML = (
  data: {
    title: string;
    metrics: MetricDataPoint[];
    statistics?: any;
    charts?: string[];
  },
  fileName: string = `report-${Date.now()}.html`
): ExportResult => {
  try {
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${data.title}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        h1, h2, h3 {
            color: #1a1a1a;
        }
        .metric-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 16px 0;
        }
        .stat-item {
            background: #f5f5f5;
            padding: 12px;
            border-radius: 6px;
        }
        .stat-label {
            font-size: 0.875rem;
            color: #666;
        }
        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #1a1a1a;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }
        th, td {
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        th {
            background-color: #f5f5f5;
            font-weight: 600;
        }
        .chart-container {
            margin: 16px 0;
            padding: 16px;
            background: #fafafa;
            border-radius: 8px;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 0.875rem;
        }
    </style>
</head>
<body>
    <h1>${data.title}</h1>
    <p>Generated on: ${new Date().toLocaleString()}</p>

    ${data.statistics ? `
    <h2>Statistics</h2>
    <div class="stat-grid">
        ${Object.entries(data.statistics)
          .map(
            ([key, value]) => `
        <div class="stat-item">
            <div class="stat-label">${key}</div>
            <div class="stat-value">${value}</div>
        </div>
        `
          )
          .join('')}
    </div>
    ` : ''}

    <h2>Metrics Data</h2>
    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            ${data.metrics
              .slice(0, 1000)
              .map(
                (metric) => `
            <tr>
                <td>${new Date(metric.timestamp).toLocaleString()}</td>
                <td>${metric.value}</td>
            </tr>
            `
              )
              .join('')}
        </tbody>
    </table>

    ${data.charts ? `
    <h2>Charts</h2>
    ${data.charts.map((chart) => `<div class="chart-container">${chart}</div>`).join('')}
    ` : ''}

    <div class="footer">
        <p>Generated by Analytics Dashboard</p>
    </div>
</body>
</html>
    `;

    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);

    return {
      success: true,
      fileName,
      mimeType: 'text/html',
      data: blob,
      size: blob.size,
      downloadUrl: url,
    };
  } catch (error) {
    return {
      success: false,
      fileName,
      mimeType: 'text/html',
      data: '',
      size: 0,
    };
  }
};

export const downloadFile = (result: ExportResult): void => {
  if (!result.success || !result.downloadUrl) {
    console.error('Export failed or no download URL available');
    return;
  }

  const link = document.createElement('a');
  link.href = result.downloadUrl;
  link.download = result.fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  setTimeout(() => {
    URL.revokeObjectURL(result.downloadUrl!);
  }, 100);
};

export const exportReport = async (
  options: ExportOptions,
  data: any[]
): Promise<ExportResult> => {
  const fileName = `analytics-report-${Date.now()}.${options.format}`;

  switch (options.format) {
    case 'json':
      return exportToJSON(data, fileName);
    case 'csv':
      return exportToCSV(data, fileName);
    case 'html':
      return exportToHTML(
        {
          title: 'Analytics Report',
          metrics: data as MetricDataPoint[],
          includeStatistics: options.includeStatistics,
        },
        fileName
      );
    case 'xlsx':
    case 'pdf':
      return {
        success: false,
        fileName,
        mimeType: options.format === 'xlsx' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'application/pdf',
        data: '',
        size: 0,
      };
    default:
      return {
        success: false,
        fileName,
        mimeType: 'application/octet-stream',
        data: '',
        size: 0,
      };
  }
};

export const scheduleReport = async (
  options: ExportOptions & {
    schedule: 'daily' | 'weekly' | 'monthly';
    recipients: string[];
  }
): Promise<{ success: boolean; scheduleId: string }> => {
  const scheduleId = `schedule-${Date.now()}`;

  console.log('Scheduling report:', {
    ...options,
    scheduleId,
  });

  await new Promise((resolve) => setTimeout(resolve, 500));

  return {
    success: true,
    scheduleId,
  };
};

import { NextRequest, NextResponse } from 'next/server';
import { ContextAnalytics } from '@/app/components/context/types';

export async function GET(request: NextRequest) {
  try {
    // Mock analytics data - replace with actual implementation
    const analytics: ContextAnalytics = {
      sessionMetrics: {
        totalCommands: 45,
        totalClipboardEntries: 28,
        activeTime: 10800,
        mostProductiveHour: 14,
      },
      keywordFrequency: [
        { keyword: 'ContextManager', count: 15, sources: ['shell', 'clipboard'] },
        { keyword: 'TypeScript', count: 12, sources: ['application', 'clipboard'] },
        { keyword: 'React', count: 10, sources: ['clipboard', 'application'] },
        { keyword: 'WebSocket', count: 8, sources: ['shell', 'application'] },
        { keyword: 'useState', count: 7, sources: ['clipboard'] },
        { keyword: 'Component', count: 6, sources: ['application', 'clipboard'] },
        { keyword: 'ContextDashboard', count: 5, sources: ['shell'] },
        { keyword: 'ClipboardManager', count: 5, sources: ['shell'] },
        { keyword: 'ShellHistoryManager', count: 4, sources: ['shell'] },
        { keyword: 'ApplicationDetector', count: 4, sources: ['shell'] },
      ],
      applicationUsage: [
        { name: 'VSCode', timeSpent: 7200, category: 'editor' },
        { name: 'Terminal', timeSpent: 3600, category: 'terminal' },
        { name: 'Chrome', timeSpent: 5400, category: 'browser' },
        { name: 'Slack', timeSpent: 1800, category: 'communication' },
        { name: 'FileManager', timeSpent: 900, category: 'system' },
      ],
      commandPatterns: [
        { pattern: 'git', frequency: 8 },
        { pattern: 'npm', frequency: 6 },
        { pattern: 'cd', frequency: 12 },
        { pattern: 'ls', frequency: 15 },
        { pattern: 'cat', frequency: 5 },
        { pattern: 'grep', frequency: 3 },
        { pattern: 'find', frequency: 4 },
        { pattern: 'yarn', frequency: 4 },
      ],
      contextEffectiveness: {
        score: 78,
        contributingFactors: [
          'Rich shell history (45 commands)',
          'Active clipboard usage (28 entries)',
          'Application context detected (VSCode)',
          'Extensive keyword vocabulary (50+ terms)',
        ],
      },
    };

    return NextResponse.json(analytics);
  } catch (error) {
    console.error('Error fetching analytics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch analytics' },
      { status: 500 }
    );
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { ContextData } from '@/app/components/context/types';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const timeRange = searchParams.get('timeRange') || '24h';
    const categories = searchParams.get('categories')?.split(',').filter(Boolean) || [];
    const keywords = searchParams.get('keywords')?.split(',').filter(Boolean) || [];
    const application = searchParams.get('application');

    // Mock data - replace with actual implementation
    const mockData: ContextData = {
      shell: {
        commands: generateMockCommands(),
        statistics: {
          totalCommands: 45,
          uniqueCommands: 23,
          mostUsedCommands: [
            { command: 'git', count: 8 },
            { command: 'npm', count: 6 },
            { command: 'cd', count: 12 },
            { command: 'ls', count: 15 },
          ],
          commandCategories: {
            git: 8,
            file: 15,
            system: 10,
            development: 12,
          },
        },
      },
      clipboard: {
        entries: generateMockClipboardEntries(),
        statistics: {
          totalEntries: 28,
          contentTypes: {
            text: 15,
            code: 8,
            url: 3,
            file: 2,
          },
        },
      },
      applications: {
        activeWindow: {
          class: 'VSCode',
          title: 'src/components/context/ContextDashboard.tsx - Hypr-Voice',
          pid: 12345,
          category: 'editor',
          timestamp: Math.floor(Date.now() / 1000),
        },
        usageStats: [
          {
            name: 'VSCode',
            category: 'editor',
            usageTime: 7200,
            usageCount: 15,
            lastUsed: Math.floor(Date.now() / 1000),
            keywords: ['TypeScript', 'React', 'Components'],
          },
          {
            name: 'Terminal',
            category: 'terminal',
            usageTime: 3600,
            usageCount: 20,
            lastUsed: Math.floor(Date.now() / 1000),
            keywords: ['Git', 'Node', 'NPM'],
          },
          {
            name: 'Chrome',
            category: 'browser',
            usageTime: 5400,
            usageCount: 8,
            lastUsed: Math.floor(Date.now() / 1000),
            keywords: ['Documentation', 'API', 'StackOverflow'],
          },
        ],
        history: generateMockWindowHistory(),
      },
    };

    return NextResponse.json(mockData);
  } catch (error) {
    console.error('Error fetching context data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch context data' },
      { status: 500 }
    );
  }
}

function generateMockCommands() {
  const commands = [
    'git status',
    'git add .',
    'git commit -m "feat: add context manager"',
    'npm run build',
    'npm test',
    'cd src/components/context',
    'ls -la',
    'cat package.json',
    'yarn dev',
    'git push origin main',
  ];

  return commands.map((cmd, i) => ({
    id: `cmd-${i}`,
    command: cmd,
    timestamp: Math.floor(Date.now() / 1000) - i * 60,
    category: cmd.startsWith('git') ? 'git' : cmd.startsWith('npm') ? 'node' : 'system',
    tags: cmd.split(' ').slice(1),
  }));
}

function generateMockClipboardEntries() {
  const entries = [
    'https://github.com/example/repo',
    'const useContext = () => { return {}; };',
    'git@github.com:user/repo.git',
    'npm install @types/react',
    'API_ENDPOINT=https://api.example.com',
  ];

  return entries.map((content, i) => ({
    id: `clip-${i}`,
    content,
    timestamp: Math.floor(Date.now() / 1000) - i * 120,
    type: content.startsWith('http') ? 'url' : content.includes('{') ? 'code' : 'text',
    category: content.includes('http') ? 'web' : content.includes('git') ? 'version-control' : 'development',
  }));
}

function generateMockWindowHistory() {
  return [
    {
      class: 'VSCode',
      title: 'src/components/context/ContextDashboard.tsx',
      pid: 12345,
      category: 'editor',
      timestamp: Math.floor(Date.now() / 1000) - 300,
    },
    {
      class: 'Terminal',
      title: 'bash - zsh',
      pid: 12346,
      category: 'terminal',
      timestamp: Math.floor(Date.now() / 1000) - 900,
    },
    {
      class: 'Chrome',
      title: 'React Documentation',
      pid: 12347,
      category: 'browser',
      timestamp: Math.floor(Date.now() / 1000) - 1500,
    },
    {
      class: 'Slack',
      title: '#general - Team Chat',
      pid: 12348,
      category: 'communication',
      timestamp: Math.floor(Date.now() / 1000) - 2100,
    },
  ];
}

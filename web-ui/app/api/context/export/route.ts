import { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const format = searchParams.get('format') || 'json';

    // Mock export data
    const exportData = {
      metadata: {
        exportedAt: new Date().toISOString(),
        version: '1.0',
        format,
      },
      shell: {
        commands: [
          {
            command: 'git status',
            timestamp: Math.floor(Date.now() / 1000) - 3600,
            category: 'git',
          },
          // Add more mock data as needed
        ],
      },
      clipboard: {
        entries: [
          {
            content: 'const useContext = () => {};',
            timestamp: Math.floor(Date.now() / 1000) - 1800,
            type: 'code',
          },
          // Add more mock data as needed
        ],
      },
      applications: {
        activeWindow: {
          class: 'VSCode',
          title: 'ContextDashboard.tsx',
          timestamp: Math.floor(Date.now() / 1000),
          category: 'editor',
        },
        history: [
          {
            class: 'Terminal',
            title: 'bash',
            timestamp: Math.floor(Date.now() / 1000) - 900,
            category: 'terminal',
          },
          // Add more mock data as needed
        ],
      },
    };

    const jsonData = JSON.stringify(exportData, null, 2);

    return new Response(jsonData, {
      headers: {
        'Content-Type': 'application/json',
        'Content-Disposition': `attachment; filename="context-export-${Date.now()}.json"`,
      },
    });
  } catch (error) {
    console.error('Error exporting context:', error);
    return new Response(
      JSON.stringify({ error: 'Failed to export context data' }),
      { status: 500 }
    );
  }
}

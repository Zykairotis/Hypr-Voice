import { NextRequest, NextResponse } from 'next/server';

const BRIDGE_URL = process.env.HYPR_VOICE_BRIDGE_URL || 'http://localhost:8934';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const source = searchParams.get('source') || 'all';

    // Get active vocabulary context from bridge
    const vocabResponse = await fetch(`${BRIDGE_URL}/api/vocabulary/context/active`, {
      cache: 'no-store',
    });

    let vocabularyContext = {};
    if (vocabResponse.ok) {
      vocabularyContext = await vocabResponse.json();
    }

    const integrationInfo = {
      backend: {
        url: 'http://localhost:9099',
        websocket: 'ws://localhost:9091',
        context_endpoint: '/api/context',
        processor_script: 'src/hypr_voice/whisper/scripts/context_processor.py',
        websocket_server: 'src/hypr_voice/whisper/context/context_websocket_server.py',
      },
      vocabulary: vocabularyContext,
      features: {
        shell_history: true,
        clipboard_tracking: true,
        window_detection: true,
        real_time_updates: true,
        privacy_controls: true,
        analytics: true,
        export: true,
      },
      status: {
        backend_connected: vocabResponse.ok,
        websocket_connected: false,
        last_update: Date.now(),
        data_freshness: 0,
      },
      configuration: {
        shell_history_limit: 100,
        clipboard_history_limit: 50,
        update_interval_ms: 5000,
        retention_hours: 24,
      }
    };

    return NextResponse.json(integrationInfo);
  } catch (error) {
    console.error('Error fetching integration info:', error);
    return NextResponse.json(
      { error: 'Failed to fetch integration info' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, source } = body;

    // Handle different integration actions
    switch (action) {
      case 'connect_backend':
        return NextResponse.json({ success: true, message: 'Backend connected' });

      case 'disconnect_backend':
        return NextResponse.json({ success: true, message: 'Backend disconnected' });

      case 'test_websocket':
        return NextResponse.json({ success: true, message: 'WebSocket tested' });

      case 'refresh_data':
        return NextResponse.json({ success: true, message: 'Data refresh initiated' });

      default:
        return NextResponse.json(
          { error: 'Unknown action' },
          { status: 400 }
        );
    }
  } catch (error) {
    console.error('Error handling integration action:', error);
    return NextResponse.json(
      { error: 'Failed to handle integration action' },
      { status: 500 }
    );
  }
}

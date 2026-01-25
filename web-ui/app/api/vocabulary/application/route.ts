import { NextRequest, NextResponse } from 'next/server';

const BRIDGE_URL = process.env.HYPR_VOICE_BRIDGE_URL || 'http://localhost:8934';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const appName = searchParams.get('name');

    if (!appName) {
      return NextResponse.json(
        { error: 'Missing application name parameter' },
        { status: 400 }
      );
    }

    const response = await fetch(`${BRIDGE_URL}/api/vocabulary/application/${appName}`, {
      cache: 'no-store',
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error detecting application:', error);
    return NextResponse.json(
      { error: 'Failed to detect application' },
      { status: 500 }
    );
  }
}

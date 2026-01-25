import { NextRequest, NextResponse } from 'next/server';

const BRIDGE_URL = process.env.HYPR_VOICE_BRIDGE_URL || 'http://localhost:8934';

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BRIDGE_URL}/api/context`, {
      cache: 'no-store',
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error fetching context:', error);
    return NextResponse.json(
      { error: 'Failed to fetch context' },
      { status: 500 }
    );
  }
}

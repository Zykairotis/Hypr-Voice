import { NextRequest, NextResponse } from 'next/server';

const BRIDGE_URL = process.env.HYPR_VOICE_BRIDGE_URL || 'http://localhost:8934';

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BRIDGE_URL}/api/vocabulary/statistics`, {
      cache: 'no-store',
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error fetching statistics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch statistics' },
      { status: 500 }
    );
  }
}

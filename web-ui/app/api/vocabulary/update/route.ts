import { NextRequest, NextResponse } from 'next/server';

const BRIDGE_URL = process.env.HYPR_VOICE_BRIDGE_URL || 'http://localhost:8934';

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const vocabId = searchParams.get('id') || 'global';

    const body = await request.json();
    const response = await fetch(`${BRIDGE_URL}/api/vocabulary/${vocabId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error updating vocabulary:', error);
    return NextResponse.json(
      { error: 'Failed to update vocabulary' },
      { status: 500 }
    );
  }
}

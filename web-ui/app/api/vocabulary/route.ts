import { NextRequest, NextResponse } from 'next/server';

const BRIDGE_URL = process.env.HYPR_VOICE_BRIDGE_URL || 'http://localhost:8934';

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BRIDGE_URL}/api/config/vocabulary`, {
      cache: 'no-store',
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error fetching vocabularies:', error);
    return NextResponse.json(
      { error: 'Failed to fetch vocabularies' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await fetch(`${BRIDGE_URL}/api/config/vocabulary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error creating vocabulary:', error);
    return NextResponse.json(
      { error: 'Failed to create vocabulary' },
      { status: 500 }
    );
  }
}

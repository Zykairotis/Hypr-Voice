import { NextRequest, NextResponse } from 'next/server';

const BRIDGE_URL = process.env.HYPR_VOICE_BRIDGE_URL || 'http://localhost:8934';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const response = await fetch(`${BRIDGE_URL}/api/vocabulary/${params.id}`, {
      cache: 'no-store',
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error fetching vocabulary:', error);
    return NextResponse.json(
      { error: 'Failed to fetch vocabulary' },
      { status: 500 }
    );
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const response = await fetch(`${BRIDGE_URL}/api/vocabulary/${params.id}`, {
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

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Vocabulary deletion requires config file modification
    return NextResponse.json(
      {
        error: 'Vocabulary deletion requires direct config file modification',
        hint: 'Edit the vocabulary files in config/hypr_voice/whisper/vocabularies/',
      },
      { status: 501 }
    );
  } catch (error) {
    console.error('Error deleting vocabulary:', error);
    return NextResponse.json(
      { error: 'Failed to delete vocabulary' },
      { status: 500 }
    );
  }
}

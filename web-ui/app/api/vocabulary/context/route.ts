import { NextRequest, NextResponse } from 'next/server';
import { get_context_manager } from '@/src/Hypr-Whisper/context_manager';

export async function GET(request: NextRequest) {
  try {
    const contextManager = get_context_manager();
    const context = contextManager.get_comprehensive_context();

    return NextResponse.json(context);
  } catch (error) {
    console.error('Error fetching context:', error);
    return NextResponse.json(
      { error: 'Failed to fetch context' },
      { status: 500 }
    );
  }
}

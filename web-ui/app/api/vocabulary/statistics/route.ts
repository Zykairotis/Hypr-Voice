import { NextRequest, NextResponse } from 'next/server';
import { get_vocabulary_manager } from '@/src/Hypr-Whisper/vocabulary_manager';

export async function GET(request: NextRequest) {
  try {
    const vocabularyManager = get_vocabulary_manager();
    const stats = vocabularyManager.get_vocabulary_stats();

    return NextResponse.json(stats);
  } catch (error) {
    console.error('Error fetching statistics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch statistics' },
      { status: 500 }
    );
  }
}

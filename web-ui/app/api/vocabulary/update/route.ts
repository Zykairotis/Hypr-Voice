import { NextRequest, NextResponse } from 'next/server';
import { get_vocabulary_manager } from '@/src/Hypr-Whisper/vocabulary_manager';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { appName, appTitle } = body;

    const vocabularyManager = get_vocabulary_manager();
    vocabularyManager.update_vocabulary(appName, appTitle);

    return NextResponse.json({
      message: 'Vocabulary updated',
      currentVocabulary: vocabularyManager.current_vocabulary,
      currentApp: vocabularyManager.current_app,
    });
  } catch (error) {
    console.error('Error updating vocabulary:', error);
    return NextResponse.json(
      { error: 'Failed to update vocabulary' },
      { status: 500 }
    );
  }
}

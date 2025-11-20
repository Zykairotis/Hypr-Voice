import { NextRequest, NextResponse } from 'next/server';
import { get_vocabulary_manager } from '@/src/Hypr-Whisper/vocabulary_manager';

export async function GET(request: NextRequest) {
  try {
    const vocabularyManager = get_vocabulary_manager();

    // Detect current application
    const appName = vocabularyManager.detect_active_application();

    // Get matched vocabulary
    let matchedVocabulary: string | undefined;
    if (appName) {
      matchedVocabulary = vocabularyManager.match_vocabulary_to_application(appName);
    }

    // Get context from window (placeholder - would need Hyprland integration)
    const windowInfo = {
      class: appName || 'unknown',
      title: 'Current Window',
    };

    // Extract keywords from window info
    const contextManager = vocabularyManager.context_manager;
    let keywords: string[] = [];

    if (contextManager) {
      const context = contextManager.extract_context_from_hyprland(windowInfo);
      keywords = Array.from(context.keywords);
    }

    return NextResponse.json({
      class: appName || 'unknown',
      title: windowInfo.title,
      keywords,
      matchedVocabulary,
    });
  } catch (error) {
    console.error('Error detecting application:', error);
    return NextResponse.json(
      { error: 'Failed to detect application' },
      { status: 500 }
    );
  }
}

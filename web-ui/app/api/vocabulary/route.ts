import { NextRequest, NextResponse } from 'next/server';
import { get_vocabulary_manager } from '@/src/Hypr-Whisper/vocabulary_manager';

export async function GET(request: NextRequest) {
  try {
    const vocabularyManager = get_vocabulary_manager();
    const vocabularies = vocabularyManager.vocabularies;

    const result = Object.entries(vocabularies).map(([id, vocab]) => ({
      name: vocab.name,
      description: vocab.description,
      keywords: vocab.keywords,
      applications: vocab.applications,
      prompts: vocab.prompts,
      priority: vocab.priority,
    }));

    return NextResponse.json(result);
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
    const vocabularyManager = get_vocabulary_manager();

    // TODO: Implement vocabulary creation logic
    // This would involve creating a new YAML file in the vocabularies directory

    return NextResponse.json({ message: 'Vocabulary created', data: body });
  } catch (error) {
    console.error('Error creating vocabulary:', error);
    return NextResponse.json(
      { error: 'Failed to create vocabulary' },
      { status: 500 }
    );
  }
}

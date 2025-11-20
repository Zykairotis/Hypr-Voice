import { NextRequest, NextResponse } from 'next/server';
import { get_vocabulary_manager } from '@/src/Hypr-Whisper/vocabulary_manager';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const vocabularyManager = get_vocabulary_manager();
    const vocabulary = vocabularyManager.vocabularies[params.id];

    if (!vocabulary) {
      return NextResponse.json(
        { error: 'Vocabulary not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      name: vocabulary.name,
      description: vocabulary.description,
      keywords: vocabulary.keywords,
      applications: vocabulary.applications,
      prompts: vocabulary.prompts,
      priority: vocabulary.priority,
    });
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
    const vocabularyManager = get_vocabulary_manager();

    // TODO: Implement vocabulary update logic
    // This would involve updating the YAML file

    return NextResponse.json({ message: 'Vocabulary updated', data: body });
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
    // TODO: Implement vocabulary deletion logic
    // This would involve deleting the YAML file

    return NextResponse.json({ message: 'Vocabulary deleted' });
  } catch (error) {
    console.error('Error deleting vocabulary:', error);
    return NextResponse.json(
      { error: 'Failed to delete vocabulary' },
      { status: 500 }
    );
  }
}

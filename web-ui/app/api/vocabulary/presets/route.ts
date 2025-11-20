import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // TODO: Load from database or file system
    // For now, return mock data
    const presets = [
      {
        id: 'preset-1',
        name: 'Development Bundle',
        description: 'Complete vocabulary for software development',
        category: 'Development',
        vocabulary: {
          name: 'Development',
          description: 'Development-related terms',
          keywords: {
            technical_terms: ['JavaScript', 'Python', 'React', 'NodeJS', 'TypeScript'],
            programming: {
              keywords: ['async', 'await', 'function', 'class', 'interface'],
            },
          },
          applications: { window_classes: ['code', 'terminal'] },
          prompts: {},
          priority: 10,
        },
        tags: ['development', 'coding', 'programming'],
        createdAt: Date.now(),
        isBuiltIn: true,
      },
      {
        id: 'preset-2',
        name: 'Writing Suite',
        description: 'Vocabulary optimized for writing and documentation',
        category: 'Writing',
        vocabulary: {
          name: 'Writing',
          description: 'Writing and documentation terms',
          keywords: {
            technical_terms: ['grammar', 'syntax', 'paragraph', 'chapter'],
          },
          applications: { window_classes: ['writer', 'editor'] },
          prompts: {},
          priority: 5,
        },
        tags: ['writing', 'documentation', 'text'],
        createdAt: Date.now(),
        isBuiltIn: true,
      },
    ];

    return NextResponse.json(presets);
  } catch (error) {
    console.error('Error fetching presets:', error);
    return NextResponse.json(
      { error: 'Failed to fetch presets' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, vocabularyId, description } = body;

    // TODO: Create preset from vocabulary
    const preset = {
      id: `preset-${Date.now()}`,
      name,
      description,
      category: 'Custom',
      vocabularyId,
      tags: ['custom'],
      createdAt: Date.now(),
      isBuiltIn: false,
    };

    return NextResponse.json(preset);
  } catch (error) {
    console.error('Error creating preset:', error);
    return NextResponse.json(
      { error: 'Failed to create preset' },
      { status: 500 }
    );
  }
}

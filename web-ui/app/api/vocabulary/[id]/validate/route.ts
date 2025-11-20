import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const errors: string[] = [];
    const warnings: string[] = [];

    // TODO: Implement vocabulary validation
    // - Check for duplicate keywords
    // - Validate YAML syntax
    // - Check for empty categories
    // - Validate application patterns

    if (params.id === 'global') {
      // Example validation for global vocabulary
      warnings.push('Global vocabulary should have priority -1');
    }

    const isValid = errors.length === 0;

    return NextResponse.json({
      isValid,
      errors,
      warnings,
    });
  } catch (error) {
    console.error('Error validating vocabulary:', error);
    return NextResponse.json(
      { error: 'Failed to validate vocabulary' },
      { status: 500 }
    );
  }
}

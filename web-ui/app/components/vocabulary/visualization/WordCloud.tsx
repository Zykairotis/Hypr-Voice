'use client';

import React, { useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { RotateCw } from 'lucide-react';

interface WordCloudProps {
  words: Array<{
    text: string;
    value: number;
    category?: string;
  }>;
  maxWords?: number;
  onWordClick?: (word: string) => void;
}

export function WordCloud({ words, maxWords = 100, onWordClick }: WordCloudProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    drawWordCloud();
  }, [words, maxWords]);

  const drawWordCloud = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Sort words by value
    const sortedWords = [...words]
      .sort((a, b) => b.value - a.value)
      .slice(0, maxWords);

    if (sortedWords.length === 0) return;

    // Calculate font sizes
    const maxValue = Math.max(...sortedWords.map(w => w.value));
    const minValue = Math.min(...sortedWords.map(w => w.value));
    const fontSizeRange = { min: 12, max: 72 };

    // Simple cloud layout (spiral)
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    let angle = 0;
    let radius = 0;
    const spiralStep = 5;
    const angleStep = 0.3;

    // Color palette
    const colors = [
      '#0088FE', '#00C49F', '#FFBB28', '#FF8042',
      '#8884d8', '#82ca9d', '#ffc658', '#ff7300'
    ];

    sortedWords.forEach((word, index) => {
      // Calculate font size
      const normalizedValue = (word.value - minValue) / (maxValue - minValue);
      const fontSize = fontSizeRange.min + (normalizedValue * (fontSizeRange.max - fontSizeRange.min));

      ctx.font = `${fontSize}px ${getFontFamily(word.category)}`;
      ctx.fillStyle = colors[index % colors.length];
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      // Measure text
      const metrics = ctx.measureText(word.text);
      const textWidth = metrics.width;
      const textHeight = fontSize;

      // Find position on spiral
      let x, y;
      let attempts = 0;
      const maxAttempts = 100;

      do {
        x = centerX + radius * Math.cos(angle);
        y = centerY + radius * Math.sin(angle);
        angle += angleStep;
        radius += spiralStep;
        attempts++;
      } while (
        attempts < maxAttempts &&
        (x - textWidth / 2 < 0 ||
         x + textWidth / 2 > canvas.width ||
         y - textHeight / 2 < 0 ||
         y + textHeight / 2 > canvas.height ||
         isColliding(ctx, x, y, textWidth, textHeight))
      );

      // Draw text
      if (attempts < maxAttempts) {
        const drawX = x - textWidth / 2;
        const drawY = y - textHeight / 2;

        // Background glow effect
        ctx.shadowColor = colors[index % colors.length];
        ctx.shadowBlur = 10;

        ctx.fillText(word.text, x, y);

        // Reset shadow
        ctx.shadowBlur = 0;

        // Store position for click detection
        (word as any)._position = {
          x: drawX,
          y: drawY,
          width: textWidth,
          height: textHeight,
        };
      }
    });
  };

  const getFontFamily = (category?: string) => {
    switch (category) {
      case 'technical':
        return 'monospace';
      case 'code':
        return 'monospace';
      default:
        return 'system-ui, sans-serif';
    }
  };

  const isColliding = (ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number): boolean => {
    // Simple collision detection
    // In a real implementation, you'd store all placed words and check against them
    return false;
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onWordClick || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const sortedWords = [...words]
      .sort((a, b) => b.value - a.value)
      .slice(0, maxWords);

    for (const word of sortedWords) {
      const pos = (word as any)._position;
      if (pos &&
          x >= pos.x &&
          x <= pos.x + pos.width &&
          y >= pos.y &&
          y <= pos.y + pos.height) {
        onWordClick(word.text);
        break;
      }
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Vocabulary Word Cloud</CardTitle>
        <CardDescription>
          Visual representation of keyword importance and frequency
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <canvas
            ref={canvasRef}
            width={800}
            height={600}
            className="w-full border rounded"
            onClick={handleCanvasClick}
          />
          {words.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <RotateCw className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No words to display</p>
              </div>
            </div>
          )}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {words.slice(0, 10).map((word, index) => (
            <Badge key={index} variant="outline" className="cursor-pointer" onClick={() => onWordClick?.(word.text)}>
              {word.text} ({word.value})
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface VocabularyGraphProps {
  words: Array<{
    text: string;
    category: string;
    related?: string[];
  }>;
  onNodeClick?: (word: string) => void;
}

export function VocabularyGraph({ words, onNodeClick }: VocabularyGraphProps) {
  // Simplified network visualization
  // In a real implementation, you'd use a library like D3.js or vis.js
  return (
    <Card>
      <CardHeader>
        <CardTitle>Vocabulary Relationship Graph</CardTitle>
        <CardDescription>
          Network view showing keyword relationships
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[600px] flex items-center justify-center border rounded bg-muted/20">
          <div className="text-center text-muted-foreground">
            <p>Graph visualization coming soon!</p>
            <p className="text-sm mt-2">This will show keyword relationships and clusters</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

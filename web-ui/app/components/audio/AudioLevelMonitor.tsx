'use client';

import React, { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/utils';
import { AudioLevelData, formatDecibels, getColorForLevel } from '@/lib/audio-utils';

interface AudioLevelMonitorProps {
  level: AudioLevelData;
  isActive?: boolean;
  size?: 'sm' | 'md' | 'lg';
  orientation?: 'horizontal' | 'vertical';
  showDbScale?: boolean;
  className?: string;
}

export const AudioLevelMonitor: React.FC<AudioLevelMonitorProps> = ({
  level,
  isActive = true,
  size = 'md',
  orientation = 'vertical',
  showDbScale = true,
  className,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  const sizeClasses = {
    sm: orientation === 'vertical' ? 'w-6 h-32' : 'w-32 h-6',
    md: orientation === 'vertical' ? 'w-8 h-48' : 'w-48 h-8',
    lg: orientation === 'vertical' ? 'w-12 h-64' : 'w-64 h-12',
  };

  const drawMeter = (canvas: HTMLCanvasElement, levelData: AudioLevelData) => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = canvas;
    ctx.clearRect(0, 0, width, height);

    const isVertical = orientation === 'vertical';
    const dimension = isVertical ? height : width;

    const dbRange = 60;
    const minDb = -60;
    const normalizedLevel = Math.max(0, Math.min(1, (levelData.db - minDb) / dbRange));

    ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.fillRect(0, 0, width, height);

    const color = getColorForLevel(levelData.db);
    ctx.fillStyle = color;

    const filledDimension = dimension * normalizedLevel;

    if (isVertical) {
      ctx.fillRect(0, height - filledDimension, width, filledDimension);

      if (levelData.peak > 0) {
        const peakHeight = height * (Math.max(0, (linearToDb(levelData.peak) - minDb) / dbRange));
        ctx.fillStyle = '#ef4444';
        ctx.fillRect(0, height - peakHeight - 2, width, 4);
      }

      if (showDbScale) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px monospace';
        ctx.textAlign = isVertical ? 'left' : 'center';
        ctx.textBaseline = 'middle';

        for (let db = -60; db <= 0; db += 10) {
          const y = height * (1 - (db - minDb) / dbRange);
          const tickHeight = db % 20 === 0 ? 8 : 4;
          ctx.fillRect(0, y - tickHeight / 2, tickHeight, tickHeight);
        }
      }
    } else {
      ctx.fillRect(0, 0, filledDimension, height);

      if (levelData.peak > 0) {
        const peakWidth = width * (Math.max(0, (linearToDb(levelData.peak) - minDb) / dbRange));
        ctx.fillStyle = '#ef4444';
        ctx.fillRect(peakWidth - 2, 0, 4, height);
      }

      if (showDbScale) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';

        for (let db = -60; db <= 0; db += 10) {
          const x = width * (1 - (db - minDb) / dbRange);
          const tickWidth = db % 20 === 0 ? 8 : 4;
          ctx.fillRect(x - tickWidth / 2, height - tickWidth, tickWidth, tickWidth);
        }
      }
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !isActive) return;

    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;

    drawMeter(canvas, level);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [level, isActive, orientation, showDbScale]);

  return (
    <div className={cn('flex flex-col items-center gap-1', className)}>
      <canvas
        ref={canvasRef}
        className={cn(
          sizeClasses[size],
          'rounded border border-border bg-black',
        )}
      />
      {showDbScale && (
        <div className="text-xs text-muted-foreground font-mono">
          {formatDecibels(level.db)}
        </div>
      )}
    </div>
  );
};

function linearToDb(linear: number): number {
  return 20 * Math.log10(Math.max(0.0001, linear));
}

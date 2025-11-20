'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface LEDVUMeterProps {
  level: number;
  orientation?: 'horizontal' | 'vertical';
  size?: 'sm' | 'md' | 'lg';
  segments?: number;
  showValues?: boolean;
  className?: string;
}

export const LEDVUMeter: React.FC<LEDVUMeterProps> = ({
  level,
  orientation = 'vertical',
  size = 'md',
  segments = 20,
  showValues = true,
  className,
}) => {
  const sizeConfig = {
    sm: {
      horizontal: { width: 200, height: 16, segmentSize: 10 },
      vertical: { width: 16, height: 200, segmentSize: 10 },
    },
    md: {
      horizontal: { width: 300, height: 24, segmentSize: 15 },
      vertical: { width: 24, height: 300, segmentSize: 15 },
    },
    lg: {
      horizontal: { width: 400, height: 32, segmentSize: 20 },
      vertical: { width: 32, height: 400, segmentSize: 20 },
    },
  };

  const config = sizeConfig[size][orientation];
  const activeSegments = Math.floor(level * segments);

  const getSegmentColor = (index: number, activeCount: number) => {
    const percentage = index / segments;
    if (activeCount === 0) return '#1e293b';

    if (index >= activeCount) return '#1e293b';

    if (percentage < 0.7) return '#22c55e';
    if (percentage < 0.9) return '#f59e0b';
    return '#ef4444';
  };

  const renderSegments = () => {
    const segmentElements = [];
    const gap = 2;

    for (let i = 0; i < segments; i++) {
      const isActive = i < activeSegments;
      const color = getSegmentColor(i, activeSegments);

      if (orientation === 'horizontal') {
        const x = i * (config.segmentSize + gap);
        segmentElements.push(
          <rect
            key={i}
            x={x}
            y={0}
            width={config.segmentSize}
            height={config.height}
            fill={color}
            rx={2}
          />
        );
      } else {
        const y = (segments - 1 - i) * (config.segmentSize + gap);
        segmentElements.push(
          <rect
            key={i}
            x={0}
            y={y}
            width={config.width}
            height={config.segmentSize}
            fill={color}
            rx={2}
          />
        );
      }
    }

    return segmentElements;
  };

  return (
    <div className={cn('flex items-center gap-4', className)}>
      <svg
        width={config.width}
        height={config.height}
        className="drop-shadow-sm"
      >
        {renderSegments()}
      </svg>
      {showValues && (
        <div className="text-sm font-mono">
          <div>{(level * 100).toFixed(0)}%</div>
          <div className="text-muted-foreground">
            {activeSegments}/{segments}
          </div>
        </div>
      )}
    </div>
  );
};

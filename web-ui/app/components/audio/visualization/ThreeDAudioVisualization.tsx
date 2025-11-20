'use client';

import React, { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

interface ThreeDAudioVisualizationProps {
  frequencyData?: Uint8Array;
  audioBuffer?: Float32Array;
  width?: number;
  height?: number;
  rotation?: number;
  color?: string;
  backgroundColor?: string;
  className?: string;
}

export const ThreeDAudioVisualization: React.FC<ThreeDAudioVisualizationProps> = ({
  frequencyData,
  audioBuffer,
  width = 800,
  height = 400,
  rotation = 0,
  color = '#3b82f6',
  backgroundColor = '#000000',
  className,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  const draw3DVisualization = (canvas: HTMLCanvasElement) => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width: canvasWidth, height: canvasHeight } = canvas;

    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    const centerX = canvasWidth / 2;
    const centerY = canvasHeight / 2;

    const data = frequencyData || audioBuffer;
    if (!data || data.length === 0) return;

    const barCount = Math.min(64, data.length);
    const angleStep = (Math.PI * 2) / barCount;
    const currentRotation = rotation + Date.now() * 0.0005;

    for (let i = 0; i < barCount; i++) {
      const value = data[Math.floor((i / barCount) * data.length)] || 0;
      const normalizedValue = value / 255;
      const barHeight = normalizedValue * 100;

      const angle = currentRotation + i * angleStep;
      const x1 = centerX + Math.cos(angle) * 50;
      const y1 = centerY + Math.sin(angle) * 50;
      const x2 = centerX + Math.cos(angle) * (50 + barHeight);
      const y2 = centerY + Math.sin(angle) * (50 + barHeight);

      const intensity = Math.min(1, normalizedValue + 0.3);
      ctx.strokeStyle = color;
      ctx.globalAlpha = intensity;
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();

      const barWidth = 4;
      const perpendicularAngle = angle + Math.PI / 2;
      const widthOffset = Math.cos(perpendicularAngle) * barWidth;
      const heightOffset = Math.sin(perpendicularAngle) * barWidth;

      ctx.fillStyle = color;
      ctx.globalAlpha = intensity * 0.3;

      ctx.beginPath();
      ctx.moveTo(x1 - widthOffset, y1 - heightOffset);
      ctx.lineTo(x1 + widthOffset, y1 + heightOffset);
      ctx.lineTo(x2 + widthOffset, y2 + heightOffset);
      ctx.lineTo(x2 - widthOffset, y2 - heightOffset);
      ctx.closePath();
      ctx.fill();
    }

    ctx.globalAlpha = 1;

    for (let i = 0; i < 3; i++) {
      const radius = 30 + i * 15;
      const alpha = 0.3 - i * 0.08;

      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
      ctx.strokeStyle = color;
      ctx.globalAlpha = alpha;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    ctx.globalAlpha = 1;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = width;
    canvas.height = height;

    const animate = () => {
      draw3DVisualization(canvas);
      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [frequencyData, audioBuffer, width, height, rotation, color, backgroundColor]);

  return (
    <canvas
      ref={canvasRef}
      className={cn('rounded border border-border', className)}
      style={{ backgroundColor }}
    />
  );
};

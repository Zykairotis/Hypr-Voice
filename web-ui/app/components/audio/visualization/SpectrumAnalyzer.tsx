'use client';

import React, { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

interface SpectrumAnalyzerProps {
  frequencyData?: Uint8Array;
  width?: number;
  height?: number;
  showGrid?: boolean;
  color?: string;
  backgroundColor?: string;
  barCount?: number;
  gradient?: boolean;
  className?: string;
}

export const SpectrumAnalyzer: React.FC<SpectrumAnalyzerProps> = ({
  frequencyData,
  width = 800,
  height = 300,
  showGrid = true,
  color = '#3b82f6',
  backgroundColor = '#000000',
  barCount = 64,
  gradient = true,
  className,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  const drawSpectrum = (canvas: HTMLCanvasElement, data?: Uint8Array) => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width: canvasWidth, height: canvasHeight } = canvas;

    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    if (showGrid) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.lineWidth = 1;

      const gridSize = 20;

      for (let x = 0; x < canvasWidth; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvasHeight);
        ctx.stroke();
      }

      for (let y = 0; y < canvasHeight; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvasWidth, y);
        ctx.stroke();
      }
    }

    if (!data || data.length === 0) return;

    const barWidth = canvasWidth / barCount;
    const step = Math.floor(data.length / barCount);

    for (let i = 0; i < barCount; i++) {
      const startIndex = i * step;
      let sum = 0;
      const endIndex = Math.min(startIndex + step, data.length);

      for (let j = startIndex; j < endIndex; j++) {
        sum += data[j];
      }

      const avg = sum / (endIndex - startIndex);
      const barHeight = (avg / 255) * canvasHeight;

      if (gradient) {
        const gradient = ctx.createLinearGradient(0, canvasHeight - barHeight, 0, canvasHeight);
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, `${color}33`);
        ctx.fillStyle = gradient;
      } else {
        ctx.fillStyle = color;
      }

      const x = i * barWidth;
      const y = canvasHeight - barHeight;

      ctx.fillRect(x, y, barWidth - 2, barHeight);

      if (avg > 200) {
        ctx.fillStyle = '#ef4444';
        ctx.fillRect(x, y, barWidth - 2, 3);
      }
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = width;
    canvas.height = height;

    drawSpectrum(canvas, frequencyData);

    if (frequencyData && frequencyData.length > 0) {
      const animate = () => {
        drawSpectrum(canvas, frequencyData);
        animationRef.current = requestAnimationFrame(animate);
      };
      animationRef.current = requestAnimationFrame(animate);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [frequencyData, width, height, showGrid, color, backgroundColor, barCount, gradient]);

  return (
    <canvas
      ref={canvasRef}
      className={cn('rounded border border-border', className)}
      style={{ backgroundColor }}
    />
  );
};

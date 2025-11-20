'use client';

import React, { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/utils';

interface AudioWaveformDisplayProps {
  buffer?: Float32Array;
  isRecording?: boolean;
  width?: number;
  height?: number;
  showGrid?: boolean;
  color?: string;
  backgroundColor?: string;
  className?: string;
}

export const AudioWaveformDisplay: React.FC<AudioWaveformDisplayProps> = ({
  buffer,
  isRecording = false,
  width = 800,
  height = 200,
  showGrid = true,
  color = '#3b82f6',
  backgroundColor = '#000000',
  className,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  const drawWaveform = (canvas: HTMLCanvasElement, audioBuffer?: Float32Array) => {
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

      ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
      ctx.beginPath();
      ctx.moveTo(0, canvasHeight / 2);
      ctx.lineTo(canvasWidth, canvasHeight / 2);
      ctx.stroke();
    }

    if (audioBuffer && audioBuffer.length > 0) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();

      const sliceWidth = canvasWidth / audioBuffer.length;
      let x = 0;

      for (let i = 0; i < audioBuffer.length; i++) {
        const v = audioBuffer[i] * 0.5;
        const y = (v + 1) * canvasHeight / 2;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }

        x += sliceWidth;
      }

      ctx.stroke();

      ctx.fillStyle = color;
      const amplitude = Math.abs(audioBuffer[audioBuffer.length - 1]) * canvasHeight / 2;
      ctx.fillRect(canvasWidth - 4, canvasHeight / 2 - amplitude, 2, amplitude * 2);
    } else if (isRecording) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();

      const midPoint = canvasHeight / 2;
      let x = 0;

      for (let i = 0; i < canvasWidth; i++) {
        const t = (Date.now() / 1000) + i * 0.01;
        const v = Math.sin(t * 10) * 0.5;
        const y = midPoint + v * midPoint;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }

        x += 1;
      }

      ctx.stroke();
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = width;
    canvas.height = height;

    drawWaveform(canvas, buffer);

    if (isRecording) {
      const animate = () => {
        drawWaveform(canvas, buffer);
        animationRef.current = requestAnimationFrame(animate);
      };
      animationRef.current = requestAnimationFrame(animate);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [buffer, isRecording, width, height, showGrid, color, backgroundColor]);

  return (
    <canvas
      ref={canvasRef}
      className={cn('rounded border border-border', className)}
      style={{ backgroundColor }}
    />
  );
};

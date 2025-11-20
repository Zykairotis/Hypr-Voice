'use client';

import React from 'react';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EffectConfig } from '@/lib/audio-utils';
import { Zap, Minimize2, Waves } from 'lucide-react';

interface AudioEffectsProps {
  effects: EffectConfig;
  onEffectsChange?: (effects: EffectConfig) => void;
  className?: string;
}

export const AudioEffects: React.FC<AudioEffectsProps> = ({
  effects,
  onEffectsChange,
  className,
}) => {
  const handleEffectChange = (key: keyof EffectConfig, value: any) => {
    onEffectsChange?.({ ...effects, [key]: value });
  };

  const handleCompressionChange = (key: string, value: any) => {
    onEffectsChange?.({
      ...effects,
      compression: {
        ...effects.compression,
        [key]: value,
      },
    });
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Waves className="w-5 h-5" />
          Audio Effects
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              <Label>Noise Reduction</Label>
            </div>
            <div className="text-sm text-muted-foreground w-12 text-right">
              {effects.noiseReduction}%
            </div>
          </div>
          <Slider
            value={[effects.noiseReduction]}
            onValueChange={(value) => handleEffectChange('noiseReduction', value[0])}
            max={100}
            min={0}
            step={1}
            className="w-full"
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Minimize2 className="w-4 h-4" />
            <Label>Echo Cancellation</Label>
          </div>
          <Switch
            checked={effects.echoCancellation}
            onCheckedChange={(checked) => handleEffectChange('echoCancellation', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <Label>Normalization</Label>
          <Switch
            checked={effects.normalization}
            onCheckedChange={(checked) => handleEffectChange('normalization', checked)}
          />
        </div>

        <div className="space-y-4 pt-4 border-t">
          <div className="flex items-center justify-between">
            <Label className="font-medium">Dynamic Range Compression</Label>
            <Switch
              checked={effects.compression.enabled}
              onCheckedChange={(checked) => handleCompressionChange('enabled', checked)}
            />
          </div>

          {effects.compression.enabled && (
            <div className="space-y-4 pl-4 border-l-2 border-primary/20">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Threshold</Label>
                  <div className="text-sm text-muted-foreground w-12 text-right">
                    {effects.compression.threshold} dB
                  </div>
                </div>
                <Slider
                  value={[effects.compression.threshold]}
                  onValueChange={(value) => handleCompressionChange('threshold', value[0])}
                  max={0}
                  min={-40}
                  step={1}
                  className="w-full"
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Ratio</Label>
                  <div className="text-sm text-muted-foreground w-12 text-right">
                    {effects.compression.ratio}:1
                  </div>
                </div>
                <Slider
                  value={[effects.compression.ratio]}
                  onValueChange={(value) => handleCompressionChange('ratio', value[0])}
                  max={20}
                  min={1}
                  step={0.1}
                  className="w-full"
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Attack</Label>
                  <div className="text-sm text-muted-foreground w-12 text-right">
                    {effects.compression.attack} ms
                  </div>
                </div>
                <Slider
                  value={[effects.compression.attack]}
                  onValueChange={(value) => handleCompressionChange('attack', value[0])}
                  max={100}
                  min={0}
                  step={1}
                  className="w-full"
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Release</Label>
                  <div className="text-sm text-muted-foreground w-12 text-right">
                    {effects.compression.release} ms
                  </div>
                </div>
                <Slider
                  value={[effects.compression.release]}
                  onValueChange={(value) => handleCompressionChange('release', value[0])}
                  max={1000}
                  min={10}
                  step={10}
                  className="w-full"
                />
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

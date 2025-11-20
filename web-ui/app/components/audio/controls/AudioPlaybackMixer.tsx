'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChannelConfig, channelColors } from '@/lib/audio-utils';
import { Volume2, VolumeX, Square, Play } from 'lucide-react';

interface AudioPlaybackMixerProps {
  channels: ChannelConfig[];
  onChannelUpdate?: (channelId: string, updates: Partial<ChannelConfig>) => void;
  onChannelAdd?: () => void;
  onChannelRemove?: (channelId: string) => void;
  className?: string;
}

export const AudioPlaybackMixer: React.FC<AudioPlaybackMixerProps> = ({
  channels,
  onChannelUpdate,
  onChannelAdd,
  onChannelRemove,
  className,
}) => {
  const handleVolumeChange = (channelId: string, volume: number) => {
    onChannelUpdate?.(channelId, { volume });
  };

  const handleMuteToggle = (channelId: string) => {
    const channel = channels.find(c => c.id === channelId);
    onChannelUpdate?.(channelId, { muted: !channel?.muted });
  };

  const handleSoloToggle = (channelId: string) => {
    const channel = channels.find(c => c.id === channelId);
    onChannelUpdate?.(channelId, { solo: !channel?.solo });
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Playback Mixer
          <Button onClick={onChannelAdd} size="sm">
            Add Channel
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {channels.map((channel, index) => (
            <div
              key={channel.id}
              className="space-y-3 p-4 rounded-lg border border-border bg-card"
              style={{ borderTopColor: channel.color, borderTopWidth: '4px' }}
            >
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <input
                    type="text"
                    value={channel.name}
                    onChange={(e) => onChannelUpdate?.(channel.id, { name: e.target.value })}
                    className="text-sm font-medium bg-transparent border-none p-0 focus:outline-none focus:ring-1 focus:ring-ring rounded"
                    style={{ color: channel.color }}
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onChannelRemove?.(channel.id)}
                    className="h-6 w-6"
                  >
                    <Square className="h-3 w-3" />
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-xs text-muted-foreground">Volume</div>
                <Slider
                  value={[channel.volume]}
                  onValueChange={(value) => handleVolumeChange(channel.id, value[0])}
                  max={100}
                  min={0}
                  step={1}
                  className="w-full"
                />
                <div className="text-xs text-muted-foreground text-center">
                  {channel.volume}%
                </div>
              </div>

              <div className="flex gap-1">
                <Button
                  variant={channel.muted ? "destructive" : "outline"}
                  size="sm"
                  onClick={() => handleMuteToggle(channel.id)}
                  className="flex-1"
                >
                  {channel.muted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                </Button>
                <Button
                  variant={channel.solo ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleSoloToggle(channel.id)}
                  className="flex-1"
                >
                  Solo
                </Button>
              </div>

              <Button variant="outline" size="sm" className="w-full">
                <Play className="h-4 w-4 mr-2" />
                Play
              </Button>

              <div className="text-xs text-muted-foreground text-center">
                {channel.color}
              </div>
            </div>
          ))}

          {channels.length === 0 && (
            <div className="col-span-full text-center text-muted-foreground py-8">
              No channels. Click "Add Channel" to start.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import {
  Play,
  Pause,
  Square,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  Repeat,
  Shuffle,
  Download,
  Share,
  Mic2,
  Maximize2,
  Waves,
  BarChart3
} from "lucide-react";
import { toast } from "sonner";

interface AudioFile {
  id: string;
  name: string;
  url: string;
  duration: number;
  provider: string;
  voice: string;
  createdAt: Date;
  waveform?: number[];
  spectrogram?: number[][];
}

export default function TTSAudioPlayer() {
  const [audioFiles, setAudioFiles] = useState<AudioFile[]>([]);
  const [currentFile, setCurrentFile] = useState<AudioFile | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1.0);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [isLooping, setIsLooping] = useState(false);
  const [isShuffling, setIsShuffling] = useState(false);
  const [visualizationMode, setVisualizationMode] = useState<"waveform" | "spectrum" | "off">("waveform");
  const [isFullscreen, setIsFullscreen] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  useEffect(() => {
    loadAudioFiles();
    setupAudioContext();
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  const loadAudioFiles = () => {
    // Load from localStorage or API
    const saved = localStorage.getItem("tts-audio-files");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setAudioFiles(parsed.map((file: any) => ({
          ...file,
          createdAt: new Date(file.createdAt)
        })));
      } catch (error) {
        console.error("Failed to load audio files:", error);
      }
    }
  };

  const setupAudioContext = async () => {
    try {
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 2048;
    } catch (error) {
      console.error("Failed to setup audio context:", error);
    }
  };

  const connectAudioElement = () => {
    if (audioRef.current && audioContextRef.current && analyserRef.current) {
      const source = audioContextRef.current.createMediaElementSource(audioRef.current);
      source.connect(analyserRef.current);
      analyserRef.current.connect(audioContextRef.current.destination);
    }
  };

  const playAudio = (file: AudioFile) => {
    if (currentFile?.id === file.id && isPlaying) {
      pauseAudio();
      return;
    }

    setCurrentFile(file);
    connectAudioElement();

    if (audioRef.current) {
      audioRef.current.src = file.url;
      audioRef.current.playbackRate = playbackRate;
      audioRef.current.loop = isLooping;
      audioRef.current.play().then(() => {
        setIsPlaying(true);
        toast.success("Playing audio");
        startVisualization();
      }).catch((error) => {
        console.error("Playback failed:", error);
        toast.error("Failed to play audio");
      });
    }
  };

  const pauseAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      stopVisualization();
    }
  };

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      setCurrentTime(0);
      stopVisualization();
    }
  };

  const seekAudio = (time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  const startVisualization = () => {
    if (!canvasRef.current || !analyserRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      if (!isPlaying) {
        animationRef.current = requestAnimationFrame(draw);
        return;
      }

      analyserRef.current!.getByteTimeDomainData(dataArray);

      ctx.fillStyle = "rgb(var(--background))";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      if (visualizationMode === "waveform") {
        drawWaveform(ctx, dataArray, canvas);
      } else if (visualizationMode === "spectrum") {
        drawSpectrum(ctx, dataArray, canvas);
      }

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();
  };

  const stopVisualization = () => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
  };

  const drawWaveform = (ctx: CanvasRenderingContext2D, dataArray: Uint8Array, canvas: HTMLCanvasElement) => {
    ctx.lineWidth = 2;
    ctx.strokeStyle = "rgb(var(--primary))";
    ctx.beginPath();

    const sliceWidth = canvas.width / dataArray.length;
    let x = 0;

    for (let i = 0; i < dataArray.length; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * canvas.height) / 2;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();
  };

  const drawSpectrum = (ctx: CanvasRenderingContext2D, dataArray: Uint8Array, canvas: HTMLCanvasElement) => {
    const barWidth = (canvas.width / dataArray.length) * 2.5;
    let x = 0;

    for (let i = 0; i < dataArray.length; i++) {
      const barHeight = (dataArray[i] / 255) * canvas.height;

      const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
      gradient.addColorStop(0, "rgb(var(--primary))");
      gradient.addColorStop(1, "rgba(var(--primary), 0.1)");

      ctx.fillStyle = gradient;
      ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

      x += barWidth + 1;
    }
  };

  const downloadAudio = (file: AudioFile) => {
    const a = document.createElement("a");
    a.href = file.url;
    a.download = file.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    toast.success("Download started");
  };

  const shareAudio = async (file: AudioFile) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: file.name,
          text: `TTS Audio: ${file.name}`,
          url: file.url,
        });
      } catch (error) {
        console.error("Share failed:", error);
      }
    } else {
      navigator.clipboard.writeText(file.url);
      toast.success("Audio URL copied to clipboard");
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div className={`space-y-6 ${isFullscreen ? "fixed inset-0 z-50 bg-background p-6" : ""}`}>
      <audio
        ref={audioRef}
        onTimeUpdate={(e) => setCurrentTime((e.target as HTMLAudioElement).currentTime)}
        onLoadedMetadata={(e) => setDuration((e.target as HTMLAudioElement).duration)}
        onEnded={() => {
          setIsPlaying(false);
          if (!isLooping) setCurrentTime(0);
        }}
        onError={() => {
          setIsPlaying(false);
          toast.error("Audio playback error");
        }}
      />

      {/* Main Player */}
      <Card className="glass border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Volume2 className="w-5 h-5" />
              Audio Player
            </CardTitle>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setVisualizationMode(
                  visualizationMode === "off" ? "waveform" :
                  visualizationMode === "waveform" ? "spectrum" : "off"
                )}
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                {visualizationMode === "off" ? "Show Viz" : visualizationMode}
              </Button>
              <Button variant="outline" size="sm" onClick={toggleFullscreen}>
                <Maximize2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
          <CardDescription>
            Advanced audio playback with real-time visualization
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Visualization */}
          {visualizationMode !== "off" && (
            <div className="w-full">
              <canvas
                ref={canvasRef}
                width={800}
                height={200}
                className="w-full h-48 bg-muted rounded-lg"
              />
            </div>
          )}

          {/* Current Track Info */}
          {currentFile ? (
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-4 rounded-lg bg-muted/50">
                <div className="p-3 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20">
                  <Mic2 className="w-6 h-6 text-purple-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold truncate">{currentFile.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline">{currentFile.provider}</Badge>
                    <span className="text-sm text-muted-foreground">
                      Voice: {currentFile.voice}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <Slider
                  value={[currentTime]}
                  max={duration || 100}
                  step={0.1}
                  onValueChange={(value) => seekAudio(value[0])}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{formatTime(currentTime)}</span>
                  <span>{formatTime(duration)}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              Select an audio file to play
            </div>
          )}

          {/* Controls */}
          <div className="space-y-4">
            {/* Main Controls */}
            <div className="flex items-center justify-center gap-4">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setIsShuffling(!isShuffling)}
                className={isShuffling ? "bg-primary/20" : ""}
              >
                <Shuffle className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => seekAudio(Math.max(0, currentTime - 10))}
                disabled={!currentFile}
              >
                <SkipBack className="w-4 h-4" />
              </Button>
              <Button
                size="lg"
                onClick={() => currentFile && (isPlaying ? pauseAudio() : playAudio(currentFile))}
                disabled={!currentFile}
              >
                {isPlaying ? (
                  <Pause className="w-6 h-6" />
                ) : (
                  <Play className="w-6 h-6" />
                )}
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => seekAudio(Math.min(duration, currentTime + 10))}
                disabled={!currentFile}
              >
                <SkipForward className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setIsLooping(!isLooping)}
                className={isLooping ? "bg-primary/20" : ""}
              >
                <Repeat className="w-4 h-4" />
              </Button>
            </div>

            {/* Secondary Controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleMute}
                >
                  {isMuted ? (
                    <VolumeX className="w-4 h-4" />
                  ) : (
                    <Volume2 className="w-4 h-4" />
                  )}
                </Button>
                <Slider
                  value={[isMuted ? 0 : volume]}
                  max={1}
                  step={0.01}
                  onValueChange={(value) => {
                    setVolume(value[0]);
                    setIsMuted(value[0] === 0);
                  }}
                  className="w-32"
                />
              </div>

              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">Speed:</span>
                <div className="flex gap-1">
                  {[0.5, 0.75, 1.0, 1.25, 1.5, 2.0].map((rate) => (
                    <Button
                      key={rate}
                      variant={playbackRate === rate ? "default" : "outline"}
                      size="sm"
                      onClick={() => {
                        setPlaybackRate(rate);
                        if (audioRef.current) {
                          audioRef.current.playbackRate = rate;
                        }
                      }}
                      className="w-12"
                    >
                      {rate}x
                    </Button>
                  ))}
                </div>
              </div>

              {currentFile && (
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => downloadAudio(currentFile)}>
                    <Download className="w-4 h-4 mr-1" />
                    Download
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => shareAudio(currentFile)}>
                    <Share className="w-4 h-4 mr-1" />
                    Share
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audio Library */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Waves className="w-5 h-5" />
            Audio Library
          </CardTitle>
          <CardDescription>
            Browse and play your synthesized audio files
          </CardDescription>
        </CardHeader>
        <CardContent>
          {audioFiles.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No audio files available. Synthesize some text to get started.
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {audioFiles.map((file) => {
                const isActive = currentFile?.id === file.id;
                return (
                  <div
                    key={file.id}
                    className={`flex items-center gap-3 p-3 rounded-lg transition-colors cursor-pointer ${
                      isActive ? "bg-primary/20" : "hover:bg-muted/50"
                    }`}
                    onClick={() => playAudio(file)}
                  >
                    <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20">
                      <Mic2 className="w-4 h-4 text-purple-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{file.name}</div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Badge variant="outline" className="text-xs">
                          {file.provider}
                        </Badge>
                        <span>{formatTime(file.duration)}</span>
                        <span>{file.createdAt.toLocaleDateString()}</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        downloadAudio(file);
                      }}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

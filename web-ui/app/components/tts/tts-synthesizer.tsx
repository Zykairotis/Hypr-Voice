"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Play,
  Pause,
  Square,
  Download,
  Copy,
  Mic2,
  Zap,
  FileAudio,
  Clock,
  Type,
  Volume2,
  Gauge,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { toast } from "sonner";

interface TTSSynthesizerProps {
  provider: string;
  voice: string;
  onProviderChange: (provider: string) => void;
  onVoiceChange: (voice: string) => void;
}

interface SynthesisJob {
  id: string;
  text: string;
  provider: string;
  voice: string;
  status: "pending" | "synthesizing" | "completed" | "failed";
  progress: number;
  audioUrl?: string;
  duration?: number;
  error?: string;
  createdAt: Date;
}

export default function TTSSynthesizer({
  provider,
  voice,
  onProviderChange,
  onVoiceChange,
}: TTSSynthesizerProps) {
  const [text, setText] = useState("");
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0);
  const [volume, setVolume] = useState(1.0);
  const [emotion, setEmotion] = useState("neutral");
  const [style, setStyle] = useState("conversational");
  const [outputFormat, setOutputFormat] = useState("mp3");
  const [batchMode, setBatchMode] = useState(false);
  const [batchTexts, setBatchTexts] = useState<string[]>([""]);
  const [currentJob, setCurrentJob] = useState<SynthesisJob | null>(null);
  const [jobHistory, setJobHistory] = useState<SynthesisJob[]>([]);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const emotions = ["neutral", "happy", "sad", "excited", "angry", "calm", "surprised"];
  const styles = ["conversational", "narration", "newscast", "customer_service", "audiobook"];

  const sampleTexts = [
    "Hello! This is a test of the text-to-speech system. How does it sound?",
    "Welcome to the Hypr-Voice TTS Control Panel. Enjoy the high-quality audio synthesis.",
    "The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.",
    "In a world of artificial intelligence, natural-sounding speech is crucial for user experience.",
    "Technology is best when it brings people together and makes life more convenient."
  ];

  useEffect(() => {
    // Load job history from localStorage
    const saved = localStorage.getItem("tts-job-history");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setJobHistory(parsed.map((job: any) => ({
          ...job,
          createdAt: new Date(job.createdAt)
        })));
      } catch (error) {
        console.error("Failed to load job history:", error);
      }
    }
  }, []);

  const saveJobHistory = (jobs: SynthesisJob[]) => {
    setJobHistory(jobs);
    localStorage.setItem("tts-job-history", JSON.stringify(jobs));
  };

  const handleSynthesize = async (textToSynthesize?: string) => {
    const textContent = textToSynthesize || text.trim();
    if (!textContent) {
      toast.error("Please enter some text to synthesize");
      return;
    }

    const job: SynthesisJob = {
      id: `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      text: textContent,
      provider,
      voice,
      status: "synthesizing",
      progress: 0,
      createdAt: new Date()
    };

    setCurrentJob(job);
    setIsSynthesizing(true);

    try {
      const response = await fetch("http://localhost:8934/api/tts/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: textContent,
          provider,
          voice,
          speed,
          pitch,
          volume,
          emotion,
          style,
          outputFormat,
          returnUrl: true
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const completedJob: SynthesisJob = {
          ...job,
          status: "completed",
          progress: 100,
          audioUrl: data.audioUrl || data.url,
          duration: data.duration
        };

        setCurrentJob(completedJob);
        const newHistory = [completedJob, ...jobHistory.slice(0, 49)]; // Keep last 50 jobs
        saveJobHistory(newHistory);
        toast.success("Synthesis completed successfully!");

        // Auto-play if enabled
        if (completedJob.audioUrl) {
          playAudio(completedJob.audioUrl);
        }
      } else {
        const error = await response.json();
        throw new Error(error.message || "Synthesis failed");
      }
    } catch (error) {
      const failedJob: SynthesisJob = {
        ...job,
        status: "failed",
        error: error instanceof Error ? error.message : "Unknown error"
      };
      setCurrentJob(failedJob);
      toast.error(`Synthesis failed: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleBatchSynthesize = async () => {
    const validTexts = batchTexts.filter(t => t.trim().length > 0);
    if (validTexts.length === 0) {
      toast.error("Please enter at least one text to synthesize");
      return;
    }

    try {
      const response = await fetch("http://localhost:8934/api/tts/batch-synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          texts: validTexts,
          provider,
          voice,
          speed,
          pitch,
          volume,
          emotion,
          style,
          outputFormat
        }),
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Batch synthesis completed! ${data.results?.length || 0} files created.`);
      } else {
        throw new Error("Batch synthesis failed");
      }
    } catch (error) {
      toast.error(`Batch synthesis failed: ${error instanceof Error ? error.message : "Unknown error"}`);
    }
  };

  const playAudio = (url: string) => {
    if (audioRef.current) {
      audioRef.current.src = url;
      audioRef.current.play();
    }
  };

  const downloadAudio = (url: string, filename: string) => {
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const copyText = () => {
    navigator.clipboard.writeText(text);
    toast.success("Text copied to clipboard");
  };

  const addBatchText = () => {
    setBatchTexts([...batchTexts, ""]);
  };

  const updateBatchText = (index: number, value: string) => {
    const updated = [...batchTexts];
    updated[index] = value;
    setBatchTexts(updated);
  };

  const removeBatchText = (index: number) => {
    setBatchTexts(batchTexts.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <audio ref={audioRef} className="hidden" />

      {/* Text Input */}
      <Card className="glass border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Type className="w-5 h-5" />
                Text Input
              </CardTitle>
              <CardDescription>
                Enter the text you want to convert to speech
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setBatchMode(!batchMode)}
              >
                <FileAudio className="w-4 h-4 mr-2" />
                {batchMode ? "Single" : "Batch"}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {batchMode ? (
            <div className="space-y-3">
              {batchTexts.map((textItem, index) => (
                <div key={index} className="flex gap-2">
                  <Textarea
                    placeholder={`Text ${index + 1}...`}
                    value={textItem}
                    onChange={(e) => updateBatchText(index, e.target.value)}
                    className="flex-1"
                    rows={2}
                  />
                  {batchTexts.length > 1 && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeBatchText(index)}
                    >
                      <Square className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button variant="outline" onClick={addBatchText} className="w-full">
                Add Another Text
              </Button>
            </div>
          ) : (
            <>
              <div className="relative">
                <Textarea
                  placeholder="Enter your text here..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="min-h-[120px] resize-none"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute top-2 right-2"
                  onClick={copyText}
                >
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {sampleTexts.slice(0, 3).map((sample, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => setText(sample)}
                    className="text-xs"
                  >
                    {sample.substring(0, 30)}...
                  </Button>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Audio Parameters */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gauge className="w-5 h-5" />
            Audio Parameters
          </CardTitle>
          <CardDescription>
            Fine-tune the audio output characteristics
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-3">
              <label className="text-sm font-medium flex items-center gap-2">
                <Gauge className="w-4 h-4" />
                Speed: {speed.toFixed(1)}x
              </label>
              <Slider
                value={[speed]}
                onValueChange={(value) => setSpeed(value[0])}
                min={0.5}
                max={2.0}
                step={0.1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0.5x</span>
                <span>Normal</span>
                <span>2.0x</span>
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-medium flex items-center gap-2">
                <Volume2 className="w-4 h-4" />
                Pitch: {pitch > 0 ? "+" : ""}{pitch}
              </label>
              <Slider
                value={[pitch]}
                onValueChange={(value) => setPitch(value[0])}
                min={-12}
                max={12}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>-12</span>
                <span>0</span>
                <span>+12</span>
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-medium">Volume: {Math.round(volume * 100)}%</label>
              <Slider
                value={[volume]}
                onValueChange={(value) => setVolume(value[0])}
                min={0}
                max={1}
                step={0.1}
                className="w-full"
              />
            </div>

            <div className="space-y-3">
              <label className="text-sm font-medium">Output Format</label>
              <Select value={outputFormat} onValueChange={setOutputFormat}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mp3">MP3</SelectItem>
                  <SelectItem value="wav">WAV</SelectItem>
                  <SelectItem value="ogg">OGG</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-3">
              <label className="text-sm font-medium">Emotion</label>
              <Select value={emotion} onValueChange={setEmotion}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {emotions.map((emo) => (
                    <SelectItem key={emo} value={emo}>
                      {emo.charAt(0).toUpperCase() + emo.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-medium">Style</label>
              <Select value={style} onValueChange={setStyle}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {styles.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Synthesize Button and Progress */}
      <Card className="glass border-border/50">
        <CardContent className="pt-6">
          <div className="space-y-4">
            <Button
              className="w-full h-12 text-lg"
              onClick={() => batchMode ? handleBatchSynthesize() : handleSynthesize()}
              disabled={isSynthesizing || (batchMode ? batchTexts.every(t => !t.trim()) : !text.trim())}
            >
              {isSynthesizing ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Synthesizing...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5 mr-2" />
                  {batchMode ? "Batch Synthesize" : "Synthesize to Speech"}
                </>
              )}
            </Button>

            {currentJob && (
              <Card className="bg-muted/50">
                <CardContent className="pt-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {currentJob.status === "completed" && (
                          <CheckCircle2 className="w-5 h-5 text-green-400" />
                        )}
                        {currentJob.status === "failed" && (
                          <AlertCircle className="w-5 h-5 text-red-400" />
                        )}
                        {currentJob.status === "synthesizing" && (
                          <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
                        )}
                        <span className="font-medium">
                          {currentJob.status === "completed" && "Synthesis Complete"}
                          {currentJob.status === "synthesizing" && "Synthesizing..."}
                          {currentJob.status === "failed" && "Synthesis Failed"}
                        </span>
                      </div>
                      <Badge variant="outline">{currentJob.provider}</Badge>
                    </div>

                    {currentJob.status === "synthesizing" && (
                      <div className="space-y-2">
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${currentJob.progress}%` }}
                          />
                        </div>
                        <div className="text-sm text-muted-foreground text-center">
                          {currentJob.progress}% complete
                        </div>
                      </div>
                    )}

                    {currentJob.status === "completed" && currentJob.audioUrl && (
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => playAudio(currentJob.audioUrl!)}
                          className="flex-1"
                        >
                          <Play className="w-4 h-4 mr-2" />
                          Play
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => downloadAudio(currentJob.audioUrl!, `tts_${currentJob.id}.${outputFormat}`)}
                          className="flex-1"
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Download
                        </Button>
                      </div>
                    )}

                    {currentJob.status === "failed" && (
                      <div className="text-sm text-red-400">
                        {currentJob.error}
                      </div>
                    )}

                    <div className="text-xs text-muted-foreground">
                      {currentJob.text.substring(0, 100)}
                      {currentJob.text.length > 100 && "..."}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Job History */}
      {jobHistory.length > 0 && (
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Recent Syntheses
            </CardTitle>
            <CardDescription>
              Your last {jobHistory.length} synthesized audio files
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {jobHistory.slice(0, 5).map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="text-xs">
                        {job.provider}
                      </Badge>
                      {job.status === "completed" && (
                        <Badge className="bg-green-500/20 text-green-400 border-green-500/50 text-xs">
                          Complete
                        </Badge>
                      )}
                    </div>
                    <div className="text-sm font-medium truncate">
                      {job.text}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {job.createdAt.toLocaleTimeString()}
                    </div>
                  </div>
                  {job.status === "completed" && job.audioUrl && (
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => playAudio(job.audioUrl!)}
                      >
                        <Play className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => downloadAudio(job.audioUrl!, `tts_${job.id}.${outputFormat}`)}
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

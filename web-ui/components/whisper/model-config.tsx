"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Save, Cpu, Zap, Settings2 } from "lucide-react";
import { toast } from "sonner";

export default function ModelConfig() {
  const [modelPath, setModelPath] = useState("openai/whisper-large-v3-turbo");
  const [device, setDevice] = useState("cuda");
  const [language, setLanguage] = useState("auto");
  const [translate, setTranslate] = useState(false);
  const [computeType, setComputeType] = useState("int8_float16");
  const [numWorkers, setNumWorkers] = useState(2);
  const [cpuThreads, setCpuThreads] = useState(4);
  const [vadEnabled, setVadEnabled] = useState(true);
  const [vadThreshold, setVadThreshold] = useState(0.1);
  const [minSpeechDuration, setMinSpeechDuration] = useState(0.3);
  const [maxSilenceDuration, setMaxSilenceDuration] = useState(1.5);
  const [isLoading, setIsLoading] = useState(false);
  const [errorCount, setErrorCount] = useState(0);

  useEffect(() => {
    loadModelConfig();
  }, []);

  const loadModelConfig = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/config/model", {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const config = await response.json();
        setModelPath(config.model_path || "openai/whisper-large-v3-turbo");
        setDevice(config.device || "cuda");
        setLanguage(config.language || "auto");
        setTranslate(config.translate || false);
        setComputeType(config.compute_type || "int8_float16");
        setNumWorkers(config.num_workers || 2);
        setCpuThreads(config.cpu_threads || 4);
        setVadEnabled(config.vad_enabled || true);
        setVadThreshold(config.vad_threshold || 0.1);
        setMinSpeechDuration(config.min_speech_duration || 0.3);
        setMaxSilenceDuration(config.max_silence_duration || 1.5);
        setErrorCount(0);
      }
    } catch (error) {
      // Only log once to avoid console spam
      if (errorCount === 0) {
        console.warn("Backend not available. Using default model configuration.");
      }
      setErrorCount(prev => prev + 1);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const config = {
        model_path: modelPath,
        device,
        language,
        translate,
        compute_type: computeType,
        num_workers: numWorkers,
        cpu_threads: cpuThreads,
        vad_enabled: vadEnabled,
        vad_threshold: vadThreshold,
        min_speech_duration: minSpeechDuration,
        max_silence_duration: maxSilenceDuration,
      };

      const response = await fetch("http://localhost:8934/api/config/model", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        toast.success("Model configuration saved successfully", {
          description: "Server restart may be required for changes to take effect"
        });
      } else {
        toast.error("Failed to save configuration");
      }
    } catch (error) {
      toast.error("Error saving configuration");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Model Selection */}
      <div className="space-y-3">
        <Label htmlFor="modelPath" className="text-base font-semibold flex items-center gap-2">
          <Settings2 className="w-4 h-4" />
          Whisper Model
        </Label>
        <Select value={modelPath} onValueChange={setModelPath}>
          <SelectTrigger id="modelPath" className="glass">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="glass border-border/50">
            <SelectItem value="openai/whisper-tiny">
              <div className="flex items-center gap-2">
                <span>Tiny</span>
                <Badge variant="outline" className="text-xs">~75MB</Badge>
              </div>
            </SelectItem>
            <SelectItem value="openai/whisper-base">
              <div className="flex items-center gap-2">
                <span>Base</span>
                <Badge variant="outline" className="text-xs">~150MB</Badge>
              </div>
            </SelectItem>
            <SelectItem value="openai/whisper-small">
              <div className="flex items-center gap-2">
                <span>Small</span>
                <Badge variant="outline" className="text-xs">~500MB</Badge>
              </div>
            </SelectItem>
            <SelectItem value="openai/whisper-medium">
              <div className="flex items-center gap-2">
                <span>Medium</span>
                <Badge variant="outline" className="text-xs">~1.5GB</Badge>
              </div>
            </SelectItem>
            <SelectItem value="openai/whisper-large-v3-turbo">
              <div className="flex items-center gap-2">
                <span>Large V3 Turbo</span>
                <Badge variant="outline" className="text-xs">~1.5GB</Badge>
                <Badge className="text-xs">Recommended</Badge>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
        <p className="text-sm text-muted-foreground">
          Large V3 Turbo offers best accuracy-to-speed ratio
        </p>
      </div>

      <Separator className="bg-border/50" />

      {/* Device & Compute */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-3">
          <Label htmlFor="device" className="text-base font-semibold flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            Device
          </Label>
          <Select value={device} onValueChange={setDevice}>
            <SelectTrigger id="device" className="glass">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="glass border-border/50">
              <SelectItem value="cuda">
                <div className="flex items-center gap-2">
                  <Zap className="w-3 h-3" />
                  <span>CUDA (GPU)</span>
                </div>
              </SelectItem>
              <SelectItem value="cpu">
                <div className="flex items-center gap-2">
                  <Cpu className="w-3 h-3" />
                  <span>CPU</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          <Label htmlFor="computeType" className="text-base font-semibold">
            Compute Type
          </Label>
          <Select value={computeType} onValueChange={setComputeType}>
            <SelectTrigger id="computeType" className="glass">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="glass border-border/50">
              <SelectItem value="int8">INT8</SelectItem>
              <SelectItem value="int8_float16">INT8 + FP16</SelectItem>
              <SelectItem value="float16">FP16</SelectItem>
              <SelectItem value="float32">FP32</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Language Settings */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-3">
          <Label htmlFor="language" className="text-base font-semibold">
            Language
          </Label>
          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger id="language" className="glass">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="glass border-border/50">
              <SelectItem value="auto">Auto Detect</SelectItem>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="es">Spanish</SelectItem>
              <SelectItem value="fr">French</SelectItem>
              <SelectItem value="de">German</SelectItem>
              <SelectItem value="zh">Chinese</SelectItem>
              <SelectItem value="ja">Japanese</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          <Label className="text-base font-semibold">Translate to English</Label>
          <div className="flex items-center h-10 px-4 rounded-lg glass-hover border border-border/50">
            <Switch
              checked={translate}
              onCheckedChange={setTranslate}
            />
            <span className="ml-3 text-sm">{translate ? "Enabled" : "Disabled"}</span>
          </div>
        </div>
      </div>

      <Separator className="bg-border/50" />

      {/* Performance Settings */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">Performance</Label>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label htmlFor="numWorkers">Workers</Label>
            <Badge variant="outline" className="glass">{numWorkers}</Badge>
          </div>
          <Slider
            id="numWorkers"
            value={[numWorkers]}
            onValueChange={([value]) => setNumWorkers(value)}
            min={1}
            max={8}
            step={1}
          />
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label htmlFor="cpuThreads">CPU Threads</Label>
            <Badge variant="outline" className="glass">{cpuThreads}</Badge>
          </div>
          <Slider
            id="cpuThreads"
            value={[cpuThreads]}
            onValueChange={([value]) => setCpuThreads(value)}
            min={1}
            max={16}
            step={1}
          />
        </div>
      </div>

      <Separator className="bg-border/50" />

      {/* VAD Settings */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">Voice Activity Detection (VAD)</Label>
          <Switch
            checked={vadEnabled}
            onCheckedChange={setVadEnabled}
          />
        </div>

        {vadEnabled && (
          <div className="space-y-4 pl-4 border-l-2 border-primary/20">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="vadThreshold">Sensitivity</Label>
                <Badge variant="outline" className="glass">{vadThreshold}</Badge>
              </div>
              <Slider
                id="vadThreshold"
                value={[vadThreshold]}
                onValueChange={([value]) => setVadThreshold(value)}
                min={0.0}
                max={1.0}
                step={0.05}
              />
              <p className="text-xs text-muted-foreground">
                Lower = more sensitive (0.1 for testing, 0.5 normal)
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="minSpeech">Min Speech Duration</Label>
                <Badge variant="outline" className="glass">{minSpeechDuration}s</Badge>
              </div>
              <Slider
                id="minSpeech"
                value={[minSpeechDuration]}
                onValueChange={([value]) => setMinSpeechDuration(value)}
                min={0.1}
                max={2.0}
                step={0.1}
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="maxSilence">Max Silence Duration</Label>
                <Badge variant="outline" className="glass">{maxSilenceDuration}s</Badge>
              </div>
              <Slider
                id="maxSilence"
                value={[maxSilenceDuration]}
                onValueChange={([value]) => setMaxSilenceDuration(value)}
                min={0.5}
                max={5.0}
                step={0.1}
              />
            </div>
          </div>
        )}
      </div>

      {/* Save Button */}
      <div className="pt-4">
        <Button
          onClick={handleSave}
          disabled={isLoading}
          className="w-full glow-hover"
          size="lg"
        >
          <Save className="w-4 h-4 mr-2" />
          {isLoading ? "Saving..." : "Save Model Configuration"}
        </Button>
      </div>
    </div>
  );
}


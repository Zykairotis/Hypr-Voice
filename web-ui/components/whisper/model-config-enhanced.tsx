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
import { Save, Cpu, Zap, Settings2, Download, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

export default function ModelConfigEnhanced() {
  // Basic Settings
  const [modelPath, setModelPath] = useState("openai/whisper-large-v3-turbo");
  const [device, setDevice] = useState("cuda");
  const [language, setLanguage] = useState("auto");
  const [translate, setTranslate] = useState(false);
  const [computeType, setComputeType] = useState("int8");
  
  // Performance Settings
  const [numWorkers, setNumWorkers] = useState(2);
  const [cpuThreads, setCpuThreads] = useState(4);
  const [downloadRoot, setDownloadRoot] = useState("/tmp/whisper-models");
  const [localFilesOnly, setLocalFilesOnly] = useState(false);
  
  // VAD Settings
  const [vadEnabled, setVadEnabled] = useState(true);
  const [vadThreshold, setVadThreshold] = useState(0.1);
  const [minSpeechDuration, setMinSpeechDuration] = useState(0.3);
  const [maxSilenceDuration, setMaxSilenceDuration] = useState(1.5);
  
  // CTranslate2 Advanced Settings
  const [beamSize, setBeamSize] = useState(3);
  const [patience, setPatience] = useState(1.0);
  const [lengthPenalty, setLengthPenalty] = useState(1.0);
  const [temperature, setTemperature] = useState(0.0);
  const [compressionRatioThreshold, setCompressionRatioThreshold] = useState(2.4);
  const [logProbThreshold, setLogProbThreshold] = useState(-1.0);
  const [noSpeechThreshold, setNoSpeechThreshold] = useState(0.6);
  const [interThreads, setInterThreads] = useState(1);
  const [intraThreads, setIntraThreads] = useState(4);
  
  const [isLoading, setIsLoading] = useState(false);
  const [errorCount, setErrorCount] = useState(0);

  useEffect(() => {
    loadModelConfig();
  }, []);

  const loadModelConfig = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/config/model/enhanced", {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const config = await response.json();
        // Basic
        setModelPath(config.model_path || "openai/whisper-large-v3-turbo");
        setDevice(config.device || "cuda");
        setLanguage(config.language || "auto");
        setTranslate(config.translate || false);
        setComputeType(config.compute_type || "int8");
        
        // Performance
        setNumWorkers(config.num_workers || 2);
        setCpuThreads(config.cpu_threads || 4);
        setDownloadRoot(config.download_root || "/tmp/whisper-models");
        setLocalFilesOnly(config.local_files_only || false);
        
        // VAD
        setVadEnabled(config.vad_enabled || true);
        setVadThreshold(config.vad_threshold || 0.1);
        setMinSpeechDuration(config.min_speech_duration || 0.3);
        setMaxSilenceDuration(config.max_silence_duration || 1.5);
        
        // CTranslate2
        setBeamSize(config.beam_size || 3);
        setPatience(config.patience || 1.0);
        setLengthPenalty(config.length_penalty || 1.0);
        setTemperature(config.temperature || 0.0);
        setCompressionRatioThreshold(config.compression_ratio_threshold || 2.4);
        setLogProbThreshold(config.log_prob_threshold || -1.0);
        setNoSpeechThreshold(config.no_speech_threshold || 0.6);
        setInterThreads(config.inter_threads || 1);
        setIntraThreads(config.intra_threads || 4);
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
        // Basic
        model_path: modelPath,
        device,
        language,
        translate,
        compute_type: computeType,
        
        // Performance
        num_workers: numWorkers,
        cpu_threads: cpuThreads,
        download_root: downloadRoot,
        local_files_only: localFilesOnly,
        
        // VAD
        vad_enabled: vadEnabled,
        vad_threshold: vadThreshold,
        min_speech_duration: minSpeechDuration,
        max_silence_duration: maxSilenceDuration,
        
        // CTranslate2
        beam_size: beamSize,
        patience: patience,
        length_penalty: lengthPenalty,
        temperature: temperature,
        compression_ratio_threshold: compressionRatioThreshold,
        log_prob_threshold: logProbThreshold,
        no_speech_threshold: noSpeechThreshold,
        inter_threads: interThreads,
        intra_threads: intraThreads,
      };

      const response = await fetch("http://localhost:8934/api/config/model/enhanced", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        toast.success("Model configuration saved successfully", {
          description: "Server restart required for changes to take effect"
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
          Whisper Model (CTranslate2)
        </Label>
        
        <div className="space-y-2">
          <Select value={modelPath} onValueChange={setModelPath}>
            <SelectTrigger id="modelPath" className="glass">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="glass border-border/50">
              <SelectItem value="tiny">Tiny (~75MB)</SelectItem>
              <SelectItem value="base">Base (~150MB)</SelectItem>
              <SelectItem value="small">Small (~500MB)</SelectItem>
              <SelectItem value="medium">Medium (~1.5GB)</SelectItem>
              <SelectItem value="large-v3-turbo">
                <div className="flex items-center gap-2">
                  Large V3 Turbo (~1.5GB)
                  <Badge className="text-xs">Recommended</Badge>
                </div>
              </SelectItem>
              <SelectItem value="turbo">Turbo (alias for large-v3-turbo)</SelectItem>
            </SelectContent>
          </Select>
          
          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
            <p className="text-sm text-blue-400">
              💡 Or enter a HuggingFace model ID (e.g., "openai/whisper-large-v3-turbo")
            </p>
          </div>
          
          <Input
            value={modelPath}
            onChange={(e) => setModelPath(e.target.value)}
            placeholder="Standard model or HuggingFace model ID"
            className="glass"
          />
        </div>
        
        <p className="text-sm text-muted-foreground">
          Supports standard models and any HuggingFace Whisper model. Will auto-convert to CTranslate2 format.
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
                  CUDA (GPU)
                </div>
              </SelectItem>
              <SelectItem value="cpu">
                <div className="flex items-center gap-2">
                  <Cpu className="w-3 h-3" />
                  CPU
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          <Label htmlFor="computeType" className="text-base font-semibold">
            Quantization
          </Label>
          <Select value={computeType} onValueChange={setComputeType}>
            <SelectTrigger id="computeType" className="glass">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="glass border-border/50">
              {device === "cuda" ? (
                <>
                  <SelectItem value="int8">INT8 (Fastest, 4GB VRAM)</SelectItem>
                  <SelectItem value="int8_float16">INT8 + FP16 (Balanced)</SelectItem>
                  <SelectItem value="float16">FP16 (Best quality, 6GB+ VRAM)</SelectItem>
                </>
              ) : (
                <>
                  <SelectItem value="int8">INT8 (Fastest)</SelectItem>
                  <SelectItem value="float16">FP16</SelectItem>
                  <SelectItem value="float32">FP32 (Best quality)</SelectItem>
                </>
              )}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Separator className="bg-border/50" />

      {/* Model Download Settings */}
      <div className="space-y-3">
        <Label className="text-base font-semibold flex items-center gap-2">
          <Download className="w-4 h-4" />
          Download & Cache Settings
        </Label>
        
        <div className="space-y-3">
          <div>
            <Label htmlFor="downloadRoot">Download Directory</Label>
            <Input
              id="downloadRoot"
              value={downloadRoot}
              onChange={(e) => setDownloadRoot(e.target.value)}
              placeholder="/tmp/whisper-models"
              className="glass mt-2"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Where models and CTranslate2 conversions are cached
            </p>
          </div>
          
          <div className="flex items-center justify-between p-4 rounded-lg glass-hover border border-border/50">
            <div className="space-y-0.5">
              <Label htmlFor="localFilesOnly" className="cursor-pointer">
                Local Files Only
              </Label>
              <p className="text-sm text-muted-foreground">
                Don't download from HuggingFace, use only cached models
              </p>
            </div>
            <Switch
              id="localFilesOnly"
              checked={localFilesOnly}
              onCheckedChange={setLocalFilesOnly}
            />
          </div>
        </div>
      </div>

      <Separator className="bg-border/50" />

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
              <SelectItem value="ko">Korean</SelectItem>
              <SelectItem value="ru">Russian</SelectItem>
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
        <Label className="text-base font-semibold">Performance Tuning</Label>
        
        <div className="grid grid-cols-2 gap-4">
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
            <p className="text-xs text-muted-foreground">
              Parallel processing workers
            </p>
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
            <p className="text-xs text-muted-foreground">
              OpenMP threads per worker
            </p>
          </div>
        </div>
      </div>

      <Separator className="bg-border/50" />

      {/* Advanced CTranslate2 Settings - Accordion */}
      <Accordion type="single" collapsible className="space-y-3">
        <AccordionItem value="ctranslate2" className="border border-border/50 rounded-lg glass-hover px-4">
          <div className="flex items-center justify-between py-4">
            <AccordionTrigger className="hover:no-underline flex-1 py-0">
              <div className="flex items-center gap-3">
                <Sparkles className="w-4 h-4" />
                <span className="font-semibold">CTranslate2 Advanced Settings</span>
                <Badge variant="outline" className="text-xs">Optional</Badge>
              </div>
            </AccordionTrigger>
          </div>
          <AccordionContent>
            <div className="space-y-6 pt-2 pb-4">
              {/* Beam Search */}
              <div className="space-y-4">
                <Label className="text-sm font-semibold">Beam Search Parameters</Label>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="beamSize" className="text-sm">Beam Size</Label>
                    <Badge variant="outline" className="glass">{beamSize}</Badge>
                  </div>
                  <Slider
                    id="beamSize"
                    value={[beamSize]}
                    onValueChange={([value]) => setBeamSize(value)}
                    min={1}
                    max={10}
                    step={1}
                  />
                  <p className="text-xs text-muted-foreground">
                    Higher = better quality, slower (default: 3)
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="patience" className="text-sm">Patience</Label>
                    <Badge variant="outline" className="glass">{patience.toFixed(1)}</Badge>
                  </div>
                  <Slider
                    id="patience"
                    value={[patience]}
                    onValueChange={([value]) => setPatience(value)}
                    min={0.0}
                    max={2.0}
                    step={0.1}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="lengthPenalty" className="text-sm">Length Penalty</Label>
                    <Badge variant="outline" className="glass">{lengthPenalty.toFixed(1)}</Badge>
                  </div>
                  <Slider
                    id="lengthPenalty"
                    value={[lengthPenalty]}
                    onValueChange={([value]) => setLengthPenalty(value)}
                    min={0.0}
                    max={2.0}
                    step={0.1}
                  />
                </div>
              </div>

              <Separator className="bg-border/50" />

              {/* Generation Parameters */}
              <div className="space-y-4">
                <Label className="text-sm font-semibold">Generation Parameters</Label>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="temperature" className="text-sm">Temperature</Label>
                    <Badge variant="outline" className="glass">{temperature.toFixed(2)}</Badge>
                  </div>
                  <Slider
                    id="temperature"
                    value={[temperature]}
                    onValueChange={([value]) => setTemperature(value)}
                    min={0.0}
                    max={1.0}
                    step={0.05}
                  />
                  <p className="text-xs text-muted-foreground">
                    0 = deterministic, higher = more random
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="compressionRatio" className="text-sm">Compression Ratio Threshold</Label>
                    <Badge variant="outline" className="glass">{compressionRatioThreshold.toFixed(1)}</Badge>
                  </div>
                  <Slider
                    id="compressionRatio"
                    value={[compressionRatioThreshold]}
                    onValueChange={([value]) => setCompressionRatioThreshold(value)}
                    min={1.0}
                    max={5.0}
                    step={0.1}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="logProbThreshold" className="text-sm">Log Prob Threshold</Label>
                    <Badge variant="outline" className="glass">{logProbThreshold.toFixed(1)}</Badge>
                  </div>
                  <Slider
                    id="logProbThreshold"
                    value={[logProbThreshold]}
                    onValueChange={([value]) => setLogProbThreshold(value)}
                    min={-2.0}
                    max={0.0}
                    step={0.1}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="noSpeechThreshold" className="text-sm">No Speech Threshold</Label>
                    <Badge variant="outline" className="glass">{noSpeechThreshold.toFixed(2)}</Badge>
                  </div>
                  <Slider
                    id="noSpeechThreshold"
                    value={[noSpeechThreshold]}
                    onValueChange={([value]) => setNoSpeechThreshold(value)}
                    min={0.0}
                    max={1.0}
                    step={0.05}
                  />
                </div>
              </div>

              <Separator className="bg-border/50" />

              {/* Threading */}
              <div className="space-y-4">
                <Label className="text-sm font-semibold">Threading (Advanced)</Label>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="interThreads" className="text-sm">Inter Threads</Label>
                      <Badge variant="outline" className="glass">{interThreads}</Badge>
                    </div>
                    <Slider
                      id="interThreads"
                      value={[interThreads]}
                      onValueChange={([value]) => setInterThreads(value)}
                      min={1}
                      max={8}
                      step={1}
                    />
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="intraThreads" className="text-sm">Intra Threads</Label>
                      <Badge variant="outline" className="glass">{intraThreads}</Badge>
                    </div>
                    <Slider
                      id="intraThreads"
                      value={[intraThreads]}
                      onValueChange={([value]) => setIntraThreads(value)}
                      min={1}
                      max={16}
                      step={1}
                    />
                  </div>
                </div>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* VAD Settings - Accordion */}
        <AccordionItem value="vad" className="border border-border/50 rounded-lg glass-hover px-4">
          <div className="flex items-center justify-between py-4">
            <AccordionTrigger className="hover:no-underline flex-1 py-0">
              <div className="flex items-center gap-3">
                <span className="font-semibold">Voice Activity Detection (VAD)</span>
              </div>
            </AccordionTrigger>
            <Switch
              checked={vadEnabled}
              onCheckedChange={setVadEnabled}
            />
          </div>
          
          {vadEnabled && (
            <AccordionContent>
              <div className="space-y-4 pt-2 pb-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="vadThreshold">Sensitivity</Label>
                    <Badge variant="outline" className="glass">{vadThreshold.toFixed(2)}</Badge>
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
            </AccordionContent>
          )}
        </AccordionItem>
      </Accordion>

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
        <p className="text-xs text-center text-muted-foreground mt-2">
          ⚠️ Server restart required for changes to take effect
        </p>
      </div>
    </div>
  );
}


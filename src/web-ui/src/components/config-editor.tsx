'use client';

import { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ConfigSection } from '@/types';
import {
  Save,
  RotateCcw,
  FileText,
  Settings,
  AudioLines,
  Brain,
  Shield,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Eye,
  EyeOff
} from 'lucide-react';
import { cn } from '@/lib/utils';
import * as yaml from 'js-yaml';

interface ConfigEditorProps {
  configs: ConfigSection[];
  onSaveConfig?: (path: string, content: string) => void;
  onResetConfig?: (path: string) => void;
  className?: string;
}

const defaultConfigs: ConfigSection[] = [
  {
    name: 'Audio Configuration',
    path: 'config/audio_config.yaml',
    content: `# Audio Configuration for Hypr-Voice
# Device settings and audio parameters

# Primary audio device
primary_device:
  name: "default"
  sample_rate: 48000
  channels: 1
  buffer_size: 1024

# Secondary (fallback) audio device
secondary_device:
  name: "usb_microphone"
  sample_rate: 48000
  channels: 1
  buffer_size: 1024

# Whisper audio settings
whisper_audio:
  sample_rate: 16000  # Downsample for Whisper
  format: "int16"
  silence_threshold: 0.01
  min_speech_duration: 0.5

# Voice activity detection
vad:
  aggressiveness: 3  # 0-3, higher is more aggressive
  frame_duration: 30  # ms
  padding_duration: 300  # ms

# Audio level settings
audio_levels:
  show_visualization: true
  auto_gain_control: true
  noise_suppression: true
  echo_cancellation: false`,
    valid: true,
  },
  {
    name: 'Application Profiles',
    path: 'config/app_profiles.yaml',
    content: `# Application Profiles Configuration
# Define behavior for different applications

profiles:
  terminal:
    name: "Terminal Applications"
    applications: ["kitty", "alacritty", "foot", "wezterm"]
    style: "technical"
    preserve_commands: true
    auto_format_commands: true
    llm_provider: "openai"
    custom_instructions: |
      Maintain technical accuracy and command structure.
      Preserve shell syntax and special characters.
      Format code snippets appropriately.

  code_editor:
    name: "Code Editors"
    applications: ["code", "cursor", "windsurf", "nvim"]
    style: "development"
    preserve_syntax: true
    llm_provider: "anthropic"
    custom_instructions: |
      Maintain code syntax and formatting.
      Preserve indentation and structure.
      Add relevant documentation comments.

  browser:
    name: "Web Browsers"
    applications: ["firefox", "chrome", "edge"]
    style: "conversational"
    auto_correct: true
    llm_provider: "xai"
    custom_instructions: |
      Improve clarity and readability.
      Fix common typos and grammatical errors.
      Maintain natural conversational tone.

  communication:
    name: "Communication Apps"
    applications: ["discord", "slack", "telegram", "teams"]
    style: "casual"
    preserve_emoji: true
    llm_provider: "xai"
    custom_instructions: |
      Maintain casual, friendly tone.
      Preserve emojis and slang where appropriate.
      Keep messages concise and clear.

default_profile:
  name: "Default"
  style: "balanced"
  llm_provider: "xai"
  custom_instructions: |
    Provide balanced improvements to text.
    Maintain original intent and meaning.
    Fix obvious errors and improve clarity.`,
    valid: true,
  },
  {
    name: 'LLM Providers',
    path: 'config/llm_providers.yaml',
    content: `# LLM Provider Configuration
# Settings for different AI providers

providers:
  xai:
    name: "xAI Grok"
    enabled: true
    priority: 1
    model: "grok-beta"
    api_base: "https://api.x.ai/v1"
    max_tokens: 4000
    temperature: 0.7
    timeout: 30
    retry_attempts: 3

  openai:
    name: "OpenAI GPT"
    enabled: true
    priority: 2
    model: "gpt-4-turbo"
    api_base: "https://api.openai.com/v1"
    max_tokens: 4000
    temperature: 0.7
    timeout: 30
    retry_attempts: 3

  anthropic:
    name: "Anthropic Claude"
    enabled: true
    priority: 3
    model: "claude-3-sonnet-20240229"
    api_base: "https://api.anthropic.com/v1"
    max_tokens: 4000
    temperature: 0.7
    timeout: 30
    retry_attempts: 3

  ollama:
    name: "Ollama Local"
    enabled: false
    priority: 4
    model: "llama3.1:8b"
    api_base: "http://localhost:11434/v1"
    max_tokens: 4000
    temperature: 0.7
    timeout: 60
    retry_attempts: 2

# Fallback settings
fallback:
  enable_cascading: true
  timeout_threshold: 10000  # ms
  error_threshold: 3  # consecutive errors

# Request optimization
optimization:
  batch_requests: false
  cache_responses: true
  cache_ttl: 3600  # seconds
  compress_requests: true`,
    valid: true,
  },
];

export function ConfigEditor({
  configs = defaultConfigs,
  onSaveConfig,
  onResetConfig,
  className
}: ConfigEditorProps) {
  const [editedConfigs, setEditedConfigs] = useState<ConfigSection[]>(configs);
  const [selectedConfig, setSelectedConfig] = useState<string>(configs[0]?.path || '');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  const selectedConfigData = editedConfigs.find(c => c.path === selectedConfig);

  const validateYAML = useCallback((content: string, path: string): { valid: boolean; error?: string } => {
    try {
      yaml.load(content);
      return { valid: true };
    } catch (error) {
      if (error instanceof Error) {
        return { valid: false, error: error.message };
      }
      return { valid: false, error: 'Invalid YAML syntax' };
    }
  }, []);

  const handleConfigChange = useCallback((path: string, content: string) => {
    const validation = validateYAML(content, path);

    setEditedConfigs(prev => prev.map(config =>
      config.path === path
        ? { ...config, content, valid: validation.valid, error: validation.error }
        : config
    ));

    if (validation.error) {
      setValidationErrors(prev => ({ ...prev, [path]: validation.error! }));
    } else {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[path];
        return newErrors;
      });
    }
  }, [validateYAML]);

  const handleSaveConfig = useCallback((path: string) => {
    const config = editedConfigs.find(c => c.path === path);
    if (config && config.valid) {
      onSaveConfig?.(path, config.content);
    }
  }, [editedConfigs, onSaveConfig]);

  const handleResetConfig = useCallback((path: string) => {
    const originalConfig = configs.find(c => c.path === path);
    if (originalConfig) {
      setEditedConfigs(prev => prev.map(config =>
        config.path === path ? originalConfig : config
      ));
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[path];
        return newErrors;
      });
    }
    onResetConfig?.(path);
  }, [configs, onResetConfig]);

  const getConfigIcon = (name: string) => {
    if (name.includes('Audio')) return <AudioLines className="h-4 w-4" />;
    if (name.includes('Application')) return <Settings className="h-4 w-4" />;
    if (name.includes('LLM')) return <Brain className="h-4 w-4" />;
    return <FileText className="h-4 w-4" />;
  };

  const hasUnsavedChanges = (path: string) => {
    const edited = editedConfigs.find(c => c.path === path);
    const original = configs.find(c => c.path === path);
    return edited && original && edited.content !== original.content;
  };

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Configuration Editor
          </CardTitle>
          <CardDescription>
            Edit and validate Hypr-Voice configuration files with real-time YAML validation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={selectedConfig} onValueChange={setSelectedConfig} className="space-y-4">
            {/* Config List Tabs */}
            <TabsList className="grid w-full grid-cols-3">
              {editedConfigs.map((config) => (
                <TabsTrigger
                  key={config.path}
                  value={config.path}
                  className="flex items-center gap-2"
                >
                  {getConfigIcon(config.name)}
                  <span className="hidden sm:inline">{config.name}</span>
                  <div className="flex items-center gap-1">
                    {config.valid ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <XCircle className="h-3 w-3 text-red-600" />
                    )}
                    {hasUnsavedChanges(config.path) && (
                      <div className="w-2 h-2 bg-blue-500 rounded-full" />
                    )}
                  </div>
                </TabsTrigger>
              ))}
            </TabsList>

            {/* Config Content */}
            {editedConfigs.map((config) => (
              <TabsContent key={config.path} value={config.path} className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-medium flex items-center gap-2">
                      {getConfigIcon(config.name)}
                      {config.name}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {config.path}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant={config.valid ? "default" : "destructive"} className="flex items-center gap-1">
                      {config.valid ? (
                        <CheckCircle className="h-3 w-3" />
                      ) : (
                        <XCircle className="h-3 w-3" />
                      )}
                      {config.valid ? "Valid" : "Invalid"}
                    </Badge>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowSecrets(prev => ({
                        ...prev,
                        [config.path]: !prev[config.path]
                      }))}
                    >
                      {showSecrets[config.path] ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleResetConfig(config.path)}
                      disabled={!hasUnsavedChanges(config.path)}
                    >
                      <RotateCcw className="h-4 w-4 mr-1" />
                      Reset
                    </Button>

                    <Button
                      size="sm"
                      onClick={() => handleSaveConfig(config.path)}
                      disabled={!config.valid || !hasUnsavedChanges(config.path)}
                    >
                      <Save className="h-4 w-4 mr-1" />
                      Save
                    </Button>
                  </div>
                </div>

                {/* Validation Error */}
                {validationErrors[config.path] && (
                  <div className="p-3 border border-red-200 bg-red-50 dark:bg-red-950/20 rounded-lg">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
                      <div>
                        <div className="text-sm font-medium text-red-800 dark:text-red-200">
                          YAML Validation Error
                        </div>
                        <div className="text-xs text-red-600 dark:text-red-300 mt-1">
                          {validationErrors[config.path]}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Config Editor */}
                <div className="space-y-2">
                  <Textarea
                    value={config.content}
                    onChange={(e) => handleConfigChange(config.path, e.target.value)}
                    className={cn(
                      "font-mono text-sm min-h-[500px]",
                      !config.valid && "border-red-500 focus:border-red-500"
                    )}
                    placeholder="Enter YAML configuration..."
                    spellCheck={false}
                  />

                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Info className="h-3 w-3" />
                      <span>YAML configuration with real-time validation</span>
                    </div>
                    <div>
                      {config.content.split('\n').length} lines, {config.content.length} characters
                    </div>
                  </div>
                </div>

                {/* Quick Help */}
                <div className="p-3 bg-muted rounded-lg">
                  <h4 className="text-sm font-medium mb-2">Quick Reference</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-muted-foreground">
                    <div>
                      <code className="bg-background px-1 py-0.5 rounded">key: value</code> - Basic key-value pair
                    </div>
                    <div>
                      <code className="bg-background px-1 py-0.5 rounded">- item</code> - List item
                    </div>
                    <div>
                      <code className="bg-background px-1 py-0.5 rounded"># comment</code> - Comment line
                    </div>
                    <div>
                      <code className="bg-background px-1 py-0.5 rounded">"quoted text"</code> - String with spaces
                    </div>
                  </div>
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
# Configuration Management System

## Overview

The configuration management system provides a comprehensive solution for managing Hypr-Voice's YAML-based configuration files through a web interface. It includes real-time validation, schema checking, backup management, and seamless integration with the existing Unix socket interface.

## Architecture

### Configuration File Structure

The system manages multiple YAML configuration files located in the `hypr-voice/config/` directory:

```
hypr-voice/config/
├── audio_config.yaml          # Audio device and processing settings
├── app_profiles.yaml          # Application-specific behavior profiles
├── llm_providers.yaml         # LLM provider configurations
├── detection_config.yaml      # Voice activity detection settings
├── model_config.json          # Whisper model configuration
├── settings.yaml              # General application settings
├── network.yaml               # Network and connectivity settings
├── security.yaml              # Security and authentication settings
├── performance.yaml           # Performance optimization settings
├── hardware.yaml              # Hardware-specific configurations
├── paths.yaml                 # File path configurations
├── servers.yaml               # Server connection settings
├── ui.yaml                    # User interface preferences
└── global_tools.yaml          # Global tool configurations
```

### Schema-Based Validation System

Each configuration file has an associated JSON schema that defines the structure, types, constraints, and validation rules.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://hypr-voice/config/schemas/audio_config.json",
  "title": "Audio Configuration Schema",
  "description": "Schema for audio device and processing settings",
  "type": "object",
  "properties": {
    "audio": {
      "type": "object",
      "properties": {
        "quality": {
          "type": "object",
          "properties": {
            "sample_rate": {
              "type": "integer",
              "minimum": 8000,
              "maximum": 96000,
              "enum": [8000, 11025, 16000, 22050, 44100, 48000, 88200, 96000],
              "description": "Sample rate in Hz for audio recording",
              "default": 48000
            },
            "channels": {
              "type": "integer",
              "minimum": 1,
              "maximum": 8,
              "enum": [1, 2],
              "description": "Number of audio channels (1=mono, 2=stereo)",
              "default": 1
            },
            "dtype": {
              "type": "string",
              "enum": ["int16", "int24", "int32", "float32"],
              "description": "Audio data type",
              "default": "float32"
            },
            "blocksize": {
              "type": "integer",
              "minimum": 64,
              "maximum": 8192,
              "description": "Block size for audio streaming",
              "default": 2048
            }
          },
          "required": ["sample_rate", "channels"]
        },
        "devices": {
          "type": "object",
          "properties": {
            "primary": {
              "$ref": "#/definitions/AudioDevice"
            },
            "secondary": {
              "$ref": "#/definitions/AudioDevice"
            },
            "auto_fallback": {
              "type": "boolean",
              "description": "Automatically switch to secondary device if primary fails",
              "default": false
            }
          },
          "required": ["primary"]
        }
      },
      "required": ["quality", "devices"]
    }
  },
  "required": ["audio"],
  "definitions": {
    "AudioDevice": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "Device name or index"
        },
        "description": {
          "type": "string",
          "description": "Human-readable device description"
        },
        "auto_detect": {
          "type": "boolean",
          "description": "Automatically detect device",
          "default": true
        }
      },
      "required": ["name"]
    }
  }
}
```

### Validation Pipeline

```typescript
// Configuration validation pipeline
interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  suggestions: string[];
  metadata: ValidationMetadata;
}

interface ValidationError {
  path: string;           // JSON path to the error location
  message: string;        // Human-readable error message
  code: string;          // Error code for categorization
  value: any;            // The invalid value
  constraint: any;       // The constraint that was violated
  severity: 'error' | 'warning' | 'info';
}

interface ValidationMetadata {
  schema_version: string;
  validation_time: string;
  file_size: number;
  checksum: string;
  dependencies_checked: string[];
}

class ConfigurationValidator {
  private schemas: Map<string, JSONSchema> = new Map();
  private yamlParser: YAMLParser;
  private jsonSchemaValidator: JSONSchemaValidator;

  constructor() {
    this.yamlParser = new YAMLParser();
    this.jsonSchemaValidator = new JSONSchemaValidator();
    this.loadSchemas();
  }

  async validateConfig(
    filename: string,
    content: string
  ): Promise<ValidationResult> {
    const result: ValidationResult = {
      valid: true,
      errors: [],
      warnings: [],
      suggestions: [],
      metadata: {
        schema_version: '1.0.0',
        validation_time: new Date().toISOString(),
        file_size: content.length,
        checksum: this.calculateChecksum(content),
        dependencies_checked: []
      }
    };

    try {
      // Parse YAML
      const configData = this.yamlParser.parse(content);

      // Get schema for this file
      const schema = this.getSchema(filename);
      if (!schema) {
        result.errors.push({
          path: '$',
          message: `No schema found for ${filename}`,
          code: 'SCHEMA_NOT_FOUND',
          value: null,
          constraint: null,
          severity: 'error'
        });
        result.valid = false;
        return result;
      }

      // Validate against schema
      const schemaValidation = this.jsonSchemaValidator.validate(
        configData,
        schema
      );

      // Convert JSON schema validation errors to our format
      schemaValidation.errors.forEach(error => {
        result.errors.push({
          path: error.instancePath || error.path,
          message: error.message,
          code: 'SCHEMA_VALIDATION',
          value: error.data,
          constraint: error.schema,
          severity: 'error'
        });
      });

      // Perform custom validation rules
      await this.performCustomValidation(filename, configData, result);

      // Check for deprecated settings
      this.checkDeprecations(filename, configData, result);

      // Provide suggestions for optimization
      this.generateSuggestions(filename, configData, result);

      result.valid = result.errors.length === 0;

    } catch (error) {
      if (error instanceof YAMLParserError) {
        result.errors.push({
          path: error.line ? `line:${error.line}` : '$',
          message: `YAML syntax error: ${error.message}`,
          code: 'YAML_SYNTAX',
          value: null,
          constraint: null,
          severity: 'error'
        });
      } else {
        result.errors.push({
          path: '$',
          message: `Validation error: ${error.message}`,
          code: 'VALIDATION_ERROR',
          value: null,
          constraint: null,
          severity: 'error'
        });
      }
      result.valid = false;
    }

    return result;
  }

  private async performCustomValidation(
    filename: string,
    data: any,
    result: ValidationResult
  ): Promise<void> {
    // Audio-specific validations
    if (filename === 'audio_config.yaml') {
      await this.validateAudioConfig(data, result);
    }

    // Application profile validations
    if (filename === 'app_profiles.yaml') {
      await this.validateAppProfiles(data, result);
    }

    // LLM provider validations
    if (filename === 'llm_providers.yaml') {
      await this.validateLLMProviders(data, result);
    }
  }

  private async validateAudioConfig(
    data: any,
    result: ValidationResult
  ): Promise<void> {
    const audio = data.audio;
    if (!audio) return;

    // Validate sample rate compatibility
    const sampleRate = audio.quality?.sample_rate;
    if (sampleRate) {
      // Check if sample rate is compatible with Whisper
      if (![8000, 16000, 48000].includes(sampleRate)) {
        result.warnings.push({
          path: 'audio.quality.sample_rate',
          message: `Sample rate ${sampleRate} may require resampling for optimal Whisper performance`,
          code: 'SAMPLE_RATE_COMPATIBILITY',
          value: sampleRate,
          constraint: { recommended: [16000, 48000] },
          severity: 'warning'
        });
      }
    }

    // Validate device availability
    if (audio.devices?.primary?.name) {
      const availableDevices = await this.getAvailableAudioDevices();
      const primaryDevice = audio.devices.primary.name;

      if (!availableDevices.includes(primaryDevice) && primaryDevice !== 'default') {
        result.errors.push({
          path: 'audio.devices.primary.name',
          message: `Audio device '${primaryDevice}' not found on system`,
          code: 'DEVICE_NOT_FOUND',
          value: primaryDevice,
          constraint: { available: availableDevices },
          severity: 'error'
        });
      }
    }

    // Validate channel configuration
    const channels = audio.quality?.channels;
    if (channels === 2 && !audio.devices.primary?.supports_stereo) {
      result.warnings.push({
        path: 'audio.quality.channels',
        message: 'Stereo recording requested but device may not support it',
        code: 'CHANNEL_SUPPORT',
        value: channels,
        constraint: null,
        severity: 'warning'
      });
    }
  }

  private generateSuggestions(
    filename: string,
    data: any,
    result: ValidationResult
  ): void {
    // Performance optimization suggestions
    if (filename === 'audio_config.yaml') {
      const blockSize = data.audio?.quality?.blocksize;
      if (blockSize && blockSize < 1024) {
        result.suggestions.push(
          'Consider increasing block size to 1024 or higher for better performance'
        );
      }

      const sampleRate = data.audio?.quality?.sample_rate;
      if (sampleRate && sampleRate > 48000) {
        result.suggestions.push(
          'Sample rates above 48kHz provide diminishing returns for voice applications'
        );
      }
    }

    // Security suggestions
    if (filename === 'network.yaml') {
      if (!data.encryption?.enabled) {
        result.suggestions.push(
          'Consider enabling encryption for secure communication'
        );
      }
    }
  }
}
```

### Configuration Manager

```typescript
// Main configuration management class
class ConfigurationManager {
  private configDir: string;
  private backupDir: string;
  private validator: ConfigurationValidator;
  private watcher: FileWatcher;
  private lockManager: ConfigLockManager;

  constructor(configDir: string) {
    this.configDir = configDir;
    this.backupDir = path.join(configDir, 'backups');
    this.validator = new ConfigurationValidator();
    this.lockManager = new ConfigLockManager();

    this.ensureDirectories();
    this.setupFileWatcher();
  }

  async getConfig(filename: string): Promise<ConfigResponse> {
    await this.lockManager.acquireReadLock(filename);

    try {
      const filePath = path.join(this.configDir, filename);
      const content = await fs.readFile(filePath, 'utf-8');
      const schema = this.getSchema(filename);
      const stats = await fs.stat(filePath);

      return {
        filename,
        content,
        schema,
        metadata: {
          last_modified: stats.mtime.toISOString(),
          checksum: this.calculateChecksum(content),
          version: await this.getConfigVersion(filename)
        }
      };
    } finally {
      this.lockManager.releaseReadLock(filename);
    }
  }

  async updateConfig(
    filename: string,
    content: string,
    options: ConfigUpdateOptions = {}
  ): Promise<ConfigUpdateResponse> {
    const { backup = true, validate = true, force = false } = options;

    await this.lockManager.acquireWriteLock(filename);

    try {
      // Validate new content
      if (validate && !force) {
        const validation = await this.validator.validateConfig(filename, content);
        if (!validation.valid) {
          return {
            success: false,
            message: 'Configuration validation failed',
            validation,
            requires_restart: false
          };
        }
      }

      const filePath = path.join(this.configDir, filename);

      // Create backup if requested
      let backupPath: string | undefined;
      if (backup && await fs.pathExists(filePath)) {
        backupPath = await this.createBackup(filename);
      }

      // Write new content
      await fs.writeFile(filePath, content, 'utf-8');

      // Validate after write to ensure consistency
      if (validate) {
        const validation = await this.validator.validateConfig(filename, content);
        if (!validation.valid) {
          // Rollback if validation failed
          if (backupPath) {
            await fs.restore(backupPath, filePath);
          }
          return {
            success: false,
            message: 'Configuration validation failed after write',
            validation,
            requires_restart: false
          };
        }
      }

      // Check if restart is required
      const requiresRestart = await this.checkRestartRequirement(filename, content);

      // Notify system of configuration change
      await this.notifyConfigChange(filename, content);

      return {
        success: true,
        message: 'Configuration updated successfully',
        backup_created: backupPath,
        validation: await this.validator.validateConfig(filename, content),
        requires_restart
      };

    } catch (error) {
      return {
        success: false,
        message: `Failed to update configuration: ${error.message}`,
        validation: { valid: false, errors: [], warnings: [], suggestions: [], metadata: {} },
        requires_restart: false
      };
    } finally {
      this.lockManager.releaseWriteLock(filename);
    }
  }

  async listConfigs(): Promise<ConfigFileList> {
    const files = await fs.readdir(this.configDir);
    const configFiles: ConfigFile[] = [];

    for (const file of files) {
      if (this.isConfigFile(file)) {
        const filePath = path.join(this.configDir, file);
        const stats = await fs.stat(filePath);

        configFiles.push({
          name: file,
          path: filePath,
          description: this.getConfigDescription(file),
          last_modified: stats.mtime.toISOString(),
          size: stats.size
        });
      }
    }

    return { files: configFiles };
  }

  private async createBackup(filename: string): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupName = `${filename}.${timestamp}`;
    const backupPath = path.join(this.backupDir, backupName);

    const sourcePath = path.join(this.configDir, filename);
    await fs.copy(sourcePath, backupPath);

    // Clean old backups (keep last 10)
    await this.cleanOldBackups(filename);

    return backupPath;
  }

  private async notifyConfigChange(filename: string, content: any): Promise<void> {
    // Send notification to Hypr-Voice via Unix socket
    const socketClient = new UnixSocketClient('/tmp/hypr-voice.sock');

    try {
      await socketClient.sendCommand({
        type: 'config_change',
        filename,
        content: content,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.warn('Failed to notify config change:', error);
    }
  }

  private async checkRestartRequirement(
    filename: string,
    content: any
  ): Promise<boolean> {
    // Certain configuration changes require service restart
    const restartRequiredFiles = [
      'audio_config.yaml',
      'detection_config.yaml',
      'model_config.json'
    ];

    if (restartRequiredFiles.includes(filename)) {
      return true;
    }

    // Check for specific changes that require restart
    const data = this.yamlParser.parse(content);

    if (filename === 'llm_providers.yaml') {
      // LLM provider changes may require restart
      return true;
    }

    return false;
  }

  private setupFileWatcher(): void {
    this.watcher = new FileWatcher(this.configDir, {
      ignored: /backups/,
      persistent: true
    });

    this.watcher.on('change', async (filename) => {
      if (this.isConfigFile(filename)) {
        // Validate config file after external change
        const filePath = path.join(this.configDir, filename);
        const content = await fs.readFile(filePath, 'utf-8');
        const validation = await this.validator.validateConfig(filename, content);

        if (!validation.valid) {
          console.warn(`Configuration validation failed for ${filename}:`, validation.errors);
          // Send notification via WebSocket
          this.broadcastValidationWarning(filename, validation);
        }
      }
    });
  }
}
```

### Web UI Components

#### Configuration Editor

```typescript
// src/components/configuration/config-editor.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  ConfigResponse,
  ConfigUpdateResponse,
  ConfigValidation
} from '@/types/config';
import { useConfig } from '@/hooks/use-config';
import { useWebSocket } from '@/hooks/use-websocket';

interface ConfigEditorProps {
  filename: string;
  onSave?: (filename: string, content: string) => void;
  className?: string;
}

export const ConfigEditor: React.FC<ConfigEditorProps> = ({
  filename,
  onSave,
  className
}) => {
  const {
    config,
    validation,
    isLoading,
    updateConfig,
    validateConfig,
    resetConfig
  } = useConfig(filename);

  const [content, setContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  const [isValid, setIsValid] = useState(true);
  const [isDirty, setIsDirty] = useState(false);
  const [autoSave, setAutoSave] = useState(false);
  const [showLineNumbers, setShowLineNumbers] = useState(true);

  const ws = useWebSocket();

  // Debounced validation
  const debouncedValidate = useCallback(
    debounce((value: string) => {
      validateConfig(filename, value);
    }, 500),
    [filename, validateConfig]
  );

  useEffect(() => {
    if (config?.content) {
      setContent(config.content);
      setOriginalContent(config.content);
      setIsDirty(false);
    }
  }, [config]);

  useEffect(() => {
    if (validation) {
      setIsValid(validation.valid);
    }
  }, [validation]);

  useEffect(() => {
    // Listen for external config changes
    const unsubscribe = ws.addMessageHandler('config_change', (data) => {
      if (data.filename === filename) {
        // Config was changed externally
        if (isDirty) {
          // Ask user if they want to reload
          if (confirm('Configuration was changed externally. Reload?')) {
            resetConfig();
          }
        } else {
          resetConfig();
        }
      }
    });

    ws.subscribe(['config_change']);

    return unsubscribe;
  }, [filename, isDirty, resetConfig, ws]);

  const handleContentChange = (value: string) => {
    setContent(value);
    setIsDirty(true);

    // Auto-save if enabled
    if (autoSave && isValid) {
      handleSave(value);
    }

    // Validate content
    debouncedValidate(value);
  };

  const handleSave = async (contentToSave?: string) => {
    const saveContent = contentToSave || content;

    try {
      const result: ConfigUpdateResponse = await updateConfig(
        filename,
        saveContent,
        { backup: true, validate: true }
      );

      if (result.success) {
        setIsDirty(false);
        setOriginalContent(saveContent);
        onSave?.(filename, saveContent);

        // Show restart notification if needed
        if (result.requires_restart) {
          showRestartNotification();
        }
      }
    } catch (error) {
      console.error('Failed to save config:', error);
    }
  };

  const handleReset = () => {
    setContent(originalContent);
    setIsDirty(false);
  };

  const handleFormatYaml = () => {
    try {
      const formatted = formatYaml(content);
      setContent(formatted);
      setIsDirty(true);
    } catch (error) {
      console.error('Failed to format YAML:', error);
    }
  };

  const showRestartNotification = () => {
    // Show toast notification about restart requirement
    toast({
      title: "Restart Required",
      description: "The server needs to be restarted for these changes to take effect.",
      action: (
        <Button onClick={() => restartServer()}>
          Restart Server
        </Button>
      )
    });
  };

  const getLineNumbers = () => {
    const lines = content.split('\n');
    return lines.map((_, index) => (
      <div key={index} className="text-gray-400 text-right pr-2 select-none">
        {index + 1}
      </div>
    ));
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {filename}
            {isDirty && <Badge variant="outline">Modified</Badge>}
          </CardTitle>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch
                id="auto-save"
                checked={autoSave}
                onCheckedChange={setAutoSave}
              />
              <Label htmlFor="auto-save">Auto Save</Label>
            </div>

            <div className="flex items-center gap-2">
              <Switch
                id="line-numbers"
                checked={showLineNumbers}
                onCheckedChange={setShowLineNumbers}
              />
              <Label htmlFor="line-numbers">Line Numbers</Label>
            </div>

            {validation && (
              <Badge variant={validation.valid ? 'default' : 'destructive'}>
                {validation.valid ? 'Valid' : 'Invalid'}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs defaultValue="editor" className="w-full">
          <TabsList>
            <TabsTrigger value="editor">Editor</TabsTrigger>
            <TabsTrigger value="validation">Validation</TabsTrigger>
            <TabsTrigger value="schema">Schema</TabsTrigger>
            <TabsTrigger value="preview">Preview</TabsTrigger>
          </TabsList>

          <TabsContent value="editor" className="space-y-4">
            <div className="flex gap-2 mb-4">
              <Button
                onClick={() => handleSave()}
                disabled={!isDirty || !isValid}
                size="sm"
              >
                Save
              </Button>

              <Button
                onClick={handleReset}
                disabled={!isDirty}
                variant="outline"
                size="sm"
              >
                Reset
              </Button>

              <Button
                onClick={handleFormatYaml}
                variant="outline"
                size="sm"
              >
                Format YAML
              </Button>
            </div>

            <div className="relative border rounded-md">
              {showLineNumbers && (
                <div className="absolute left-0 top-0 bottom-0 w-12 bg-gray-50 border-r overflow-hidden">
                  <div className="p-2 text-sm font-mono">
                    {getLineNumbers()}
                  </div>
                </div>
              )}

              <Textarea
                value={content}
                onChange={(e) => handleContentChange(e.target.value)}
                className={`min-h-[500px] font-mono text-sm ${
                  showLineNumbers ? 'pl-14' : ''
                }`}
                placeholder="Enter YAML configuration..."
                spellCheck={false}
              />
            </div>
          </TabsContent>

          <TabsContent value="validation" className="space-y-4">
            <ValidationPanel validation={validation} />
          </TabsContent>

          <TabsContent value="schema" className="space-y-4">
            <SchemaPanel schema={config?.schema} />
          </TabsContent>

          <TabsContent value="preview" className="space-y-4">
            <PreviewPanel content={content} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
```

#### Validation Panel Component

```typescript
// src/components/configuration/validation-panel.tsx
import React from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ConfigValidation } from '@/types/config';

interface ValidationPanelProps {
  validation: ConfigValidation | null;
}

export const ValidationPanel: React.FC<ValidationPanelProps> = ({
  validation
}) => {
  if (!validation) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500">No validation results available</p>
        </CardContent>
      </Card>
    );
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return 'destructive';
      case 'warning': return 'default';
      case 'info': return 'secondary';
      default: return 'outline';
    }
  };

  return (
    <div className="space-y-4">
      {validation.errors.length > 0 && (
        <Alert variant="destructive">
          <AlertDescription>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge variant="destructive">
                  {validation.errors.length} Errors
                </Badge>
                <span>Configuration has critical issues that must be fixed</span>
              </div>

              <div className="space-y-2">
                {validation.errors.map((error, index) => (
                  <div key={index} className="border-l-4 border-red-500 pl-4">
                    <div className="flex items-center gap-2 mb-1">
                      <code className="bg-red-100 px-2 py-1 rounded text-sm">
                        {error.path}
                      </code>
                      <Badge variant={getSeverityColor(error.severity)}>
                        {error.severity}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-700">{error.message}</p>
                    {error.value !== undefined && (
                      <p className="text-xs text-gray-500">
                        Current value: {JSON.stringify(error.value)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {validation.warnings.length > 0 && (
        <Alert>
          <AlertDescription>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge variant="default">
                  {validation.warnings.length} Warnings
                </Badge>
                <span>Configuration has potential issues</span>
              </div>

              <div className="space-y-2">
                {validation.warnings.map((warning, index) => (
                  <div key={index} className="border-l-4 border-yellow-500 pl-4">
                    <div className="flex items-center gap-2 mb-1">
                      <code className="bg-yellow-100 px-2 py-1 rounded text-sm">
                        {warning.path}
                      </code>
                      <Badge variant={getSeverityColor(warning.severity)}>
                        {warning.severity}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-700">{warning.message}</p>
                  </div>
                ))}
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {validation.suggestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Suggestions</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {validation.suggestions.map((suggestion, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-blue-500 mt-1">•</span>
                  <span className="text-sm">{suggestion}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {validation.valid && validation.errors.length === 0 && (
        <Alert>
          <AlertDescription>
            <div className="flex items-center gap-2">
              <Badge variant="default">Valid</Badge>
              <span>Configuration is valid and ready to use</span>
            </div>
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Validation Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Schema Version:</span>
              <p>{validation.metadata.schema_version}</p>
            </div>
            <div>
              <span className="font-medium">Validated At:</span>
              <p>{new Date(validation.metadata.validation_time).toLocaleString()}</p>
            </div>
            <div>
              <span className="font-medium">File Size:</span>
              <p>{validation.metadata.file_size} bytes</p>
            </div>
            <div>
              <span className="font-medium">Checksum:</span>
              <p className="font-mono text-xs">
                {validation.metadata.checksum.substring(0, 16)}...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
```

### API Bridge Integration

```python
# api_bridge/routers/config.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import asyncio
from datetime import datetime

from ..models.config import (
    ConfigFile,
    ConfigResponse,
    ConfigUpdateRequest,
    ConfigUpdateResponse,
    ConfigValidationRequest,
    ConfigValidationResponse
)
from ..services.config_manager import ConfigurationManager
from ..services.validation_service import ValidationService
from ..utils.auth import get_current_user
from ..utils.dependencies import get_config_manager

router = APIRouter(prefix="/api/config", tags=["configuration"])

@router.get("/list", response_model=List[ConfigFile])
async def list_config_files(
    config_manager: ConfigurationManager = Depends(get_config_manager),
    current_user = Depends(get_current_user)
):
    """List all available configuration files"""
    try:
        result = await config_manager.list_configs()
        return result.files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{filename}", response_model=ConfigResponse)
async def get_config(
    filename: str,
    config_manager: ConfigurationManager = Depends(get_config_manager),
    current_user = Depends(get_current_user)
):
    """Get specific configuration file content"""
    try:
        result = await config_manager.getConfig(filename)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Configuration file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{filename}", response_model=ConfigUpdateResponse)
async def update_config(
    filename: str,
    request: ConfigUpdateRequest,
    background_tasks: BackgroundTasks,
    config_manager: ConfigurationManager = Depends(get_config_manager),
    current_user = Depends(get_current_user)
):
    """Update configuration file"""
    try:
        result = await config_manager.updateConfig(
            filename=filename,
            content=request.content,
            backup=request.backup,
            validate=request.validate,
            force=False
        )

        # Add background task to notify about the change
        if result.success:
            background_tasks.add_task(
                notify_config_change,
                filename,
                current_user.username,
                result.requires_restart
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate", response_model=ConfigValidationResponse)
async def validate_config(
    request: ConfigValidationRequest,
    validation_service: ValidationService = Depends(),
    current_user = Depends(get_current_user)
):
    """Validate configuration without saving"""
    try:
        result = await validation_service.validateConfig(
            filename=request.filename,
            content=request.content
        )
        return ConfigValidationResponse(
            valid=result.valid,
            errors=result.errors,
            warnings=result.warnings,
            suggestions=result.suggestions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schemas/{filename}")
async def get_config_schema(
    filename: str,
    config_manager: ConfigurationManager = Depends(get_config_manager),
    current_user = Depends(get_current_user)
):
    """Get JSON schema for configuration file"""
    try:
        schema = await config_manager.getSchema(filename)
        if not schema:
            raise HTTPException(status_code=404, detail="Schema not found")
        return schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/{filename}")
async def list_config_backups(
    filename: str,
    config_manager: ConfigurationManager = Depends(get_config_manager),
    current_user = Depends(get_current_user)
):
    """List available backups for configuration file"""
    try:
        backups = await config_manager.listBackups(filename)
        return {"backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/{filename}/restore")
async def restore_config_backup(
    filename: str,
    backup_timestamp: str,
    config_manager: ConfigurationManager = Depends(get_config_manager),
    current_user = Depends(get_current_user)
):
    """Restore configuration from backup"""
    try:
        result = await config_manager.restoreFromBackup(
            filename=filename,
            backup_timestamp=backup_timestamp
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def notify_config_change(filename: str, username: str, requires_restart: bool):
    """Background task to notify about configuration changes"""
    # Send WebSocket notification
    websocket_manager.broadcast({
        "type": "config_change",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "filename": filename,
            "applied_by": username,
            "requires_restart": requires_restart
        }
    })

    # Log the change
    logger.info(f"Configuration {filename} updated by {username}")

    # If restart is required, notify the system
    if requires_restart:
        await notify_restart_required(filename)
```

This comprehensive configuration management system provides:

1. **Real-time YAML validation** with JSON schema support
2. **Automatic backup and rollback** capabilities
3. **File watching** for external changes
4. **Concurrent access control** with locking mechanisms
5. **Rich web UI** with syntax highlighting and validation feedback
6. **WebSocket integration** for real-time notifications
7. **Schema-driven forms** for easier configuration editing
8. **Performance optimization** suggestions and warnings

The system maintains compatibility with the existing Hypr-Voice architecture while providing modern web-based configuration management capabilities.
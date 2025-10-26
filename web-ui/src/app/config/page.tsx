'use client';

import { useState } from 'react';
import { ConfigEditor } from '@/components/config-editor';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Settings,
  FileText,
  Download,
  Upload,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Info,
  Shield
} from 'lucide-react';
import { ConfigSection } from '@/types';

export default function ConfigurationPage() {
  const [configs, setConfigs] = useState<ConfigSection[]>([]);
  const [lastSaveTime, setLastSaveTime] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);

  const handleSaveConfig = async (path: string, content: string) => {
    setIsSaving(true);
    try {
      // Simulate API call to save configuration
      await new Promise(resolve => setTimeout(resolve, 1000));

      setConfigs(prev => prev.map(config =>
        config.path === path ? { ...config, content } : config
      ));
      setLastSaveTime(new Date());

      showNotification('success', `Configuration saved: ${path}`);
    } catch (error) {
      showNotification('error', `Failed to save configuration: ${path}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetConfig = (path: string) => {
    setConfigs(prev => prev.map(config =>
      config.path === path
        ? { ...config, content: getDefaultConfigContent(config.name) }
        : config
    ));
    showNotification('info', `Configuration reset: ${path}`);
  };

  const handleExportConfigs = () => {
    const configData = JSON.stringify(configs, null, 2);
    const blob = new Blob([configData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hypr-voice-configs-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showNotification('success', 'Configurations exported successfully');
  };

  const handleImportConfigs = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const importedConfigs = JSON.parse(e.target?.result as string);
          setConfigs(importedConfigs);
          showNotification('success', 'Configurations imported successfully');
        } catch (error) {
          showNotification('error', 'Failed to import configurations');
        }
      };
      reader.readAsText(file);
    }
  };

  const handleValidateAllConfigs = () => {
    const invalidConfigs = configs.filter(config => !config.valid);
    if (invalidConfigs.length === 0) {
      showNotification('success', 'All configurations are valid');
    } else {
      showNotification('error', `${invalidConfigs.length} configurations have validation errors`);
    }
  };

  const showNotification = (type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 3000);
  };

  const getDefaultConfigContent = (name: string): string => {
    // Return default content based on config name
    return `# Default configuration for ${name}\n# Add your settings here\n`;
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Configuration</h1>
          <p className="text-muted-foreground">
            Manage and edit Hypr-Voice configuration files
          </p>
        </div>
        <div className="flex items-center gap-2">
          {lastSaveTime && (
            <Badge variant="outline" className="flex items-center gap-1">
              <CheckCircle className="h-3 w-3" />
              Last saved: {lastSaveTime.toLocaleTimeString()}
            </Badge>
          )}
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <Alert className={cn(
          notification.type === 'success' && "border-green-200 bg-green-50 dark:bg-green-950/20",
          notification.type === 'error' && "border-red-200 bg-red-50 dark:bg-red-950/20",
          notification.type === 'info' && "border-blue-200 bg-blue-50 dark:bg-blue-950/20"
        )}>
          <div className="flex items-center gap-2">
            {notification.type === 'success' && <CheckCircle className="h-4 w-4 text-green-600" />}
            {notification.type === 'error' && <AlertTriangle className="h-4 w-4 text-red-600" />}
            {notification.type === 'info' && <Info className="h-4 w-4 text-blue-600" />}
            <AlertDescription>{notification.message}</AlertDescription>
          </div>
        </Alert>
      )}

      {/* Action Bar */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Configuration Management
          </CardTitle>
          <CardDescription>
            Import, export, and validate configuration files
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={handleValidateAllConfigs}
              className="flex items-center gap-2"
            >
              <Shield className="h-4 w-4" />
              Validate All
            </Button>

            <Button
              variant="outline"
              onClick={handleExportConfigs}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export All
            </Button>

            <div className="relative">
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={() => document.getElementById('import-configs')?.click()}
              >
                <Upload className="h-4 w-4" />
                Import
              </Button>
              <input
                id="import-configs"
                type="file"
                accept=".json"
                onChange={handleImportConfigs}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
            </div>

            <Button
              variant="outline"
              className="flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Reload from Disk
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Configuration Editor */}
      <ConfigEditor
        configs={configs}
        onSaveConfig={handleSaveConfig}
        onResetConfig={handleResetConfig}
      />

      {/* Configuration Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-5 w-5" />
            Configuration Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-2">File Locations</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• Audio: <code className="bg-muted px-1 py-0.5 rounded">~/.config/hypr-voice/audio_config.yaml</code></div>
                <div>• Applications: <code className="bg-muted px-1 py-0.5 rounded">~/.config/hypr-voice/app_profiles.yaml</code></div>
                <div>• LLM Providers: <code className="bg-muted px-1 py-0.5 rounded">~/.config/hypr-voice/llm_providers.yaml</code></div>
              </div>
            </div>

            <div>
              <h4 className="font-medium mb-2">Best Practices</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>• Always validate YAML syntax before saving</div>
                <div>• Keep API keys and secrets secure</div>
                <div>• Test configuration changes in a safe environment</div>
                <div>• Backup configurations before making changes</div>
              </div>
            </div>
          </div>

          <div className="p-4 bg-muted rounded-lg">
            <h4 className="font-medium mb-2">Security Notice</h4>
            <p className="text-sm text-muted-foreground">
              Configuration files may contain sensitive information such as API keys and personal settings.
              Ensure proper file permissions and avoid sharing configuration files publicly.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper function for className conditional styling
function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
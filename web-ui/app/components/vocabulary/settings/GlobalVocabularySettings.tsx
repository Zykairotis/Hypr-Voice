'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Settings, Save, RotateCcw, Book, Code, MessageSquare } from 'lucide-react';
import { vocabularyAPI } from '@/lib/vocabulary/api';

interface GlobalSettings {
  technicalTerms: string[];
  programmingKeywords: string[];
  commonCorrections: Record<string, string>;
  enableContextExtraction: boolean;
  enableAutoUpdate: boolean;
  updateInterval: number;
  maxContextCommands: number;
  maxClipboardEntries: number;
  fuzzyMatchThreshold: number;
}

export function GlobalVocabularySettings() {
  const [settings, setSettings] = useState<GlobalSettings>({
    technicalTerms: [],
    programmingKeywords: [],
    commonCorrections: {},
    enableContextExtraction: true,
    enableAutoUpdate: true,
    updateInterval: 500,
    maxContextCommands: 40,
    maxClipboardEntries: 5,
    fuzzyMatchThreshold: 0.85,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const globalVocab = await vocabularyAPI.getVocabulary('global');

      // Parse settings from global vocabulary
      setSettings({
        technicalTerms: globalVocab.keywords['technical_terms'] || [],
        programmingKeywords: globalVocab.keywords['programming']?.['keywords'] || [],
        commonCorrections: globalVocab.keywords['common_corrections'] || {},
        enableContextExtraction: true,
        enableAutoUpdate: true,
        updateInterval: 500,
        maxContextCommands: 40,
        maxClipboardEntries: 5,
        fuzzyMatchThreshold: 0.85,
      });
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      // Update global vocabulary
      const updatedVocab = {
        keywords: {
          'technical_terms': settings.technicalTerms,
          'programming': {
            'keywords': settings.programmingKeywords,
          },
          'common_corrections': settings.commonCorrections,
        },
        applications: {},
        prompts: {},
        priority: -1,
      };

      await vocabularyAPI.updateVocabulary('global', updatedVocab);
      setUnsavedChanges(false);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    loadSettings();
    setUnsavedChanges(false);
  };

  const updateSetting = (key: keyof GlobalSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setUnsavedChanges(true);
  };

  const addToArray = (key: 'technicalTerms' | 'programmingKeywords', value: string) => {
    const array = settings[key];
    if (value.trim() && !array.includes(value.trim())) {
      updateSetting(key, [...array, value.trim()]);
    }
  };

  const removeFromArray = (key: 'technicalTerms' | 'programmingKeywords', index: number) => {
    const array = settings[key];
    updateSetting(key, array.filter((_, i) => i !== index));
  };

  const addCorrection = (wrong: string, correct: string) => {
    if (wrong.trim() && correct.trim()) {
      updateSetting('commonCorrections', {
        ...settings.commonCorrections,
        [wrong.trim()]: correct.trim(),
      });
    }
  };

  const removeCorrection = (wrong: string) => {
    const corrections = { ...settings.commonCorrections };
    delete corrections[wrong];
    updateSetting('commonCorrections', corrections);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Global Vocabulary Settings</h2>
          <p className="text-muted-foreground">
            Manage global vocabulary settings and defaults
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
          <Button onClick={handleSave} disabled={saving || !unsavedChanges}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="vocabulary" className="space-y-4">
        <TabsList>
          <TabsTrigger value="vocabulary">Vocabulary</TabsTrigger>
          <TabsTrigger value="corrections">Corrections</TabsTrigger>
          <TabsTrigger value="behavior">Behavior</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>

        <TabsContent value="vocabulary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Book className="h-5 w-5" />
                Technical Terms
              </CardTitle>
              <CardDescription>
                Global technical terms available to all applications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Add technical term..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addToArray('technicalTerms', e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                />
                <Button onClick={(e) => {
                  const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                  addToArray('technicalTerms', input.value);
                  input.value = '';
                }}>
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {settings.technicalTerms.map((term, index) => (
                  <Badge key={index} variant="outline" className="gap-1">
                    {term}
                    <button onClick={() => removeFromArray('technicalTerms', index)}>
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                Programming Keywords
              </CardTitle>
              <CardDescription>
                Programming languages and framework keywords
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Add programming keyword..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addToArray('programmingKeywords', e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                />
                <Button onClick={(e) => {
                  const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                  addToArray('programmingKeywords', input.value);
                  input.value = '';
                }}>
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {settings.programmingKeywords.map((keyword, index) => (
                  <Badge key={index} variant="outline" className="gap-1">
                    {keyword}
                    <button onClick={() => removeFromArray('programmingKeywords', index)}>
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="corrections" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Common Corrections
              </CardTitle>
              <CardDescription>
                Automatic corrections for frequently misheard words
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-2">
                <Input
                  placeholder="Wrong word..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const wrongInput = e.currentTarget;
                      const correctInput = wrongInput.nextElementSibling as HTMLInputElement;
                      if (correctInput.value) {
                        addCorrection(wrongInput.value, correctInput.value);
                        wrongInput.value = '';
                        correctInput.value = '';
                      }
                    }
                  }}
                />
                <Input
                  placeholder="Correct word..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const correctInput = e.currentTarget;
                      const wrongInput = correctInput.previousElementSibling as HTMLInputElement;
                      if (wrongInput.value) {
                        addCorrection(wrongInput.value, correctInput.value);
                        wrongInput.value = '';
                        correctInput.value = '';
                      }
                    }
                  }}
                />
              </div>
              <div className="space-y-2">
                {Object.entries(settings.commonCorrections).map(([wrong, correct]) => (
                  <div key={wrong} className="flex items-center justify-between p-2 border rounded">
                    <div className="flex items-center gap-4">
                      <span className="font-mono text-sm text-red-500">{wrong}</span>
                      <span>→</span>
                      <span className="font-mono text-sm text-green-500">{correct}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeCorrection(wrong)}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="behavior" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Context Extraction</CardTitle>
              <CardDescription>
                Configure how vocabulary is extracted from context
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Context Extraction</Label>
                  <p className="text-sm text-muted-foreground">
                    Extract vocabulary from shell and clipboard
                  </p>
                </div>
                <Switch
                  checked={settings.enableContextExtraction}
                  onCheckedChange={(checked) => updateSetting('enableContextExtraction', checked)}
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Auto Update</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically update vocabulary based on context
                  </p>
                </div>
                <Switch
                  checked={settings.enableAutoUpdate}
                  onCheckedChange={(checked) => updateSetting('enableAutoUpdate', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="advanced" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Advanced Settings</CardTitle>
              <CardDescription>
                Fine-tune vocabulary behavior
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Update Interval (ms)</Label>
                <Input
                  type="number"
                  value={settings.updateInterval}
                  onChange={(e) => updateSetting('updateInterval', parseInt(e.target.value))}
                  min="100"
                  max="5000"
                  step="100"
                />
                <p className="text-sm text-muted-foreground">
                  How often to check for context changes
                </p>
              </div>
              <Separator />
              <div className="space-y-2">
                <Label>Max Context Commands</Label>
                <Input
                  type="number"
                  value={settings.maxContextCommands}
                  onChange={(e) => updateSetting('maxContextCommands', parseInt(e.target.value))}
                  min="10"
                  max="200"
                />
                <p className="text-sm text-muted-foreground">
                  Number of shell commands to analyze
                </p>
              </div>
              <Separator />
              <div className="space-y-2">
                <Label>Max Clipboard Entries</Label>
                <Input
                  type="number"
                  value={settings.maxClipboardEntries}
                  onChange={(e) => updateSetting('maxClipboardEntries', parseInt(e.target.value))}
                  min="1"
                  max="50"
                />
                <p className="text-sm text-muted-foreground">
                  Number of clipboard entries to analyze
                </p>
              </div>
              <Separator />
              <div className="space-y-2">
                <Label>Fuzzy Match Threshold</Label>
                <Input
                  type="number"
                  value={settings.fuzzyMatchThreshold}
                  onChange={(e) => updateSetting('fuzzyMatchThreshold', parseFloat(e.target.value))}
                  min="0.5"
                  max="1.0"
                  step="0.05"
                />
                <p className="text-sm text-muted-foreground">
                  Minimum similarity for fuzzy matching (0.5-1.0)
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

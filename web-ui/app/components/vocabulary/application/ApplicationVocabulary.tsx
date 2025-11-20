'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Monitor, CheckCircle, RefreshCw, Settings, Search } from 'lucide-react';
import { ApplicationContext, VocabularyConfig } from '@/lib/vocabulary/types';
import { vocabularyAPI } from '@/lib/vocabulary/api';
import { vocabularyWS } from '@/lib/vocabulary/websocket';

export function ApplicationVocabulary() {
  const [applicationContext, setApplicationContext] = useState<ApplicationContext | null>(null);
  const [availableVocabularies, setAvailableVocabularies] = useState<VocabularyConfig[]>([]);
  const [selectedVocabulary, setSelectedVocabulary] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);

  useEffect(() => {
    loadData();

    // Subscribe to application changes
    vocabularyWS.on('application_switch', (update) => {
      setApplicationContext(update.payload);
      loadVocabularies();
    });

    vocabularyWS.on('vocabulary_change', (update) => {
      if (update.payload?.vocabulary) {
        setSelectedVocabulary(update.payload.vocabulary);
      }
    });

    return () => {
      vocabularyWS.off('application_switch', () => {});
      vocabularyWS.off('vocabulary_change', () => {});
    };
  }, []);

  const loadData = async () => {
    try {
      const [appContext, vocabularies] = await Promise.all([
        vocabularyAPI.getApplicationContext(),
        vocabularyAPI.getVocabularies()
      ]);
      setApplicationContext(appContext);
      setAvailableVocabularies(vocabularies);

      // Find matching vocabulary
      if (appContext.matchedVocabulary) {
        setSelectedVocabulary(appContext.matchedVocabulary);
      }
    } catch (error) {
      console.error('Failed to load application data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadVocabularies = async () => {
    try {
      const vocabularies = await vocabularyAPI.getVocabularies();
      setAvailableVocabularies(vocabularies);
    } catch (error) {
      console.error('Failed to load vocabularies:', error);
    }
  };

  const handleDetectApplication = async () => {
    setDetecting(true);
    try {
      const appContext = await vocabularyAPI.getApplicationContext();
      setApplicationContext(appContext);

      if (appContext.matchedVocabulary) {
        setSelectedVocabulary(appContext.matchedVocabulary);
      }
    } catch (error) {
      console.error('Failed to detect application:', error);
    } finally {
      setDetecting(false);
    }
  };

  const handleVocabularyChange = async (vocabId: string) => {
    setSelectedVocabulary(vocabId);
    try {
      await vocabularyAPI.forceVocabularyUpdate(
        applicationContext?.class,
        applicationContext?.title
      );
    } catch (error) {
      console.error('Failed to update vocabulary:', error);
    }
  };

  const handleApplyVocabulary = async () => {
    if (!selectedVocabulary || !applicationContext) return;

    try {
      await vocabularyAPI.forceVocabularyUpdate(
        applicationContext.class,
        applicationContext.title
      );

      // Reload to confirm
      await loadData();
    } catch (error) {
      console.error('Failed to apply vocabulary:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const matchedVocab = availableVocabularies.find(v => v.name === selectedVocabulary);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Application-Specific Vocabulary</h2>
          <p className="text-muted-foreground">
            Detect and configure vocabulary for current application
          </p>
        </div>
        <Button onClick={handleDetectApplication} disabled={detecting}>
          <RefreshCw className={`h-4 w-4 mr-2 ${detecting ? 'animate-spin' : ''}`} />
          Detect App
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Monitor className="h-5 w-5" />
              Current Application
            </CardTitle>
            <CardDescription>
              Detected active window and application information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium">Window Class</p>
              <p className="text-lg font-mono">{applicationContext?.class || 'Unknown'}</p>
            </div>

            <Separator />

            <div>
              <p className="text-sm font-medium">Window Title</p>
              <p className="text-sm text-muted-foreground break-all">
                {applicationContext?.title || 'No title'}
              </p>
            </div>

            <Separator />

            <div>
              <p className="text-sm font-medium">Detected Keywords</p>
              <div className="flex flex-wrap gap-1 mt-2">
                {applicationContext?.keywords && applicationContext.keywords.length > 0 ? (
                  applicationContext.keywords.slice(0, 10).map((keyword, index) => (
                    <Badge key={index} variant="outline" className="font-mono text-xs">
                      {keyword}
                    </Badge>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No keywords detected</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Vocabulary Selection
            </CardTitle>
            <CardDescription>
              Choose vocabulary to use for this application
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Vocabulary</label>
              <Select value={selectedVocabulary} onValueChange={handleVocabularyChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select vocabulary" />
                </SelectTrigger>
                <SelectContent>
                  {availableVocabularies.map((vocab) => (
                    <SelectItem key={vocab.name} value={vocab.name}>
                      <div className="flex items-center justify-between w-full">
                        <span>{vocab.name}</span>
                        <Badge variant="secondary" className="ml-2">
                          {Object.values(vocab.keywords).flat().length}
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={handleApplyVocabulary}
              className="w-full"
              disabled={!selectedVocabulary}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Apply Vocabulary
            </Button>

            {matchedVocab && (
              <>
                <Separator />
                <div className="space-y-2">
                  <p className="text-sm font-medium">Selected Vocabulary Details</p>
                  <p className="text-sm text-muted-foreground">
                    {matchedVocab.description}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {Object.keys(matchedVocab.keywords).map((category) => (
                      <Badge key={category} variant="outline" className="text-xs">
                        {category}
                      </Badge>
                    ))}
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Available Vocabularies</CardTitle>
          <CardDescription>
            All configured vocabularies and their application patterns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {availableVocabularies.map((vocab) => (
              <div key={vocab.name} className="border rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold">{vocab.name}</h4>
                  <Badge variant={vocab.name === selectedVocabulary ? 'default' : 'secondary'}>
                    {vocab.name === selectedVocabulary ? 'Selected' : 'Available'}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{vocab.description}</p>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>{Object.values(vocab.keywords).flat().length} keywords</span>
                  <span>Priority: {vocab.priority}</span>
                </div>
                {vocab.applications.window_classes && vocab.applications.window_classes.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {vocab.applications.window_classes.map((pattern) => (
                      <Badge key={pattern} variant="outline" className="font-mono text-xs">
                        {pattern}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

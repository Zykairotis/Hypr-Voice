'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Edit, Trash2, Search, Upload, Download, Save, X } from 'lucide-react';
import { VocabularyWord, VocabularyConfig } from '@/lib/vocabulary/types';
import { vocabularyAPI } from '@/lib/vocabulary/api';
import { vocabularyWS } from '@/lib/vocabulary/websocket';

interface VocabularyEditorProps {
  vocabularyId?: string;
}

export function VocabularyEditor({ vocabularyId = 'global' }: VocabularyEditorProps) {
  const [vocabulary, setVocabulary] = useState<VocabularyConfig | null>(null);
  const [words, setWords] = useState<VocabularyWord[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedWords, setSelectedWords] = useState<Set<string>>(new Set());
  const [editingWord, setEditingWord] = useState<VocabularyWord | null>(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [importText, setImportText] = useState('');
  const [importFormat, setImportFormat] = useState<'csv' | 'json' | 'yaml'>('csv');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadVocabulary();
  }, [vocabularyId]);

  const loadVocabulary = async () => {
    try {
      setLoading(true);
      const vocab = await vocabularyAPI.getVocabulary(vocabularyId);
      setVocabulary(vocab);

      // Convert vocabulary keywords to words array
      const wordList: VocabularyWord[] = [];
      Object.entries(vocab.keywords).forEach(([category, categoryWords]) => {
        if (Array.isArray(categoryWords)) {
          categoryWords.forEach((word, index) => {
            wordList.push({
              id: `${category}-${index}`,
              word,
              category,
              priority: 0,
              weight: 1,
            });
          });
        } else if (typeof categoryWords === 'object') {
          Object.entries(categoryWords).forEach(([subcategory, words]) => {
            if (Array.isArray(words)) {
              words.forEach((word, index) => {
                wordList.push({
                  id: `${category}-${subcategory}-${index}`,
                  word,
                  category: `${category}.${subcategory}`,
                  priority: 0,
                  weight: 1,
                });
              });
            }
          });
        }
      });
      setWords(wordList);
    } catch (error) {
      console.error('Failed to load vocabulary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddWord = async (wordData: Partial<VocabularyWord>) => {
    if (!vocabulary) return;

    const newWord: VocabularyWord = {
      id: `new-${Date.now()}`,
      word: wordData.word || '',
      category: wordData.category || 'custom',
      priority: wordData.priority || 0,
      weight: wordData.weight || 1,
      corrections: wordData.corrections,
      metadata: wordData.metadata,
    };

    try {
      await vocabularyAPI.addWords(vocabularyId, [newWord]);
      setWords([...words, newWord]);
      setIsAddDialogOpen(false);

      // Notify via WebSocket
      vocabularyWS.send('vocabulary_change', { action: 'add_word', word: newWord });
    } catch (error) {
      console.error('Failed to add word:', error);
    }
  };

  const handleRemoveWords = async (wordIds: string[]) => {
    try {
      await vocabularyAPI.removeWords(vocabularyId, wordIds);
      setWords(words.filter(w => !wordIds.includes(w.id)));
      setSelectedWords(new Set());

      // Notify via WebSocket
      vocabularyWS.send('vocabulary_change', { action: 'remove_words', wordIds });
    } catch (error) {
      console.error('Failed to remove words:', error);
    }
  };

  const handleBulkImport = async () => {
    try {
      const result = await vocabularyAPI.bulkImport(vocabularyId, importText, importFormat);
      if (result.imported > 0) {
        await loadVocabulary();
        setImportText('');
        setIsImportDialogOpen(false);
      }
    } catch (error) {
      console.error('Failed to import:', error);
    }
  };

  const handleExport = async (format: 'csv' | 'json' | 'yaml') => {
    try {
      const data = await vocabularyAPI.exportVocabulary(vocabularyId, format);
      const blob = new Blob([data], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${vocabularyId}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export:', error);
    }
  };

  const filteredWords = words.filter(word => {
    const matchesCategory = selectedCategory === 'all' || word.category === selectedCategory;
    const matchesSearch = searchQuery === '' ||
      word.word.toLowerCase().includes(searchQuery.toLowerCase()) ||
      word.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const categories = Array.from(new Set(words.map(w => w.category)));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading vocabulary...</p>
        </div>
      </div>
    );
  }

  if (!vocabulary) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Vocabulary not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Vocabulary Editor</h2>
          <p className="text-muted-foreground">
            Manage keywords and categories for {vocabulary.name}
          </p>
        </div>
        <div className="flex gap-2">
          <Dialog open={isImportDialogOpen} onOpenChange={setIsImportDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Upload className="h-4 w-4 mr-2" />
                Import
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Import Vocabulary</DialogTitle>
                <DialogDescription>
                  Import vocabulary from CSV, JSON, or YAML format
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Format</Label>
                  <Select value={importFormat} onValueChange={(v: any) => setImportFormat(v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="csv">CSV</SelectItem>
                      <SelectItem value="json">JSON</SelectItem>
                      <SelectItem value="yaml">YAML</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Data</Label>
                  <Textarea
                    value={importText}
                    onChange={(e) => setImportText(e.target.value)}
                    placeholder="Paste your vocabulary data here..."
                    className="min-h-[200px]"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsImportDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleBulkImport}>Import</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Button variant="outline" onClick={() => handleExport('csv')}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Word
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Word</DialogTitle>
                <DialogDescription>
                  Add a new keyword to the vocabulary
                </DialogDescription>
              </DialogHeader>
              <AddWordForm onSubmit={handleAddWord} categories={categories} />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{vocabulary.name}</CardTitle>
              <CardDescription>{vocabulary.description}</CardDescription>
            </div>
            <Badge variant="secondary">{filteredWords.length} words</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search words..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map((category) => (
                  <SelectItem key={category} value={category}>
                    {category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedWords.size > 0 && (
            <div className="mb-4 p-4 border rounded-lg bg-muted/50">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  {selectedWords.size} word(s) selected
                </span>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleRemoveWords(Array.from(selectedWords))}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Remove
                </Button>
              </div>
            </div>
          )}

          <div className="space-y-2">
            {filteredWords.map((word) => (
              <WordItem
                key={word.id}
                word={word}
                selected={selectedWords.has(word.id)}
                onToggleSelect={(id) => {
                  const newSelected = new Set(selectedWords);
                  if (newSelected.has(id)) {
                    newSelected.delete(id);
                  } else {
                    newSelected.add(id);
                  }
                  setSelectedWords(newSelected);
                }}
                onEdit={setEditingWord}
                onDelete={() => handleRemoveWords([word.id])}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function AddWordForm({
  onSubmit,
  categories
}: {
  onSubmit: (data: Partial<VocabularyWord>) => void;
  categories: string[];
}) {
  const [formData, setFormData] = useState<Partial<VocabularyWord>>({
    category: categories[0] || 'custom',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label>Word</Label>
        <Input
          value={formData.word || ''}
          onChange={(e) => setFormData({ ...formData, word: e.target.value })}
          required
        />
      </div>
      <div>
        <Label>Category</Label>
        <Input
          value={formData.category || ''}
          onChange={(e) => setFormData({ ...formData, category: e.target.value })}
          placeholder="custom"
        />
      </div>
      <div>
        <Label>Corrections (comma-separated)</Label>
        <Input
          value={formData.corrections?.join(', ') || ''}
          onChange={(e) => setFormData({
            ...formData,
            corrections: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
          })}
        />
      </div>
      <DialogFooter>
        <Button type="submit">Add Word</Button>
      </DialogFooter>
    </form>
  );
}

function WordItem({
  word,
  selected,
  onToggleSelect,
  onEdit,
  onDelete,
}: {
  word: VocabularyWord;
  selected: boolean;
  onToggleSelect: (id: string) => void;
  onEdit: (word: VocabularyWord) => void;
  onDelete: () => void;
}) {
  return (
    <div
      className={`flex items-center gap-4 p-3 border rounded-lg cursor-pointer transition-colors ${
        selected ? 'bg-primary/10 border-primary' : 'hover:bg-muted/50'
      }`}
      onClick={() => onToggleSelect(word.id)}
    >
      <input
        type="checkbox"
        checked={selected}
        onChange={() => onToggleSelect(word.id)}
        className="rounded"
      />
      <div className="flex-1 min-w-0">
        <p className="font-mono font-medium truncate">{word.word}</p>
        <p className="text-xs text-muted-foreground">{word.category}</p>
      </div>
      <div className="flex items-center gap-2">
        {word.corrections && word.corrections.length > 0 && (
          <Badge variant="outline" className="text-xs">
            {word.corrections.length} corrections
          </Badge>
        )}
        <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); onEdit(word); }}>
          <Edit className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); onDelete(); }}>
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

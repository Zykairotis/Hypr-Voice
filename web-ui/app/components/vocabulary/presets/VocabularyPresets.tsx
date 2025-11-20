'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Package, Download, Upload, Star, Search, Plus, Trash2 } from 'lucide-react';
import { VocabularyPreset, VocabularyConfig } from '@/lib/vocabulary/types';
import { vocabularyAPI } from '@/lib/vocabulary/api';

export function VocabularyPresets() {
  const [presets, setPresets] = useState<VocabularyPreset[]>([]);
  const [vocabularies, setVocabularies] = useState<VocabularyConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newPreset, setNewPreset] = useState({
    name: '',
    description: '',
    category: '',
    vocabularyId: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [presetsData, vocabulariesData] = await Promise.all([
        vocabularyAPI.getPresets(),
        vocabularyAPI.getVocabularies()
      ]);
      setPresets(presetsData);
      setVocabularies(vocabulariesData);
    } catch (error) {
      console.error('Failed to load presets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePreset = async () => {
    try {
      const preset = await vocabularyAPI.createPreset(
        newPreset.name,
        newPreset.vocabularyId,
        newPreset.description
      );
      setPresets([preset, ...presets]);
      setIsCreateDialogOpen(false);
      setNewPreset({ name: '', description: '', category: '', vocabularyId: '' });
    } catch (error) {
      console.error('Failed to create preset:', error);
    }
  };

  const handleApplyPreset = async (presetId: string) => {
    try {
      await vocabularyAPI.applyPreset(presetId);
      await loadData(); // Refresh to show applied state
    } catch (error) {
      console.error('Failed to apply preset:', error);
    }
  };

  const categories = Array.from(new Set(presets.map(p => p.category)));

  const filteredPresets = presets.filter(preset => {
    const matchesSearch = preset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         preset.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         preset.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = selectedCategory === 'all' || preset.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading presets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Vocabulary Presets</h2>
          <p className="text-muted-foreground">
            Pre-built vocabularies and custom templates
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Preset
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Vocabulary Preset</DialogTitle>
              <DialogDescription>
                Save current vocabulary as a reusable template
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Name</Label>
                <Input
                  value={newPreset.name}
                  onChange={(e) => setNewPreset({ ...newPreset, name: e.target.value })}
                  placeholder="My Custom Preset"
                />
              </div>
              <div>
                <Label>Description</Label>
                <Textarea
                  value={newPreset.description}
                  onChange={(e) => setNewPreset({ ...newPreset, description: e.target.value })}
                  placeholder="Describe this preset..."
                />
              </div>
              <div>
                <Label>Category</Label>
                <Input
                  value={newPreset.category}
                  onChange={(e) => setNewPreset({ ...newPreset, category: e.target.value })}
                  placeholder="e.g., Development, Writing, Gaming"
                />
              </div>
              <div>
                <Label>Vocabulary</Label>
                <Select value={newPreset.vocabularyId} onValueChange={(v) => setNewPreset({ ...newPreset, vocabularyId: v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select vocabulary to save" />
                  </SelectTrigger>
                  <SelectContent>
                    {vocabularies.map((vocab) => (
                      <SelectItem key={vocab.name} value={vocab.name}>
                        {vocab.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreatePreset} disabled={!newPreset.name || !newPreset.vocabularyId}>
                Create Preset
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search presets..."
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

      <Tabs defaultValue="presets" className="space-y-4">
        <TabsList>
          <TabsTrigger value="presets">My Presets</TabsTrigger>
          <TabsTrigger value="built-in">Built-in Templates</TabsTrigger          >
          <TabsTrigger value="community">Community</TabsTrigger>
        </TabsList>

        <TabsContent value="presets" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredPresets.filter(p => !p.isBuiltIn).map((preset) => (
              <Card key={preset.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1">
                      <CardTitle className="text-lg">{preset.name}</CardTitle>
                      <CardDescription className="line-clamp-2">
                        {preset.description}
                      </CardDescription>
                    </div>
                    <Badge variant="secondary">Custom</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-1">
                    {preset.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                    {preset.tags.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{preset.tags.length - 3}
                      </Badge>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Created {new Date(preset.createdAt).toLocaleDateString()}
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" className="flex-1" onClick={() => handleApplyPreset(preset.id)}>
                      <Download className="h-4 w-4 mr-2" />
                      Apply
                    </Button>
                    <Button size="sm" variant="outline">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="built-in" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredPresets.filter(p => p.isBuiltIn).map((preset) => (
              <Card key={preset.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1">
                      <CardTitle className="text-lg flex items-center gap-2">
                        {preset.name}
                        <Star className="h-4 w-4 text-yellow-500" />
                      </CardTitle>
                      <CardDescription className="line-clamp-2">
                        {preset.description}
                      </CardDescription>
                    </div>
                    <Badge variant="default">Built-in</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-1">
                    {preset.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                    {preset.tags.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{preset.tags.length - 3}
                      </Badge>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" className="flex-1" onClick={() => handleApplyPreset(preset.id)}>
                      <Download className="h-4 w-4 mr-2" />
                      Apply
                    </Button>
                    <Button size="sm" variant="outline">
                      <Star className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="community" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Community Presets</CardTitle>
              <CardDescription>
                Presets shared by the community
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <Package className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <p className="text-muted-foreground">
                  Community presets coming soon! Share your custom vocabularies with others.
                </p>
                <Button className="mt-4" variant="outline">
                  <Upload className="h-4 w-4 mr-2" />
                  Submit Preset
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {filteredPresets.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Package className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">
              No presets found. Try adjusting your search or create a new preset.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

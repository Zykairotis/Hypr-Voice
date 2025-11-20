"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Save, Plus, X, BookOpen, Code, Terminal, Globe } from "lucide-react";
import { toast } from "sonner";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

interface VocabularyCategory {
  name: string;
  icon: React.ReactNode;
  words: string[];
  enabled: boolean;
}

// Move static category templates outside component to prevent recreation
const CATEGORY_TEMPLATES = [
  { name: "Technical Terms", iconName: "Code" as const, words: [] as string[], enabled: true },
  { name: "Programming", iconName: "Terminal" as const, words: [] as string[], enabled: true },
  { name: "System Admin", iconName: "Globe" as const, words: [] as string[], enabled: true },
];

// Default categories for when backend is unavailable
const DEFAULT_CATEGORIES = [
  {
    name: "Technical Terms",
    words: ["API", "SDK", "CLI", "REST", "GraphQL", "Docker", "Kubernetes"],
    enabled: true
  },
  {
    name: "Programming",
    words: ["TypeScript", "JavaScript", "Python", "React", "Node.js"],
    enabled: true
  },
  {
    name: "System Admin",
    words: ["systemctl", "journalctl", "iptables", "ssh-keygen", "rsync"],
    enabled: true
  },
];

export default function VocabularyConfig() {
  const [customWords, setCustomWords] = useState<string[]>([]);
  const [newWord, setNewWord] = useState("");
  const [vocabularyEnabled, setVocabularyEnabled] = useState(true);
  const [categories, setCategories] = useState<Omit<VocabularyCategory, 'icon'>[]>(
    CATEGORY_TEMPLATES.map(({ name, words, enabled }) => ({ name, words, enabled }))
  );
  const [isLoading, setIsLoading] = useState(false);
  const [errorCount, setErrorCount] = useState(0);

  // Memoize category icons to prevent recreation on every render
  const categoryIcons = useMemo(() => ({
    "Technical Terms": <Code className="w-4 h-4" />,
    "Programming": <Terminal className="w-4 h-4" />,
    "System Admin": <Globe className="w-4 h-4" />,
  }), []);

  // Memoize categories with icons
  const categoriesWithIcons = useMemo(
    () => categories.map(cat => ({ ...cat, icon: categoryIcons[cat.name as keyof typeof categoryIcons] })),
    [categories, categoryIcons]
  );

  // Memoize statistics to avoid recalculating on every render
  const stats = useMemo(() => ({
    customWordsCount: customWords.length,
    activeCategoriesCount: categories.filter(c => c.enabled).length,
    totalActiveWords: categories.reduce((sum, cat) => sum + (cat.enabled ? cat.words.length : 0), 0)
  }), [customWords.length, categories]);

  useEffect(() => {
    loadVocabularyConfig();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  const loadVocabularyConfig = useCallback(async () => {
    try {
      const response = await fetch("http://localhost:8934/api/config/vocabulary", {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const config = await response.json();
        setVocabularyEnabled(config.enabled || true);
        setCustomWords(config.custom_words || []);
        
        // Load categorized vocabulary
        if (config.categories) {
          const loadedCategories = CATEGORY_TEMPLATES.map(template => ({
            name: template.name,
            words: config.categories[template.name.toLowerCase().replace(/\s/g, '_')] || [],
            enabled: config.categories_enabled?.[template.name.toLowerCase().replace(/\s/g, '_')] ?? true
          }));
          setCategories(loadedCategories);
        }
        setErrorCount(0);
      }
    } catch (error) {
      // Only log once to avoid console spam
      if (errorCount === 0) {
        console.warn("Backend not available. Using default vocabulary configuration.");
      }
      setErrorCount(prev => prev + 1);
      // Load default vocabulary for demo
      setCategories(DEFAULT_CATEGORIES);
      setCustomWords(["Hyprland", "Wayland", "Zykairotis"]);
    }
  }, [errorCount]);

  const handleAddWord = useCallback(() => {
    if (newWord.trim() && !customWords.includes(newWord.trim())) {
      setCustomWords([...customWords, newWord.trim()]);
      setNewWord("");
      toast.success(`Added "${newWord}" to custom vocabulary`);
    }
  }, [newWord, customWords]);

  const handleRemoveWord = useCallback((word: string) => {
    setCustomWords(customWords.filter(w => w !== word));
    toast.success(`Removed "${word}" from vocabulary`);
  }, [customWords]);

  const toggleCategory = useCallback((index: number) => {
    const updated = [...categories];
    updated[index].enabled = !updated[index].enabled;
    setCategories(updated);
  }, [categories]);

  const handleSave = useCallback(async () => {
    setIsLoading(true);
    try {
      const config = {
        enabled: vocabularyEnabled,
        custom_words: customWords,
        categories: categories.reduce((acc, cat) => ({
          ...acc,
          [cat.name.toLowerCase().replace(/\s/g, '_')]: cat.words
        }), {}),
        categories_enabled: categories.reduce((acc, cat) => ({
          ...acc,
          [cat.name.toLowerCase().replace(/\s/g, '_')]: cat.enabled
        }), {})
      };

      const response = await fetch("http://localhost:8934/api/config/vocabulary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        toast.success("Vocabulary configuration saved successfully");
      } else {
        toast.error("Failed to save configuration");
      }
    } catch (error) {
      toast.error("Error saving configuration");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }, [vocabularyEnabled, customWords, categories]);

  return (
    <div className="space-y-6">
      {/* Vocabulary Enable/Disable */}
      <div className="flex items-center justify-between p-4 rounded-lg glass-hover border border-border/50">
        <div className="flex items-center gap-3">
          <BookOpen className="w-5 h-5 text-primary" />
          <div>
            <Label className="text-base font-semibold">Vocabulary Enhancement</Label>
            <p className="text-sm text-muted-foreground">
              Improve transcription accuracy for technical terms
            </p>
          </div>
        </div>
        <Switch
          checked={vocabularyEnabled}
          onCheckedChange={setVocabularyEnabled}
        />
      </div>

      {vocabularyEnabled && (
        <>
          <Separator className="bg-border/50" />

          {/* Custom Words */}
          <div className="space-y-4">
            <Label className="text-base font-semibold">Custom Words</Label>
            
            <div className="flex gap-2">
              <Input
                placeholder="Add custom word or phrase..."
                value={newWord}
                onChange={(e) => setNewWord(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAddWord()}
                className="glass"
              />
              <Button onClick={handleAddWord} className="glow-hover">
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex flex-wrap gap-2">
              {customWords.map((word) => (
                <Badge
                  key={word}
                  variant="secondary"
                  className="glass-hover px-3 py-1.5 text-sm group"
                >
                  {word}
                  <button
                    onClick={() => handleRemoveWord(word)}
                    className="ml-2 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
              {customWords.length === 0 && (
                <p className="text-sm text-muted-foreground">No custom words added yet</p>
              )}
            </div>
          </div>

          <Separator className="bg-border/50" />

          {/* Category Vocabularies */}
          <div className="space-y-4">
            <Label className="text-base font-semibold">Category Vocabularies</Label>
            
            <Accordion type="single" collapsible className="space-y-3">
              {categoriesWithIcons.map((category, index) => (
                <AccordionItem
                  key={category.name}
                  value={category.name}
                  className="border border-border/50 rounded-lg glass-hover px-4"
                >
                  <div className="flex items-center justify-between py-4">
                    <AccordionTrigger className="hover:no-underline flex-1 py-0">
                      <div className="flex items-center gap-3">
                        {category.icon}
                        <span className="font-medium">{category.name}</span>
                        <Badge variant="outline" className="text-xs">
                          {category.words.length} words
                        </Badge>
                      </div>
                    </AccordionTrigger>
                    <Switch
                      checked={category.enabled}
                      onCheckedChange={() => toggleCategory(index)}
                    />
                  </div>
                  <AccordionContent>
                    <div className="flex flex-wrap gap-2 pt-2 pb-2">
                      {category.words.map((word) => (
                        <Badge
                          key={word}
                          variant="outline"
                          className="glass text-xs"
                        >
                          {word}
                        </Badge>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>

          {/* Statistics */}
          <Card className="glass border-border/50 p-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-primary">
                  {stats.customWordsCount}
                </div>
                <div className="text-sm text-muted-foreground">Custom Words</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-primary">
                  {stats.activeCategoriesCount}
                </div>
                <div className="text-sm text-muted-foreground">Active Categories</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-primary">
                  {stats.totalActiveWords}
                </div>
                <div className="text-sm text-muted-foreground">Total Active Words</div>
              </div>
            </div>
          </Card>
        </>
      )}

      {/* Save Button */}
      <div className="pt-4">
        <Button
          onClick={handleSave}
          disabled={isLoading}
          className="w-full glow-hover"
          size="lg"
        >
          <Save className="w-4 h-4 mr-2" />
          {isLoading ? "Saving..." : "Save Vocabulary Configuration"}
        </Button>
      </div>
    </div>
  );
}


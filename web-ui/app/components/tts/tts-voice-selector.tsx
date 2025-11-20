"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Search,
  Play,
  Pause,
  Volume2,
  User,
  Heart,
  Filter,
  Grid,
  List,
  Star
} from "lucide-react";
import { toast } from "sonner";

interface TTSVoiceSelectorProps {
  provider: string;
  selectedVoice: string;
  onVoiceChange: (voice: string) => void;
}

interface Voice {
  id: string;
  name: string;
  gender: "male" | "female" | "neutral";
  accent?: string;
  age?: string;
  language?: string;
  description?: string;
  preview?: string;
  isFavorite?: boolean;
  isCustom?: boolean;
  quality: "high" | "medium" | "premium";
  emotionSupport?: string[];
  styleSupport?: string[];
}

export default function TTSVoiceSelector({
  provider,
  selectedVoice,
  onVoiceChange,
}: TTSVoiceSelectorProps) {
  const [voices, setVoices] = useState<Record<string, Voice[]>>({});
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterGender, setFilterGender] = useState<string>("all");
  const [filterAccent, setFilterAccent] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [previewingVoice, setPreviewingVoice] = useState<string | null>(null);
  const [favorites, setFavorites] = useState<string[]>([]);

  useEffect(() => {
    loadVoices();
    loadFavorites();
  }, [provider]);

  const loadVoices = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8934/api/tts/voices/${provider}`, {
        method: "GET",
      });

      if (response.ok) {
        const data = await response.json();
        setVoices(data.voices || getDefaultVoices(provider));
      } else {
        setVoices(getDefaultVoices(provider));
      }
    } catch (error) {
      console.error("Failed to load voices:", error);
      setVoices(getDefaultVoices(provider));
    } finally {
      setLoading(false);
    }
  };

  const loadFavorites = () => {
    const saved = localStorage.getItem("tts-favorites");
    if (saved) {
      setFavorites(JSON.parse(saved));
    }
  };

  const saveFavorites = (newFavorites: string[]) => {
    setFavorites(newFavorites);
    localStorage.setItem("tts-favorites", JSON.stringify(newFavorites));
  };

  const getDefaultVoices = (provider: string): Record<string, Voice[]> => {
    const voiceData: Record<string, Voice[]> = {
      kokoro: [
        {
          id: "af_bella",
          name: "Bella",
          gender: "female",
          accent: "american",
          age: "young adult",
          language: "English",
          description: "Warm, friendly female voice with a slight southern accent",
          quality: "high",
          emotionSupport: ["happy", "sad", "excited", "neutral"],
        },
        {
          id: "af_sky",
          name: "Sky",
          gender: "female",
          accent: "american",
          age: "adult",
          language: "English",
          description: "Clear, professional female voice",
          quality: "high",
          emotionSupport: ["happy", "sad", "excited", "neutral"],
        },
        {
          id: "am_adam",
          name: "Adam",
          gender: "male",
          accent: "american",
          age: "adult",
          language: "English",
          description: "Deep, authoritative male voice",
          quality: "high",
          emotionSupport: ["happy", "sad", "excited", "neutral"],
        },
        {
          id: "am_michael",
          name: "Michael",
          gender: "male",
          accent: "american",
          age: "adult",
          language: "English",
          description: "Conversational, friendly male voice",
          quality: "high",
          emotionSupport: ["happy", "sad", "excited", "neutral"],
        },
        {
          id: "bm_george",
          name: "George",
          gender: "male",
          accent: "british",
          age: "adult",
          language: "English (British)",
          description: "Distinguished British male voice",
          quality: "high",
          emotionSupport: ["happy", "sad", "excited", "neutral"],
        },
        {
          id: "bf_emma",
          name: "Emma",
          gender: "female",
          accent: "british",
          age: "young adult",
          language: "English (British)",
          description: "Elegant British female voice",
          quality: "high",
          emotionSupport: ["happy", "sad", "excited", "neutral"],
        },
      ],
      deepgram: [
        {
          id: "luna",
          name: "Luna",
          gender: "female",
          accent: "american",
          age: "young adult",
          language: "English",
          description: "Soft, soothing female voice",
          quality: "premium",
          emotionSupport: ["happy", "sad", "neutral"],
          styleSupport: ["conversational", "narration"],
        },
        {
          id: "apollo",
          name: "Apollo",
          gender: "male",
          accent: "american",
          age: "adult",
          language: "English",
          description: "Strong, confident male voice",
          quality: "premium",
          emotionSupport: ["happy", "sad", "neutral"],
          styleSupport: ["conversational", "narration"],
        },
        {
          id: "asteria",
          name: "Asteria",
          gender: "female",
          accent: "american",
          age: "adult",
          language: "English",
          description: "Professional, clear female voice",
          quality: "premium",
          emotionSupport: ["happy", "sad", "neutral"],
          styleSupport: ["conversational", "narration"],
        },
        {
          id: "atlas",
          name: "Atlas",
          gender: "male",
          accent: "american",
          age: "adult",
          language: "English",
          description: "Deep, resonant male voice",
          quality: "premium",
          emotionSupport: ["happy", "sad", "neutral"],
          styleSupport: ["conversational", "narration"],
        },
      ],
      elevenlabs: [
        {
          id: "rachel",
          name: "Rachel",
          gender: "female",
          accent: "american",
          age: "young adult",
          language: "English",
          description: "Dynamic young female voice",
          quality: "premium",
          emotionSupport: ["all"],
          styleSupport: ["all"],
        },
        {
          id: "adam",
          name: "Adam",
          gender: "male",
          accent: "american",
          age: "adult",
          language: "English",
          description: "Warm, deep male voice",
          quality: "premium",
          emotionSupport: ["all"],
          styleSupport: ["all"],
        },
        {
          id: "sarah",
          name: "Sarah",
          gender: "female",
          accent: "american",
          age: "adult",
          language: "English",
          description: "Clear, articulate female voice",
          quality: "premium",
          emotionSupport: ["all"],
          styleSupport: ["all"],
        },
        {
          id: "antoni",
          name: "Antoni",
          gender: "male",
          accent: "american",
          age: "adult",
          language: "English",
          description: "Sophisticated male voice",
          quality: "premium",
          emotionSupport: ["all"],
          styleSupport: ["all"],
        },
      ],
    };

    return voiceData[provider] ? { [provider]: voiceData[provider] } : {};
  };

  const filteredVoices = voices[provider]?.filter((voice) => {
    const matchesSearch =
      searchQuery === "" ||
      voice.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      voice.description?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesGender =
      filterGender === "all" || voice.gender === filterGender;

    const matchesAccent =
      filterAccent === "all" || voice.accent === filterAccent;

    return matchesSearch && matchesGender && matchesAccent;
  }) || [];

  const previewVoice = async (voiceId: string) => {
    if (previewingVoice === voiceId) {
      setPreviewingVoice(null);
      return;
    }

    setPreviewingVoice(voiceId);
    try {
      const response = await fetch("http://localhost:8934/api/tts/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: `Hello, this is a preview of the ${voiceId} voice. How does it sound?`,
          provider,
          voice: voiceId,
          preview: true,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.audioUrl) {
          const audio = new Audio(data.audioUrl);
          audio.play();
          audio.onended = () => setPreviewingVoice(null);
        }
      }
      toast.success("Voice preview played");
    } catch (error) {
      toast.error("Failed to play voice preview");
    } finally {
      setTimeout(() => setPreviewingVoice(null), 3000);
    }
  };

  const toggleFavorite = (voiceId: string) => {
    const newFavorites = favorites.includes(voiceId)
      ? favorites.filter((id) => id !== voiceId)
      : [...favorites, voiceId];
    saveFavorites(newFavorites);
    toast.success(
      favorites.includes(voiceId)
        ? "Removed from favorites"
        : "Added to favorites"
    );
  };

  const getQualityBadge = (quality: string) => {
    const colors = {
      high: "bg-green-500/20 text-green-400 border-green-500/50",
      premium: "bg-purple-500/20 text-purple-400 border-purple-500/50",
      medium: "bg-blue-500/20 text-blue-400 border-blue-500/50",
    };

    return (
      <Badge className={colors[quality] || colors.medium}>
        {quality.charAt(0).toUpperCase() + quality.slice(1)}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:gap-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            placeholder="Search voices..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Select value={filterGender} onValueChange={setFilterGender}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Gender" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Genders</SelectItem>
              <SelectItem value="female">Female</SelectItem>
              <SelectItem value="male">Male</SelectItem>
              <SelectItem value="neutral">Neutral</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filterAccent} onValueChange={setFilterAccent}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Accent" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Accents</SelectItem>
              <SelectItem value="american">American</SelectItem>
              <SelectItem value="british">British</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setViewMode(viewMode === "grid" ? "list" : "grid")}
          >
            {viewMode === "grid" ? <List className="w-4 h-4" /> : <Grid className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Voice List */}
      {loading ? (
        <div className="text-center py-8 text-muted-foreground">Loading voices...</div>
      ) : (
        <div className={viewMode === "grid" ? "grid gap-4 md:grid-cols-2 lg:grid-cols-3" : "space-y-2"}>
          {filteredVoices.map((voice) => {
            const isSelected = selectedVoice === voice.id;
            const isFavorite = favorites.includes(voice.id);

            return (
              <Card
                key={voice.id}
                className={`transition-all duration-200 glass-hover cursor-pointer ${
                  isSelected ? "ring-2 ring-primary border-primary" : "border-border/50"
                } ${viewMode === "list" ? "flex-row items-center" : ""}`}
                onClick={() => onVoiceChange(voice.id)}
              >
                <CardContent className={`p-4 ${viewMode === "list" ? "flex-1" : ""}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1">
                      <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20">
                        <User className="w-5 h-5 text-purple-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold">{voice.name}</h3>
                          {getQualityBadge(voice.quality)}
                        </div>
                        <div className="text-sm text-muted-foreground mb-2">
                          {voice.description}
                        </div>
                        <div className="flex flex-wrap gap-2 mb-2">
                          <Badge variant="outline" className="text-xs">
                            {voice.gender}
                          </Badge>
                          {voice.accent && (
                            <Badge variant="outline" className="text-xs">
                              {voice.accent}
                            </Badge>
                          )}
                          {voice.age && (
                            <Badge variant="outline" className="text-xs">
                              {voice.age}
                            </Badge>
                          )}
                        </div>
                        {voice.emotionSupport && (
                          <div className="text-xs text-muted-foreground">
                            Emotions: {voice.emotionSupport.join(", ")}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleFavorite(voice.id);
                        }}
                      >
                        <Heart
                          className={`w-4 h-4 ${
                            isFavorite ? "fill-red-500 text-red-500" : "text-muted-foreground"
                          }`}
                        />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          previewVoice(voice.id);
                        }}
                        disabled={previewingVoice === voice.id}
                      >
                        {previewingVoice === voice.id ? (
                          <Pause className="w-4 h-4" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {filteredVoices.length === 0 && !loading && (
        <div className="text-center py-8 text-muted-foreground">
          No voices found matching your criteria
        </div>
      )}

      {/* Voice Comparison Tool */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="text-lg">Voice Comparison</CardTitle>
          <CardDescription>
            Test voices with custom text to compare quality
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input placeholder="Enter test text..." className="w-full" />
          <div className="flex flex-wrap gap-2">
            {filteredVoices.slice(0, 4).map((voice) => (
              <Button
                key={voice.id}
                variant="outline"
                size="sm"
                onClick={() => previewVoice(voice.id)}
                disabled={previewingVoice === voice.id}
              >
                {previewingVoice === voice.id ? (
                  <>
                    <Pause className="w-3 h-3 mr-1" />
                    Stop {voice.name}
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3 mr-1" />
                    Test {voice.name}
                  </>
                )}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

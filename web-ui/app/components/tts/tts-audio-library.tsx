"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Search,
  Filter,
  Download,
  Play,
  Pause,
  Trash2,
  Heart,
  Star,
  SortAsc,
  SortDesc,
  Grid,
  List,
  Clock,
  HardDrive,
  FolderOpen,
  Archive,
  MoreHorizontal
} from "lucide-react";
import { toast } from "sonner";

interface AudioItem {
  id: string;
  name: string;
  text: string;
  url: string;
  provider: string;
  voice: string;
  duration: number;
  size: number; // in bytes
  createdAt: Date;
  tags: string[];
  isFavorite: boolean;
  rating: number;
}

export default function TTSAudioLibrary() {
  const [audioItems, setAudioItems] = useState<AudioItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<AudioItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterProvider, setFilterProvider] = useState("all");
  const [filterVoice, setFilterVoice] = useState("all");
  const [sortBy, setSortBy] = useState<"date" | "name" | "duration" | "size">("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [currentlyPlaying, setCurrentlyPlaying] = useState<string | null>(null);

  useEffect(() => {
    loadAudioItems();
  }, []);

  useEffect(() => {
    filterAndSortItems();
  }, [audioItems, searchQuery, filterProvider, filterVoice, sortBy, sortOrder]);

  const loadAudioItems = () => {
    const saved = localStorage.getItem("tts-audio-library");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setAudioItems(parsed.map((item: any) => ({
          ...item,
          createdAt: new Date(item.createdAt)
        })));
      } catch (error) {
        console.error("Failed to load audio library:", error);
      }
    }
  };

  const saveAudioItems = (items: AudioItem[]) => {
    setAudioItems(items);
    localStorage.setItem("tts-audio-library", JSON.stringify(items));
  };

  const filterAndSortItems = () => {
    let filtered = audioItems;

    // Apply filters
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        item =>
          item.name.toLowerCase().includes(query) ||
          item.text.toLowerCase().includes(query) ||
          item.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    if (filterProvider !== "all") {
      filtered = filtered.filter(item => item.provider === filterProvider);
    }

    if (filterVoice !== "all") {
      filtered = filtered.filter(item => item.voice === filterVoice);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case "date":
          comparison = a.createdAt.getTime() - b.createdAt.getTime();
          break;
        case "name":
          comparison = a.name.localeCompare(b.name);
          break;
        case "duration":
          comparison = a.duration - b.duration;
          break;
        case "size":
          comparison = a.size - b.size;
          break;
      }

      return sortOrder === "asc" ? comparison : -comparison;
    });

    setFilteredItems(filtered);
  };

  const toggleFavorite = (id: string) => {
    const updated = audioItems.map(item =>
      item.id === id ? { ...item, isFavorite: !item.isFavorite } : item
    );
    saveAudioItems(updated);
    toast.success("Updated favorite status");
  };

  const toggleRating = (id: string) => {
    const updated = audioItems.map(item => {
      if (item.id === id) {
        const newRating = item.rating === 5 ? 0 : 5;
        return { ...item, rating: newRating };
      }
      return item;
    });
    saveAudioItems(updated);
    toast.success("Updated rating");
  };

  const deleteItem = (id: string) => {
    const updated = audioItems.filter(item => item.id !== id);
    saveAudioItems(updated);
    setSelectedItems(selectedItems.filter(itemId => itemId !== id));
    toast.success("Audio item deleted");
  };

  const deleteSelected = () => {
    const updated = audioItems.filter(item => !selectedItems.includes(item.id));
    saveAudioItems(updated);
    setSelectedItems([]);
    toast.success(`${selectedItems.length} items deleted`);
  };

  const downloadItem = (item: AudioItem) => {
    const a = document.createElement("a");
    a.href = item.url;
    a.download = item.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    toast.success("Download started");
  };

  const playItem = (item: AudioItem) => {
    if (currentlyPlaying === item.id) {
      setCurrentlyPlaying(null);
      return;
    }
    setCurrentlyPlaying(item.id);
    // In a real implementation, you would control an audio element here
    toast.success(`Playing: ${item.name}`);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ["Bytes", "KB", "MB", "GB"];
    if (bytes === 0) return "0 Bytes";
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + " " + sizes[i];
  };

  const exportLibrary = () => {
    const dataStr = JSON.stringify(filteredItems, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "tts-audio-library.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Library exported");
  };

  const clearAll = () => {
    if (confirm("Are you sure you want to delete all audio items? This cannot be undone.")) {
      saveAudioItems([]);
      setSelectedItems([]);
      toast.success("Library cleared");
    }
  };

  const getTotalDuration = () => {
    return filteredItems.reduce((total, item) => total + item.duration, 0);
  };

  const getTotalSize = () => {
    return filteredItems.reduce((total, item) => total + item.size, 0);
  };

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <HardDrive className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold">{filteredItems.length}</div>
                <div className="text-sm text-muted-foreground">Total Files</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Clock className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <div className="text-2xl font-bold">{formatDuration(getTotalDuration())}</div>
                <div className="text-sm text-muted-foreground">Total Duration</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/20">
                <Archive className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold">{formatFileSize(getTotalSize())}</div>
                <div className="text-sm text-muted-foreground">Total Size</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/20">
                <Heart className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {filteredItems.filter(item => item.isFavorite).length}
                </div>
                <div className="text-sm text-muted-foreground">Favorites</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card className="glass border-border/50">
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                placeholder="Search by name, text, or tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="flex gap-2">
              <Select value={filterProvider} onValueChange={setFilterProvider}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Providers</SelectItem>
                  <SelectItem value="kokoro">Kokoro</SelectItem>
                  <SelectItem value="deepgram">Deepgram</SelectItem>
                  <SelectItem value="elevenlabs">ElevenLabs</SelectItem>
                </SelectContent>
              </Select>

              <Select value={filterVoice} onValueChange={setFilterVoice}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Voice" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Voices</SelectItem>
                  <SelectItem value="af_bella">Bella</SelectItem>
                  <SelectItem value="af_sky">Sky</SelectItem>
                  <SelectItem value="am_adam">Adam</SelectItem>
                  <SelectItem value="am_michael">Michael</SelectItem>
                </SelectContent>
              </Select>

              <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="name">Name</SelectItem>
                  <SelectItem value="duration">Duration</SelectItem>
                  <SelectItem value="size">Size</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                size="icon"
                onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
              >
                {sortOrder === "asc" ? (
                  <SortAsc className="w-4 h-4" />
                ) : (
                  <SortDesc className="w-4 h-4" />
                )}
              </Button>

              <Button
                variant="outline"
                size="icon"
                onClick={() => setViewMode(viewMode === "grid" ? "list" : "grid")}
              >
                {viewMode === "grid" ? <List className="w-4 h-4" /> : <Grid className="w-4 h-4" />}
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-2 mt-4">
            {selectedItems.length > 0 && (
              <>
                <span className="text-sm text-muted-foreground">
                  {selectedItems.length} selected
                </span>
                <Button variant="destructive" size="sm" onClick={deleteSelected}>
                  <Trash2 className="w-4 h-4 mr-1" />
                  Delete Selected
                </Button>
              </>
            )}
            <Button variant="outline" size="sm" onClick={exportLibrary}>
              <Download className="w-4 h-4 mr-1" />
              Export
            </Button>
            <Button variant="destructive" size="sm" onClick={clearAll}>
              <Trash2 className="w-4 h-4 mr-1" />
              Clear All
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Audio List */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderOpen className="w-5 h-5" />
            Audio Library
          </CardTitle>
          <CardDescription>
            {filteredItems.length} items in your library
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredItems.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Archive className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No audio files found</p>
              <p className="text-sm mt-2">Synthesize some text to get started</p>
            </div>
          ) : (
            <div className={viewMode === "grid" ? "grid gap-4 md:grid-cols-2 lg:grid-cols-3" : "space-y-2"}>
              {filteredItems.map((item) => (
                <div
                  key={item.id}
                  className={`p-4 rounded-lg border border-border/50 glass-hover cursor-pointer ${
                    viewMode === "list" ? "flex items-center gap-4" : ""
                  }`}
                  onClick={() => {
                    if (viewMode === "list") {
                      playItem(item);
                    }
                  }}
                >
                  {viewMode === "grid" ? (
                    <>
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={selectedItems.includes(item.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedItems([...selectedItems, item.id]);
                              } else {
                                setSelectedItems(selectedItems.filter(id => id !== item.id));
                              }
                            }}
                            className="rounded"
                          />
                          <h3 className="font-semibold truncate">{item.name}</h3>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteItem(item.id);
                          }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>

                      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                        {item.text}
                      </p>

                      <div className="flex flex-wrap gap-2 mb-3">
                        <Badge variant="outline">{item.provider}</Badge>
                        <Badge variant="outline">{item.voice}</Badge>
                      </div>

                      <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                        <span>{formatDuration(item.duration)}</span>
                        <span>{formatFileSize(item.size)}</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleFavorite(item.id);
                            }}
                          >
                            <Heart
                              className={`w-4 h-4 ${
                                item.isFavorite ? "fill-red-500 text-red-500" : "text-muted-foreground"
                              }`}
                            />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleRating(item.id);
                            }}
                          >
                            <Star
                              className={`w-4 h-4 ${
                                item.rating === 5 ? "fill-yellow-500 text-yellow-500" : "text-muted-foreground"
                              }`}
                            />
                          </Button>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation();
                              playItem(item);
                            }}
                          >
                            {currentlyPlaying === item.id ? (
                              <Pause className="w-4 h-4" />
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation();
                              downloadItem(item);
                            }}
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <input
                        type="checkbox"
                        checked={selectedItems.includes(item.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedItems([...selectedItems, item.id]);
                          } else {
                            setSelectedItems(selectedItems.filter(id => id !== item.id));
                          }
                        }}
                        className="rounded"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold truncate">{item.name}</h3>
                          {item.isFavorite && <Heart className="w-4 h-4 fill-red-500 text-red-500" />}
                          {item.rating === 5 && <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />}
                        </div>
                        <p className="text-sm text-muted-foreground truncate">
                          {item.text}
                        </p>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <Badge variant="outline">{item.provider}</Badge>
                        <span>{formatDuration(item.duration)}</span>
                        <span>{formatFileSize(item.size)}</span>
                      </div>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            playItem(item);
                          }}
                        >
                          {currentlyPlaying === item.id ? (
                            <Pause className="w-4 h-4" />
                          ) : (
                            <Play className="w-4 h-4" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            downloadItem(item);
                          }}
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

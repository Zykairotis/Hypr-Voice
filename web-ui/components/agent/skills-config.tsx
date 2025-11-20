"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Save, Zap, FileText, Terminal, Mic2, Bot, Search } from "lucide-react";
import { toast } from "sonner";

interface Skill {
  name: string;
  description: string;
  enabled: boolean;
  category: "core" | "voice" | "advanced";
  icon: React.ReactNode;
}

export default function SkillsConfig() {
  const [skills, setSkills] = useState<Skill[]>([
    {
      name: "file_operations",
      description: "Read, write, and manipulate files",
      enabled: true,
      category: "core",
      icon: <FileText className="w-4 h-4" />,
    },
    {
      name: "bash_execution",
      description: "Execute bash commands",
      enabled: true,
      category: "core",
      icon: <Terminal className="w-4 h-4" />,
    },
    {
      name: "voice_synthesis",
      description: "Convert text to speech using TTS providers",
      enabled: true,
      category: "voice",
      icon: <Mic2 className="w-4 h-4" />,
    },
    {
      name: "hierarchical_agents",
      description: "Create and manage sub-agents",
      enabled: true,
      category: "advanced",
      icon: <Bot className="w-4 h-4" />,
    },
    {
      name: "web_search",
      description: "Search the web using Brave Search",
      enabled: false,
      category: "advanced",
      icon: <Search className="w-4 h-4" />,
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorCount, setErrorCount] = useState(0);

  useEffect(() => {
    loadSkillsConfig();
  }, []);

  const loadSkillsConfig = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/config/skills", {
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const config = await response.json();
        if (config.skills) {
          setSkills(prevSkills =>
            prevSkills.map(skill => ({
              ...skill,
              enabled: config.skills[skill.name]?.enabled ?? skill.enabled,
            }))
          );
        }
        setErrorCount(0);
      }
    } catch (error) {
      // Only log once to avoid console spam
      if (errorCount === 0) {
        console.warn("Backend not available. Using default skills configuration.");
      }
      setErrorCount(prev => prev + 1);
    }
  };

  const toggleSkill = (index: number) => {
    setSkills(prevSkills => {
      const updated = [...prevSkills];
      updated[index].enabled = !updated[index].enabled;
      return updated;
    });
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const config = {
        skills: skills.reduce((acc, skill) => ({
          ...acc,
          [skill.name]: {
            enabled: skill.enabled,
            description: skill.description,
          },
        }), {}),
      };

      const response = await fetch("http://localhost:8934/api/config/skills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        toast.success("Skills configuration saved successfully");
      } else {
        toast.error("Failed to save configuration");
      }
    } catch (error) {
      toast.error("Error saving configuration");
    } finally {
      setIsLoading(false);
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case "core":
        return "Core Skills";
      case "voice":
        return "Voice Skills";
      case "advanced":
        return "Advanced Skills";
      default:
        return "Other";
    }
  };

  const groupedSkills = skills.reduce((acc, skill) => {
    if (!acc[skill.category]) {
      acc[skill.category] = [];
    }
    acc[skill.category].push(skill);
    return acc;
  }, {} as Record<string, Skill[]>);

  return (
    <div className="space-y-6">
      {/* Skills Info */}
      <div className="p-4 rounded-lg glass border border-border/50">
        <div className="flex items-start gap-3">
          <Zap className="w-5 h-5 text-primary mt-0.5" />
          <div>
            <p className="font-medium">Agent Skills</p>
            <p className="text-sm text-muted-foreground mt-1">
              Skills define what your agents can do. Enable the skills needed for your tasks.
            </p>
          </div>
        </div>
      </div>

      {/* Skill Categories */}
      {Object.entries(groupedSkills).map(([category, categorySkills]) => (
        <div key={category} className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-base font-semibold">
              {getCategoryLabel(category)}
            </Label>
            <Badge variant="outline" className="glass">
              {categorySkills.filter(s => s.enabled).length}/{categorySkills.length} enabled
            </Badge>
          </div>

          <div className="space-y-3">
            {categorySkills.map((skill, globalIndex) => {
              const index = skills.findIndex(s => s.name === skill.name);
              return (
                <Card
                  key={skill.name}
                  className="glass-hover border-border/50 p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <div className={`p-2 rounded-lg ${
                        skill.enabled 
                          ? "bg-primary/10 border border-primary/20" 
                          : "bg-muted/10 border border-border/20"
                      }`}>
                        {skill.icon}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">
                            {skill.name.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                          </span>
                          {skill.enabled && (
                            <Badge variant="outline" className="text-xs bg-green-500/10 text-green-500 border-green-500/30">
                              Active
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-0.5">
                          {skill.description}
                        </p>
                      </div>
                    </div>

                    <Switch
                      checked={skill.enabled}
                      onCheckedChange={() => toggleSkill(index)}
                    />
                  </div>
                </Card>
              );
            })}
          </div>

          {category !== "advanced" && <Separator className="bg-border/50 mt-6" />}
        </div>
      ))}

      {/* Statistics */}
      <Card className="glass border-border/50 p-4">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-primary">
              {skills.filter(s => s.enabled).length}
            </div>
            <div className="text-sm text-muted-foreground">Active Skills</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-muted-foreground">
              {skills.length}
            </div>
            <div className="text-sm text-muted-foreground">Total Skills</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-500">
              {Object.keys(groupedSkills).length}
            </div>
            <div className="text-sm text-muted-foreground">Categories</div>
          </div>
        </div>
      </Card>

      {/* Save Button */}
      <div className="pt-4">
        <Button
          onClick={handleSave}
          disabled={isLoading}
          className="w-full glow-hover"
          size="lg"
        >
          <Save className="w-4 h-4 mr-2" />
          {isLoading ? "Saving..." : "Save Skills Configuration"}
        </Button>
      </div>
    </div>
  );
}


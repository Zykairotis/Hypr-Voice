"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
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
  Grid3X3,
  List,
  Plus,
  Sparkles,
} from "lucide-react";
import SkillCard from "./SkillCard";
import SkillExecutionMonitor from "./SkillExecutionMonitor";
import SkillAnalytics from "./SkillAnalytics";
import SkillConfiguration from "./SkillConfiguration";
import CustomSkillCreator from "./CustomSkillCreator";
import ToolsMarketplace from "./ToolsMarketplace";
import SkillDocumentation from "./SkillDocumentation";
import CommunityMarketplace from "./CommunityMarketplace";
import type { Skill } from "@/types/skills";

export default function SkillsLibrary() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [filteredSkills, setFilteredSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [activeTab, setActiveTab] = useState("library");

  useEffect(() => {
    fetchSkills();
  }, []);

  useEffect(() => {
    filterSkills();
  }, [skills, searchQuery, categoryFilter]);

  const fetchSkills = async () => {
    try {
      const response = await fetch("/api/skills/list");
      const data = await response.json();
      setSkills(data.skills);
    } catch (error) {
      console.error("Failed to fetch skills:", error);
    } finally {
      setLoading(false);
    }
  };

  const filterSkills = () => {
    let filtered = skills;

    if (searchQuery) {
      filtered = filtered.filter(
        (skill) =>
          skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          skill.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
          skill.tags.some((tag) =>
            tag.toLowerCase().includes(searchQuery.toLowerCase())
          )
      );
    }

    if (categoryFilter !== "all") {
      filtered = filtered.filter((skill) => skill.category === categoryFilter);
    }

    setFilteredSkills(filtered);
  };

  const handleToggleSkill = (skillId: string, enabled: boolean) => {
    setSkills((prev) =>
      prev.map((skill) =>
        skill.id === skillId ? { ...skill, enabled } : skill
      )
    );
  };

  const handleConfigureSkill = (skill: Skill) => {
    setSelectedSkill(skill);
    setActiveTab("configuration");
  };

  const handleExecuteSkill = (skill: Skill) => {
    setSelectedSkill(skill);
    setActiveTab("monitor");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
            Skills & Tools Marketplace
          </h2>
          <p className="text-white/60 mt-1">
            Discover, configure, and manage agent skills
          </p>
        </div>
        <Button
          onClick={() => setActiveTab("creator")}
          className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Skill
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-white/5 border border-white/10">
          <TabsTrigger value="library" className="data-[state=active]:bg-white/10">
            <Sparkles className="w-4 h-4 mr-2" />
            Library
          </TabsTrigger>
          <TabsTrigger value="creator" className="data-[state=active]:bg-white/10">
            <Plus className="w-4 h-4 mr-2" />
            Creator
          </TabsTrigger>
          <TabsTrigger value="tools" className="data-[state=active]:bg-white/10">
            <Grid3X3 className="w-4 h-4 mr-2" />
            Tools
          </TabsTrigger>
          <TabsTrigger value="analytics" className="data-[state=active]:bg-white/10">
            <Filter className="w-4 h-4 mr-2" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="docs" className="data-[state=active]:bg-white/10">
            <Search className="w-4 h-4 mr-2" />
            Docs
          </TabsTrigger>
          <TabsTrigger value="community" className="data-[state=active]:bg-white/10">
            <Grid3X3 className="w-4 h-4 mr-2" />
            Community
          </TabsTrigger>
          <TabsTrigger value="monitor" className="data-[state=active]:bg-white/10">
            <Filter className="w-4 h-4 mr-2" />
            Monitor
          </TabsTrigger>
        </TabsList>

        <TabsContent value="library" className="space-y-6">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
              <Input
                placeholder="Search skills..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-white/5 border-white/10"
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[180px] bg-white/5 border-white/10">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="core">Core</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
                <SelectItem value="mcp">MCP</SelectItem>
                <SelectItem value="community">Community</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex border border-white/10 rounded-lg">
              <Button
                variant={viewMode === "grid" ? "default" : "ghost"}
                size="sm"
                onClick={() => setViewMode("grid")}
                className="rounded-r-none"
              >
                <Grid3X3 className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === "list" ? "default" : "ghost"}
                size="sm"
                onClick={() => setViewMode("list")}
                className="rounded-l-none"
              >
                <List className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <Card key={i} className="h-64 bg-white/5 animate-pulse" />
              ))}
            </div>
          ) : filteredSkills.length === 0 ? (
            <Card className="p-12 text-center bg-white/5">
              <p className="text-white/60">No skills found</p>
            </Card>
          ) : (
            <motion.div
              layout
              className={`grid gap-4 ${
                viewMode === "grid"
                  ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
                  : "grid-cols-1"
              }`}
            >
              <AnimatePresence>
                {filteredSkills.map((skill) => (
                  <motion.div
                    key={skill.id}
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                  >
                    <SkillCard
                      skill={skill}
                      onToggle={handleToggleSkill}
                      onConfigure={handleConfigureSkill}
                      onExecute={handleExecuteSkill}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>
          )}
        </TabsContent>

        <TabsContent value="creator">
          <CustomSkillCreator />
        </TabsContent>

        <TabsContent value="tools">
          <ToolsMarketplace />
        </TabsContent>

        <TabsContent value="analytics">
          <SkillAnalytics />
        </TabsContent>

        <TabsContent value="docs">
          <SkillDocumentation />
        </TabsContent>

        <TabsContent value="community">
          <CommunityMarketplace />
        </TabsContent>

        <TabsContent value="monitor">
          <SkillExecutionMonitor selectedSkill={selectedSkill} />
        </TabsContent>

        <TabsContent value="configuration">
          {selectedSkill && (
            <SkillConfiguration skill={selectedSkill} onClose={() => setActiveTab("library")} />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Star,
  Download,
  Search,
  Filter,
  TrendingUp,
  Heart,
  User,
} from "lucide-react";

const COMMUNITY_SKILLS = [
  {
    id: "web_scraper",
    name: "Web Scraper",
    description: "Advanced web scraping tool with CSS selector support",
    author: "SkillCraft Community",
    category: "web",
    downloads: 1567,
    rating: 4.8,
    reviews: 234,
    verified: true,
    tags: ["web", "scrape", "html"],
    difficulty: "intermediate",
  },
  {
    id: "data_analyzer",
    name: "Data Analyzer",
    description: "Comprehensive data analysis with visualizations",
    author: "DataTools Inc",
    category: "data",
    downloads: 2341,
    rating: 4.6,
    reviews: 187,
    verified: true,
    tags: ["data", "analysis", "ml"],
    difficulty: "advanced",
  },
  {
    id: "image_processor",
    name: "Image Processor",
    description: "Process and manipulate images with AI",
    author: "VisionAI",
    category: "media",
    downloads: 892,
    rating: 4.9,
    reviews: 156,
    verified: false,
    tags: ["image", "ai", "media"],
    difficulty: "intermediate",
  },
  {
    id: "email_sender",
    name: "Email Sender",
    description: "Send emails with templates and attachments",
    author: "CommTools",
    category: "communication",
    downloads: 1205,
    rating: 4.5,
    reviews: 98,
    verified: true,
    tags: ["email", "templates", "smtp"],
    difficulty: "beginner",
  },
  {
    id: "pdf_generator",
    name: "PDF Generator",
    description: "Generate professional PDF documents",
    author: "DocTools",
    category: "document",
    downloads: 1789,
    rating: 4.7,
    reviews: 203,
    verified: false,
    tags: ["pdf", "document", "export"],
    difficulty: "intermediate",
  },
  {
    id: "translator",
    name: "AI Translator",
    description: "Multi-language translation with context",
    author: "LangTech",
    category: "nlp",
    downloads: 3421,
    rating: 4.8,
    reviews: 567,
    verified: true,
    tags: ["translate", "nlp", "multilingual"],
    difficulty: "advanced",
  },
];

export default function CommunityMarketplace() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [sortBy, setSortBy] = useState("downloads");

  const categories = ["all", ...new Set(COMMUNITY_SKILLS.map((s) => s.category))];

  const filteredSkills = COMMUNITY_SKILLS.filter((skill) => {
    const matchesSearch =
      skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.tags.some((tag) =>
        tag.toLowerCase().includes(searchQuery.toLowerCase())
      );

    const matchesCategory =
      filterCategory === "all" || skill.category === filterCategory;

    return matchesSearch && matchesCategory;
  }).sort((a, b) => {
    switch (sortBy) {
      case "downloads":
        return b.downloads - a.downloads;
      case "rating":
        return b.rating - a.rating;
      case "name":
        return a.name.localeCompare(b.name);
      default:
        return 0;
    }
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
          Community Marketplace
        </h2>
        <p className="text-white/60 mt-1">
          Discover and install skills from the community
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
          <Input
            placeholder="Search community skills..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-white/5 border-white/10"
          />
        </div>
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="bg-white/5 border-white/10 rounded-md px-4 py-2 text-white"
        >
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="bg-white/5 border-white/10 rounded-md px-4 py-2 text-white"
        >
          <option value="downloads">Most Downloads</option>
          <option value="rating">Highest Rated</option>
          <option value="name">Name</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredSkills.map((skill) => (
          <motion.div
            key={skill.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -4 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
          >
            <Card className="h-full">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CardTitle className="text-lg">{skill.name}</CardTitle>
                      {skill.verified && (
                        <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                          Verified
                        </Badge>
                      )}
                    </div>
                    <CardDescription className="text-sm text-white/60">
                      {skill.description}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="flex items-center gap-2 text-sm text-white/60">
                  <User className="w-4 h-4" />
                  <span>{skill.author}</span>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="bg-white/5 border-white/10 text-white/70">
                    {skill.category}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={
                      skill.difficulty === "beginner"
                        ? "bg-green-500/20 text-green-400 border-green-500/30"
                        : skill.difficulty === "intermediate"
                        ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                        : "bg-red-500/20 text-red-400 border-red-500/30"
                    }
                  >
                    {skill.difficulty}
                  </Badge>
                </div>

                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                    <span className="font-semibold text-white">{skill.rating}</span>
                    <span className="text-white/60">({skill.reviews})</span>
                  </div>
                  <div className="flex items-center gap-1 text-white/60">
                    <Download className="w-4 h-4" />
                    <span>{skill.downloads.toLocaleString()}</span>
                  </div>
                </div>

                {skill.tags && skill.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {skill.tags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="outline"
                        className="text-xs bg-white/5 border-white/10 text-white/60"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>

              <CardFooter className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1">
                  View Details
                </Button>
                <Button size="sm" className="flex-1">
                  <Download className="w-4 h-4 mr-2" />
                  Install
                </Button>
              </CardFooter>
            </Card>
          </motion.div>
        ))}
      </div>

      {filteredSkills.length === 0 && (
        <Card className="p-12 text-center bg-white/5">
          <p className="text-white/60">No community skills found</p>
        </Card>
      )}
    </div>
  );
}

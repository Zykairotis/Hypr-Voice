"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Book,
  Search,
  Code,
  Play,
  FileText,
  Youtube,
  ExternalLink,
} from "lucide-react";

const SKILL_DOCS = {
  "file_operations": {
    name: "File Operations",
    description: "Complete guide to file operations skill",
    sections: [
      {
        id: "overview",
        title: "Overview",
        content: `The File Operations skill provides comprehensive file system operations within the agent's working directory. It allows agents to read, write, list, and delete files safely.

**Key Features:**
- Read file contents
- Write new files or overwrite existing ones
- List directory contents recursively
- Delete files and directories
- Safe path handling

**Security:**
All file operations are restricted to the agent's working directory to prevent unauthorized access to the filesystem.`,
      },
      {
        id: "parameters",
        title: "Parameters",
        content: `**operation** (required) - string
The operation to perform. Valid values: "read", "write", "list", "delete"

**path** (required) - string
Relative path to the file or directory within the working directory

**content** (optional) - string
Content to write (required for "write" operation)`,
      },
      {
        id: "examples",
        title: "Examples",
        content: `// Read a file
{
  "operation": "read",
  "path": "data.txt"
}

// Write a file
{
  "operation": "write",
  "path": "output.txt",
  "content": "Hello, World!"
}

// List directory contents
{
  "operation": "list",
  "path": "."
}

// Delete a file
{
  "operation": "delete",
  "path": "old_file.txt"
}`,
      },
    ],
  },
};

const QUICK_TUTORIALS = [
  {
    id: "getting-started",
    title: "Getting Started with Skills",
    description: "Learn the basics of using skills in your agents",
    duration: "5 min",
    difficulty: "Beginner",
    type: "video",
  },
  {
    id: "creating-skills",
    title: "Creating Custom Skills",
    description: "Build your own skills from scratch",
    duration: "15 min",
    difficulty: "Intermediate",
    type: "tutorial",
  },
  {
    id: "skill-parameters",
    title: "Skill Parameters & Configuration",
    description: "Master skill configuration and parameters",
    duration: "10 min",
    difficulty: "Intermediate",
    type: "article",
  },
];

export default function SkillDocumentation() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDoc, setSelectedDoc] = useState("file_operations");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
          Skill Documentation
        </h2>
        <p className="text-white/60 mt-1">
          Comprehensive guides and API reference
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
          <Input
            placeholder="Search documentation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-white/5 border-white/10"
          />
        </div>
      </div>

      <Tabs defaultValue="guides" className="space-y-6">
        <TabsList className="bg-white/5 border border-white/10">
          <TabsTrigger value="guides" className="data-[state=active]:bg-white/10">
            <Book className="w-4 h-4 mr-2" />
            Guides
          </TabsTrigger>
          <TabsTrigger value="api" className="data-[state=active]:bg-white/10">
            <Code className="w-4 h-4 mr-2" />
            API Reference
          </TabsTrigger>
          <TabsTrigger value="tutorials" className="data-[state=active]:bg-white/10">
            <Play className="w-4 h-4 mr-2" />
            Tutorials
          </TabsTrigger>
        </TabsList>

        <TabsContent value="guides" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {SKILL_DOCS[selectedDoc as keyof typeof SKILL_DOCS] && (
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle>
                      {SKILL_DOCS[selectedDoc as keyof typeof SKILL_DOCS].name}
                    </CardTitle>
                    <CardDescription>
                      {
                        SKILL_DOCS[selectedDoc as keyof typeof SKILL_DOCS]
                          .description
                      }
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {SKILL_DOCS[selectedDoc as keyof typeof SKILL_DOCS].sections.map(
                      (section) => (
                        <div key={section.id} className="space-y-2">
                          <h3 className="text-lg font-semibold">{section.title}</h3>
                          <div className="prose prose-invert max-w-none">
                            <pre className="bg-black/40 p-4 rounded-lg overflow-x-auto text-sm">
                              {section.content}
                            </pre>
                          </div>
                        </div>
                      )
                    )}
                  </CardContent>
                </Card>
              )}
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Available Skills</h3>
              {Object.entries(SKILL_DOCS).map(([key, doc]) => (
                <motion.div
                  key={key}
                  whileHover={{ x: 4 }}
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                >
                  <Card
                    className={`cursor-pointer transition-all ${
                      selectedDoc === key
                        ? "bg-purple-500/20 border-purple-500/50"
                        : "bg-white/5 border-white/10 hover:bg-white/10"
                    }`}
                    onClick={() => setSelectedDoc(key)}
                  >
                    <CardHeader>
                      <CardTitle className="text-base">{doc.name}</CardTitle>
                      <CardDescription className="text-sm">
                        {doc.description}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="api">
          <Card className="bg-white/5 border-white/10">
            <CardHeader>
              <CardTitle>API Reference</CardTitle>
              <CardDescription>
                Complete API documentation for all skills
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-6">
                  {Object.entries(SKILL_DOCS).map(([key, doc]) => (
                    <div key={key} className="space-y-4">
                      <h3 className="text-xl font-semibold">{doc.name}</h3>
                      <div className="pl-4 border-l-2 border-white/10 space-y-4">
                        {doc.sections.map((section) => (
                          <div key={section.id}>
                            <h4 className="font-medium mb-2">{section.title}</h4>
                            <pre className="bg-black/40 p-4 rounded-lg overflow-x-auto text-sm">
                              {section.content}
                            </pre>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tutorials">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {QUICK_TUTORIALS.map((tutorial) => (
              <motion.div
                key={tutorial.id}
                whileHover={{ y: -4 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
              >
                <Card className="bg-white/5 border-white/10 hover:bg-white/10 cursor-pointer">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{tutorial.title}</CardTitle>
                        <CardDescription>{tutorial.description}</CardDescription>
                      </div>
                      {tutorial.type === "video" ? (
                        <Youtube className="w-5 h-5 text-red-400" />
                      ) : (
                        <FileText className="w-5 h-5 text-blue-400" />
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={
                          tutorial.difficulty === "Beginner"
                            ? "bg-green-500/20 text-green-400 border-green-500/30"
                            : tutorial.difficulty === "Intermediate"
                            ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                            : "bg-red-500/20 text-red-400 border-red-500/30"
                        }
                      >
                        {tutorial.difficulty}
                      </Badge>
                      <span className="text-sm text-white/60">
                        {tutorial.duration}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

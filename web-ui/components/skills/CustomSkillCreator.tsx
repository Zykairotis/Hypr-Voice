"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Editor from "@monaco-editor/react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Save,
  Play,
  Code2,
  Book,
  Wand2,
  FileCode,
} from "lucide-react";
import type { SkillTemplate } from "@/types/skills";

const SKILL_TEMPLATES: SkillTemplate[] = [
  {
    id: "basic",
    name: "Basic Skill",
    description: "Simple skill with basic functionality",
    category: "beginner",
    difficulty: "beginner",
    estimated_time: "5 minutes",
    code: `import { Skill } from 'hypr-voice/core/skills';

export default class BasicSkill extends Skill {
  constructor() {
    super({
      name: "basic_skill",
      description: "A basic skill implementation",
      parameters: [
        {
          name: "input",
          type: "string",
          description: "Input parameter",
          required: true
        }
      ]
    });
  }

  async execute(params) {
    // Your skill logic here
    return {
      success: true,
      result: \`Processed: \${params.input}\`
    };
  }
}`,
    parameters: [
      {
        name: "input",
        type: "string",
        description: "Input parameter",
        required: true,
      },
    ],
  },
  {
    id: "api",
    name: "API Integration",
    description: "Skill that integrates with external APIs",
    category: "intermediate",
    difficulty: "intermediate",
    estimated_time: "15 minutes",
    code: `import { Skill } from 'hypr-voice/core/skills';
import fetch from 'node-fetch';

export default class APISkill extends Skill {
  constructor() {
    super({
      name: "api_integration",
      description: "Integrate with external APIs",
      parameters: [
        {
          name: "endpoint",
          type: "string",
          description: "API endpoint URL",
          required: true
        },
        {
          name: "method",
          type: "string",
          description: "HTTP method",
          required: false,
          options: ["GET", "POST", "PUT", "DELETE"]
        }
      ]
    });
  }

  async execute(params) {
    try {
      const response = await fetch(params.endpoint, {
        method: params.method || 'GET'
      });
      const data = await response.json();
      return {
        success: true,
        data
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}`,
    parameters: [
      {
        name: "endpoint",
        type: "string",
        description: "API endpoint URL",
        required: true,
      },
      {
        name: "method",
        type: "string",
        description: "HTTP method",
        required: false,
        options: ["GET", "POST", "PUT", "DELETE"],
      },
    ],
  },
];

export default function CustomSkillCreator() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [code, setCode] = useState(SKILL_TEMPLATES[0].code);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("basic");
  const [showPreview, setShowPreview] = useState(false);

  const handleTemplateChange = (templateId: string) => {
    const template = SKILL_TEMPLATES.find((t) => t.id === templateId);
    if (template) {
      setSelectedTemplate(templateId);
      setCode(template.code);
    }
  };

  const handleSave = () => {
    console.log("Saving skill:", { name, description, code });
  };

  const handleTest = () => {
    console.log("Testing skill:", { name, description, code });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
          Custom Skill Creator
        </h2>
        <p className="text-white/60 mt-1">
          Build and deploy custom skills for your agents
        </p>
      </div>

      <Tabs defaultValue="editor" className="space-y-6">
        <TabsList className="bg-white/5 border border-white/10">
          <TabsTrigger value="editor" className="data-[state=active]:bg-white/10">
            <Code2 className="w-4 h-4 mr-2" />
            Editor
          </TabsTrigger>
          <TabsTrigger value="templates" className="data-[state=active]:bg-white/10">
            <FileCode className="w-4 h-4 mr-2" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="preview" className="data-[state=active]:bg-white/10">
            <Book className="w-4 h-4 mr-2" />
            Preview
          </TabsTrigger>
        </TabsList>

        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {SKILL_TEMPLATES.map((template) => (
              <motion.div
                key={template.id}
                whileHover={{ y: -4 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <Card
                  className={`cursor-pointer transition-all ${
                    selectedTemplate === template.id
                      ? "bg-purple-500/20 border-purple-500/50"
                      : "bg-white/5 border-white/10 hover:bg-white/10"
                  }`}
                  onClick={() => handleTemplateChange(template.id)}
                >
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{template.name}</CardTitle>
                      <Badge
                        variant="outline"
                        className={
                          template.difficulty === "beginner"
                            ? "bg-green-500/20 text-green-400 border-green-500/30"
                            : template.difficulty === "intermediate"
                            ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                            : "bg-red-500/20 text-red-400 border-red-500/30"
                        }
                      >
                        {template.difficulty}
                      </Badge>
                    </div>
                    <CardDescription>{template.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4 text-sm text-white/60">
                      <div className="flex items-center gap-1">
                        <Wand2 className="w-4 h-4" />
                        {template.estimated_time}
                      </div>
                      <div>{template.category}</div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="editor" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Skill Name</Label>
                <Input
                  id="name"
                  placeholder="my_custom_skill"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="bg-white/5 border-white/10"
                />
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe what this skill does..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="bg-white/5 border-white/10"
                  rows={3}
                />
              </div>
            </div>
            <div className="bg-white/5 rounded-lg border border-white/10 overflow-hidden">
              <div className="bg-white/10 px-4 py-2 border-b border-white/10 flex items-center justify-between">
                <span className="text-sm font-medium">Skill Code</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowPreview(true)}
                >
                  <Play className="w-3 h-3 mr-1" />
                  Preview
                </Button>
              </div>
              <Editor
                height="400px"
                defaultLanguage="typescript"
                value={code}
                onChange={(value) => setCode(value || "")}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  padding: { top: 16 },
                  scrollBeyondLastLine: false,
                }}
              />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="preview">
          <Card className="bg-white/5 border-white/10">
            <CardHeader>
              <CardTitle>Skill Preview</CardTitle>
              <CardDescription>
                Preview your skill configuration and code
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-sm text-white/60">Name</Label>
                <p className="text-white">{name || "Unnamed Skill"}</p>
              </div>
              <div>
                <Label className="text-sm text-white/60">Description</Label>
                <p className="text-white">{description || "No description"}</p>
              </div>
              <div>
                <Label className="text-sm text-white/60">Code</Label>
                <pre className="mt-2 p-4 bg-black/40 rounded-lg overflow-x-auto text-sm">
                  <code>{code}</code>
                </pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex gap-2">
        <Button onClick={handleSave} className="flex-1">
          <Save className="w-4 h-4 mr-2" />
          Save Skill
        </Button>
        <Button onClick={handleTest} variant="outline" className="flex-1">
          <Play className="w-4 h-4 mr-2" />
          Test Skill
        </Button>
      </div>

      <Dialog open={showPreview} onOpenChange={setShowPreview}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Skill Preview</DialogTitle>
            <DialogDescription>
              Review your skill before saving
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Name</Label>
              <p className="text-white">{name}</p>
            </div>
            <div>
              <Label>Description</Label>
              <p className="text-white">{description}</p>
            </div>
            <div>
              <Label>Code</Label>
              <pre className="mt-2 p-4 bg-black/40 rounded-lg overflow-x-auto text-sm">
                <code>{code}</code>
              </pre>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowPreview(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Code,
  Save,
  Play,
  TestTube,
  FileCode,
  Settings,
  Wrench,
  Download,
  Upload,
  GitBranch,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { motion } from "framer-motion";
import { useMCPStore } from "@/lib/mcp-store";
import type { CustomMCPServer, MCPServerCategory } from "@/types/mcp";
import { toast } from "sonner";

export default function CustomServerBuilder() {
  const { customServers, createCustomServer, updateCustomServer } = useMCPStore();
  const [selectedTemplate, setSelectedTemplate] = useState("basic");
  const [previewMode, setPreviewMode] = useState(false);
  const [activeTab, setActiveTab] = useState("editor");

  const templates = {
    basic: {
      name: "Basic Server",
      description: "Simple MCP server with basic functionality",
      code: `import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolResultSchema } from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  {
    name: "example-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler("tools/list", async () => {
  return {
    tools: [
      {
        name: "example_tool",
        description: "An example tool",
        inputSchema: {
          type: "object",
          properties: {
            input: {
              type: "string",
              description: "Input value",
            },
          },
          required: ["input"],
        },
      },
    ],
  };
});

server.setRequestHandler("tools/call", async (request) => {
  if (request.params.name === "example_tool") {
    return {
      content: [
        {
          type: "text",
          text: \`Processed: \${request.params.arguments.input}\`,
        },
      ],
    };
  }
  throw new Error("Tool not found");
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});`,
    },
    filesystem: {
      name: "Filesystem Server",
      description: "Server for file and directory operations",
      code: `// Filesystem MCP Server implementation
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { promises as fs } from "fs";
import path from "path";

const server = new Server(
  {
    name: "filesystem-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler("tools/list", async () => {
  return {
    tools: [
      {
        name: "read_file",
        description: "Read the contents of a file",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to the file",
            },
          },
          required: ["path"],
        },
      },
      {
        name: "write_file",
        description: "Write content to a file",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to the file",
            },
            content: {
              type: "string",
              description: "Content to write",
            },
          },
          required: ["path", "content"],
        },
      },
    ],
  };
});

server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "read_file": {
        const content = await fs.readFile(args.path, "utf-8");
        return {
          content: [
            {
              type: "text",
              text: content,
            },
          ],
        };
      }
      case "write_file": {
        await fs.writeFile(args.path, args.content);
        return {
          content: [
            {
              type: "text",
              text: "File written successfully",
            },
          ],
        };
      }
      default:
        throw new Error("Tool not found");
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: \`Error: \${error.message}\`,
        },
      ],
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Filesystem MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});`,
    },
  };

  const [server, setServer] = useState<CustomMCPServer>({
    id: "new",
    name: "",
    description: "",
    category: "custom",
    template: "basic",
    config: {
      command: "node",
      args: ["server.js"],
      enabled: true,
      capabilities: [],
    },
    code: templates.basic.code,
    testingEnabled: true,
    createdAt: new Date(),
    updatedAt: new Date(),
  });

  const handleTemplateChange = (templateId: string) => {
    setServer((prev) => ({
      ...prev,
      template: templateId,
      code: templates[templateId as keyof typeof templates]?.code || prev.code,
    }));
  };

  const handleSave = () => {
    if (server.id === "new") {
      createCustomServer({
        ...server,
        id: `custom-${Date.now()}`,
        createdAt: new Date(),
        updatedAt: new Date(),
      });
      toast.success("Custom server created successfully");
    } else {
      updateCustomServer(server.id, server);
      toast.success("Custom server updated successfully");
    }
  };

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(server, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${server.name || "custom-server"}.json`;
    a.click();
    toast.success("Server exported successfully");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Custom MCP Server Builder</h2>
          <p className="text-muted-foreground">
            Build and configure your own MCP servers
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" onClick={() => setPreviewMode(!previewMode)}>
            <FileCode className="w-4 h-4 mr-2" />
            {previewMode ? "Editor Mode" : "Preview Mode"}
          </Button>
          <Button onClick={handleSave}>
            <Save className="w-4 h-4 mr-2" />
            Save Server
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Server Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Server Name</Label>
                  <Input
                    id="name"
                    value={server.name}
                    onChange={(e) => setServer({ ...server, name: e.target.value })}
                    placeholder="my-custom-server"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Select
                    value={server.category}
                    onValueChange={(value) =>
                      setServer({ ...server, category: value as MCPServerCategory })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="custom">Custom</SelectItem>
                      <SelectItem value="filesystem">Filesystem</SelectItem>
                      <SelectItem value="web">Web</SelectItem>
                      <SelectItem value="database">Database</SelectItem>
                      <SelectItem value="ai">AI</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={server.description}
                  onChange={(e) => setServer({ ...server, description: e.target.value })}
                  placeholder="Describe your server..."
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label>Template</Label>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(templates).map(([id, template]) => (
                    <Card
                      key={id}
                      className={`cursor-pointer transition-all ${
                        server.template === id ? "ring-2 ring-primary" : "hover:shadow-md"
                      }`}
                      onClick={() => handleTemplateChange(id)}
                    >
                      <CardContent className="p-4">
                        <h3 className="font-medium mb-1">{template.name}</h3>
                        <p className="text-sm text-muted-foreground">{template.description}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Code className="w-5 h-5" />
                  Server Code
                </CardTitle>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <TestTube className="w-4 h-4 mr-2" />
                    Test
                  </Button>
                  <Button variant="outline" size="sm">
                    <Play className="w-4 h-4 mr-2" />
                    Run
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {previewMode ? (
                <div className="bg-muted p-4 rounded-lg">
                  <pre className="text-sm overflow-auto">
                    <code>{server.code}</code>
                  </pre>
                </div>
              ) : (
                <Textarea
                  value={server.code}
                  onChange={(e) => setServer({ ...server, code: e.target.value })}
                  className="font-mono text-sm min-h-[400px]"
                  placeholder="Enter your server code here..."
                />
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Execution Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="command">Command</Label>
                <Input
                  id="command"
                  value={server.config.command || ""}
                  onChange={(e) =>
                    setServer({
                      ...server,
                      config: { ...server.config, command: e.target.value },
                    })
                  }
                  placeholder="node"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="args">Arguments</Label>
                <Textarea
                  id="args"
                  value={(server.config.args || []).join("\n")}
                  onChange={(e) =>
                    setServer({
                      ...server,
                      config: {
                        ...server.config,
                        args: e.target.value.split("\n").filter((arg) => arg.trim()),
                      },
                    })
                  }
                  placeholder="One argument per line"
                  rows={4}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Testing</Label>
                  <p className="text-sm text-muted-foreground">
                    Run tests automatically
                  </p>
                </div>
                <Switch
                  checked={server.testingEnabled}
                  onCheckedChange={(checked) =>
                    setServer({ ...server, testingEnabled: checked })
                  }
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Custom Servers</CardTitle>
              <CardDescription>Previously created servers</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {customServers.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No custom servers created yet
                  </p>
                ) : (
                  customServers.map((srv) => (
                    <div
                      key={srv.id}
                      className="p-3 border rounded-lg cursor-pointer hover:bg-accent"
                      onClick={() => setServer(srv)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <p className="font-medium text-sm">{srv.name}</p>
                        <Badge variant="outline" className="text-xs">
                          {srv.category}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {srv.description}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {server.testingEnabled && (
            <Card>
              <CardHeader>
                <CardTitle>Test Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-muted-foreground">
                  <TestTube className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="text-sm">No tests run yet</p>
                  <p className="text-xs">Click "Test" to run server tests</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

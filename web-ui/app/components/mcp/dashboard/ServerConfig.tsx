"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Save,
  Key,
  Server,
  Settings,
  Activity,
  Eye,
  EyeOff,
  TestTube,
  RefreshCw,
} from "lucide-react";
import { motion } from "framer-motion";
import { useMCPStore } from "@/lib/mcp-store";
import type { MCPServerConfig, MCPServerCategory } from "@/types/mcp";
import { toast } from "sonner";

export default function ServerConfig() {
  const { servers, selectedServerId, setSelectedServer, updateServer } = useMCPStore();
  const [showApiKey, setShowApiKey] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const server = selectedServerId ? servers[selectedServerId] : null;

  if (!server) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <Settings className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No server selected</h3>
          <p className="text-muted-foreground">
            Select a server from the list to configure its settings
          </p>
        </CardContent>
      </Card>
    );
  }

  const handleSave = () => {
    updateServer(server.id, server);
    toast.success("Server configuration saved");
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);

    try {
      // Simulate test
      await new Promise((resolve) => setTimeout(resolve, 2000));
      setTestResult({
        success: true,
        latency: Math.floor(Math.random() * 200) + 50,
        message: "Connection successful",
      });
      toast.success("Server test passed");
    } catch (error) {
      setTestResult({
        success: false,
        message: "Connection failed",
      });
      toast.error("Server test failed");
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Server className="w-5 h-5" />
                {server.name}
              </CardTitle>
              <CardDescription>{server.description}</CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleTestConnection} disabled={isTesting}>
                <TestTube className="w-4 h-4 mr-2" />
                {isTesting ? "Testing..." : "Test Connection"}
              </Button>
              <Button size="sm" onClick={handleSave}>
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs defaultValue="general" className="space-y-4">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="connection">Connection</TabsTrigger>
          <TabsTrigger value="auth">Authentication</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
          <TabsTrigger value="tests">Tests</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
              <CardDescription>
                Configure the basic settings for your MCP server
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Server Name</Label>
                  <Input
                    id="name"
                    value={server.name}
                    onChange={(e) => updateServer(server.id, { name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Select
                    value={server.category}
                    onValueChange={(value) =>
                      updateServer(server.id, { category: value as MCPServerCategory })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="filesystem">Filesystem</SelectItem>
                      <SelectItem value="github">GitHub</SelectItem>
                      <SelectItem value="git">Git</SelectItem>
                      <SelectItem value="web">Web</SelectItem>
                      <SelectItem value="database">Database</SelectItem>
                      <SelectItem value="memory">Memory</SelectItem>
                      <SelectItem value="ai">AI</SelectItem>
                      <SelectItem value="custom">Custom</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={server.description}
                  onChange={(e) => updateServer(server.id, { description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label>Tags</Label>
                <div className="flex flex-wrap gap-2">
                  {server.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary">
                      {tag}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="ml-2 h-auto p-0"
                        onClick={() => {
                          const newTags = server.tags.filter((_, i) => i !== index);
                          updateServer(server.id, { tags: newTags });
                        }}
                      >
                        ×
                      </Button>
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="connection" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Connection Settings</CardTitle>
              <CardDescription>
                Configure how to connect to your MCP server
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="command">Command</Label>
                <Input
                  id="command"
                  value={server.command}
                  onChange={(e) => updateServer(server.id, { command: e.target.value })}
                  placeholder="e.g., npx, python, node"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="args">Arguments</Label>
                <Textarea
                  id="args"
                  value={server.args?.join("\n") || ""}
                  onChange={(e) =>
                    updateServer(server.id, {
                      args: e.target.value.split("\n").filter((arg) => arg.trim()),
                    })
                  }
                  placeholder="One argument per line"
                  rows={4}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="host">Host</Label>
                  <Input
                    id="host"
                    value={server.host || ""}
                    onChange={(e) => updateServer(server.id, { host: e.target.value })}
                    placeholder="localhost"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="port">Port</Label>
                  <Input
                    id="port"
                    type="number"
                    value={server.port || ""}
                    onChange={(e) => updateServer(server.id, { port: parseInt(e.target.value) })}
                    placeholder="3000"
                  />
                </div>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Auto-start</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically start this server when the application starts
                  </p>
                </div>
                <Switch
                  checked={server.autoStart}
                  onCheckedChange={(checked) => updateServer(server.id, { autoStart: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enabled</Label>
                  <p className="text-sm text-muted-foreground">
                    Enable this server for use
                  </p>
                </div>
                <Switch
                  checked={server.enabled}
                  onCheckedChange={(checked) => updateServer(server.id, { enabled: checked })}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="auth" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Authentication</CardTitle>
              <CardDescription>
                Configure authentication settings for your server
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="authType">Authentication Type</Label>
                <Select
                  value={server.authType || "none"}
                  onValueChange={(value) => updateServer(server.id, { authType: value as any })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="api-key">API Key</SelectItem>
                    <SelectItem value="bearer">Bearer Token</SelectItem>
                    <SelectItem value="oauth">OAuth</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {server.authType === "api-key" && (
                <div className="space-y-2">
                  <Label htmlFor="apiKey">API Key</Label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Input
                        id="apiKey"
                        type={showApiKey ? "text" : "password"}
                        value={server.apiKey || ""}
                        onChange={(e) => updateServer(server.id, { apiKey: e.target.value })}
                        placeholder="Enter your API key"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-2 top-1/2 -translate-y-1/2"
                        onClick={() => setShowApiKey(!showApiKey)}
                      >
                        {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                    <Button variant="outline">
                      <Key className="w-4 h-4 mr-2" />
                      Generate
                    </Button>
                  </div>
                </div>
              )}

              {server.authType === "bearer" && (
                <div className="space-y-2">
                  <Label htmlFor="bearerToken">Bearer Token</Label>
                  <Input
                    id="bearerToken"
                    type="password"
                    value={server.apiKey || ""}
                    onChange={(e) => updateServer(server.id, { apiKey: e.target.value })}
                    placeholder="Enter your bearer token"
                  />
                </div>
              )}

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Encrypt API Keys</Label>
                  <p className="text-sm text-muted-foreground">
                    Encrypt stored API keys for added security
                  </p>
                </div>
                <Switch
                  checked={server.apiKeyEncrypted || false}
                  onCheckedChange={(checked) =>
                    updateServer(server.id, { apiKeyEncrypted: checked })
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="advanced" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Advanced Settings</CardTitle>
              <CardDescription>
                Fine-tune advanced server settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="timeout">Timeout (seconds)</Label>
                  <Input
                    id="timeout"
                    type="number"
                    value={server.timeout || 30}
                    onChange={(e) =>
                      updateServer(server.id, { timeout: parseInt(e.target.value) })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="retryAttempts">Retry Attempts</Label>
                  <Input
                    id="retryAttempts"
                    type="number"
                    value={server.retryAttempts || 3}
                    onChange={(e) =>
                      updateServer(server.id, { retryAttempts: parseInt(e.target.value) })
                    }
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="healthCheckInterval">
                  Health Check Interval (seconds)
                </Label>
                <Input
                  id="healthCheckInterval"
                  type="number"
                  value={server.healthCheckInterval || 60}
                  onChange={(e) =>
                    updateServer(server.id, {
                      healthCheckInterval: parseInt(e.target.value),
                    })
                  }
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Environment Variables</Label>
                <div className="space-y-2">
                  {Object.entries(server.env || {}).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <Input
                        value={key}
                        placeholder="KEY"
                        className="flex-1"
                        readOnly
                      />
                      <Input
                        value={value as string}
                        placeholder="value"
                        className="flex-1"
                        onChange={(e) => {
                          const newEnv = { ...server.env, [key]: e.target.value };
                          updateServer(server.id, { env: newEnv });
                        }}
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const { [key]: removed, ...rest } = server.env || {};
                          updateServer(server.id, { env: rest });
                        }}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const newEnv = { ...server.env, "": "" };
                      updateServer(server.id, { env: newEnv });
                    }}
                  >
                    Add Variable
                  </Button>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Capabilities</Label>
                <div className="grid grid-cols-2 gap-2">
                  {["read", "write", "delete", "search", "analytics", "real-time", "batch"].map(
                    (capability) => (
                      <div key={capability} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id={capability}
                          checked={server.capabilities.includes(capability as any)}
                          onChange={(e) => {
                            const capabilities = e.target.checked
                              ? [...server.capabilities, capability as any]
                              : server.capabilities.filter((c) => c !== capability);
                            updateServer(server.id, { capabilities });
                          }}
                          className="rounded"
                        />
                        <Label htmlFor={capability} className="capitalize">
                          {capability}
                        </Label>
                      </div>
                    )
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tests" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Server Tests</CardTitle>
              <CardDescription>
                Configure and run tests for your server
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {testResult && (
                  <div
                    className={`p-4 rounded-lg ${
                      testResult.success ? "bg-green-500/10" : "bg-red-500/10"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      {testResult.success ? (
                        <RefreshCw className="w-4 h-4 text-green-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      <span className="font-medium">
                        {testResult.success ? "Test Passed" : "Test Failed"}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">{testResult.message}</p>
                    {testResult.latency && (
                      <p className="text-sm text-muted-foreground mt-1">
                        Latency: {testResult.latency}ms
                      </p>
                    )}
                  </div>
                )}

                <div className="text-center py-8 text-muted-foreground">
                  <TestTube className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No tests configured</p>
                  <p className="text-sm">Add custom tests to validate server functionality</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

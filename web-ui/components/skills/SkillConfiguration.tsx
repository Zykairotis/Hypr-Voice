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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import {
  ArrowLeft,
  Settings,
  Save,
  RefreshCw,
  Info,
  Key,
  Zap,
} from "lucide-react";
import type { Skill } from "@/types/skills";

interface SkillConfigurationProps {
  skill: Skill;
  onClose: () => void;
}

export default function SkillConfiguration({
  skill,
  onClose,
}: SkillConfigurationProps) {
  const [config, setConfig] = useState({
    enabled: skill.enabled,
    custom_name: "",
    timeout: 30,
    retry_count: 3,
    auto_retry: true,
    parameters: skill.parameters.reduce((acc, param) => {
      acc[param.name] = param.default_value || "";
      return acc;
    }, {} as Record<string, any>),
  });

  const handleSave = () => {
    console.log("Saving configuration:", config);
  };

  const handleReset = () => {
    setConfig({
      enabled: skill.enabled,
      custom_name: "",
      timeout: 30,
      retry_count: 3,
      auto_retry: true,
      parameters: skill.parameters.reduce((acc, param) => {
        acc[param.name] = param.default_value || "";
        return acc;
      }, {} as Record<string, any>),
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={onClose} className="p-2">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div className="flex-1">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
            Configure Skill: {skill.name}
          </h2>
          <p className="text-white/60 mt-1">{skill.description}</p>
        </div>
        <Badge variant="outline" className="bg-white/5 border-white/10">
          v{skill.version}
        </Badge>
      </div>

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList className="bg-white/5 border border-white/10">
          <TabsTrigger value="general" className="data-[state=active]:bg-white/10">
            <Settings className="w-4 h-4 mr-2" />
            General
          </TabsTrigger>
          <TabsTrigger value="parameters" className="data-[state=active]:bg-white/10">
            <Key className="w-4 h-4 mr-2" />
            Parameters
          </TabsTrigger>
          <TabsTrigger value="advanced" className="data-[state=active]:bg-white/10">
            <Zap className="w-4 h-4 mr-2" />
            Advanced
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-6">
          <Card className="bg-white/5 border-white/10">
            <CardHeader>
              <CardTitle>Basic Configuration</CardTitle>
              <CardDescription>
                Configure basic settings for this skill
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Skill</Label>
                  <p className="text-sm text-white/60">
                    Enable or disable this skill globally
                  </p>
                </div>
                <Switch
                  checked={config.enabled}
                  onCheckedChange={(checked) =>
                    setConfig({ ...config, enabled: checked })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="custom_name">Custom Name</Label>
                <Input
                  id="custom_name"
                  placeholder={skill.name}
                  value={config.custom_name}
                  onChange={(e) =>
                    setConfig({ ...config, custom_name: e.target.value })
                  }
                  className="bg-white/5 border-white/10"
                />
                <p className="text-sm text-white/60">
                  Give this skill a custom display name (optional)
                </p>
              </div>

              <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-400 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-blue-400 mb-1">
                      Skill Information
                    </h4>
                    <div className="text-sm text-white/70 space-y-1">
                      <p>Category: {skill.category}</p>
                      <p>Version: {skill.version}</p>
                      {skill.author && <p>Author: {skill.author}</p>}
                      <p>Usage Count: {skill.usage_count}</p>
                      <p>Success Rate: {skill.success_rate.toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
              </div>

              {skill.tags && skill.tags.length > 0 && (
                <div className="space-y-2">
                  <Label>Tags</Label>
                  <div className="flex flex-wrap gap-2">
                    {skill.tags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="outline"
                        className="bg-white/5 border-white/10 text-white/70"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="parameters" className="space-y-6">
          <Card className="bg-white/5 border-white/10">
            <CardHeader>
              <CardTitle>Parameters</CardTitle>
              <CardDescription>
                Configure parameters for this skill
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {skill.parameters.map((param) => (
                <div key={param.name} className="space-y-2">
                  <Label htmlFor={param.name}>
                    {param.name}
                    {param.required && (
                      <span className="text-red-400 ml-1">*</span>
                    )}
                  </Label>
                  {param.type === "string" && !param.options && (
                    <Input
                      id={param.name}
                      type="text"
                      value={config.parameters[param.name] || ""}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          parameters: {
                            ...config.parameters,
                            [param.name]: e.target.value,
                          },
                        })
                      }
                      className="bg-white/5 border-white/10"
                      placeholder={param.description}
                    />
                  )}
                  {param.options && (
                    <select
                      value={config.parameters[param.name] || ""}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          parameters: {
                            ...config.parameters,
                            [param.name]: e.target.value,
                          },
                        })
                      }
                      className="bg-white/5 border-white/10 rounded-md px-4 py-2 text-white w-full"
                    >
                      <option value="">Select...</option>
                      {param.options.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  )}
                  {param.type === "number" && (
                    <Input
                      id={param.name}
                      type="number"
                      value={config.parameters[param.name] || ""}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          parameters: {
                            ...config.parameters,
                            [param.name]: parseFloat(e.target.value),
                          },
                        })
                      }
                      className="bg-white/5 border-white/10"
                    />
                  )}
                  {param.type === "boolean" && (
                    <Switch
                      checked={config.parameters[param.name] || false}
                      onCheckedChange={(checked) =>
                        setConfig({
                          ...config,
                          parameters: {
                            ...config.parameters,
                            [param.name]: checked,
                          },
                        })
                      }
                    />
                  )}
                  <p className="text-sm text-white/60">{param.description}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="advanced" className="space-y-6">
          <Card className="bg-white/5 border-white/10">
            <CardHeader>
              <CardTitle>Advanced Settings</CardTitle>
              <CardDescription>
                Fine-tune execution behavior
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="timeout">Timeout (seconds)</Label>
                <Input
                  id="timeout"
                  type="number"
                  value={config.timeout}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      timeout: parseInt(e.target.value),
                    })
                  }
                  className="bg-white/5 border-white/10"
                />
                <p className="text-sm text-white/60">
                  Maximum time to wait for skill execution
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="retry_count">Retry Count</Label>
                <Input
                  id="retry_count"
                  type="number"
                  value={config.retry_count}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      retry_count: parseInt(e.target.value),
                    })
                  }
                  className="bg-white/5 border-white/10"
                />
                <p className="text-sm text-white/60">
                  Number of times to retry on failure
                </p>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Auto Retry</Label>
                  <p className="text-sm text-white/60">
                    Automatically retry failed executions
                  </p>
                </div>
                <Switch
                  checked={config.auto_retry}
                  onCheckedChange={(checked) =>
                    setConfig({ ...config, auto_retry: checked })
                  }
                />
              </div>

              {skill.dependencies && skill.dependencies.length > 0 && (
                <div className="space-y-2">
                  <Label>Dependencies</Label>
                  <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
                    <p className="text-sm text-yellow-300 mb-2">
                      This skill requires the following dependencies:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {skill.dependencies.map((dep) => (
                        <Badge
                          key={dep}
                          variant="outline"
                          className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                        >
                          {dep}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex gap-2">
        <Button onClick={handleSave} className="flex-1">
          <Save className="w-4 h-4 mr-2" />
          Save Configuration
        </Button>
        <Button onClick={handleReset} variant="outline" className="flex-1">
          <RefreshCw className="w-4 h-4 mr-2" />
          Reset to Defaults
        </Button>
      </div>
    </div>
  );
}

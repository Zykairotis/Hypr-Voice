"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Brain,
  Settings,
  User,
  Volume2,
  Play,
  Pause,
  RotateCcw,
  Save,
  Trash2,
  Plus,
  Edit,
  Check,
  X
} from "lucide-react";
import { toast } from "sonner";

interface AgentConfig {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  autoSynthesize: boolean;
  provider: string;
  voice: string;
  settings: {
    speed: number;
    pitch: number;
    volume: number;
    emotion?: string;
    style?: string;
  };
}

export default function TTSAgentIntegration() {
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentConfig | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingConfig, setEditingConfig] = useState<AgentConfig | null>(null);
  const [testPlaying, setTestPlaying] = useState<string | null>(null);

  useEffect(() => {
    loadAgentConfigs();
  }, []);

  const loadAgentConfigs = () => {
    const saved = localStorage.getItem("tts-agent-configs");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setAgents(parsed);
        if (parsed.length > 0) {
          setSelectedAgent(parsed[0]);
        }
      } catch (error) {
        console.error("Failed to load agent configs:", error);
        initializeDefaultConfigs();
      }
    } else {
      initializeDefaultConfigs();
    }
  };

  const initializeDefaultConfigs = () => {
    const defaultAgents: AgentConfig[] = [
      {
        id: "claude-1",
        name: "Claude Assistant",
        description: "Default Claude agent for general assistance",
        enabled: true,
        autoSynthesize: false,
        provider: "kokoro",
        voice: "af_bella",
        settings: {
          speed: 1.0,
          pitch: 0,
          volume: 1.0,
          emotion: "neutral",
          style: "conversational"
        }
      },
      {
        id: "claude-2",
        name: "Claude Coder",
        description: "Specialized for code explanations and reviews",
        enabled: false,
        autoSynthesize: false,
        provider: "kokoro",
        voice: "am_adam",
        settings: {
          speed: 0.9,
          pitch: -2,
          volume: 1.0,
          emotion: "neutral",
          style: "conversational"
        }
      },
      {
        id: "claude-3",
        name: "Claude Narrator",
        description: "Optimized for storytelling and narration",
        enabled: false,
        autoSynthesize: false,
        provider: "deepgram",
        voice: "luna",
        settings: {
          speed: 0.85,
          pitch: 1,
          volume: 1.0,
          emotion: "calm",
          style: "narration"
        }
      }
    ];
    setAgents(defaultAgents);
    setSelectedAgent(defaultAgents[0]);
    saveAgentConfigs(defaultAgents);
  };

  const saveAgentConfigs = (configs: AgentConfig[]) => {
    setAgents(configs);
    localStorage.setItem("tts-agent-configs", JSON.stringify(configs));
  };

  const handleToggleAgent = (agentId: string) => {
    const updated = agents.map(agent =>
      agent.id === agentId ? { ...agent, enabled: !agent.enabled } : agent
    );
    saveAgentConfigs(updated);
    if (selectedAgent?.id === agentId) {
      setSelectedAgent({ ...selectedAgent, enabled: !selectedAgent.enabled });
    }
    toast.success("Agent configuration updated");
  };

  const handleToggleAutoSynthesize = (agentId: string) => {
    const updated = agents.map(agent =>
      agent.id === agentId ? { ...agent, autoSynthesize: !agent.autoSynthesize } : agent
    );
    saveAgentConfigs(updated);
    if (selectedAgent?.id === agentId) {
      setSelectedAgent({ ...selectedAgent, autoSynthesize: !selectedAgent.autoSynthesize });
    }
  };

  const startEditing = (agent: AgentConfig) => {
    setEditingConfig({ ...agent });
    setIsEditing(true);
  };

  const cancelEditing = () => {
    setEditingConfig(null);
    setIsEditing(false);
  };

  const saveEditing = () => {
    if (!editingConfig) return;

    const updated = agents.map(agent =>
      agent.id === editingConfig.id ? editingConfig : agent
    );
    saveAgentConfigs(updated);
    setSelectedAgent(editingConfig);
    setEditingConfig(null);
    setIsEditing(false);
    toast.success("Agent configuration saved");
  };

  const deleteAgent = (agentId: string) => {
    if (agents.length <= 1) {
      toast.error("Cannot delete the last agent");
      return;
    }

    const updated = agents.filter(agent => agent.id !== agentId);
    saveAgentConfigs(updated);
    if (selectedAgent?.id === agentId) {
      setSelectedAgent(updated[0] || null);
    }
    toast.success("Agent deleted");
  };

  const addNewAgent = () => {
    const newAgent: AgentConfig = {
      id: `agent_${Date.now()}`,
      name: "New Agent",
      description: "Custom agent configuration",
      enabled: true,
      autoSynthesize: false,
      provider: "kokoro",
      voice: "af_bella",
      settings: {
        speed: 1.0,
        pitch: 0,
        volume: 1.0,
        emotion: "neutral",
        style: "conversational"
      }
    };
    setEditingConfig(newAgent);
    setIsEditing(true);
  };

  const testVoice = async (agent: AgentConfig) => {
    if (testPlaying === agent.id) {
      setTestPlaying(null);
      return;
    }

    setTestPlaying(agent.id);
    try {
      const response = await fetch("http://localhost:8934/api/tts/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: `This is a test of the ${agent.name} voice configuration. How does it sound?`,
          provider: agent.provider,
          voice: agent.voice,
          ...agent.settings,
          preview: true
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.audioUrl) {
          const audio = new Audio(data.audioUrl);
          audio.play();
          audio.onended = () => setTestPlaying(null);
        }
      }
      toast.success("Voice test played");
    } catch (error) {
      toast.error("Failed to test voice");
      setTestPlaying(null);
    }
  };

  const exportConfigs = () => {
    const blob = new Blob([JSON.stringify(agents, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "tts-agent-configs.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Configuration exported");
  };

  const importConfigs = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const configs = JSON.parse(e.target?.result as string);
        if (Array.isArray(configs)) {
          saveAgentConfigs(configs);
          toast.success("Configuration imported");
        } else {
          toast.error("Invalid configuration format");
        }
      } catch (error) {
        toast.error("Failed to parse configuration file");
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="w-6 h-6 text-purple-400" />
            Agent Integration
          </h2>
          <p className="text-muted-foreground mt-1">
            Configure TTS settings for individual Claude agents
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportConfigs}>
            <Save className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" onClick={() => document.getElementById("import-configs")?.click()}>
            <RotateCcw className="w-4 h-4 mr-2" />
            Import
          </Button>
          <input
            id="import-configs"
            type="file"
            accept=".json"
            onChange={importConfigs}
            className="hidden"
          />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Agent List */}
        <Card className="glass border-border/50 lg:col-span-1">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Configured Agents</CardTitle>
              <Button size="sm" onClick={addNewAgent}>
                <Plus className="w-4 h-4 mr-1" />
                Add
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedAgent?.id === agent.id
                      ? "bg-primary/20 border-primary"
                      : "hover:bg-muted/50 border-border/50"
                  }`}
                  onClick={() => setSelectedAgent(agent)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <User className="w-4 h-4 text-muted-foreground" />
                        <h3 className="font-semibold truncate">{agent.name}</h3>
                      </div>
                      {agent.description && (
                        <p className="text-xs text-muted-foreground truncate">
                          {agent.description}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        <Badge
                          variant={agent.enabled ? "default" : "outline"}
                          className="text-xs"
                        >
                          {agent.enabled ? "Enabled" : "Disabled"}
                        </Badge>
                        {agent.autoSynthesize && (
                          <Badge variant="outline" className="text-xs">
                            Auto
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Agent Details */}
        <Card className="glass border-border/50 lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  {isEditing ? "Edit Agent" : "Agent Configuration"}
                </CardTitle>
                <CardDescription>
                  {isEditing
                    ? "Modify agent TTS settings"
                    : selectedAgent?.description || "Configure TTS for this agent"}
                </CardDescription>
              </div>
              <div className="flex gap-2">
                {isEditing ? (
                  <>
                    <Button variant="outline" size="sm" onClick={cancelEditing}>
                      <X className="w-4 h-4 mr-1" />
                      Cancel
                    </Button>
                    <Button size="sm" onClick={saveEditing}>
                      <Check className="w-4 h-4 mr-1" />
                      Save
                    </Button>
                  </>
                ) : selectedAgent ? (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => testVoice(selectedAgent)}
                      disabled={testPlaying === selectedAgent.id}
                    >
                      {testPlaying === selectedAgent.id ? (
                        <>
                          <Pause className="w-4 h-4 mr-1" />
                          Stop
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-1" />
                          Test
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => startEditing(selectedAgent)}
                    >
                      <Edit className="w-4 h-4 mr-1" />
                      Edit
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => deleteAgent(selectedAgent.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </>
                ) : null}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {selectedAgent || isEditing ? (
              <div className="space-y-6">
                {/* Basic Settings */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="agent-name">Agent Name</Label>
                    <Input
                      id="agent-name"
                      value={isEditing ? editingConfig?.name || "" : selectedAgent?.name || ""}
                      onChange={(e) =>
                        isEditing && setEditingConfig({
                          ...editingConfig!,
                          name: e.target.value
                        })
                      }
                      disabled={!isEditing}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="agent-description">Description</Label>
                    <Input
                      id="agent-description"
                      value={isEditing ? editingConfig?.description || "" : selectedAgent?.description || ""}
                      onChange={(e) =>
                        isEditing && setEditingConfig({
                          ...editingConfig!,
                          description: e.target.value
                        })
                      }
                      disabled={!isEditing}
                    />
                  </div>
                </div>

                {/* Provider Settings */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>TTS Provider</Label>
                    <Select
                      value={isEditing ? editingConfig?.provider || "" : selectedAgent?.provider || ""}
                      onValueChange={(value) =>
                        isEditing && setEditingConfig({
                          ...editingConfig!,
                          provider: value
                        })
                      }
                      disabled={!isEditing}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="kokoro">Kokoro (Local)</SelectItem>
                        <SelectItem value="deepgram">Deepgram (Cloud)</SelectItem>
                        <SelectItem value="elevenlabs">ElevenLabs (Cloud)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Voice</Label>
                    <Select
                      value={isEditing ? editingConfig?.voice || "" : selectedAgent?.voice || ""}
                      onValueChange={(value) =>
                        isEditing && setEditingConfig({
                          ...editingConfig!,
                          voice: value
                        })
                      }
                      disabled={!isEditing}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="af_bella">Bella (Female)</SelectItem>
                        <SelectItem value="af_sky">Sky (Female)</SelectItem>
                        <SelectItem value="am_adam">Adam (Male)</SelectItem>
                        <SelectItem value="am_michael">Michael (Male)</SelectItem>
                        <SelectItem value="bm_george">George (British)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Audio Parameters */}
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label>Speed: {isEditing ? editingConfig?.settings.speed.toFixed(1) : selectedAgent?.settings.speed.toFixed(1)}x</Label>
                    <input
                      type="range"
                      min="0.5"
                      max="2.0"
                      step="0.1"
                      value={isEditing ? editingConfig?.settings.speed || 1 : selectedAgent?.settings.speed || 1}
                      onChange={(e) =>
                        isEditing && setEditingConfig({
                          ...editingConfig!,
                          settings: {
                            ...editingConfig!.settings,
                            speed: parseFloat(e.target.value)
                          }
                        })
                      }
                      disabled={!isEditing}
                      className="w-full"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Pitch: {isEditing ? editingConfig?.settings.pitch : selectedAgent?.settings.pitch}</Label>
                    <input
                      type="range"
                      min="-12"
                      max="12"
                      step="1"
                      value={isEditing ? editingConfig?.settings.pitch || 0 : selectedAgent?.settings.pitch || 0}
                      onChange={(e) =>
                        isEditing && setEditingConfig({
                          ...editingConfig!,
                          settings: {
                            ...editingConfig!.settings,
                            pitch: parseInt(e.target.value)
                          }
                        })
                      }
                      disabled={!isEditing}
                      className="w-full"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Volume: {Math.round((isEditing ? editingConfig?.settings.volume || 1 : selectedAgent?.settings.volume || 1) * 100)}%</Label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={isEditing ? editingConfig?.settings.volume || 1 : selectedAgent?.settings.volume || 1}
                      onChange={(e) =>
                        isEditing && setEditingConfig({
                          ...editingConfig!,
                          settings: {
                            ...editingConfig!.settings,
                            volume: parseFloat(e.target.value)
                          }
                        })
                      }
                      disabled={!isEditing}
                      className="w-full"
                    />
                  </div>
                </div>

                {/* Toggles */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                    <div>
                      <Label htmlFor="enable-agent">Enable TTS for Agent</Label>
                      <p className="text-sm text-muted-foreground">
                        Allow this agent to use TTS
                      </p>
                    </div>
                    <Switch
                      id="enable-agent"
                      checked={isEditing ? editingConfig?.enabled || false : selectedAgent?.enabled || false}
                      onCheckedChange={() =>
                        isEditing && setEditingConfig({
                          ...editingConfig!,
                          enabled: !editingConfig?.enabled
                        })
                      }
                      disabled={!isEditing}
                    />
                  </div>

                  <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                    <div>
                      <Label htmlFor="auto-synthesize">Auto-Synthesize</Label>
                      <p className="text-sm text-muted-foreground">
                        Automatically synthesize agent responses
                      </p>
                    </div>
                    <Switch
                      id="auto-synthesize"
                      checked={isEditing ? editingConfig?.autoSynthesize || false : selectedAgent?.autoSynthesize || false}
                      onCheckedChange={() =>
                        isEditing && setEditingConfig({
                          ...editingConfig!,
                          autoSynthesize: !editingConfig?.autoSynthesize
                        })
                      }
                      disabled={!isEditing}
                    />
                  </div>
                </div>

                {/* Status */}
                {selectedAgent && !isEditing && (
                  <div className="p-4 rounded-lg bg-muted/50 space-y-3">
                    <h4 className="font-semibold">Current Status</h4>
                    <div className="grid gap-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Enabled:</span>
                        <Badge variant={selectedAgent.enabled ? "default" : "outline"}>
                          {selectedAgent.enabled ? "Yes" : "No"}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Auto-Synthesize:</span>
                        <Badge variant={selectedAgent.autoSynthesize ? "default" : "outline"}>
                          {selectedAgent.autoSynthesize ? "Yes" : "No"}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Provider:</span>
                        <span>{selectedAgent.provider}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Voice:</span>
                        <span>{selectedAgent.voice}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Select an agent to configure
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

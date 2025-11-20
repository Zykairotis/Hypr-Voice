"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Monitor, 
  Terminal, 
  Clipboard, 
  Code, 
  GitBranch, 
  Folder,
  Zap,
  Eye,
  Hash,
  RefreshCw
} from "lucide-react";
import { motion } from "framer-motion";

interface ContextData {
  workspace: {
    application: string;
    category: string;
    window_title: string;
    active_file: string | null;
    workspace_id: number | null;
    workspace_name: string | null;
    monitor: number | null;
    geometry: {
      x: number | null;
      y: number | null;
      width: number | null;
      height: number | null;
    };
    states: {
      floating: boolean;
      fullscreen: boolean;
      pinned: boolean;
      xwayland: boolean;
    };
    pid: number | null;
    address: string | null;
  };
  recent_activity: {
    commands: string[];
    clipboard: string[];
    keywords: string[];
  };
  project_context: {
    git_branch: string | null;
    git_status: string | null;
    project_root: string | null;
  };
  hooks: {
    triggered: string[];
    context_additions: Record<string, any>;
  };
}

export default function ContextPanel() {
  const [context, setContext] = useState<ContextData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [backendAvailable, setBackendAvailable] = useState(true);
  const [errorCount, setErrorCount] = useState(0);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;

    const connect = () => {
      try {
        ws = new WebSocket("ws://localhost:8934/ws/context");

        ws.onopen = () => {
          console.log("✅ WebSocket connected - Real-time context updates active");
          setWsConnected(true);
          setBackendAvailable(true);
          setErrorCount(0);
          reconnectAttempts = 0;
          setLoading(false);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            // Check for error messages
            if (data.error) {
              setBackendAvailable(false);
              setErrorCount(prev => {
                const newCount = prev + 1;
                if (newCount === 1 || newCount % 10 === 0) {
                  console.warn(`Backend error: ${data.error}`);
                }
                return newCount;
              });
            } else {
              setContext(data);
              setLastUpdate(new Date());
              setBackendAvailable(true);
              setErrorCount(0);
            }
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          setWsConnected(false);
        };

        ws.onclose = () => {
          console.log("WebSocket disconnected");
          setWsConnected(false);
          setBackendAvailable(false);
          
          // Attempt reconnection with exponential backoff
          if (reconnectAttempts < maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
            reconnectAttempts++;
            
            if (reconnectAttempts === 1 || reconnectAttempts % 5 === 0) {
              console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`);
            }
            
            reconnectTimeout = setTimeout(connect, delay);
          } else {
            console.error("Max reconnection attempts reached. Please restart the backend.");
            setErrorCount(prev => {
              if (prev === 0) {
                console.warn("Backend not available on port 8934. Run './start-ui.sh' to start the backend.");
              }
              return prev + 1;
            });
          }
        };

      } catch (error) {
        console.error("Failed to create WebSocket:", error);
        setLoading(false);
        setBackendAvailable(false);
      }
    };

    connect();

    return () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        ws.close();
      }
    };
  }, [])

  if (loading) {
    return (
      <Card className="p-6 glass border-border/50">
        <div className="flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-primary" />
          <span className="ml-2 text-sm text-muted-foreground">Loading context...</span>
        </div>
      </Card>
    );
  }

  if (!context) {
    return (
      <Card className="p-6 glass border-border/50">
        {!backendAvailable ? (
          <div className="text-center space-y-3">
            <div className="flex items-center justify-center gap-2">
              <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              <p className="text-sm font-medium text-muted-foreground">Backend Not Running</p>
            </div>
            <div className="space-y-2 text-xs text-muted-foreground">
              <p>The backend bridge on port 8934 is not available.</p>
              <p className="font-mono bg-muted/30 rounded px-2 py-1">
                cd web-ui && ./start-ui.sh
              </p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground text-center">No context available</p>
        )}
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Eye className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-semibold">Live Context</h3>
          {wsConnected && backendAvailable ? (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>WebSocket Live</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-amber-400">
              <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
              <span>{wsConnected ? "Waiting..." : "Disconnected"}</span>
            </div>
          )}
        </div>
        <Badge variant="outline" className="text-xs">
          {backendAvailable ? `Updated ${lastUpdate.toLocaleTimeString()}` : "Waiting for backend"}
        </Badge>
      </div>

      <Tabs defaultValue="workspace" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="workspace">
            <Monitor className="w-4 h-4 mr-2" />
            Workspace
          </TabsTrigger>
          <TabsTrigger value="activity">
            <Terminal className="w-4 h-4 mr-2" />
            Activity
          </TabsTrigger>
          <TabsTrigger value="project">
            <GitBranch className="w-4 h-4 mr-2" />
            Project
          </TabsTrigger>
          <TabsTrigger value="hooks">
            <Zap className="w-4 h-4 mr-2" />
            Hooks
          </TabsTrigger>
        </TabsList>

        {/* Workspace Tab */}
        <TabsContent value="workspace" className="space-y-3">
          {/* Basic Info */}
          <Card className="p-4 glass border-border/50">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Application</span>
                <Badge className="font-mono">{context.workspace.application || "None"}</Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Category</span>
                <CategoryBadge category={context.workspace.category} />
              </div>

              {context.workspace.window_title && (
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground">Window Title</span>
                  <div className="text-xs font-mono bg-muted/30 rounded p-2 truncate">
                    {context.workspace.window_title}
                  </div>
                </div>
              )}

              {context.workspace.active_file && (
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground flex items-center gap-1">
                    <Code className="w-3 h-3" />
                    Active File
                  </span>
                  <div className="text-xs font-mono bg-muted/30 rounded p-2">
                    {context.workspace.active_file}
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Window Details */}
          <Card className="p-4 glass border-border/50">
            <div className="flex items-center gap-2 mb-3">
              <Monitor className="w-4 h-4 text-primary" />
              <h4 className="text-sm font-semibold">Window Details</h4>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Workspace</span>
                <Badge variant="outline" className="font-mono text-xs">
                  {context.workspace.workspace_name || "N/A"}
                </Badge>
              </div>
              
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Monitor</span>
                <Badge variant="outline" className="font-mono text-xs">
                  {context.workspace.monitor !== null ? `Monitor ${context.workspace.monitor}` : "N/A"}
                </Badge>
              </div>

              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Process ID</span>
                <Badge variant="outline" className="font-mono text-xs">
                  {context.workspace.pid || "N/A"}
                </Badge>
              </div>

              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Backend</span>
                <Badge variant="outline" className="font-mono text-xs">
                  {context.workspace.states.xwayland ? "XWayland" : "Wayland"}
                </Badge>
              </div>
            </div>
          </Card>

          {/* Window State */}
          <Card className="p-4 glass border-border/50">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-primary" />
              <h4 className="text-sm font-semibold">Window State</h4>
            </div>
            <div className="flex flex-wrap gap-2">
              {context.workspace.states.fullscreen && (
                <Badge className="bg-green-500/20 text-green-400 border-0">
                  ⛶ Fullscreen
                </Badge>
              )}
              {context.workspace.states.floating && (
                <Badge className="bg-blue-500/20 text-blue-400 border-0">
                  ⬚ Floating
                </Badge>
              )}
              {context.workspace.states.pinned && (
                <Badge className="bg-amber-500/20 text-amber-400 border-0">
                  📌 Pinned
                </Badge>
              )}
              {!context.workspace.states.fullscreen && 
               !context.workspace.states.floating && 
               !context.workspace.states.pinned && (
                <Badge className="bg-gray-500/20 text-gray-400 border-0">
                  ▭ Tiled
                </Badge>
              )}
            </div>
          </Card>

          {/* Geometry */}
          {context.workspace.geometry.width && context.workspace.geometry.height && (
            <Card className="p-4 glass border-border/50">
              <div className="flex items-center gap-2 mb-3">
                <Monitor className="w-4 h-4 text-primary" />
                <h4 className="text-sm font-semibold">Geometry</h4>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="space-y-1">
                  <span className="text-muted-foreground">Position</span>
                  <div className="font-mono bg-muted/30 rounded px-2 py-1">
                    X: {context.workspace.geometry.x}, Y: {context.workspace.geometry.y}
                  </div>
                </div>
                <div className="space-y-1">
                  <span className="text-muted-foreground">Size</span>
                  <div className="font-mono bg-muted/30 rounded px-2 py-1">
                    {context.workspace.geometry.width} × {context.workspace.geometry.height}
                  </div>
                </div>
              </div>
            </Card>
          )}
        </TabsContent>

        {/* Activity Tab */}
        <TabsContent value="activity" className="space-y-3">
          {/* Shell Commands */}
          <Card className="p-4 glass border-border/50">
            <div className="flex items-center gap-2 mb-3">
              <Terminal className="w-4 h-4 text-primary" />
              <h4 className="text-sm font-semibold">Recent Commands</h4>
              <Badge variant="secondary" className="ml-auto text-xs">
                {context.recent_activity.commands.length}
              </Badge>
            </div>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {context.recent_activity.commands.slice(0, 10).map((cmd, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="text-xs font-mono bg-muted/20 rounded px-2 py-1 truncate"
                >
                  {cmd}
                </motion.div>
              ))}
            </div>
          </Card>

          {/* Clipboard */}
          <Card className="p-4 glass border-border/50">
            <div className="flex items-center gap-2 mb-3">
              <Clipboard className="w-4 h-4 text-primary" />
              <h4 className="text-sm font-semibold">Clipboard History</h4>
              <Badge variant="secondary" className="ml-auto text-xs">
                {context.recent_activity.clipboard.length}
              </Badge>
            </div>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {context.recent_activity.clipboard.slice(0, 5).map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="text-xs bg-muted/20 rounded px-2 py-1.5 truncate"
                >
                  {item.length > 60 ? item.substring(0, 60) + "..." : item}
                </motion.div>
              ))}
            </div>
          </Card>

          {/* Extracted Keywords */}
          <Card className="p-4 glass border-border/50">
            <div className="flex items-center gap-2 mb-3">
              <Hash className="w-4 h-4 text-primary" />
              <h4 className="text-sm font-semibold">Extracted Vocabulary</h4>
              <Badge variant="secondary" className="ml-auto text-xs">
                {context.recent_activity.keywords.length}
              </Badge>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {context.recent_activity.keywords.map((keyword, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.02 }}
                >
                  <Badge variant="outline" className="text-xs font-mono">
                    {keyword}
                  </Badge>
                </motion.div>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* Project Tab */}
        <TabsContent value="project" className="space-y-3">
          <Card className="p-4 glass border-border/50">
            <div className="space-y-3">
              {context.project_context.project_root && (
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground flex items-center gap-1">
                    <Folder className="w-3 h-3" />
                    Project Root
                  </span>
                  <div className="text-xs font-mono bg-muted/30 rounded p-2 truncate">
                    {context.project_context.project_root}
                  </div>
                </div>
              )}

              {context.project_context.git_branch && (
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground flex items-center gap-1">
                    <GitBranch className="w-3 h-3" />
                    Git Branch
                  </span>
                  <Badge className="font-mono bg-primary/20">
                    {context.project_context.git_branch}
                  </Badge>
                </div>
              )}

              {context.project_context.git_status && (
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground">Git Status</span>
                  <pre className="text-xs font-mono bg-muted/30 rounded p-2 overflow-x-auto">
                    {context.project_context.git_status}
                  </pre>
                </div>
              )}

              {!context.project_context.project_root && (
                <p className="text-xs text-muted-foreground text-center py-4">
                  No project context available
                </p>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Hooks Tab */}
        <TabsContent value="hooks" className="space-y-3">
          <Card className="p-4 glass border-border/50">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                <h4 className="text-sm font-semibold">Triggered Hooks</h4>
                <Badge variant="secondary" className="ml-auto text-xs">
                  {context.hooks.triggered.length}
                </Badge>
              </div>

              {context.hooks.triggered.length > 0 ? (
                <div className="space-y-1.5">
                  {context.hooks.triggered.map((hook, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex items-center gap-2 text-xs bg-amber-500/10 rounded px-2 py-1.5 border border-amber-500/20"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                      <span className="font-mono">{hook}</span>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground text-center py-2">
                  No hooks triggered yet
                </p>
              )}

              {Object.keys(context.hooks.context_additions).length > 0 && (
                <div className="mt-4 space-y-2">
                  <span className="text-xs text-muted-foreground">Context Additions</span>
                  <pre className="text-xs font-mono bg-muted/30 rounded p-2 overflow-x-auto max-h-40">
                    {JSON.stringify(context.hooks.context_additions, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function CategoryBadge({ category }: { category: string }) {
  const categoryStyles: Record<string, { bg: string; text: string }> = {
    development: { bg: "bg-blue-500/20", text: "text-blue-400" },
    communication: { bg: "bg-green-500/20", text: "text-green-400" },
    productivity: { bg: "bg-purple-500/20", text: "text-purple-400" },
    media: { bg: "bg-pink-500/20", text: "text-pink-400" },
    gaming: { bg: "bg-red-500/20", text: "text-red-400" },
    system: { bg: "bg-yellow-500/20", text: "text-yellow-400" },
    other: { bg: "bg-gray-500/20", text: "text-gray-400" },
  };

  const style = categoryStyles[category] || categoryStyles.other;

  return (
    <Badge className={`${style.bg} ${style.text} border-0 font-medium`}>
      {category}
    </Badge>
  );
}


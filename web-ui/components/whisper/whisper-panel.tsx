"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Settings, Mic, BookOpen, Activity, Eye } from "lucide-react";
import AudioConfig from "./audio-config";
import ModelConfigEnhanced from "./model-config-enhanced";
import VocabularyConfig from "./vocabulary-config";
import ServerStatus from "./server-status";
import ContextPanel from "./context-panel";

interface WhisperPanelProps {
  onStatusChange: (status: "online" | "offline" | "error") => void;
}

export default function WhisperPanel({ onStatusChange }: WhisperPanelProps) {
  const [isLoading, setIsLoading] = useState(false);

  // Check server status on mount
  useEffect(() => {
    checkServerStatus();
    const interval = setInterval(checkServerStatus, 5000); // Check every 5s
    return () => clearInterval(interval);
  }, []);

  const checkServerStatus = async () => {
    try {
      const response = await fetch("http://localhost:8934/api/whisper/status", {
        method: "GET",
      });
      
      if (response.ok) {
        const data = await response.json();
        onStatusChange(data.status || "offline");
      } else {
        onStatusChange("error");
      }
    } catch (error) {
      onStatusChange("offline");
    }
  };

  return (
    <div className="space-y-6">
      {/* Server Status Card */}
      <Card className="glass glass-hover border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
                <Activity className="w-5 h-5 text-primary" />
              </div>
              <div>
                <CardTitle>Server Status</CardTitle>
                <CardDescription>WhisperLive hybrid server monitoring</CardDescription>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <ServerStatus />
        </CardContent>
      </Card>

      {/* Configuration Tabs */}
      <Card className="glass glass-hover border-border/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
              <Settings className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle>Configuration</CardTitle>
              <CardDescription>Manage Hypr-Whisper settings</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="context" className="w-full">
            <TabsList className="grid w-full grid-cols-4 glass p-1">
              <TabsTrigger value="context">
                <Eye className="w-4 h-4 mr-2" />
                Context
              </TabsTrigger>
              <TabsTrigger value="audio">
                <Mic className="w-4 h-4 mr-2" />
                Audio
              </TabsTrigger>
              <TabsTrigger value="model">
                <Settings className="w-4 h-4 mr-2" />
                Model
              </TabsTrigger>
              <TabsTrigger value="vocabulary">
                <BookOpen className="w-4 h-4 mr-2" />
                Vocabulary
              </TabsTrigger>
            </TabsList>

            <TabsContent value="context" className="mt-6">
              <ContextPanel />
            </TabsContent>

            <TabsContent value="audio" className="mt-6">
              <AudioConfig />
            </TabsContent>

            <TabsContent value="model" className="mt-6">
              <ModelConfigEnhanced />
            </TabsContent>

            <TabsContent value="vocabulary" className="mt-6">
              <VocabularyConfig />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}


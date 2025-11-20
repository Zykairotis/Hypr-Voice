"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  PlayCircle,
  Square,
  Clock,
  CheckCircle,
  XCircle,
  Zap,
  Terminal,
  FileCode,
} from "lucide-react";
import type { Skill, SkillExecution } from "@/types/skills";

interface SkillExecutionMonitorProps {
  selectedSkill?: Skill | null;
}

const MOCK_EXECUTIONS: SkillExecution[] = [
  {
    id: "1",
    skill_id: "file_operations",
    agent_id: "agent-1",
    status: "completed",
    started_at: new Date(Date.now() - 30000).toISOString(),
    completed_at: new Date(Date.now() - 25000).toISOString(),
    input: { operation: "read", path: "test.txt" },
    output: { content: "Hello World" },
    duration: 120,
  },
  {
    id: "2",
    skill_id: "bash_execution",
    agent_id: "agent-1",
    status: "completed",
    started_at: new Date(Date.now() - 60000).toISOString(),
    completed_at: new Date(Date.now() - 55000).toISOString(),
    input: { command: "ls -la" },
    output: { stdout: "total 8\ndrwxr-xr-x 2 user user 4096\n", stderr: "" },
    duration: 450,
  },
  {
    id: "3",
    skill_id: "voice_synthesis",
    agent_id: "agent-1",
    status: "failed",
    started_at: new Date(Date.now() - 90000).toISOString(),
    completed_at: new Date(Date.now() - 89500).toISOString(),
    input: { text: "Hello", voice: "invalid_voice" },
    error: "Invalid voice parameter",
    duration: 50,
  },
];

export default function SkillExecutionMonitor({
  selectedSkill,
}: SkillExecutionMonitorProps) {
  const [executions, setExecutions] = useState<SkillExecution[]>(MOCK_EXECUTIONS);
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentOutput, setCurrentOutput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [currentOutput, executions]);

  const handleExecute = async () => {
    if (!selectedSkill) return;

    setIsExecuting(true);
    const executionId = `exec-${Date.now()}`;

    const newExecution: SkillExecution = {
      id: executionId,
      skill_id: selectedSkill.id,
      agent_id: "current-agent",
      status: "running",
      started_at: new Date().toISOString(),
      input: { test: "data" },
    };

    setExecutions((prev) => [newExecution, ...prev]);
    setCurrentOutput("");

    setTimeout(() => {
      const completedExecution: SkillExecution = {
        ...newExecution,
        status: "completed",
        completed_at: new Date().toISOString(),
        output: { result: "Skill executed successfully" },
        duration: Math.floor(Math.random() * 1000),
      };

      setExecutions((prev) =>
        prev.map((ex) =>
          ex.id === executionId ? completedExecution : ex
        )
      );
      setIsExecuting(false);
      setCurrentOutput("Skill executed successfully\n");
    }, 2000);
  };

  const handleStop = () => {
    setIsExecuting(false);
    setCurrentOutput("Execution stopped\n");
  };

  const getStatusIcon = (status: SkillExecution["status"]) => {
    switch (status) {
      case "running":
        return <Clock className="w-4 h-4 text-blue-400 animate-spin" />;
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-400" />;
    }
  };

  const getStatusColor = (status: SkillExecution["status"]) => {
    switch (status) {
      case "running":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "completed":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "failed":
        return "bg-red-500/20 text-red-400 border-red-500/30";
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
          Execution Monitor
        </h2>
        <p className="text-white/60 mt-1">
          Real-time skill execution tracking and debugging
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/5 border-white/10">
          <CardHeader>
            <CardTitle>Control Panel</CardTitle>
            <CardDescription>
              Execute and monitor skill operations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedSkill ? (
              <>
                <div>
                  <p className="text-sm text-white/60">Current Skill</p>
                  <p className="text-lg font-semibold">{selectedSkill.name}</p>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={handleExecute}
                    disabled={isExecuting}
                    className="flex-1"
                  >
                    <PlayCircle className="w-4 h-4 mr-2" />
                    Execute
                  </Button>
                  <Button
                    onClick={handleStop}
                    variant="outline"
                    disabled={!isExecuting}
                    className="flex-1"
                  >
                    <Square className="w-4 h-4 mr-2" />
                    Stop
                  </Button>
                </div>

                <div className="bg-black/40 rounded-lg p-4 font-mono text-sm h-64 overflow-y-auto">
                  <ScrollArea className="h-full" ref={scrollRef}>
                    <div className="space-y-1">
                      <div className="text-green-400">$ Executing: {selectedSkill.name}</div>
                      {currentOutput && (
                        <div className="text-white/80">{currentOutput}</div>
                      )}
                      {isExecuting && (
                        <div className="flex items-center gap-2 text-blue-400">
                          <div className="animate-pulse">●</div>
                          <div>Processing...</div>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </div>
              </>
            ) : (
              <p className="text-white/60 text-center py-8">
                Select a skill to execute
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10">
          <CardHeader>
            <CardTitle>Execution History</CardTitle>
            <CardDescription>Recent skill executions</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="space-y-3">
                <AnimatePresence>
                  {executions.map((execution) => (
                    <motion.div
                      key={execution.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className="bg-white/5 rounded-lg p-3 border border-white/10"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Zap className="w-4 h-4 text-blue-400" />
                          <span className="font-medium">
                            {execution.skill_id}
                          </span>
                        </div>
                        <Badge
                          variant="outline"
                          className={getStatusColor(execution.status)}
                        >
                          {getStatusIcon(execution.status)}
                          <span className="ml-1">{execution.status}</span>
                        </Badge>
                      </div>
                      <div className="text-xs text-white/60 space-y-1">
                        <div>
                          Started:{" "}
                          {new Date(execution.started_at).toLocaleTimeString()}
                        </div>
                        {execution.duration && (
                          <div>Duration: {execution.duration}ms</div>
                        )}
                        {execution.error && (
                          <div className="text-red-400">{execution.error}</div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-white/5 border-white/10">
        <CardHeader>
          <CardTitle>Execution Details</CardTitle>
          <CardDescription>Detailed execution information</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-64">
            <div className="space-y-3">
              {executions.map((execution) => (
                <div
                  key={execution.id}
                  className="bg-black/40 rounded-lg p-4 font-mono text-sm"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Terminal className="w-4 h-4 text-blue-400" />
                    <span className="font-semibold">Execution: {execution.id}</span>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <span className="text-white/60">Input:</span>
                      <pre className="mt-1 text-green-400">
                        {JSON.stringify(execution.input, null, 2)}
                      </pre>
                    </div>
                    {execution.output && (
                      <div>
                        <span className="text-white/60">Output:</span>
                        <pre className="mt-1 text-blue-400">
                          {JSON.stringify(execution.output, null, 2)}
                        </pre>
                      </div>
                    )}
                    {execution.error && (
                      <div>
                        <span className="text-white/60">Error:</span>
                        <pre className="mt-1 text-red-400">{execution.error}</pre>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

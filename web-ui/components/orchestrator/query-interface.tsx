"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Send, Loader2, Sparkles, Keyboard, Brain, Clock } from "lucide-react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { endpoints } from "@/lib/endpoints";
import { streamingFetch, OrchestratorEvent } from "@/lib/orchestrator-websocket";

interface QueryInterfaceProps {
  disabled?: boolean;
}

interface QueryResult {
  type: string;
  content?: string;
  agent?: string;
  error?: string;
  reasoning?: string;
  confidence?: number;
  ttft_ms?: number;
}

export default function QueryInterface({ disabled }: QueryInterfaceProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [results, setResults] = useState<QueryResult[]>([]);
  const [currentRouting, setCurrentRouting] = useState<{ agent: string; reasoning: string; confidence: number } | null>(null);
  const [ttft, setTtft] = useState<number | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (resultsRef.current) {
      resultsRef.current.scrollTop = resultsRef.current.scrollHeight;
    }
  }, [results, streamingContent]);

  const sendQueryStreaming = useCallback(async () => {
    if (!query.trim() || disabled || loading) return;

    setLoading(true);
    setIsStreaming(true);
    setResults([]);
    setStreamingContent("");
    setCurrentRouting(null);
    setTtft(null);

    const queryText = query.trim();
    setQuery("");

    let fullContent = "";
    let agentType = "";

    try {
      await streamingFetch(
        endpoints.direct.voice.processStreaming,
        { text: queryText, auto_play: false },
        (token) => {
          fullContent += token;
          setStreamingContent(fullContent);
        },
        (event: OrchestratorEvent) => {
          switch (event.type) {
            case "routing":
              agentType = event.data?.agent || event.agent || "";
              setCurrentRouting({
                agent: agentType,
                reasoning: event.data?.reasoning || event.reasoning || "",
                confidence: event.data?.confidence ?? event.confidence ?? 0,
              });
              break;
            case "first_token":
              setTtft(event.data?.ttft_ms || event.ttft_ms);
              break;
          }
        }
      );

      setResults([
        {
          type: "result",
          content: fullContent,
          agent: agentType,
          reasoning: currentRouting?.reasoning,
          confidence: currentRouting?.confidence,
          ttft_ms: ttft || undefined,
        },
      ]);
    } catch (error) {
      toast.error("Error connecting to orchestrator");
      setResults([{ type: "error", error: "Connection failed" }]);
    } finally {
      setLoading(false);
      setIsStreaming(false);
      setStreamingContent("");
      setCurrentRouting(null);
    }
  }, [query, disabled, loading, currentRouting?.reasoning, currentRouting?.confidence, ttft]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      sendQueryStreaming();
    }
  };

  return (
    <div className="space-y-4">
      {/* Input Area */}
      <div className="relative">
        <Textarea
          placeholder={disabled ? "Orchestrator offline..." : "Ask the orchestrator anything..."}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || loading}
          className="min-h-[80px] sm:min-h-[100px] pr-20 sm:pr-24 glass border-border/50 focus:border-violet-500/50 resize-none text-sm"
        />
        <div className="absolute bottom-2 sm:bottom-3 right-2 sm:right-3 flex items-center gap-1 sm:gap-2">
          <Badge variant="outline" className="text-xs bg-black/20 hidden sm:flex">
            <Keyboard className="w-3 h-3 mr-1" />
            Ctrl+Enter
          </Badge>
          <Button
            size="sm"
            onClick={sendQueryStreaming}
            disabled={disabled || loading || !query.trim()}
            className="bg-violet-600 hover:bg-violet-500 h-8 px-3"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Streaming indicator with routing info */}
      <AnimatePresence>
        {isStreaming && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex flex-wrap items-center gap-2"
          >
            {currentRouting && (
              <Badge variant="outline" className="bg-violet-500/10 text-violet-400 border-violet-500/30 text-xs">
                <Brain className="w-3 h-3 mr-1" />
                {currentRouting.agent}
              </Badge>
            )}
            {ttft && (
              <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30 text-xs">
                <Clock className="w-3 h-3 mr-1" />
                {ttft}ms TTFT
              </Badge>
            )}
            {currentRouting?.reasoning && (
              <span className="text-xs text-white/40 truncate max-w-xs">
                {currentRouting.reasoning}
              </span>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Streaming content */}
      <AnimatePresence>
        {isStreaming && streamingContent && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="rounded-lg bg-black/30 border border-violet-500/30 p-3 sm:p-4">
              <p className="text-xs sm:text-sm text-white/90 whitespace-pre-wrap">
                {streamingContent}
                <span className="inline-block w-2 h-4 bg-violet-400 animate-pulse ml-0.5" />
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Area */}
      <AnimatePresence>
        {results.length > 0 && !isStreaming && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div
              ref={resultsRef}
              className="max-h-[300px] sm:max-h-[400px] overflow-y-auto rounded-lg bg-black/30 border border-border/50 p-3 sm:p-4 space-y-3"
            >
              {results.map((result, index) => (
                <ResultItem key={index} result={result} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ResultItem({ result }: { result: QueryResult }) {
  const getTypeStyles = () => {
    switch (result.type) {
      case "text":
        return "border-l-violet-500 bg-violet-500/5";
      case "tool_use":
        return "border-l-blue-500 bg-blue-500/5";
      case "result":
        return "border-l-green-500 bg-green-500/5";
      case "error":
        return "border-l-red-500 bg-red-500/5";
      case "info":
        return "border-l-amber-500 bg-amber-500/5";
      default:
        return "border-l-gray-500 bg-gray-500/5";
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={`pl-3 sm:pl-4 py-2 border-l-2 rounded-r-lg ${getTypeStyles()}`}
    >
      <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 mb-1">
        <Badge variant="outline" className="text-xs">
          {result.type}
        </Badge>
        {result.agent && (
          <Badge variant="secondary" className="text-xs bg-violet-500/20 text-violet-300">
            {result.agent}
          </Badge>
        )}
        {result.confidence !== undefined && (
          <Badge variant="outline" className="text-xs bg-yellow-500/10 text-yellow-400 border-yellow-500/30">
            {Math.round(result.confidence * 100)}%
          </Badge>
        )}
        {result.ttft_ms && (
          <Badge variant="outline" className="text-xs bg-blue-500/10 text-blue-400 border-blue-500/30">
            <Clock className="w-2.5 h-2.5 mr-0.5" />
            {result.ttft_ms}ms
          </Badge>
        )}
      </div>
      {result.reasoning && (
        <p className="text-xs text-white/40 mb-1 italic">{result.reasoning}</p>
      )}
      <p className="text-xs sm:text-sm text-white/80 whitespace-pre-wrap">
        {result.content || result.error || JSON.stringify(result)}
      </p>
    </motion.div>
  );
}

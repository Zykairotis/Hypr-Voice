"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Send, Loader2, Sparkles, Keyboard } from "lucide-react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";

interface QueryInterfaceProps {
  disabled?: boolean;
}

interface QueryResult {
  type: string;
  content?: string;
  agent?: string;
  error?: string;
}

export default function QueryInterface({ disabled }: QueryInterfaceProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<QueryResult[]>([]);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (resultsRef.current) {
      resultsRef.current.scrollTop = resultsRef.current.scrollHeight;
    }
  }, [results]);

  const sendQuery = async () => {
    if (!query.trim() || disabled || loading) return;

    setLoading(true);
    setResults([]);

    try {
      const response = await fetch("http://localhost:8934/api/orchestrator/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim() }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.results) {
          setResults(data.results);
        } else if (data.error) {
          toast.error(data.error);
          setResults([{ type: "error", error: data.error }]);
        }
      } else {
        toast.error("Failed to send query");
      }
    } catch (error) {
      toast.error("Error connecting to orchestrator");
      setResults([{ type: "error", error: "Connection failed" }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      sendQuery();
    }
  };

  return (
    <div className="space-y-4">
      {/* Input Area */}
      <div className="relative">
        <Textarea
          placeholder={disabled ? "Orchestrator offline..." : "Ask the orchestrator anything... (Ctrl+Enter to send)"}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || loading}
          className="min-h-[100px] pr-24 glass border-border/50 focus:border-violet-500/50 resize-none"
        />
        <div className="absolute bottom-3 right-3 flex items-center gap-2">
          <Badge variant="outline" className="text-xs bg-black/20">
            <Keyboard className="w-3 h-3 mr-1" />
            Ctrl+Enter
          </Badge>
          <Button
            size="sm"
            onClick={sendQuery}
            disabled={disabled || loading || !query.trim()}
            className="bg-violet-600 hover:bg-violet-500"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>

      {/* F10 Hint */}
      <div className="flex items-center gap-2 text-xs text-white/40">
        <Sparkles className="w-3 h-3" />
        <span>Pro tip: Press and hold F10 for voice input</span>
      </div>

      {/* Results Area */}
      <AnimatePresence>
        {results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div
              ref={resultsRef}
              className="max-h-[400px] overflow-y-auto rounded-lg bg-black/30 border border-border/50 p-4 space-y-3"
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
      className={`pl-4 py-2 border-l-2 rounded-r-lg ${getTypeStyles()}`}
    >
      <div className="flex items-center gap-2 mb-1">
        <Badge variant="outline" className="text-xs">
          {result.type}
        </Badge>
        {result.agent && (
          <Badge variant="secondary" className="text-xs bg-violet-500/20 text-violet-300">
            {result.agent}
          </Badge>
        )}
      </div>
      <p className="text-sm text-white/80 whitespace-pre-wrap">
        {result.content || result.error || JSON.stringify(result)}
      </p>
    </motion.div>
  );
}

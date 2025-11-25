"""
Context Manager

Manages context windows to keep them clean and efficient.
Implements context isolation and compression strategies.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """A single entry in the context window."""
    content: str
    entry_type: str  # "query", "result", "tool_use", "system"
    timestamp: str
    token_estimate: int
    agent_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "type": self.entry_type,
            "timestamp": self.timestamp,
            "tokens": self.token_estimate,
            "agent_id": self.agent_id,
            "metadata": self.metadata,
        }


@dataclass 
class ContextWindow:
    """Represents a context window for an agent."""
    agent_id: str
    max_tokens: int = 100000
    entries: list[ContextEntry] = field(default_factory=list)
    total_tokens: int = 0
    compression_threshold: float = 0.8  # Compress when 80% full
    
    def add(self, entry: ContextEntry):
        """Add an entry to the context window."""
        self.entries.append(entry)
        self.total_tokens += entry.token_estimate
    
    def should_compress(self) -> bool:
        """Check if context should be compressed."""
        return self.total_tokens >= (self.max_tokens * self.compression_threshold)
    
    def get_usage_ratio(self) -> float:
        """Get current usage as a ratio."""
        return self.total_tokens / self.max_tokens if self.max_tokens > 0 else 0


class ContextManager:
    """
    Manages context windows for orchestrator and subagents.
    
    Key Strategies:
    1. Subagent Isolation - Each agent has its own context
    2. Result Summarization - Compress subagent output before returning
    3. Automatic Compaction - SDK handles long sessions via compaction
    4. Deduplication - Avoid storing redundant information
    """
    
    def __init__(self, default_max_tokens: int = 100000):
        self.default_max_tokens = default_max_tokens
        self.windows: dict[str, ContextWindow] = {}
        self._result_cache: dict[str, str] = {}  # Hash -> compressed result
    
    def create_window(self, agent_id: str, max_tokens: Optional[int] = None) -> ContextWindow:
        """Create a new context window for an agent."""
        window = ContextWindow(
            agent_id=agent_id,
            max_tokens=max_tokens or self.default_max_tokens,
        )
        self.windows[agent_id] = window
        logger.debug(f"Created context window for agent {agent_id}")
        return window
    
    def get_window(self, agent_id: str) -> Optional[ContextWindow]:
        """Get context window for an agent."""
        return self.windows.get(agent_id)
    
    def add_entry(
        self,
        agent_id: str,
        content: str,
        entry_type: str,
        metadata: dict = None,
    ) -> bool:
        """
        Add an entry to an agent's context window.
        
        Returns:
            True if added successfully, False if compression needed
        """
        window = self.windows.get(agent_id)
        if not window:
            window = self.create_window(agent_id)
        
        # Estimate tokens (rough: 4 chars per token)
        token_estimate = len(content) // 4
        
        entry = ContextEntry(
            content=content,
            entry_type=entry_type,
            timestamp=datetime.utcnow().isoformat(),
            token_estimate=token_estimate,
            agent_id=agent_id,
            metadata=metadata or {},
        )
        
        window.add(entry)
        
        # Check if compression is needed
        if window.should_compress():
            logger.info(f"Context window {agent_id} needs compression ({window.get_usage_ratio():.1%} full)")
            return False
        
        return True
    
    def compress_result(self, result: str, max_tokens: int = 500) -> str:
        """
        Compress a result for efficient context storage.
        
        This extracts key information and discards verbose output.
        """
        if not result:
            return ""
        
        # Check cache
        result_hash = hashlib.md5(result.encode()).hexdigest()
        if result_hash in self._result_cache:
            return self._result_cache[result_hash]
        
        # Estimate current tokens
        current_tokens = len(result) // 4
        
        if current_tokens <= max_tokens:
            return result
        
        # Apply compression strategies
        compressed = self._apply_compression(result, max_tokens)
        
        # Cache the result
        self._result_cache[result_hash] = compressed
        
        return compressed
    
    def _apply_compression(self, text: str, max_tokens: int) -> str:
        """Apply various compression strategies to text."""
        lines = text.split('\n')
        
        # Strategy 1: Remove empty lines and excessive whitespace
        lines = [line.strip() for line in lines if line.strip()]
        
        # Strategy 2: Truncate very long lines
        max_line_length = 200
        lines = [
            line[:max_line_length] + "..." if len(line) > max_line_length else line
            for line in lines
        ]
        
        # Strategy 3: Keep first and last sections, summarize middle
        max_chars = max_tokens * 4
        result = '\n'.join(lines)
        
        if len(result) > max_chars:
            # Keep first 40%, last 40%, summarize middle
            first_part = result[:int(max_chars * 0.4)]
            last_part = result[-int(max_chars * 0.4):]
            
            middle_summary = f"\n[... {len(result) - len(first_part) - len(last_part)} chars omitted ...]\n"
            result = first_part + middle_summary + last_part
        
        return result
    
    def summarize_for_handoff(self, agent_id: str) -> str:
        """
        Create a summary of agent context for handoff to orchestrator.
        
        This extracts only the essential findings and results.
        """
        window = self.windows.get(agent_id)
        if not window:
            return ""
        
        # Extract key entries
        results = []
        for entry in window.entries:
            if entry.entry_type == "result":
                results.append(entry.content)
        
        if not results:
            # No explicit results, summarize the last few entries
            recent = window.entries[-3:] if len(window.entries) >= 3 else window.entries
            return "\n".join(e.content for e in recent)
        
        return "\n\n".join(results)
    
    def clear_window(self, agent_id: str):
        """Clear a context window."""
        if agent_id in self.windows:
            del self.windows[agent_id]
            logger.debug(f"Cleared context window for agent {agent_id}")
    
    def get_stats(self) -> dict:
        """Get statistics about all context windows."""
        return {
            "total_windows": len(self.windows),
            "windows": {
                agent_id: {
                    "entries": len(window.entries),
                    "tokens": window.total_tokens,
                    "usage_ratio": window.get_usage_ratio(),
                }
                for agent_id, window in self.windows.items()
            },
            "cache_size": len(self._result_cache),
        }
    
    def should_spawn_subagent(self, query: str) -> tuple[bool, str]:
        """
        Determine if a query should spawn a subagent.
        
        Returns:
            (should_spawn, reason)
        """
        # Complex queries benefit from subagent isolation
        indicators = [
            (len(query) > 500, "Long query benefits from dedicated context"),
            ("multiple" in query.lower(), "Multiple tasks benefit from parallelization"),
            ("and then" in query.lower(), "Sequential tasks benefit from isolation"),
            ("files" in query.lower() and "all" in query.lower(), "Bulk operations benefit from dedicated agent"),
        ]
        
        for condition, reason in indicators:
            if condition:
                return True, reason
        
        return False, "Simple query can be handled directly"
    
    def estimate_complexity(self, query: str) -> dict:
        """
        Estimate query complexity for resource planning.
        
        Returns:
            Complexity metrics
        """
        words = query.split()
        
        return {
            "word_count": len(words),
            "estimated_turns": max(1, len(words) // 50),
            "estimated_tokens": len(query) // 4,
            "complexity": "high" if len(words) > 100 else "medium" if len(words) > 30 else "low",
            "should_parallelize": len(words) > 150,
        }

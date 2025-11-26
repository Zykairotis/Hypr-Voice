"""
Query Router

Classifies queries and routes them to appropriate subagents.
Implements the Routing workflow pattern from Anthropic docs.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Available agent types for routing."""
    CODE = "code-worker"
    RESEARCH = "research-worker"
    SHELL = "shell-worker"
    VOICE = "voice-worker"
    GENERAL = "general-conversation"
    ORCHESTRATOR = "orchestrator"  # Handle directly


@dataclass
class RouteDecision:
    """Routing decision with confidence and reasoning."""
    agent_type: str
    confidence: float  # 0.0 to 1.0
    reasoning: str
    keywords_matched: list[str]
    should_parallelize: bool = False
    secondary_agents: list[str] = None
    
    def __post_init__(self):
        if self.secondary_agents is None:
            self.secondary_agents = []


class QueryRouter:
    """
    Routes queries to appropriate specialized agents.
    
    Uses keyword matching and pattern recognition for fast routing.
    Can be extended with LLM-based classification for complex cases.
    """
    
    def __init__(self):
        # Define routing patterns for each agent type
        self.patterns = {
            AgentType.CODE: {
                "keywords": [
                    "code", "function", "class", "implement", "refactor",
                    "debug", "fix", "error", "bug", "compile", "syntax",
                    "python", "javascript", "typescript", "rust", "go",
                    "variable", "loop", "array", "object", "method",
                    "api", "endpoint", "test", "unit test", "coverage",
                    "import", "module", "package", "dependency",
                    "git", "commit", "branch", "merge", "pr", "pull request",
                ],
                "patterns": [
                    r"write\s+(a\s+)?.*\s+(function|class|script|program)",
                    r"create\s+(a\s+)?.*\.(py|js|ts|rs|go|cpp|c|java)",
                    r"fix\s+(the\s+)?.*\s+(error|bug|issue)",
                    r"implement\s+",
                    r"refactor\s+",
                    r"add\s+(a\s+)?.*\s+to\s+.*\.(py|js|ts)",
                ],
                "weight": 1.0,
            },
            AgentType.RESEARCH: {
                "keywords": [
                    "search", "find", "look up", "what is", "how does",
                    "explain", "documentation", "docs", "reference",
                    "example", "tutorial", "guide", "learn",
                    "compare", "difference", "between", "vs",
                    "best practice", "recommendation", "suggest",
                ],
                "patterns": [
                    r"what\s+(is|are)\s+",
                    r"how\s+(do|does|to)\s+",
                    r"explain\s+",
                    r"find\s+(information|docs|examples)",
                    r"search\s+for\s+",
                ],
                "weight": 0.8,
            },
            AgentType.SHELL: {
                "keywords": [
                    "run", "execute", "command", "terminal", "shell",
                    "bash", "sh", "zsh", "script", "chmod", "chown",
                    "install", "apt", "pacman", "npm", "pip", "cargo",
                    "process", "kill", "ps", "top", "htop",
                    "file", "directory", "folder", "mkdir", "rm", "mv", "cp",
                    "permission", "sudo", "root", "user",
                    "service", "systemctl", "daemon", "start", "stop", "restart",
                    "network", "curl", "wget", "ssh", "scp",
                    "environment", "env", "export", "path",
                ],
                "patterns": [
                    r"run\s+(the\s+)?command",
                    r"execute\s+",
                    r"install\s+",
                    r"start\s+(the\s+)?.*\s+service",
                    r"(list|show)\s+(all\s+)?.*\s+(files|directories|processes)",
                    r"check\s+(the\s+)?(status|logs)",
                ],
                "weight": 0.9,
            },
            AgentType.VOICE: {
                "keywords": [
                    "speak", "say", "read aloud", "tts", "text to speech",
                    "voice", "audio", "synthesize", "pronounce",
                    "listen", "transcribe", "stt", "speech to text",
                ],
                "patterns": [
                    r"(speak|say|read)\s+(this|the|out)",
                    r"convert\s+.*\s+to\s+(speech|audio)",
                    r"(generate|create)\s+(a\s+)?voice",
                ],
                "weight": 0.9,
            },
            AgentType.GENERAL: {
                "keywords": [
                    "hi", "hello", "hey", "howdy", "greetings",
                    "how are you", "what's up", "how is life", "how's it going",
                    "thanks", "thank you", "appreciate",
                    "advice", "help me", "what do you think", "your opinion",
                    "tell me about", "can you explain", "i'm feeling",
                    "life", "success", "happy", "motivation", "inspire",
                    "chat", "talk", "conversation", "discuss",
                    "good morning", "good night", "goodbye", "bye",
                    "please", "could you", "would you", "i need",
                    "how can i", "what should i", "why do", "why is",
                ],
                "patterns": [
                    r"^(hi|hello|hey|howdy)\b",
                    r"^(good\s+)?(morning|afternoon|evening|night)",
                    r"how\s+(are|is)\s+(you|life|everything|things)",
                    r"what('s|\s+is)\s+(up|new|happening)",
                    r"(thanks?|thank\s+you)",
                    r"(can|could|would)\s+you\s+(please\s+)?(help|tell|explain)",
                    r"i('m|\s+am)\s+(feeling|wondering|thinking|curious)",
                    r"what\s+do\s+you\s+think",
                    r"(your|any)\s+(advice|suggestions?|thoughts?|opinion)",
                    r"how\s+(can|do|should)\s+i\s+",
                ],
                "weight": 1.1,  # Slightly higher to catch conversational queries
            },
        }
        
        # Compile regex patterns
        self._compiled_patterns = {}
        for agent_type, config in self.patterns.items():
            self._compiled_patterns[agent_type] = [
                re.compile(p, re.IGNORECASE) for p in config["patterns"]
            ]
    
    def route(self, query: str) -> RouteDecision:
        """
        Route a query to the most appropriate agent.
        
        Args:
            query: The user query to route
            
        Returns:
            RouteDecision with agent type and confidence
        """
        query_lower = query.lower()
        scores = {}
        matched_keywords = {}
        
        # Score each agent type
        for agent_type, config in self.patterns.items():
            score = 0.0
            keywords = []
            
            # Check keywords
            for keyword in config["keywords"]:
                if keyword in query_lower:
                    score += 0.1
                    keywords.append(keyword)
            
            # Check patterns
            for pattern in self._compiled_patterns[agent_type]:
                if pattern.search(query):
                    score += 0.3
            
            # Apply weight
            score *= config["weight"]
            
            scores[agent_type] = min(score, 1.0)  # Cap at 1.0
            matched_keywords[agent_type] = keywords
        
        # Find best match
        if scores:
            best_agent = max(scores, key=scores.get)
            best_score = scores[best_agent]
            
            # If confidence is too low, route to orchestrator
            if best_score < 0.2:
                return RouteDecision(
                    agent_type=AgentType.ORCHESTRATOR.value,
                    confidence=0.5,
                    reasoning="Query doesn't clearly match any specialist. Handling directly.",
                    keywords_matched=[],
                )
            
            # Check if multiple agents should work together
            secondary = []
            should_parallelize = False
            for agent_type, score in scores.items():
                if agent_type != best_agent and score >= 0.3:
                    secondary.append(agent_type.value)
                    should_parallelize = True
            
            return RouteDecision(
                agent_type=best_agent.value,
                confidence=best_score,
                reasoning=self._generate_reasoning(best_agent, matched_keywords[best_agent]),
                keywords_matched=matched_keywords[best_agent],
                should_parallelize=should_parallelize,
                secondary_agents=secondary,
            )
        
        # Default to orchestrator
        return RouteDecision(
            agent_type=AgentType.ORCHESTRATOR.value,
            confidence=0.5,
            reasoning="No specific patterns matched. Handling with general capabilities.",
            keywords_matched=[],
        )
    
    def _generate_reasoning(self, agent_type: AgentType, keywords: list[str]) -> str:
        """Generate human-readable reasoning for the routing decision."""
        reasons = {
            AgentType.CODE: "Query involves code-related tasks",
            AgentType.RESEARCH: "Query requires information gathering",
            AgentType.SHELL: "Query involves system operations",
            AgentType.VOICE: "Query involves voice synthesis",
            AgentType.GENERAL: "Query is conversational or general chat",
            AgentType.ORCHESTRATOR: "General query for direct handling",
        }
        
        base_reason = reasons.get(agent_type, "Matched agent capabilities")
        
        if keywords:
            return f"{base_reason}. Matched keywords: {', '.join(keywords[:5])}"
        return base_reason
    
    def add_pattern(self, agent_type: AgentType, keywords: list[str] = None, patterns: list[str] = None):
        """
        Add custom patterns for routing.
        
        Args:
            agent_type: The agent type to add patterns for
            keywords: Additional keywords to match
            patterns: Additional regex patterns to match
        """
        if agent_type not in self.patterns:
            self.patterns[agent_type] = {
                "keywords": [],
                "patterns": [],
                "weight": 1.0,
            }
        
        if keywords:
            self.patterns[agent_type]["keywords"].extend(keywords)
        
        if patterns:
            self.patterns[agent_type]["patterns"].extend(patterns)
            # Recompile patterns
            self._compiled_patterns[agent_type] = [
                re.compile(p, re.IGNORECASE) 
                for p in self.patterns[agent_type]["patterns"]
            ]
    
    def get_all_keywords(self) -> dict[str, list[str]]:
        """Get all keywords for each agent type."""
        return {
            agent_type.value: config["keywords"]
            for agent_type, config in self.patterns.items()
        }

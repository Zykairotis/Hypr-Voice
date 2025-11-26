"""
Cerebras-Powered Intelligent Router

Uses Cerebras fast inference (gpt-oss-120b) for intelligent query analysis
and agent selection. Supports key rotation for rate limiting.
"""

import os
import json
import logging
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Available agent types for routing."""
    CODE = "code-worker"
    RESEARCH = "research-worker"
    SHELL = "shell-worker"
    VOICE = "voice-worker"
    GENERAL = "general-conversation"
    ORCHESTRATOR = "orchestrator"


@dataclass
class RouteDecision:
    """Result of routing decision from Cerebras."""
    agent_type: str
    confidence: float
    reasoning: str
    keywords_matched: List[str] = None
    
    def __post_init__(self):
        if self.keywords_matched is None:
            self.keywords_matched = []


# System prompt for Cerebras routing
ROUTING_PROMPT = """You are a query router for a voice assistant system. Analyze the user's query and select the most appropriate agent to handle it.

AVAILABLE AGENTS:
1. general-conversation: For greetings, casual chat, life advice, emotional support, general questions about life/relationships/motivation
2. code-worker: For programming tasks, debugging, code analysis, writing functions, fixing bugs, code refactoring
3. research-worker: For information lookup, explanations, documentation, "what is X", "how does Y work"
4. shell-worker: For system commands, bash operations, file management, running scripts, terminal operations
5. voice-worker: For text-to-speech operations, voice synthesis, audio generation

ROUTING RULES:
- Greetings like "hi", "hello", "how are you" → general-conversation
- Questions about feelings, life, motivation → general-conversation
- Code/programming questions → code-worker
- "What is X" or explanation requests → research-worker
- Terminal/bash commands → shell-worker
- Default to general-conversation for ambiguous queries

Respond with ONLY a JSON object (no markdown, no explanation):
{"agent": "agent-name", "confidence": 0.0-1.0, "reason": "brief explanation"}"""


class CerebrasRouter:
    """
    Intelligent query router using Cerebras fast inference.
    
    Features:
    - Uses gpt-oss-120b for smart routing (~200ms)
    - Rotates between multiple API keys
    - Falls back to keyword matching if Cerebras fails
    """
    
    def __init__(self):
        """Initialize router with API keys from environment."""
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        self.model = "llama3.1-8b"  # Fast inference model (~200ms)
        
        if not self.api_keys:
            logger.warning("No Cerebras API keys found - will use fallback routing")
        else:
            logger.info(f"CerebrasRouter initialized with {len(self.api_keys)} API keys")
    
    def _load_api_keys(self) -> List[str]:
        """Load API keys from environment."""
        keys = []
        key_names = [
            "CEREBRAS_API_KEY_ONE",
            "CEREBRAS_API_KEY_TWO", 
            "CEREBRAS_API_KEY_THREE",
            "CEREBRAS_API_KEY",  # Fallback single key
        ]
        
        for name in key_names:
            key = os.getenv(name)
            if key and key not in keys:
                keys.append(key)
        
        return keys
    
    def _get_next_key(self) -> Optional[str]:
        """Get next API key using round-robin rotation."""
        if not self.api_keys:
            return None
        
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def route(self, query: str) -> RouteDecision:
        """
        Route query to appropriate agent using Cerebras.
        
        Args:
            query: User's input query
            
        Returns:
            RouteDecision with agent_type, confidence, and reasoning
        """
        api_key = self._get_next_key()
        
        if not api_key:
            logger.warning("No API key available, using fallback routing")
            return self._fallback_route(query)
        
        try:
            from cerebras.cloud.sdk import Cerebras
            
            client = Cerebras(api_key=api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ROUTING_PROMPT},
                    {"role": "user", "content": query}
                ],
                max_tokens=150,
                temperature=0.1,  # Low temperature for consistent routing
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            logger.debug(f"Cerebras routing response: {content}")
            
            # Try to parse JSON
            try:
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                
                result = json.loads(content)
                
                agent = result.get("agent", "general-conversation")
                confidence = float(result.get("confidence", 0.8))
                reason = result.get("reason", "Cerebras routing decision")
                
                # Validate agent type
                valid_agents = [e.value for e in AgentType]
                if agent not in valid_agents:
                    logger.warning(f"Invalid agent type '{agent}', defaulting to general-conversation")
                    agent = "general-conversation"
                
                return RouteDecision(
                    agent_type=agent,
                    confidence=confidence,
                    reasoning=reason,
                )
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse Cerebras response as JSON: {e}")
                return self._fallback_route(query)
                
        except Exception as e:
            logger.error(f"Cerebras routing error: {e}")
            return self._fallback_route(query)
    
    async def route_async(self, query: str) -> RouteDecision:
        """
        Async version of route for better performance.
        
        Args:
            query: User's input query
            
        Returns:
            RouteDecision with agent_type, confidence, and reasoning
        """
        api_key = self._get_next_key()
        
        if not api_key:
            return self._fallback_route(query)
        
        try:
            from cerebras.cloud.sdk import AsyncCerebras
            
            client = AsyncCerebras(api_key=api_key)
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ROUTING_PROMPT},
                    {"role": "user", "content": query}
                ],
                max_tokens=150,
                temperature=0.1,
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                
                result = json.loads(content)
                
                agent = result.get("agent", "general-conversation")
                confidence = float(result.get("confidence", 0.8))
                reason = result.get("reason", "Cerebras routing decision")
                
                valid_agents = [e.value for e in AgentType]
                if agent not in valid_agents:
                    agent = "general-conversation"
                
                return RouteDecision(
                    agent_type=agent,
                    confidence=confidence,
                    reasoning=reason,
                )
                
            except json.JSONDecodeError:
                return self._fallback_route(query)
                
        except Exception as e:
            logger.error(f"Async Cerebras routing error: {e}")
            return self._fallback_route(query)
    
    def _fallback_route(self, query: str) -> RouteDecision:
        """
        Fallback keyword-based routing when Cerebras is unavailable.
        
        Args:
            query: User's input query
            
        Returns:
            RouteDecision based on keyword matching
        """
        query_lower = query.lower()
        
        # Keyword patterns for each agent
        patterns = {
            AgentType.GENERAL: [
                "hi", "hello", "hey", "howdy", "greetings",
                "how are you", "what's up", "how is life",
                "advice", "help me with life", "motivation",
                "feeling", "thank", "thanks", "bye", "goodbye",
            ],
            AgentType.CODE: [
                "code", "function", "class", "implement", "debug",
                "fix", "error", "bug", "python", "javascript",
                "program", "script", "variable", "loop",
            ],
            AgentType.RESEARCH: [
                "what is", "what are", "explain", "how does",
                "documentation", "search", "find", "look up",
                "tell me about", "describe",
            ],
            AgentType.SHELL: [
                "run", "execute", "command", "terminal", "bash",
                "shell", "chmod", "mkdir", "install", "sudo",
            ],
            AgentType.VOICE: [
                "speak", "say", "read aloud", "tts", "voice",
                "pronounce", "audio",
            ],
        }
        
        # Score each agent
        scores = {}
        matched_keywords = {}
        
        for agent_type, keywords in patterns.items():
            score = 0
            matches = []
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
                    matches.append(keyword)
            scores[agent_type] = score
            matched_keywords[agent_type] = matches
        
        # Find best match
        best_agent = max(scores, key=scores.get)
        best_score = scores[best_agent]
        
        if best_score == 0:
            # No matches, default to general conversation
            return RouteDecision(
                agent_type=AgentType.GENERAL.value,
                confidence=0.5,
                reasoning="No specific patterns matched, defaulting to general conversation",
            )
        
        confidence = min(0.9, 0.5 + (best_score * 0.1))
        
        return RouteDecision(
            agent_type=best_agent.value,
            confidence=confidence,
            reasoning=f"Keyword match: {', '.join(matched_keywords[best_agent])}",
            keywords_matched=matched_keywords[best_agent],
        )

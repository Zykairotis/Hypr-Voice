"""
MCP-Compatible Tool Wrappers

This module provides MCP-compatible wrappers for helper agent capabilities,
bridging existing tools with the MCP protocol.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPToolWrappers:
    """Factory class for creating MCP-compatible tool wrappers."""
    
    def __init__(self, helper_agent_instance=None):
        """
        Initialize MCP tool wrappers.
        
        Args:
            helper_agent_instance: HelperAgent instance for capability access
        """
        self.agent = helper_agent_instance
    
    async def summarize_text_mcp(
        self,
        text: str,
        max_length: int = 500,
        style: str = "voice_optimized",
        focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP wrapper for text summarization."""
        if not self.agent:
            return {
                "error": "Agent instance not available",
                "summary": "",
                "key_points": []
            }
        
        try:
            result = await self.agent.summarize_text(
                text=text,
                max_length=max_length,
                focus=focus
            )
            
            return {
                "summary": result.get("summary", ""),
                "key_points": result.get("key_points", []),
                "metadata": {
                    "original_length": result.get("original_length", 0),
                    "summary_length": result.get("summary_length", 0),
                    "compression_ratio": result.get("compression_ratio", 0.0),
                    "style": style,
                    "focus": focus
                }
            }
        except Exception as e:
            logger.error(f"Summarization MCP error: {e}")
            return {
                "error": str(e),
                "summary": "",
                "key_points": []
            }
    
    async def analyze_content_mcp(
        self,
        content: str,
        analysis_type: str = "comprehensive",
        optimize_for_voice: bool = True
    ) -> Dict[str, Any]:
        """MCP wrapper for content analysis."""
        if not self.agent:
            return {
                "error": "Agent instance not available",
                "analysis": {},
                "recommendations": []
            }
        
        try:
            result = await self.agent.analyze_content(
                content=content,
                optimize_for_voice=optimize_for_voice
            )
            
            return {
                "analysis": result.get("analysis", {}),
                "recommendations": result.get("recommendations", []),
                "score": result.get("score", 0.0),
                "metadata": {
                    "analysis_type": analysis_type,
                    "optimize_for_voice": optimize_for_voice
                }
            }
        except Exception as e:
            logger.error(f"Analysis MCP error: {e}")
            return {
                "error": str(e),
                "analysis": {},
                "recommendations": []
            }
    
    async def plan_task_mcp(
        self,
        task: str,
        max_steps: int = 10,
        context: Optional[str] = None,
        complexity: str = "medium"
    ) -> Dict[str, Any]:
        """MCP wrapper for task planning."""
        if not self.agent:
            return {
                "error": "Agent instance not available",
                "plan": [],
                "estimated_time": ""
            }
        
        try:
            result = await self.agent.plan_task(
                task=task,
                max_steps=max_steps,
                context=context
            )
            
            return {
                "plan": result.get("plan", []),
                "estimated_time": result.get("estimated_time", ""),
                "priority": result.get("priority", "medium"),
                "metadata": {
                    "complexity": complexity,
                    "max_steps": max_steps,
                    "has_context": context is not None
                }
            }
        except Exception as e:
            logger.error(f"Planning MCP error: {e}")
            return {
                "error": str(e),
                "plan": [],
                "estimated_time": ""
            }
    
    async def extract_information_mcp(
        self,
        text: str,
        information_types: List[str] = None
    ) -> Dict[str, Any]:
        """MCP wrapper for information extraction."""
        if information_types is None:
            information_types = ["actions", "key_points", "decisions"]
        
        if not self.agent:
            return {
                "error": "Agent instance not available",
                "extracted": {},
                "confidence": 0.0
            }
        
        try:
            # Use summarization tools for extraction
            from .summarization import SummarizationTools
            
            if not hasattr(self.agent, 'sglang_client'):
                return {
                    "error": "SGLang client not available",
                    "extracted": {},
                    "confidence": 0.0
                }
            
            summ_tools = SummarizationTools(
                self.agent.sglang_client,
                self.agent.prompts
            )
            
            result = await summ_tools.extract_key_information(
                text=text,
                information_types=information_types
            )
            
            return {
                "extracted": result.get("extracted_information", {}),
                "confidence": 0.85,  # Default confidence
                "metadata": {
                    "information_types": information_types,
                    "original_text_length": result.get("original_text_length", 0)
                }
            }
        except Exception as e:
            logger.error(f"Extraction MCP error: {e}")
            return {
                "error": str(e),
                "extracted": {},
                "confidence": 0.0
            }
    
    async def calculator_mcp(
        self,
        expression: str,
        precision: int = 2
    ) -> Dict[str, Any]:
        """MCP wrapper for calculator."""
        try:
            import math
            
            # Safe evaluation
            allowed_names = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow,
                "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
                "tan": math.tan, "log": math.log, "exp": math.exp,
                "pi": math.pi, "e": math.e
            }
            
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            formatted = f"{result:.{precision}f}"
            
            return {
                "result": result,
                "formatted": formatted,
                "expression": expression,
                "metadata": {
                    "precision": precision
                }
            }
        except Exception as e:
            logger.error(f"Calculator MCP error: {e}")
            return {
                "error": str(e),
                "result": 0.0,
                "formatted": "0.00"
            }
    
    async def claude_sdk_bridge_mcp(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        voice_optimized: bool = True
    ) -> Dict[str, Any]:
        """MCP wrapper for Claude SDK bridge."""
        if not self.agent:
            return {
                "error": "Agent instance not available",
                "response": ""
            }
        
        try:
            result = await self.agent.bridge_to_claude_sdk(
                request=request,
                context=context or {},
                voice_optimized=voice_optimized
            )
            
            return {
                "response": result.get("response", ""),
                "metadata": result.get("metadata", {}),
                "voice_optimized": voice_optimized
            }
        except Exception as e:
            logger.error(f"Claude SDK bridge MCP error: {e}")
            return {
                "error": str(e),
                "response": ""
            }
    
    def register_all_with_mcp_server(self, mcp_server):
        """
        Register all MCP tools with an MCP server.
        
        Args:
            mcp_server: MCPServer instance
        """
        # Summarization tool
        mcp_server.register_tool(
            name="summarize_text",
            description="Summarize text content for voice agent consumption",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to summarize"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum summary length",
                        "default": 500
                    },
                    "style": {
                        "type": "string",
                        "enum": ["voice_optimized", "concise", "detailed"],
                        "default": "voice_optimized"
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["technical", "actionable", "key_points", "decisions"],
                        "nullable": True
                    }
                },
                "required": ["text"]
            },
            func=self.summarize_text_mcp,
            category="text_processing",
            enabled=True
        )
        
        # Analysis tool
        mcp_server.register_tool(
            name="analyze_content",
            description="Analyze content for voice agent optimization",
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Content to analyze"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["comprehensive", "sentiment", "readability", "technical"],
                        "default": "comprehensive"
                    },
                    "optimize_for_voice": {
                        "type": "boolean",
                        "default": True
                    }
                },
                "required": ["content"]
            },
            func=self.analyze_content_mcp,
            category="text_processing",
            enabled=True
        )
        
        # Planning tool
        mcp_server.register_tool(
            name="plan_task",
            description="Break down complex tasks into actionable steps",
            parameters={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Task to plan"
                    },
                    "max_steps": {
                        "type": "integer",
                        "default": 10
                    },
                    "context": {
                        "type": "string",
                        "nullable": True
                    },
                    "complexity": {
                        "type": "string",
                        "enum": ["simple", "medium", "complex"],
                        "default": "medium"
                    }
                },
                "required": ["task"]
            },
            func=self.plan_task_mcp,
            category="planning",
            enabled=True
        )
        
        # Extraction tool
        mcp_server.register_tool(
            name="extract_information",
            description="Extract specific information from text",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to extract from"
                    },
                    "information_types": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "default": ["actions", "key_points", "decisions"]
                    }
                },
                "required": ["text"]
            },
            func=self.extract_information_mcp,
            category="text_processing",
            enabled=True
        )
        
        # Calculator tool
        mcp_server.register_tool(
            name="calculator",
            description="Perform mathematical calculations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression"
                    },
                    "precision": {
                        "type": "integer",
                        "default": 2
                    }
                },
                "required": ["expression"]
            },
            func=self.calculator_mcp,
            category="computation",
            enabled=True
        )
        
        # Claude SDK bridge tool
        mcp_server.register_tool(
            name="claude_sdk_bridge",
            description="Bridge to Claude Code SDK for context-aware assistance",
            parameters={
                "type": "object",
                "properties": {
                    "request": {
                        "type": "string",
                        "description": "Request to process"
                    },
                    "context": {
                        "type": "object",
                        "nullable": True
                    },
                    "voice_optimized": {
                        "type": "boolean",
                        "default": True
                    }
                },
                "required": ["request"]
            },
            func=self.claude_sdk_bridge_mcp,
            category="ai_integration",
            enabled=True
        )
        
        logger.info("Registered all MCP tools with server")


__all__ = ["MCPToolWrappers"]


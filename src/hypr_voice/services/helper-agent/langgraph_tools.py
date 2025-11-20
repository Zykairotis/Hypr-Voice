"""
LangChain Tool Wrappers for Helper Agent

This module provides LangChain-compatible tool wrappers for all helper agent capabilities,
enabling integration with LangGraph workflows and agent systems.
"""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from langchain.tools import tool, Tool, StructuredTool
    from langchain_core.tools import BaseTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available. Install with: pip install langchain langchain-core")

logger = logging.getLogger(__name__)


# Input schemas for tools
class SummarizeTextInput(BaseModel):
    """Input schema for summarization tool."""
    text: str = Field(..., description="The text content to summarize")
    max_length: int = Field(500, description="Maximum length of summary in characters", ge=50, le=2000)
    style: str = Field("voice_optimized", description="Summary style: voice_optimized, concise, or detailed")
    focus: Optional[str] = Field(None, description="Specific focus area: technical, actionable, key_points, or decisions")


class AnalyzeContentInput(BaseModel):
    """Input schema for content analysis tool."""
    content: str = Field(..., description="Content to analyze")
    analysis_type: str = Field("comprehensive", description="Type of analysis: comprehensive, sentiment, readability, or technical")
    optimize_for_voice: bool = Field(True, description="Whether to optimize analysis for voice output")


class PlanTaskInput(BaseModel):
    """Input schema for task planning tool."""
    task: str = Field(..., description="Task description to plan")
    max_steps: int = Field(10, description="Maximum number of steps to generate", ge=1, le=20)
    context: Optional[str] = Field(None, description="Additional context for planning")
    complexity: str = Field("medium", description="Task complexity: simple, medium, or complex")


class ExtractInformationInput(BaseModel):
    """Input schema for information extraction tool."""
    text: str = Field(..., description="Text to extract information from")
    information_types: List[str] = Field(
        default=["actions", "key_points", "decisions"],
        description="Types of information to extract: dates, people, locations, actions, technical_terms, decisions"
    )


class CalculatorInput(BaseModel):
    """Input schema for calculator tool."""
    expression: str = Field(..., description="Mathematical expression to evaluate")
    precision: int = Field(2, description="Number of decimal places", ge=0, le=10)


class ClaudeSDKBridgeInput(BaseModel):
    """Input schema for Claude SDK bridge tool."""
    request: str = Field(..., description="Request to process via Claude SDK")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    voice_optimized: bool = Field(True, description="Optimize response for voice output")


class LangChainTools:
    """Factory class for creating LangChain tools from helper agent capabilities."""
    
    def __init__(self, litellm_client=None, agent_instance=None):
        """
        Initialize LangChain tools.
        
        Args:
            litellm_client: LiteLLM client instance for direct LLM access
            agent_instance: HelperAgent instance for capability access
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is required but not installed")
        
        self.litellm_client = litellm_client
        self.agent_instance = agent_instance
        
        # Initialize tool functions
        self._init_tool_functions()
    
    def _init_tool_functions(self):
        """Initialize tool function implementations."""
        
        async def _summarize_text(text: str, max_length: int = 500, style: str = "voice_optimized", focus: Optional[str] = None) -> str:
            """Summarize text content for voice agent consumption."""
            if not self.agent_instance:
                return "Error: Agent instance not available"
            
            try:
                result = await self.agent_instance.summarize_text(
                    text=text,
                    max_length=max_length,
                    focus=focus
                )
                return result.get("summary", "")
            except Exception as e:
                logger.error(f"Summarization error: {e}")
                return f"Error during summarization: {str(e)}"
        
        async def _analyze_content(content: str, analysis_type: str = "comprehensive", optimize_for_voice: bool = True) -> str:
            """Analyze content for voice agent optimization."""
            if not self.agent_instance:
                return "Error: Agent instance not available"
            
            try:
                result = await self.agent_instance.analyze_content(
                    content=content,
                    optimize_for_voice=optimize_for_voice
                )
                analysis = result.get("analysis", {})
                return f"Analysis: {analysis}"
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                return f"Error during analysis: {str(e)}"
        
        async def _plan_task(task: str, max_steps: int = 10, context: Optional[str] = None, complexity: str = "medium") -> str:
            """Break down complex tasks into actionable steps."""
            if not self.agent_instance:
                return "Error: Agent instance not available"
            
            try:
                result = await self.agent_instance.plan_task(
                    task=task,
                    max_steps=max_steps,
                    context=context
                )
                plan = result.get("plan", [])
                steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(plan)])
                return f"Task Plan:\n{steps}"
            except Exception as e:
                logger.error(f"Planning error: {e}")
                return f"Error during planning: {str(e)}"
        
        async def _extract_information(text: str, information_types: List[str] = None) -> str:
            """Extract specific types of information from text."""
            if not self.agent_instance:
                return "Error: Agent instance not available"
            
            if information_types is None:
                information_types = ["actions", "key_points", "decisions"]
            
            try:
                # Use summarization tools for extraction
                from .tools.summarization import SummarizationTools
                from .sglang_client import SGLangClient, SGLangConfig
                
                # Create temporary client if needed
                if not hasattr(self.agent_instance, 'sglang_client'):
                    return "Error: SGLang client not available"
                
                summ_tools = SummarizationTools(
                    self.agent_instance.sglang_client,
                    self.agent_instance.prompts
                )
                
                result = await summ_tools.extract_key_information(
                    text=text,
                    information_types=information_types
                )
                
                extracted = result.get("extracted_information", {})
                output = []
                for info_type, items in extracted.items():
                    if items:
                        output.append(f"{info_type.title()}: {', '.join(items)}")
                
                return "\n".join(output) if output else "No information extracted"
                
            except Exception as e:
                logger.error(f"Extraction error: {e}")
                return f"Error during extraction: {str(e)}"
        
        async def _calculator(expression: str, precision: int = 2) -> str:
            """Perform mathematical calculations."""
            try:
                # Safe evaluation using eval with restricted globals
                import math
                allowed_names = {
                    "abs": abs, "round": round, "min": min, "max": max,
                    "sum": sum, "pow": pow,
                    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
                    "tan": math.tan, "log": math.log, "exp": math.exp,
                    "pi": math.pi, "e": math.e
                }
                
                result = eval(expression, {"__builtins__": {}}, allowed_names)
                formatted = f"{result:.{precision}f}"
                return f"Result: {formatted}"
            except Exception as e:
                logger.error(f"Calculator error: {e}")
                return f"Error: {str(e)}"
        
        async def _claude_sdk_bridge(request: str, context: Optional[Dict[str, Any]] = None, voice_optimized: bool = True) -> str:
            """Bridge to Claude Code SDK for context-aware assistance."""
            if not self.agent_instance:
                return "Error: Agent instance not available"
            
            try:
                result = await self.agent_instance.bridge_to_claude_sdk(
                    request=request,
                    context=context or {},
                    voice_optimized=voice_optimized
                )
                return result.get("response", "")
            except Exception as e:
                logger.error(f"Claude SDK bridge error: {e}")
                return f"Error: {str(e)}"
        
        # Store function references
        self._summarize_text = _summarize_text
        self._analyze_content = _analyze_content
        self._plan_task = _plan_task
        self._extract_information = _extract_information
        self._calculator = _calculator
        self._claude_sdk_bridge = _claude_sdk_bridge
    
    def get_summarization_tool(self) -> StructuredTool:
        """Get summarization tool."""
        return StructuredTool.from_function(
            func=self._summarize_text,
            name="summarize_text",
            description="Summarize text content for voice agent consumption with configurable length and style",
            args_schema=SummarizeTextInput,
            return_direct=False
        )
    
    def get_analysis_tool(self) -> StructuredTool:
        """Get content analysis tool."""
        return StructuredTool.from_function(
            func=self._analyze_content,
            name="analyze_content",
            description="Analyze content for voice agent optimization including sentiment, readability, and key insights",
            args_schema=AnalyzeContentInput,
            return_direct=False
        )
    
    def get_planning_tool(self) -> StructuredTool:
        """Get task planning tool."""
        return StructuredTool.from_function(
            func=self._plan_task,
            name="plan_task",
            description="Break down complex tasks into actionable steps with priorities and time estimates",
            args_schema=PlanTaskInput,
            return_direct=False
        )
    
    def get_extraction_tool(self) -> StructuredTool:
        """Get information extraction tool."""
        return StructuredTool.from_function(
            func=self._extract_information,
            name="extract_information",
            description="Extract specific types of information from text (dates, people, actions, etc.)",
            args_schema=ExtractInformationInput,
            return_direct=False
        )
    
    def get_calculator_tool(self) -> StructuredTool:
        """Get calculator tool."""
        return StructuredTool.from_function(
            func=self._calculator,
            name="calculator",
            description="Perform mathematical calculations with support for basic arithmetic and functions",
            args_schema=CalculatorInput,
            return_direct=False
        )
    
    def get_claude_sdk_tool(self) -> StructuredTool:
        """Get Claude SDK bridge tool."""
        return StructuredTool.from_function(
            func=self._claude_sdk_bridge,
            name="claude_sdk_bridge",
            description="Bridge to Claude Code SDK for context-aware assistance and coding support",
            args_schema=ClaudeSDKBridgeInput,
            return_direct=False
        )
    
    def get_all_tools(self) -> List[StructuredTool]:
        """Get all available tools."""
        return [
            self.get_summarization_tool(),
            self.get_analysis_tool(),
            self.get_planning_tool(),
            self.get_extraction_tool(),
            self.get_calculator_tool(),
            self.get_claude_sdk_tool()
        ]
    
    def get_tools_by_category(self, category: str) -> List[StructuredTool]:
        """
        Get tools by category.
        
        Args:
            category: Category name (text_processing, planning, computation, ai_integration)
            
        Returns:
            List of tools in that category
        """
        categories = {
            "text_processing": [
                self.get_summarization_tool(),
                self.get_analysis_tool(),
                self.get_extraction_tool()
            ],
            "planning": [
                self.get_planning_tool()
            ],
            "computation": [
                self.get_calculator_tool()
            ],
            "ai_integration": [
                self.get_claude_sdk_tool()
            ]
        }
        
        return categories.get(category, [])


# Utility functions for creating simple tools
@tool
def quick_calculator(expression: str) -> str:
    """
    Perform quick mathematical calculations.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Calculation result as string
    """
    try:
        import math
        allowed_names = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow,
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
            "tan": math.tan, "log": math.log, "exp": math.exp,
            "pi": math.pi, "e": math.e
        }
        
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def text_length_counter(text: str) -> str:
    """
    Count characters, words, and lines in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Text statistics
    """
    char_count = len(text)
    word_count = len(text.split())
    line_count = len(text.splitlines())
    
    return f"Characters: {char_count}, Words: {word_count}, Lines: {line_count}"


def create_custom_tool(
    name: str,
    description: str,
    func: callable,
    args_schema: Optional[BaseModel] = None
) -> StructuredTool:
    """
    Create a custom LangChain tool.
    
    Args:
        name: Tool name
        description: Tool description
        func: Tool function
        args_schema: Pydantic schema for arguments
        
    Returns:
        StructuredTool instance
    """
    if args_schema:
        return StructuredTool.from_function(
            func=func,
            name=name,
            description=description,
            args_schema=args_schema
        )
    else:
        return Tool(
            name=name,
            description=description,
            func=func
        )


__all__ = [
    "LangChainTools",
    "SummarizeTextInput",
    "AnalyzeContentInput",
    "PlanTaskInput",
    "ExtractInformationInput",
    "CalculatorInput",
    "ClaudeSDKBridgeInput",
    "quick_calculator",
    "text_length_counter",
    "create_custom_tool"
]


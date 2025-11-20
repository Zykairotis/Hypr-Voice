"""
Claude Code SDK Integration Bridge

This module provides integration between the helper agent and Claude Code SDK,
enabling context-aware assistance and tool orchestration.
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from ..sglang_client import SGLangClient

logger = logging.getLogger(__name__)


class ClaudeSDKBridge:
    """
    Bridge between helper agent and Claude Code SDK.

    Provides context-aware processing and communication with Claude Code SDK
    for enhanced voice agent capabilities.
    """

    def __init__(self, sglang_client: SGLangClient, prompts: Dict[str, Any]):
        """
        Initialize Claude SDK bridge.

        Args:
            sglang_client: Initialized SGLang client
            prompts: Prompts configuration dictionary
        """
        self.sglang_client = sglang_client
        self.prompts = prompts.get("claude_bridge", {})
        self.active_contexts: Dict[str, Dict[str, Any]] = {}
        self.claude_sdk_tools = self._initialize_claude_sdk_tools()

    def _initialize_claude_sdk_tools(self) -> Dict[str, Any]:
        """Initialize available Claude Code SDK tools."""
        return {
            "file_operations": {
                "read": True,
                "write": True,
                "edit": True,
                "search": True
            },
            "system_operations": {
                "bash": True,
                "git": True,
                "package_manager": True
            },
            "development_tools": {
                "testing": True,
                "linting": True,
                "documentation": True
            },
            "voice_specific": {
                "text_to_speech": True,
                "audio_processing": True,
                "clipboard": True
            }
        }

    async def process_request(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        voice_optimized: bool = True,
        available_tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a request for Claude Code SDK integration.

        Args:
            request: Request to process
            context: Additional context for the request
            voice_optimized: Whether to optimize response for voice output
            available_tools: List of available Claude SDK tools

        Returns:
            Dictionary containing processed response and actions.
        """
        try:
            if not request or not request.strip():
                return {"error": "No request provided"}

            # Enrich context
            enriched_context = await self._enrich_context(context or {})

            # Determine if this requires Claude SDK tools
            tool_analysis = await self._analyze_tool_requirements(request, enriched_context)

            # Prepare bridge messages
            messages = [
                {
                    "role": "system",
                    "content": self._get_bridge_system_prompt(voice_optimized, tool_analysis)
                },
                {
                    "role": "user",
                    "content": self._format_bridge_prompt(request, enriched_context, tool_analysis)
                }
            ]

            # Generate response
            bridge_response = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=1200,
                temperature=0.5
            )

            if not bridge_response:
                return {"error": "Failed to generate bridge response"}

            # Parse and structure the response
            structured_response = self._parse_bridge_response(bridge_response, tool_analysis)

            # Add context and metadata
            structured_response.update({
                "original_request": request,
                "context": enriched_context,
                "voice_optimized": voice_optimized,
                "tools_required": tool_analysis.get("required_tools", []),
                "processed_at": datetime.now().isoformat(),
                "context_id": self._generate_context_id(enriched_context)
            })

            # Store context for future reference
            self._store_context(structured_response["context_id"], enriched_context, structured_response)

            return structured_response

        except Exception as e:
            logger.error(f"Claude SDK bridge processing failed: {e}")
            return {"error": f"Claude SDK bridge processing failed: {str(e)}"}

    async def suggest_claude_actions(
        self,
        situation: str,
        goal: str,
        constraints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Suggest Claude Code SDK actions for a given situation.

        Args:
            situation: Current situation description
            goal: Desired outcome
            constraints: Any constraints or limitations

        Returns:
            Dictionary containing suggested Claude SDK actions.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert in Claude Code SDK capabilities. Suggest appropriate Claude Code tools and actions to achieve the given goal."
                },
                {
                    "role": "user",
                    "content": self._format_action_suggestion_prompt(situation, goal, constraints)
                }
            ]

            suggestions = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=1000,
                temperature=0.4
            )

            if not suggestions:
                return {"error": "Failed to generate action suggestions"}

            parsed_suggestions = self._parse_action_suggestions(suggestions)

            return {
                "situation": situation,
                "goal": goal,
                "constraints": constraints or [],
                "suggested_actions": parsed_suggestions,
                "confidence_score": self._calculate_action_confidence(parsed_suggestions)
            }

        except Exception as e:
            logger.error(f"Action suggestion failed: {e}")
            return {"error": f"Action suggestion failed: {str(e)}"}

    async def format_for_claude_sdk(
        self,
        content: str,
        purpose: str = "general",
        target_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Format content for Claude Code SDK consumption.

        Args:
            content: Content to format
            purpose: Purpose of formatting ("query", "instruction", "context")
            target_format: Target format ("json", "markdown", "plain")

        Returns:
            Dictionary containing formatted content.
        """
        try:
            formatting_rules = self._get_formatting_rules(purpose, target_format)

            messages = [
                {
                    "role": "system",
                    "content": f"You are an expert in formatting content for Claude Code SDK. Format the content according to these rules: {formatting_rules}"
                },
                {
                    "role": "user",
                    "content": f"Format this content for {purpose} in {target_format} format:\n\n{content}"
                }
            ]

            formatted_result = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=800,
                temperature=0.2  # Low temperature for consistent formatting
            )

            if not formatted_result:
                return {"error": "Failed to format content"}

            # Parse and validate the formatted result
            validated_result = self._validate_formatted_content(formatted_result, target_format)

            return {
                "original_content": content,
                "formatted_content": validated_result,
                "purpose": purpose,
                "target_format": target_format,
                "formatting_applied": True
            }

        except Exception as e:
            logger.error(f"Content formatting failed: {e}")
            return {"error": f"Content formatting failed: {str(e)}"}

    async def translate_voice_to_claude(
        self,
        voice_input: str,
        intent: str = "general",
        context_window: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate voice input to Claude Code SDK compatible format.

        Args:
            voice_input: Raw voice input text
            intent: Intended action or purpose
            context_window: Additional context for translation

        Returns:
            Dictionary containing translated input and metadata.
        """
        try:
            # Clean and preprocess voice input
            cleaned_input = self._preprocess_voice_input(voice_input)

            # Analyze intent and extract entities
            intent_analysis = await self._analyze_voice_intent(cleaned_input, intent)

            # Generate Claude SDK compatible command/query
            claude_command = await self._generate_claude_command(cleaned_input, intent_analysis, context_window)

            return {
                "original_voice_input": voice_input,
                "cleaned_input": cleaned_input,
                "intent_analysis": intent_analysis,
                "claude_command": claude_command,
                "context_window": context_window,
                "translation_confidence": self._calculate_translation_confidence(intent_analysis)
            }

        except Exception as e:
            logger.error(f"Voice to Claude translation failed: {e}")
            return {"error": f"Voice to Claude translation failed: {str(e)}"}

    async def get_context_recommendations(
        self,
        current_task: str,
        context_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Get context recommendations for better Claude SDK integration.

        Args:
            current_task: Current task description
            context_history: Previous context interactions

        Returns:
            Dictionary containing context recommendations.
        """
        try:
            # Analyze current task
            task_analysis = await self._analyze_task_context(current_task)

            # Review context history
            history_analysis = self._analyze_context_history(context_history or [])

            # Generate recommendations
            recommendations = await self._generate_context_recommendations(
                task_analysis, history_analysis
            )

            return {
                "current_task": current_task,
                "task_analysis": task_analysis,
                "history_analysis": history_analysis,
                "recommendations": recommendations,
                "optimal_context_size": self._calculate_optimal_context_size(task_analysis),
                "suggested_inclusions": self._suggest_context_inclusions(task_analysis, history_analysis)
            }

        except Exception as e:
            logger.error(f"Context recommendation failed: {e}")
            return {"error": f"Context recommendation failed: {str(e)}"}

    def _get_bridge_system_prompt(self, voice_optimized: bool, tool_analysis: Dict[str, Any]) -> str:
        """Get system prompt for bridge processing."""
        base_prompt = self.prompts.get("system",
            "You are a bridge between voice systems and Claude Code SDK, providing context-aware assistance.")

        if voice_optimized:
            base_prompt += " Optimize your response for voice output - use clear, concise language that's easy to understand when spoken."

        if tool_analysis.get("requires_tools", False):
            base_prompt += " The user's request requires Claude Code SDK tools. Provide specific tool recommendations and usage instructions."

        return base_prompt

    def _format_bridge_prompt(self, request: str, context: Dict[str, Any], tool_analysis: Dict[str, Any]) -> str:
        """Format the bridge prompt."""
        template = self.prompts.get("user_template",
            "Context: {context}\n\nUser request: {request}\n\nProvide assistance:")

        # Format context for inclusion
        formatted_context = self._format_context_for_prompt(context)

        prompt = template.format(context=formatted_context, request=request)

        if tool_analysis.get("requires_tools", False):
            prompt += f"\n\nRequired tools: {', '.join(tool_analysis.get('required_tools', []))}"
            prompt += "\nProvide specific guidance on using these Claude Code SDK tools."

        return prompt

    async def _enrich_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich context with additional information."""
        enriched = context.copy()

        # Add timestamp if not present
        if "timestamp" not in enriched:
            enriched["timestamp"] = datetime.now().isoformat()

        # Add system information
        enriched["system_info"] = {
            "platform": "Hypr-Voice Helper Agent",
            "version": "1.0.0",
            "available_tools": list(self.claude_sdk_tools.keys())
        }

        # Add recent context if available
        if "session_id" in enriched:
            recent_context = self._get_recent_context(enriched["session_id"])
            if recent_context:
                enriched["recent_context"] = recent_context

        return enriched

    async def _analyze_tool_requirements(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if request requires Claude Code SDK tools."""
        # Simple keyword-based analysis for tool requirements
        tool_keywords = {
            "file_operations": ["file", "read", "write", "edit", "save", "open", "create", "delete"],
            "system_operations": ["run", "execute", "command", "terminal", "bash", "git", "install"],
            "development_tools": ["test", "lint", "debug", "build", "compile", "document"],
            "voice_specific": ["speak", "voice", "audio", "sound", "play", "record"]
        }

        request_lower = request.lower()
        required_tools = []

        for tool_category, keywords in tool_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                required_tools.append(tool_category)

        return {
            "requires_tools": len(required_tools) > 0,
            "required_tools": required_tools,
            "confidence": min(len(required_tools) * 0.25, 1.0)  # Simple confidence calculation
        }

    def _parse_bridge_response(self, response: str, tool_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure the bridge response."""
        structured = {
            "response": response,
            "actions": [],
            "claude_instructions": [],
            "voice_output": response
        }

        # Extract action items
        action_patterns = [
            r'(?:action|step|do this):\s*(.+?)(?=\n|$)',
            r'[-•*]\s*(.+?)(?=[-•*]|\n\n|$)',
            r'\d+\.\s*(.+?)(?=\n\d+\.|$)'
        ]

        for pattern in action_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE | re.DOTALL)
            if matches:
                structured["actions"] = [match.strip() for match in matches if len(match.strip()) > 5]
                break

        # Extract Claude SDK specific instructions
        if tool_analysis.get("requires_tools", False):
            claude_patterns = [
                r'(?:claude|sdk|tool):\s*(.+?)(?=\n|$)',
                r'(?:use|run|execute):\s*(.+?)(?=\n|$)'
            ]

            for pattern in claude_patterns:
                matches = re.findall(pattern, response, re.IGNORECASE | re.DOTALL)
                if matches:
                    structured["claude_instructions"] = [match.strip() for match in matches]
                    break

        return structured

    def _format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format context for inclusion in prompt."""
        context_parts = []

        # Add key context information
        if "application" in context:
            context_parts.append(f"Application: {context['application']}")

        if "task" in context:
            context_parts.append(f"Current task: {context['task']}")

        if "recent_context" in context:
            context_parts.append(f"Recent activity: {context['recent_context']}")

        if "user_preferences" in context:
            context_parts.append(f"Preferences: {context['user_preferences']}")

        return " | ".join(context_parts) if context_parts else "No specific context"

    def _generate_context_id(self, context: Dict[str, Any]) -> str:
        """Generate a context ID for storage."""
        # Simple hash-based ID generation
        context_str = json.dumps(context, sort_keys=True)
        return str(hash(context_str))[:16]

    def _store_context(self, context_id: str, context: Dict[str, Any], response: Dict[str, Any]):
        """Store context for future reference."""
        self.active_contexts[context_id] = {
            "context": context,
            "response": response,
            "timestamp": datetime.now(),
            "access_count": 0
        }

        # Limit stored contexts
        if len(self.active_contexts) > 100:
            # Remove oldest contexts
            sorted_contexts = sorted(
                self.active_contexts.items(),
                key=lambda x: x[1]["timestamp"]
            )
            for old_id, _ in sorted_contexts[:20]:
                del self.active_contexts[old_id]

    def _get_recent_context(self, session_id: str) -> Optional[str]:
        """Get recent context for a session."""
        # Find contexts for this session
        session_contexts = [
            ctx for ctx in self.active_contexts.values()
            if ctx["context"].get("session_id") == session_id
        ]

        if session_contexts:
            # Sort by timestamp and get the most recent
            latest = max(session_contexts, key=lambda x: x["timestamp"])
            latest["access_count"] += 1
            return latest["response"].get("response", "")

        return None

    def _format_action_suggestion_prompt(self, situation: str, goal: str, constraints: Optional[List[str]]) -> str:
        """Format action suggestion prompt."""
        prompt = f"Situation: {situation}\n\nGoal: {goal}\n\n"

        if constraints:
            prompt += f"Constraints: {', '.join(constraints)}\n\n"

        prompt += "Suggest specific Claude Code SDK actions to achieve this goal. "
        prompt += "Include tool names, parameters, and usage examples where appropriate."

        return prompt

    def _parse_action_suggestions(self, suggestions_text: str) -> List[Dict[str, Any]]:
        """Parse action suggestions from text."""
        suggestions = []

        # Look for structured suggestions
        patterns = [
            r'(?:tool|action|step)\s*(\d+):\s*(.+?)(?=(?:tool|action|step)\s*\d+|$)',
            r'[-•*]\s*(.+?)(?=[-•*]|\n\n|$)',
            r'\d+\.\s*(.+?)(?=\n\d+\.|$)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, suggestions_text, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        suggestion = match[1] if len(match) > 1 else match[0]
                    else:
                        suggestion = match

                    # Extract tool name if present
                    tool_name = self._extract_tool_name(suggestion)

                    suggestions.append({
                        "description": suggestion.strip(),
                        "tool": tool_name,
                        "priority": self._calculate_suggestion_priority(suggestion)
                    })

                if suggestions:
                    break

        return suggestions

    def _extract_tool_name(self, suggestion: str) -> Optional[str]:
        """Extract tool name from suggestion."""
        tool_patterns = [
            r'(?:use|tool|command):\s*(\w+)',
            r'\b(\w+)\s+(?:command|tool|function)',
        ]

        for pattern in tool_patterns:
            match = re.search(pattern, suggestion, re.IGNORECASE)
            if match:
                return match.group(1).lower()

        return None

    def _calculate_suggestion_priority(self, suggestion: str) -> str:
        """Calculate priority level for suggestion."""
        suggestion_lower = suggestion.lower()

        high_priority_keywords = ["immediately", "urgent", "critical", "essential", "required"]
        medium_priority_keywords = ["recommended", "suggested", "should", "advise"]

        if any(keyword in suggestion_lower for keyword in high_priority_keywords):
            return "high"
        elif any(keyword in suggestion_lower for keyword in medium_priority_keywords):
            return "medium"
        else:
            return "low"

    def _calculate_action_confidence(self, suggestions: List[Dict[str, Any]]) -> float:
        """Calculate confidence in action suggestions."""
        if not suggestions:
            return 0.0

        # Simple confidence based on number and specificity of suggestions
        base_confidence = min(len(suggestions) * 0.2, 0.8)

        # Boost confidence if suggestions have specific tools
        tool_specific = sum(1 for s in suggestions if s.get("tool"))
        tool_boost = (tool_specific / len(suggestions)) * 0.2

        return min(base_confidence + tool_boost, 1.0)

    def _get_formatting_rules(self, purpose: str, target_format: str) -> str:
        """Get formatting rules for content."""
        rules = []

        format_rules = {
            "json": "Use valid JSON format with proper escaping and structure",
            "markdown": "Use Markdown syntax with headers, lists, and code blocks",
            "plain": "Use plain text with clear separation and minimal formatting"
        }

        purpose_rules = {
            "query": "Format as a clear question or search query",
            "instruction": "Format as step-by-step instructions",
            "context": "Format as structured contextual information"
        }

        if target_format in format_rules:
            rules.append(format_rules[target_format])

        if purpose in purpose_rules:
            rules.append(purpose_rules[purpose])

        return " | ".join(rules)

    def _validate_formatted_content(self, content: str, target_format: str) -> str:
        """Validate and fix formatted content."""
        if target_format == "json":
            try:
                # Try to parse as JSON
                json.loads(content)
                return content
            except json.JSONDecodeError:
                # If invalid JSON, try to fix common issues
                return self._fix_json_format(content)
        elif target_format == "markdown":
            # Ensure proper Markdown formatting
            return self._fix_markdown_format(content)

        return content

    def _fix_json_format(self, content: str) -> str:
        """Fix common JSON formatting issues."""
        # Remove any non-JSON content
        json_start = content.find('{')
        json_end = content.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            content = content[json_start:json_end]

        # Try to fix common issues
        content = content.replace("'", '"')  # Single quotes to double quotes
        content = re.sub(r',\s*}', '}', content)  # Remove trailing commas
        content = re.sub(r',\s*]', ']', content)  # Remove trailing commas in arrays

        return content

    def _fix_markdown_format(self, content: str) -> str:
        """Fix common Markdown formatting issues."""
        # Ensure proper spacing for headers
        content = re.sub(r'^(#+)([^\s])', r'\1 \2', content, flags=re.MULTILINE)

        # Ensure proper list formatting
        content = re.sub(r'^([-*])([^\s])', r'\1 \2', content, flags=re.MULTILINE)

        return content

    def _preprocess_voice_input(self, voice_input: str) -> str:
        """Preprocess voice input for better translation."""
        # Clean up common voice recognition artifacts
        cleaned = voice_input.strip()

        # Remove filler words and repetitions
        filler_words = ["um", "uh", "like", "you know", "actually", "basically"]
        for filler in filler_words:
            cleaned = re.sub(rf'\b{filler}\b', '', cleaned, flags=re.IGNORECASE)

        # Fix common punctuation issues
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single
        cleaned = re.sub(r'([.!?])\1+', r'\1', cleaned)  # Multiple punctuation to single

        return cleaned.strip()

    async def _analyze_voice_intent(self, input_text: str, intent_hint: str) -> Dict[str, Any]:
        """Analyze intent from voice input."""
        messages = [
            {
                "role": "system",
                "content": "You are an expert at understanding user intent from voice input. Analyze the text and extract the user's intent, entities, and action type."
            },
            {
                "role": "user",
                "content": f"Analyze the intent of this voice input (hint: {intent_hint}): {input_text}"
            }
        ]

        analysis = await self.sglang_client.chat_completion(
            messages=messages,
            max_tokens=400,
            temperature=0.2
        )

        return {
            "raw_analysis": analysis or "",
            "intent_hint": intent_hint,
            "extracted_entities": self._extract_entities(input_text),
            "action_type": self._determine_action_type(input_text, intent_hint)
        }

    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text."""
        # Simple entity extraction (can be enhanced)
        entities = []

        # Look for file paths
        file_pattern = r'[/\\][\w/\\.-]+\.\w+'
        entities.extend(re.findall(file_pattern, text))

        # Look for URLs
        url_pattern = r'https?://[^\s]+'
        entities.extend(re.findall(url_pattern, text))

        # Look for quoted text
        quote_pattern = r'"([^"]+)"'
        entities.extend(re.findall(quote_pattern, text))

        return list(set(entities))  # Remove duplicates

    def _determine_action_type(self, text: str, intent_hint: str) -> str:
        """Determine the type of action requested."""
        text_lower = text.lower()

        action_keywords = {
            "create": ["create", "make", "new", "add", "generate"],
            "modify": ["change", "modify", "edit", "update", "fix"],
            "read": ["read", "show", "display", "get", "find", "search"],
            "delete": ["delete", "remove", "clean", "clear"],
            "execute": ["run", "execute", "start", "launch", "perform"]
        }

        for action_type, keywords in action_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return action_type

        return "general"

    async def _generate_claude_command(self, voice_input: str, intent_analysis: Dict[str, Any], context_window: Optional[str]) -> str:
        """Generate Claude SDK compatible command."""
        messages = [
            {
                "role": "system",
                "content": "Convert voice input to a clear, actionable command for Claude Code SDK. Be specific and actionable."
            },
            {
                "role": "user",
                "content": f"Convert this voice input to a Claude command: {voice_input}\n\n"
                f"Intent analysis: {intent_analysis.get('raw_analysis', '')}\n\n"
                f"Context: {context_window or 'None'}"
            }
        ]

        command = await self.sglang_client.chat_completion(
            messages=messages,
            max_tokens=300,
            temperature=0.3
        )

        return command or voice_input  # Fallback to original input

    def _calculate_translation_confidence(self, intent_analysis: Dict[str, Any]) -> float:
        """Calculate confidence in voice translation."""
        # Simple confidence based on analysis completeness
        if intent_analysis.get("raw_analysis"):
            return 0.8
        elif intent_analysis.get("action_type") != "general":
            return 0.6
        else:
            return 0.4

    async def _analyze_task_context(self, task: str) -> Dict[str, Any]:
        """Analyze task context."""
        return {
            "task_type": self._determine_task_type(task),
            "complexity": self._estimate_task_complexity(task),
            "keywords": self._extract_task_keywords(task),
            "estimated_duration": self._estimate_task_duration(task)
        }

    def _analyze_context_history(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze context history."""
        if not history:
            return {"status": "no_history"}

        return {
            "total_interactions": len(history),
            "recent_patterns": self._identify_patterns(history),
            "success_rate": self._calculate_success_rate(history),
            "common_tools": self._identify_common_tools(history)
        }

    async def _generate_context_recommendations(self, task_analysis: Dict[str, Any], history_analysis: Dict[str, Any]) -> List[str]:
        """Generate context recommendations."""
        recommendations = []

        # Task-based recommendations
        if task_analysis.get("complexity") == "high":
            recommendations.append("Include detailed background information")
            recommendations.append("Provide examples of similar completed tasks")

        # History-based recommendations
        if history_analysis.get("success_rate", 0) < 0.7:
            recommendations.append("Include more explicit instructions")
            recommendations.append("Break down into smaller, clearer steps")

        # Add general recommendations
        recommendations.extend([
            "Include current working directory and file context",
            "Specify desired output format",
            "Mention any constraints or requirements"
        ])

        return recommendations[:6]  # Limit to 6 recommendations

    def _determine_task_type(self, task: str) -> str:
        """Determine the type of task."""
        task_lower = task.lower()

        if any(word in task_lower for word in ["code", "programming", "develop", "implement"]):
            return "development"
        elif any(word in task_lower for word in ["write", "document", "explain"]):
            return "documentation"
        elif any(word in task_lower for word in ["test", "verify", "check"]):
            return "testing"
        elif any(word in task_lower for word in ["fix", "debug", "solve"]):
            return "troubleshooting"
        else:
            return "general"

    def _estimate_task_complexity(self, task: str) -> str:
        """Estimate task complexity."""
        complexity_indicators = {
            "high": ["complex", "difficult", "multiple", "several", "system"],
            "medium": ["implement", "create", "build", "design"],
            "low": ["simple", "basic", "quick", "easy"]
        }

        task_lower = task.lower()
        for complexity, indicators in complexity_indicators.items():
            if any(indicator in task_lower for indicator in indicators):
                return complexity

        return "medium"

    def _extract_task_keywords(self, task: str) -> List[str]:
        """Extract keywords from task."""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', task.lower())
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        return [word for word in words if word not in stop_words and len(word) > 2][:10]

    def _estimate_task_duration(self, task: str) -> str:
        """Estimate task duration."""
        word_count = len(task.split())

        if word_count < 10:
            return "5-15 minutes"
        elif word_count < 25:
            return "15-30 minutes"
        elif word_count < 50:
            return "30-60 minutes"
        else:
            return "1+ hours"

    def _identify_patterns(self, history: List[Dict[str, Any]]) -> List[str]:
        """Identify patterns in context history."""
        # Simple pattern identification
        patterns = []

        # Look for frequent task types
        task_types = [h.get("task_type", "unknown") for h in history]
        common_tasks = [task for task in set(task_types) if task_types.count(task) > 1]
        if common_tasks:
            patterns.append(f"Frequent task types: {', '.join(common_tasks)}")

        return patterns

    def _calculate_success_rate(self, history: List[Dict[str, Any]]) -> float:
        """Calculate success rate from history."""
        if not history:
            return 0.0

        successful = sum(1 for h in history if h.get("success", True))
        return successful / len(history)

    def _identify_common_tools(self, history: List[Dict[str, Any]]) -> List[str]:
        """Identify commonly used tools from history."""
        tools = []
        for h in history:
            if "tools_used" in h:
                tools.extend(h["tools_used"])

        # Count frequency
        tool_counts = {}
        for tool in tools:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

        # Return most common tools
        sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)
        return [tool for tool, count in sorted_tools[:5]]

    def _calculate_optimal_context_size(self, task_analysis: Dict[str, Any]) -> str:
        """Calculate optimal context size based on task analysis."""
        complexity = task_analysis.get("complexity", "medium")

        size_recommendations = {
            "low": "brief",
            "medium": "moderate",
            "high": "comprehensive"
        }

        return size_recommendations.get(complexity, "moderate")

    def _suggest_context_inclusions(self, task_analysis: Dict[str, Any], history_analysis: Dict[str, Any]) -> List[str]:
        """Suggest specific context inclusions."""
        inclusions = []

        # Task-based inclusions
        task_type = task_analysis.get("task_type", "general")
        if task_type == "development":
            inclusions.extend(["Current file contents", "Error messages", "Expected behavior"])
        elif task_type == "documentation":
            inclusions.extend(["Target audience", "Documentation style", "Key points to cover"])

        # History-based inclusions
        if history_analysis.get("common_tools"):
            inclusions.append(f"Previously used tools: {', '.join(history_analysis['common_tools'][:3])}")

        return inclusions[:5]  # Limit to 5 inclusions
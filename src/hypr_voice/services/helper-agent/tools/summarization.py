"""
Summarization Tools for Helper Agent

This module provides summarization capabilities optimized for voice agent applications.
"""

import logging
import re
from typing import Dict, Any, Optional, List
import json

from ..sglang_client import SGLangClient

logger = logging.getLogger(__name__)


class SummarizationTools:
    """
    Tools for text summarization optimized for voice agent output.

    Provides intelligent summarization with configurable length and focus areas.
    """

    def __init__(self, sglang_client: SGLangClient, prompts: Dict[str, Any]):
        """
        Initialize summarization tools.

        Args:
            sglang_client: Initialized SGLang client
            prompts: Prompts configuration dictionary
        """
        self.sglang_client = sglang_client
        self.prompts = prompts.get("summarization", {})
        self.default_max_length = 500

    async def summarize_text(
        self,
        text: str,
        max_length: int = 500,
        focus: Optional[str] = None,
        style: str = "voice_optimized"
    ) -> Dict[str, Any]:
        """
        Summarize text for voice agent consumption.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary in characters
            focus: Specific focus area (e.g., "technical", "actionable", "key_points")
            style: Summary style ("voice_optimized", "concise", "detailed")

        Returns:
            Dictionary containing summary and metadata.
        """
        try:
            if not text or not text.strip():
                return {"error": "No text provided for summarization"}

            # Prepare messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt(focus, style)
                },
                {
                    "role": "user",
                    "content": self._format_user_prompt(text, max_length, focus)
                }
            ]

            # Generate summary
            summary = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=min(1024, max_length * 2),  # Estimate tokens needed
                temperature=0.3  # Lower temperature for consistent summaries
            )

            if not summary:
                return {"error": "Failed to generate summary"}

            # Post-process summary for voice optimization
            processed_summary = self._post_process_summary(summary, max_length, style)

            # Extract key points if possible
            key_points = self._extract_key_points(processed_summary)

            return {
                "summary": processed_summary,
                "key_points": key_points,
                "original_length": len(text),
                "summary_length": len(processed_summary),
                "compression_ratio": len(processed_summary) / len(text),
                "focus": focus,
                "style": style,
                "tokens_used": len(summary.split())  # Rough estimate
            }

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return {"error": f"Summarization failed: {str(e)}"}

    async def summarize_multiple_texts(
        self,
        texts: List[str],
        max_length_per_summary: int = 200,
        overall_max_length: int = 800
    ) -> Dict[str, Any]:
        """
        Summarize multiple texts with individual and overall summaries.

        Args:
            texts: List of texts to summarize
            max_length_per_summary: Maximum length for each individual summary
            overall_max_length: Maximum length for overall summary

        Returns:
            Dictionary containing individual and overall summaries.
        """
        try:
            if not texts:
                return {"error": "No texts provided for summarization"}

            individual_summaries = []

            # Summarize each text individually
            for i, text in enumerate(texts):
                result = await self.summarize_text(
                    text=text,
                    max_length=max_length_per_summary,
                    focus="key_points",
                    style="concise"
                )

                if "error" not in result:
                    individual_summaries.append({
                        "index": i,
                        "summary": result["summary"],
                        "key_points": result["key_points"]
                    })
                else:
                    individual_summaries.append({
                        "index": i,
                        "error": result["error"]
                    })

            # Create overall summary
            combined_text = "\n\n".join([
                f"Text {i+1}: {text}" for i, text in enumerate(texts)
                if text.strip()
            ])

            overall_result = await self.summarize_text(
                text=combined_text,
                max_length=overall_max_length,
                focus="key_points",
                style="voice_optimized"
            )

            return {
                "individual_summaries": individual_summaries,
                "overall_summary": overall_result.get("summary", ""),
                "overall_key_points": overall_result.get("key_points", []),
                "total_texts": len(texts),
                "successful_summaries": len([s for s in individual_summaries if "error" not in s])
            }

        except Exception as e:
            logger.error(f"Multiple text summarization failed: {e}")
            return {"error": f"Multiple text summarization failed: {str(e)}"}

    async def extract_key_information(
        self,
        text: str,
        information_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Extract specific types of information from text.

        Args:
            text: Text to analyze
            information_types: Types of information to extract
                (e.g., ["actions", "dates", "people", "technical_terms"])

        Returns:
            Dictionary containing extracted information.
        """
        try:
            if information_types is None:
                information_types = ["actions", "key_points", "decisions", "deadlines"]

            # Create extraction prompt
            extraction_prompt = self._create_extraction_prompt(text, information_types)

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at extracting specific types of information from text. Provide structured, accurate extractions."
                },
                {
                    "role": "user",
                    "content": extraction_prompt
                }
            ]

            result = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=800,
                temperature=0.2  # Low temperature for accurate extraction
            )

            if not result:
                return {"error": "Failed to extract information"}

            # Parse the extraction result
            extracted_info = self._parse_extraction_result(result, information_types)

            return {
                "extracted_information": extracted_info,
                "information_types": information_types,
                "original_text_length": len(text)
            }

        except Exception as e:
            logger.error(f"Information extraction failed: {e}")
            return {"error": f"Information extraction failed: {str(e)}"}

    def _get_system_prompt(self, focus: Optional[str], style: str) -> str:
        """Get system prompt based on focus and style."""
        base_prompt = self.prompts.get("system",
            "You are a helpful assistant that creates concise, accurate summaries optimized for voice output.")

        focus_prompts = {
            "technical": " Focus on technical concepts, terminology, and implementation details.",
            "actionable": " Focus on action items, tasks, and concrete next steps.",
            "key_points": " Focus on the most important points and main ideas.",
            "decisions": " Focus on decisions made and their implications."
        }

        style_prompts = {
            "voice_optimized": " Use clear, simple language that's easy to speak and understand. Avoid complex sentence structures and technical jargon unless necessary.",
            "concise": " Be extremely brief and to the point. Use bullet points or short sentences.",
            "detailed": " Provide comprehensive coverage while maintaining clarity."
        }

        prompt = base_prompt
        if focus and focus in focus_prompts:
            prompt += focus_prompts[focus]
        if style in style_prompts:
            prompt += style_prompts[style]

        return prompt

    def _format_user_prompt(self, text: str, max_length: int, focus: Optional[str]) -> str:
        """Format the user prompt for summarization."""
        template = self.prompts.get("user_template",
            "Please summarize the following text for a voice agent application:\n\n{text}\n\nSummary:")

        prompt = template.format(text=text)

        # Add length constraint
        prompt += f"\n\nPlease keep the summary under {max_length} characters."

        # Add focus instruction
        if focus:
            prompt += f" Focus on {focus.replace('_', ' ')}."

        return prompt

    def _post_process_summary(self, summary: str, max_length: int, style: str) -> str:
        """Post-process summary for voice optimization."""
        # Clean up common issues
        summary = summary.strip()

        # Remove extra whitespace
        summary = re.sub(r'\s+', ' ', summary)

        # Ensure it ends with proper punctuation
        if summary and summary[-1] not in '.!?':
            summary += '.'

        # Truncate if too long
        if len(summary) > max_length:
            # Try to truncate at sentence boundary
            truncated = summary[:max_length-3]
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')

            last_sentence_end = max(last_period, last_exclamation, last_question)
            if last_sentence_end > max_length * 0.7:  # Only cut at sentence if it's not too short
                summary = truncated[:last_sentence_end + 1]
            else:
                summary = truncated + '...'

        # Voice optimization for specific styles
        if style == "voice_optimized":
            # Expand abbreviations that might be unclear when spoken
            abbreviations = {
                r'\betc\.': 'et cetera',
                r'\bi\.e\.': 'that is',
                r'\be\.g\.': 'for example',
                r'\bvs\.': 'versus'
            }
            for abbr, expansion in abbreviations.items():
                summary = re.sub(abbr, expansion, summary, flags=re.IGNORECASE)

        return summary

    def _extract_key_points(self, summary: str) -> List[str]:
        """Extract key points from summary."""
        # Look for bullet points, numbered lists, or sentences with key indicators
        key_points = []

        # Split by common list markers
        list_patterns = [r'\d+\.\s*', r'[-•*]\s*', r'→\s*']

        for pattern in list_patterns:
            if re.search(pattern, summary):
                points = re.split(pattern, summary)
                key_points.extend([p.strip() for p in points if p.strip()])
                break
        else:
            # No explicit list, look for key indicator sentences
            sentences = re.split(r'[.!?]+', summary)
            key_indicators = ['important', 'key', 'critical', 'essential', 'main', 'primary']

            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and any(indicator in sentence.lower() for indicator in key_indicators):
                    key_points.append(sentence)

        # Limit to top 5 key points
        return key_points[:5]

    def _create_extraction_prompt(self, text: str, information_types: List[str]) -> str:
        """Create prompt for information extraction."""
        prompt = f"Extract the following types of information from the text:\n\n"

        for info_type in information_types:
            prompt += f"- {info_type.replace('_', ' ').title()}\n"

        prompt += f"\nText to analyze:\n\n{text}\n\n"
        prompt += "Provide the extracted information in a structured format using clear labels."

        return prompt

    def _parse_extraction_result(self, result: str, information_types: List[str]) -> Dict[str, List[str]]:
        """Parse the extraction result into structured information."""
        extracted = {info_type: [] for info_type in information_types}

        # Simple parsing - look for each information type in the result
        for info_type in information_types:
            pattern = rf"{info_type.replace('_', ' ').title()}.+?:\s*(.+?)(?=\n[A-Z]|$)"
            matches = re.findall(pattern, result, re.IGNORECASE | re.DOTALL)

            if matches:
                # Split by common separators and clean up
                items = []
                for match in matches:
                    items.extend([item.strip() for item in re.split(r'[,;•]', match) if item.strip()])
                extracted[info_type] = items[:10]  # Limit to 10 items per type

        return extracted
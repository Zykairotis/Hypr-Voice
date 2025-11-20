"""
Content Analysis Tools for Helper Agent

This module provides content analysis capabilities optimized for voice agent applications.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
import json

from ..sglang_client import SGLangClient

logger = logging.getLogger(__name__)


class AnalysisTools:
    """
    Tools for content analysis optimized for voice agent output.

    Provides intelligent analysis with voice optimization recommendations.
    """

    def __init__(self, sglang_client: SGLangClient, prompts: Dict[str, Any]):
        """
        Initialize analysis tools.

        Args:
            sglang_client: Initialized SGLang client
            prompts: Prompts configuration dictionary
        """
        self.sglang_client = sglang_client
        self.prompts = prompts.get("analysis", {})

    async def analyze_content(
        self,
        content: str,
        optimize_for_voice: bool = True,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze content for voice agent optimization.

        Args:
            content: Content to analyze
            optimize_for_voice: Whether to provide voice optimization recommendations
            analysis_type: Type of analysis ("comprehensive", "readability", "structure", "sentiment")

        Returns:
            Dictionary containing analysis and recommendations.
        """
        try:
            if not content or not content.strip():
                return {"error": "No content provided for analysis"}

            # Prepare analysis messages
            messages = [
                {
                    "role": "system",
                    "content": self._get_analysis_system_prompt(optimize_for_voice, analysis_type)
                },
                {
                    "role": "user",
                    "content": self._format_analysis_prompt(content, optimize_for_voice, analysis_type)
                }
            ]

            # Generate analysis
            analysis_result = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=1500,
                temperature=0.4  # Moderate temperature for analytical consistency
            )

            if not analysis_result:
                return {"error": "Failed to generate analysis"}

            # Parse and structure the analysis
            structured_analysis = self._parse_analysis_result(analysis_result, analysis_type)

            # Add quantitative metrics
            metrics = self._calculate_content_metrics(content)

            # Add voice optimization suggestions if requested
            voice_recommendations = None
            if optimize_for_voice:
                voice_recommendations = await self._generate_voice_recommendations(content)

            return {
                "analysis": structured_analysis,
                "metrics": metrics,
                "voice_optimization": voice_recommendations,
                "analysis_type": analysis_type,
                "content_length": len(content),
                "optimize_for_voice": optimize_for_voice,
                "tokens_used": len(analysis_result.split())
            }

        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return {"error": f"Content analysis failed: {str(e)}"}

    async def check_readability(
        self,
        content: str,
        target_audience: str = "general"
    ) -> Dict[str, Any]:
        """
        Check readability and provide improvement suggestions.

        Args:
            content: Content to check
            target_audience: Target audience ("general", "technical", "executive", "educational")

        Returns:
            Dictionary containing readability analysis and suggestions.
        """
        try:
            # Calculate readability metrics
            readability_metrics = self._calculate_readability_metrics(content)

            # Generate readability improvement suggestions
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert in content readability and clear communication. Provide specific, actionable suggestions to improve text clarity."
                },
                {
                    "role": "user",
                    "content": self._format_readability_prompt(content, target_audience, readability_metrics)
                }
            ]

            suggestions = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=800,
                temperature=0.3
            )

            if not suggestions:
                return {"error": "Failed to generate readability suggestions"}

            return {
                "readability_score": readability_metrics["overall_score"],
                "metrics": readability_metrics,
                "suggestions": self._parse_suggestions(suggestions),
                "target_audience": target_audience,
                "improvement_priority": self._calculate_improvement_priority(readability_metrics)
            }

        except Exception as e:
            logger.error(f"Readability check failed: {e}")
            return {"error": f"Readability check failed: {str(e)}"}

    async def analyze_sentiment(
        self,
        content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment and emotional tone of content.

        Args:
            content: Content to analyze
            context: Additional context for sentiment analysis

        Returns:
            Dictionary containing sentiment analysis.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at analyzing sentiment and emotional tone in text. Provide nuanced analysis considering context and subtext."
                },
                {
                    "role": "user",
                    "content": self._format_sentiment_prompt(content, context)
                }
            ]

            sentiment_result = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=600,
                temperature=0.2  # Low temperature for consistent sentiment analysis
            )

            if not sentiment_result:
                return {"error": "Failed to analyze sentiment"}

            # Parse sentiment analysis
            sentiment_data = self._parse_sentiment_result(sentiment_result)

            # Add keyword-based sentiment validation
            keyword_sentiment = self._analyze_sentiment_keywords(content)

            return {
                "sentiment": sentiment_data,
                "keyword_validation": keyword_sentiment,
                "context": context,
                "confidence": self._calculate_sentiment_confidence(sentiment_data, keyword_sentiment)
            }

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"error": f"Sentiment analysis failed: {str(e)}"}

    async def suggest_voice_improvements(
        self,
        content: str,
        voice_style: str = "conversational"
    ) -> Dict[str, Any]:
        """
        Suggest improvements for voice delivery.

        Args:
            content: Content to improve
            voice_style: Target voice style ("conversational", "professional", "energetic", "calm")

        Returns:
            Dictionary containing voice improvement suggestions.
        """
        try:
            # Analyze current content for voice-friendliness
            voice_issues = self._identify_voice_issues(content)

            # Generate improvement suggestions
            messages = [
                {
                    "role": "system",
                    "content": f"You are an expert in voice communication and speech optimization. Provide specific suggestions to make content more natural and effective when spoken in a {voice_style} style."
                },
                {
                    "role": "user",
                    "content": self._format_voice_improvement_prompt(content, voice_issues, voice_style)
                }
            ]

            improvements = await self.sglang_client.chat_completion(
                messages=messages,
                max_tokens=1000,
                temperature=0.4
            )

            if not improvements:
                return {"error": "Failed to generate voice improvements"}

            return {
                "current_issues": voice_issues,
                "suggested_improvements": self._parse_voice_improvements(improvements),
                "voice_style": voice_style,
                "improved_version": await self._generate_improved_version(content, voice_style),
                "delivery_notes": self._generate_delivery_notes(content, voice_style)
            }

        except Exception as e:
            logger.error(f"Voice improvement analysis failed: {e}")
            return {"error": f"Voice improvement analysis failed: {str(e)}"}

    def _get_analysis_system_prompt(self, optimize_for_voice: bool, analysis_type: str) -> str:
        """Get system prompt for content analysis."""
        base_prompt = self.prompts.get("system",
            "You are a content analysis expert specializing in optimizing text for voice output.")

        if optimize_for_voice:
            base_prompt += " Pay special attention to how the content will sound when spoken and provide specific voice optimization recommendations."

        type_prompts = {
            "comprehensive": " Provide a thorough analysis covering structure, clarity, tone, and effectiveness.",
            "readability": " Focus on readability, clarity, and comprehension.",
            "structure": " Analyze the organization, flow, and logical structure.",
            "sentiment": " Focus on emotional tone, sentiment, and impact."
        }

        if analysis_type in type_prompts:
            base_prompt += type_prompts[analysis_type]

        return base_prompt

    def _format_analysis_prompt(self, content: str, optimize_for_voice: bool, analysis_type: str) -> str:
        """Format the analysis prompt."""
        template = self.prompts.get("user_template",
            "Analyze the following content:\n\n{text}\n\nAnalysis:")

        prompt = template.format(text=content)

        if optimize_for_voice:
            prompt += "\n\nProvide specific recommendations for making this content more suitable for voice delivery."

        return prompt

    def _parse_analysis_result(self, result: str, analysis_type: str) -> Dict[str, Any]:
        """Parse and structure the analysis result."""
        # Try to extract structured information from the result
        structured = {
            "overall_assessment": "",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "detailed_analysis": result
        }

        # Look for specific patterns in the result
        sections = {
            "strengths": r"(?:strengths?|positive aspects?|what works well)[:\s]*([^-\n]+(?:\n[^-\n]+)*)",
            "weaknesses": r"(?:weaknesses?|areas for improvement|issues)[:\s]*([^-\n]+(?:\n[^-\n]+)*)",
            "recommendations": r"(?:recommendations?|suggestions?|improvements?)[:\s]*([^-\n]+(?:\n[^-\n]+)*)"
        }

        for section, pattern in sections.items():
            matches = re.findall(pattern, result, re.IGNORECASE | re.DOTALL)
            if matches:
                # Split by bullet points or numbered lists
                items = re.split(r'[-•*\d+.)]\s*', matches[0])
                items = [item.strip() for item in items if item.strip() and len(item) > 10]
                structured[section] = items[:5]  # Limit to 5 items per section

        # Extract overall assessment (first paragraph or first few sentences)
        lines = result.split('\n')
        for line in lines:
            if line.strip() and not line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                structured["overall_assessment"] = line.strip()
                break

        return structured

    def _calculate_content_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate quantitative content metrics."""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = content.split()
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # Calculate average sentence length
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

        # Calculate vocabulary complexity (unique words / total words)
        unique_words = set(word.lower().strip('.,!?;:"()[]') for word in words)
        vocabulary_diversity = len(unique_words) / len(words) if words else 0

        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "vocabulary_diversity": round(vocabulary_diversity, 2),
            "avg_words_per_paragraph": round(len(words) / len(paragraphs), 1) if paragraphs else 0
        }

    async def _generate_voice_recommendations(self, content: str) -> Dict[str, Any]:
        """Generate voice-specific recommendations."""
        voice_issues = self._identify_voice_issues(content)

        if not voice_issues:
            return {"status": "optimal", "suggestions": []}

        messages = [
            {
                "role": "system",
                "content": "You are a voice communication expert. Provide specific, actionable suggestions to make text more natural and effective when spoken aloud."
            },
            {
                "role": "user",
                "content": f"The following text has these voice delivery issues: {', '.join(voice_issues)}\n\nText: {content}\n\nProvide specific improvements to address these issues."
            }
        ]

        suggestions = await self.sglang_client.chat_completion(
            messages=messages,
            max_tokens=600,
            temperature=0.4
        )

        return {
            "status": "needs_improvement",
            "issues_identified": voice_issues,
            "suggestions": self._parse_suggestions(suggestions) if suggestions else []
        }

    def _identify_voice_issues(self, content: str) -> List[str]:
        """Identify potential issues for voice delivery."""
        issues = []

        # Check for very long sentences
        sentences = re.split(r'[.!?]+', content)
        long_sentences = [s for s in sentences if len(s.split()) > 25]
        if long_sentences:
            issues.append("long_sentences")

        # Check for complex words or jargon
        complex_patterns = [
            r'\b\w{10,}\b',  # Long words
            r'[A-Z]{2,}',    # Acronyms
            r'\b\w+ization\b',  # Words ending in 'ization'
        ]
        for pattern in complex_patterns:
            if re.search(pattern, content):
                issues.append("complex_language")
                break

        # Check for numbers and symbols that might be hard to pronounce
        if re.search(r'\d+|\$|[%@#&*]', content):
            issues.append("numbers_symbols")

        # Check for nested parentheses or complex punctuation
        if re.search(r'\([^()]*\([^()]*\)', content):
            issues.append("complex_structure")

        # Check for abbreviations that might be unclear
        if re.search(r'\b[A-Z]\.[A-Z]\.', content):
            issues.append("abbreviations")

        return issues

    def _parse_suggestions(self, suggestions_text: str) -> List[str]:
        """Parse suggestions from text into a list."""
        # Split by common list markers
        suggestions = re.split(r'[-•*\d+.)]\s*', suggestions_text)
        suggestions = [s.strip() for s in suggestions if s.strip() and len(s) > 10]
        return suggestions[:8]  # Limit to 8 suggestions

    def _calculate_readability_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate readability metrics."""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = content.split()

        # Simple readability score based on sentence length and word length
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0

        # Normalize to 0-100 scale (higher is more readable)
        sentence_score = max(0, 100 - (avg_sentence_length - 15) * 2)  # Ideal ~15 words per sentence
        word_score = max(0, 100 - (avg_word_length - 5) * 10)  # Ideal ~5 characters per word

        overall_score = (sentence_score + word_score) / 2

        return {
            "overall_score": round(overall_score, 1),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_word_length": round(avg_word_length, 1),
            "sentence_score": round(sentence_score, 1),
            "word_score": round(word_score, 1)
        }

    def _format_readability_prompt(self, content: str, target_audience: str, metrics: Dict[str, Any]) -> str:
        """Format readability analysis prompt."""
        prompt = f"Analyze the readability of this content for a {target_audience} audience:\n\n{content}\n\n"
        prompt += f"Current metrics: Overall score {metrics['overall_score']}/100, "
        prompt += f"Average sentence length: {metrics['avg_sentence_length']} words, "
        prompt += f"Average word length: {metrics['avg_word_length']} characters.\n\n"
        prompt += "Provide specific, actionable suggestions to improve readability."

        return prompt

    def _calculate_improvement_priority(self, metrics: Dict[str, Any]) -> str:
        """Calculate improvement priority based on metrics."""
        if metrics["overall_score"] >= 80:
            return "low"
        elif metrics["overall_score"] >= 60:
            return "medium"
        else:
            return "high"

    def _format_sentiment_prompt(self, content: str, context: Optional[str]) -> str:
        """Format sentiment analysis prompt."""
        prompt = f"Analyze the sentiment and emotional tone of this content:\n\n{content}\n\n"

        if context:
            prompt += f"Context: {context}\n\n"

        prompt += "Provide: 1) Overall sentiment (positive/negative/neutral), 2) Emotional tone, 3) Key emotional indicators, 4) Confidence level."

        return prompt

    def _parse_sentiment_result(self, result: str) -> Dict[str, Any]:
        """Parse sentiment analysis result."""
        # Look for sentiment indicators
        sentiment_patterns = {
            "overall": r"(?:overall sentiment|sentiment)[:\s]*(positive|negative|neutral)",
            "tone": r"(?:tone|emotional tone)[:\s]*([^.!?]+)",
            "indicators": r"(?:indicators|key emotions)[:\s]*([^.!?]+)",
            "confidence": r"(?:confidence|certainty)[:\s]*(\d+%?\s*\d*/?\d*)"
        }

        parsed = {"raw_analysis": result}

        for key, pattern in sentiment_patterns.items():
            match = re.search(pattern, result, re.IGNORECASE)
            if match:
                parsed[key] = match.group(1).strip()

        return parsed

    def _analyze_sentiment_keywords(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment using keyword approach."""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'best', 'perfect', 'awesome']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'worst', 'poor', 'disappointing', 'frustrated', 'annoying']

        content_lower = content.lower()

        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)

        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "positive_words": positive_count,
            "negative_words": negative_count,
            "total_indicators": positive_count + negative_count
        }

    def _calculate_sentiment_confidence(self, ai_sentiment: Dict[str, Any], keyword_sentiment: Dict[str, Any]) -> float:
        """Calculate confidence in sentiment analysis."""
        # If both methods agree, high confidence
        if ai_sentiment.get("overall", "").lower() == keyword_sentiment.get("sentiment", ""):
            return 0.85

        # If keyword analysis found many indicators, moderate confidence
        if keyword_sentiment.get("total_indicators", 0) >= 3:
            return 0.70

        # Otherwise, lower confidence
        return 0.50

    def _format_voice_improvement_prompt(self, content: str, issues: List[str], voice_style: str) -> str:
        """Format voice improvement prompt."""
        prompt = f"Improve this content for {voice_style} voice delivery:\n\n{content}\n\n"

        if issues:
            prompt += f"Issues to address: {', '.join(issues)}\n\n"

        prompt += "Provide: 1) Specific improvements, 2) Rewritten examples, 3) Delivery suggestions"

        return prompt

    def _parse_voice_improvements(self, improvements_text: str) -> Dict[str, Any]:
        """Parse voice improvement suggestions."""
        return {
            "suggestions": self._parse_suggestions(improvements_text),
            "raw_text": improvements_text
        }

    async def _generate_improved_version(self, content: str, voice_style: str) -> str:
        """Generate an improved version of the content."""
        messages = [
            {
                "role": "system",
                "content": f"You are an expert in voice communication. Rewrite the given content to be more natural and effective when spoken in a {voice_style} style."
            },
            {
                "role": "user",
                "content": f"Rewrite this for voice delivery: {content}"
            }
        ]

        improved = await self.sglang_client.chat_completion(
            messages=messages,
            max_tokens=len(content) + 100,  # Allow some expansion
            temperature=0.5
        )

        return improved or content

    def _generate_delivery_notes(self, content: str, voice_style: str) -> List[str]:
        """Generate delivery notes for the content."""
        notes = []

        # Add style-specific notes
        style_notes = {
            "conversational": ["Speak naturally", "Use pauses effectively", "Maintain friendly tone"],
            "professional": ["Speak clearly", "Maintain steady pace", "Emphasize key points"],
            "energetic": ["Vary your pitch", "Use dynamic pace", "Show enthusiasm"],
            "calm": ["Speak slowly", "Use gentle tone", "Maintain steady rhythm"]
        }

        if voice_style in style_notes:
            notes.extend(style_notes[voice_style])

        # Add content-specific notes
        if '?' in content:
            notes.append("Raise pitch for questions")
        if '!' in content:
            notes.append("Add energy to exclamations")
        if re.search(r'\d+', content):
            notes.append("Speak numbers clearly")

        return notes[:6]  # Limit to 6 notes
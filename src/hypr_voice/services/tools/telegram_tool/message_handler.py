"""
Telegram Message Handler for Helper Agent

This module handles Telegram message processing, including message parsing,
content analysis, and integration with the Helper Agent system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import re
import json

try:
    from telegram import Update, Message
    from telegram.ext import ContextTypes, filters
    from telegram.constants import ParseMode
except ImportError:
    raise ImportError("python-telegram-bot is required for Telegram integration")

from ..helper_agent import HelperAgent
from ..config_loader import get_config

logger = logging.getLogger(__name__)


class TelegramMessageHandler:
    """
    Handles Telegram message processing for Helper Agent integration.

    Provides functionality to:
    - Process incoming messages
    - Extract content for analysis
    - Handle different message types
    - Format responses for Telegram
    - Manage conversation context
    """

    def __init__(self, helper_agent: Optional[HelperAgent] = None):
        """
        Initialize Telegram message handler.

        Args:
            helper_agent: Optional HelperAgent instance for processing
        """
        self.helper_agent = helper_agent
        self.conversation_contexts: Dict[str, Dict[str, Any]] = {}
        self.message_processors: Dict[str, Callable] = {}

        # Register default processors
        self._register_default_processors()

    def _register_default_processors(self):
        """Register default message processors."""
        self.message_processors.update({
            "text": self._process_text_message,
            "document": self._process_document_message,
            "photo": self._process_photo_message,
            "command": self._process_command_message,
            "location": self._process_location_message,
            "contact": self._process_contact_message
        })

    async def process_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        custom_processor: Optional[Callable] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process an incoming Telegram message.

        Args:
            update: Telegram Update object
            context: Telegram context
            custom_processor: Optional custom processor function

        Returns:
            Dictionary containing processing results or None
        """
        try:
            if not update.message:
                logger.warning("No message in update")
                return None

            message = update.message
            message_type = self._get_message_type(message)
            chat_id = str(message.chat.id)

            # Extract message data
            message_data = self._extract_message_data(message, message_type)

            # Get or create conversation context
            conversation_context = self._get_conversation_context(chat_id)
            message_data["conversation_context"] = conversation_context

            # Process message
            if custom_processor:
                result = await custom_processor(message_data, update, context)
            elif message_type in self.message_processors:
                processor = self.message_processors[message_type]
                result = await processor(message_data, update, context)
            else:
                result = await self._process_generic_message(message_data, update, context)

            # Update conversation context
            if result:
                self._update_conversation_context(chat_id, message_data, result)

            return result

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None

    async def _process_text_message(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Process text messages."""
        text = message_data.get("text", "").strip()

        if not text:
            return None

        # Check if this is a request for helper agent processing
        if self._is_helper_agent_request(text):
            return await self._process_helper_agent_request(
                text, message_data, update, context
            )

        # Check for specific commands
        if text.lower().startswith(("summarize", "analyze", "plan", "help")):
            return await self._process_command_request(
                text, message_data, update, context
            )

        # Generic response
        return await self._generate_generic_response(
            text, message_data, update, context
        )

    async def _process_document_message(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Process document messages."""
        document = message_data.get("document", {})
        file_name = document.get("file_name", "")
        file_size = document.get("file_size", 0)
        mime_type = document.get("mime_type", "")

        # Check if it's a CSV file for special processing
        if file_name.lower().endswith('.csv'):
            return await self._process_csv_file(
                message_data, update, context
            )

        # Check if it's a text file
        if mime_type.startswith('text/') or file_name.lower().endswith(('.txt', '.md')):
            return await self._process_text_file(
                message_data, update, context
            )

        # Generic document processing
        response_text = (
            f"📄 I received your document: *{file_name}*\n"
            f"📊 Size: {file_size:,} bytes\n"
            f"🔍 Type: {mime_type}\n\n"
            "If you'd like me to analyze this file, please let me know what you need!"
        )

        return await self._send_response(response_text, update, context)

    async def _process_photo_message(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Process photo messages."""
        photo = message_data.get("photo", {})
        width = photo.get("width", 0)
        height = photo.get("height", 0)

        response_text = (
            f"📸 Nice photo! ({width}x{height})\n\n"
            "I can't directly analyze images yet, but I can help you with:\n"
            "• Text analysis and summarization\n"
            "• Task planning and organization\n"
            "• File processing (CSV, text files)\n\n"
            "Just let me know what you need help with!"
        )

        return await self._send_response(response_text, update, context)

    async def _process_command_message(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Process command messages."""
        text = message_data.get("text", "").lower()

        if text.startswith("/summarize"):
            return await self._handle_summarize_command(message_data, update, context)
        elif text.startswith("/analyze"):
            return await self._handle_analyze_command(message_data, update, context)
        elif text.startswith("/plan"):
            return await self._handle_plan_command(message_data, update, context)
        elif text.startswith("/help"):
            return await self._handle_help_command(message_data, update, context)
        else:
            return await self._handle_unknown_command(message_data, update, context)

    async def _process_location_message(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Process location messages."""
        location = message_data.get("location", {})
        latitude = location.get("latitude", 0)
        longitude = location.get("longitude", 0)

        response_text = (
            f"📍 Location received:\n"
            f"Latitude: {latitude}\n"
            f"Longitude: {longitude}\n\n"
            "I can help you with location-based tasks or information!"
        )

        return await self._send_response(response_text, update, context)

    async def _process_contact_message(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Process contact messages."""
        contact = message_data.get("contact", {})
        first_name = contact.get("first_name", "")
        phone_number = contact.get("phone_number", "")

        response_text = (
            f"👤 Contact received:\n"
            f"Name: {first_name}\n"
            f"Phone: {phone_number}\n\n"
            "Thanks for sharing your contact information!"
        )

        return await self._send_response(response_text, update, context)

    async def _process_generic_message(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Process generic messages."""
        response_text = (
            "🤖 I received your message!\n\n"
            "I can help you with:\n"
            "• 📝 Text summarization\n"
            "• 📊 Content analysis\n"
            "• 📋 Task planning\n"
            "• 🤖 Claude Code SDK integration\n\n"
            "Just send me text or files, or use /help for commands!"
        )

        return await self._send_response(response_text, update, context)

    async def _process_helper_agent_request(
        self,
        text: str,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Process requests for Helper Agent functionality."""
        if not self.helper_agent:
            return await self._send_response(
                "❌ Helper Agent is not available right now. Please try again later.",
                update, context
            )

        try:
            # Determine the type of request
            if self._is_summarization_request(text):
                result = await self.helper_agent.summarize_text(
                    text=text,
                    max_length=300,
                    focus="key_points"
                )
                return await self._format_summarization_result(result, update, context)

            elif self._is_analysis_request(text):
                result = await self.helper_agent.analyze_content(
                    content=text,
                    optimize_for_voice=True
                )
                return await self._format_analysis_result(result, update, context)

            elif self._is_planning_request(text):
                result = await self.helper_agent.plan_task(
                    task=text,
                    max_steps=5
                )
                return await self._format_planning_result(result, update, context)

            else:
                # Generic helper agent processing
                result = await self.helper_agent.bridge_to_claude_sdk(
                    request=text,
                    context=message_data.get("conversation_context", {}),
                    voice_optimized=False
                )
                return await self._format_claude_result(result, update, context)

        except Exception as e:
            logger.error(f"Error processing helper agent request: {e}")
            return await self._send_response(
                "❌ Sorry, I encountered an error while processing your request.",
                update, context
            )

    async def _process_csv_file(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Process CSV file uploads."""
        document = message_data.get("document", {})
        file_name = document.get("file_name", "")
        file_id = document.get("file_id", "")

        response_text = (
            f"📊 I received your CSV file: *{file_name}*\n\n"
            "I can help you with:\n"
            "• 📈 Data analysis and insights\n"
            "• 📋 Summary of key information\n"
            "• 🔍 Search for specific data\n"
            "• 📤 Export processed results\n\n"
            "What would you like me to do with this CSV file?"
        )

        # Store file info for later processing
        self._store_file_info(update.message.chat.id, {
            "file_id": file_id,
            "file_name": file_name,
            "file_type": "csv"
        })

        return await self._send_response(response_text, update, context)

    async def _process_text_file(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Process text file uploads."""
        document = message_data.get("document", {})
        file_name = document.get("file_name", "")

        response_text = (
            f"📄 I received your text file: *{file_name}*\n\n"
            "I can help you with:\n"
            "• 📝 Summarize the content\n"
            "• 🔍 Extract key information\n"
            "• 📊 Analyze for voice optimization\n"
            "• 🤖 Process with Claude Code SDK\n\n"
            "What would you like me to do with this file?"
        )

        return await self._send_response(response_text, update, context)

    async def _process_command_request(
        self,
        text: str,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """Process command-like requests in text messages."""
        # Remove command prefix and process
        command_text = re.sub(r'^/(summarize|analyze|plan|help)\s*', '', text.lower(), flags=re.IGNORECASE)

        if not command_text.strip():
            return await self._send_response(
                "Please provide some text or context for the command!",
                update, context
            )

        # Create a mock message with the command text
        mock_message_data = message_data.copy()
        mock_message_data["text"] = command_text

        if text.lower().startswith("/summarize"):
            return await self._process_helper_agent_request(
                f"Summarize: {command_text}", mock_message_data, update, context
            )
        elif text.lower().startswith("/analyze"):
            return await self._process_helper_agent_request(
                f"Analyze: {command_text}", mock_message_data, update, context
            )
        elif text.lower().startswith("/plan"):
            return await self._process_helper_agent_request(
                f"Plan: {command_text}", mock_message_data, update, context
            )
        else:
            return await self._process_helper_agent_request(
                command_text, mock_message_data, update, context
            )

    def _get_message_type(self, message: Message) -> str:
        """Get the type of a message."""
        if message.text:
            return "text"
        elif message.document:
            return "document"
        elif message.photo:
            return "photo"
        elif message.audio:
            return "audio"
        elif message.video:
            return "video"
        elif message.location:
            return "location"
        elif message.contact:
            return "contact"
        elif message.sticker:
            return "sticker"
        elif message.voice:
            return "voice"
        elif message.video_note:
            return "video_note"
        else:
            return "unknown"

    def _extract_message_data(self, message: Message, message_type: str) -> Dict[str, Any]:
        """Extract data from a Telegram message."""
        base_data = {
            "message_id": message.message_id,
            "chat_id": str(message.chat.id),
            "chat_type": message.chat.type,
            "date": message.date,
            "message_type": message_type,
            "from_user": {
                "id": message.from_user.id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name
            } if message.from_user else None
        }

        # Add type-specific data
        if message_type == "text":
            base_data["text"] = message.text
        elif message_type == "document":
            base_data["document"] = {
                "file_id": message.document.file_id,
                "file_name": message.document.file_name,
                "file_size": message.document.file_size,
                "mime_type": message.document.mime_type
            }
        elif message_type == "photo":
            photo = message.photo[-1]  # Highest resolution
            base_data["photo"] = {
                "file_id": photo.file_id,
                "width": photo.width,
                "height": photo.height,
                "file_size": photo.file_size
            }
        elif message_type == "location":
            base_data["location"] = {
                "latitude": message.location.latitude,
                "longitude": message.location.longitude
            }
        elif message_type == "contact":
            base_data["contact"] = {
                "phone_number": message.contact.phone_number,
                "first_name": message.contact.first_name,
                "last_name": message.contact.last_name,
                "user_id": message.contact.user_id
            }

        return base_data

    def _get_conversation_context(self, chat_id: str) -> Dict[str, Any]:
        """Get or create conversation context for a chat."""
        if chat_id not in self.conversation_contexts:
            self.conversation_contexts[chat_id] = {
                "chat_id": chat_id,
                "started_at": datetime.now(),
                "message_count": 0,
                "last_message_time": None,
                "topics_discussed": [],
                "files_shared": []
            }

        return self.conversation_contexts[chat_id]

    def _update_conversation_context(
        self,
        chat_id: str,
        message_data: Dict[str, Any],
        processing_result: Dict[str, Any]
    ):
        """Update conversation context with new message."""
        context = self.conversation_contexts.get(chat_id, {})

        context["message_count"] += 1
        context["last_message_time"] = datetime.now()

        # Track topics discussed
        if processing_result.get("analysis"):
            topics = processing_result["analysis"].get("key_topics", [])
            context["topics_discussed"].extend(topics)
            context["topics_discussed"] = list(set(context["topics_discussed"]))[-10:]  # Keep last 10

        # Track files shared
        if message_data.get("document") or message_data.get("photo"):
            file_info = {
                "type": message_data["message_type"],
                "name": (message_data.get("document", {}).get("file_name") or
                        message_data.get("photo", {}).get("file_id", "unknown")),
                "time": datetime.now()
            }
            context["files_shared"].append(file_info)
            context["files_shared"] = context["files_shared"][-20:]  # Keep last 20

    def _is_helper_agent_request(self, text: str) -> bool:
        """Check if text is a request for Helper Agent processing."""
        helper_keywords = [
            "summarize", "summarization", "summary",
            "analyze", "analysis", "analyze this",
            "plan", "planning", "help me plan",
            "claude", "code", "programming",
            "optimize", "improve", "suggest"
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in helper_keywords)

    def _is_summarization_request(self, text: str) -> bool:
        """Check if text is a summarization request."""
        summary_keywords = [
            "summarize", "summarization", "summary", "give me the gist",
            "main points", "key points", "in short", "briefly"
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in summary_keywords)

    def _is_analysis_request(self, text: str) -> bool:
        """Check if text is an analysis request."""
        analysis_keywords = [
            "analyze", "analysis", "what do you think", "tell me about",
            "break down", "explain", "what does this mean"
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in analysis_keywords)

    def _is_planning_request(self, text: str) -> bool:
        """Check if text is a planning request."""
        planning_keywords = [
            "plan", "planning", "how to", "steps to", "what should i do",
            "help me plan", "create a plan", "project plan"
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in planning_keywords)

    async def _send_response(
        self,
        text: str,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """Send a response message."""
        try:
            message = await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            return {
                "response_sent": True,
                "message_id": message.message_id,
                "response_text": text
            }
        except Exception as e:
            logger.error(f"Failed to send response: {e}")
            return {"response_sent": False, "error": str(e)}

    async def _format_summarization_result(
        self,
        result: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """Format summarization result for Telegram."""
        if "error" in result:
            return await self._send_response(
                f"❌ {result['error']}", update, context
            )

        summary = result.get("summary", "")
        original_length = result.get("original_length", 0)
        summary_length = result.get("summary_length", 0)

        response_text = (
            f"📝 **Summary**\n\n"
            f"{summary}\n\n"
            f"📊 *Stats:*\n"
            f"• Original: {original_length:,} characters\n"
            f"• Summary: {summary_length:,} characters\n"
            f"• Compression: {((summary_length/original_length)*100):.1f}%\n"
        )

        return await self._send_response(response_text, update, context)

    async def _format_analysis_result(
        self,
        result: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """Format analysis result for Telegram."""
        if "error" in result:
            return await self._send_response(
                f"❌ {result['error']}", update, context
            )

        analysis = result.get("analysis", {})
        assessment = analysis.get("overall_assessment", "Analysis completed")

        response_text = (
            f"🔍 **Content Analysis**\n\n"
            f"*Assessment:* {assessment}\n\n"
        )

        # Add voice optimization if available
        if result.get("voice_optimization"):
            voice_opt = result["voice_optimization"]
            status = voice_opt.get("status", "unknown")
            suggestions = voice_opt.get("suggestions", [])

            response_text += f"🎤 *Voice Optimization:* {status.title()}\n\n"
            if suggestions:
                response_text += "*Suggestions:*\n"
                for suggestion in suggestions[:3]:  # Limit to 3 suggestions
                    response_text += f"• {suggestion}\n"
                response_text += "\n"

        return await self._send_response(response_text, update, context)

    async def _format_planning_result(
        self,
        result: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """Format planning result for Telegram."""
        if "error" in result:
            return await self._send_response(
                f"❌ {result['error']}", update, context
            )

        steps = result.get("steps", [])
        total_time = result.get("total_estimated_time_formatted", "Unknown")

        response_text = f"📋 **Task Plan**\n\n"

        for step in steps[:5]:  # Limit to 5 steps for readability
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(step.get("priority", "medium"), "⚪")
            response_text += (
                f"{priority_emoji} *Step {step['step_number']}*\n"
                f"{step['description']}\n"
                f"⏱ {step['estimated_time']}\n\n"
            )

        if len(steps) > 5:
            remaining = len(steps) - 5
            response_text += f"... and {remaining} more steps\n\n"

        response_text += f"⏱ *Total estimated time:* {total_time}\n"

        return await self._send_response(response_text, update, context)

    async def _format_claude_result(
        self,
        result: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """Format Claude Code SDK result for Telegram."""
        if "error" in result:
            return await self._send_response(
                f"❌ {result['error']}", update, context
            )

        response = result.get("response", "")
        actions = result.get("actions", [])
        claude_instructions = result.get("claude_instructions", [])

        response_text = f"🤖 **Claude Code SDK Response**\n\n{response}\n\n"

        if actions:
            response_text += "🛠️ *Suggested Actions:*\n"
            for action in actions[:3]:  # Limit to 3 actions
                response_text += f"• {action}\n"
            response_text += "\n"

        return await self._send_response(response_text, update, context)

    def _store_file_info(self, chat_id: str, file_info: Dict[str, Any]):
        """Store file information for later processing."""
        if "files" not in self.conversation_contexts.get(chat_id, {}):
            self.conversation_contexts[chat_id]["files"] = []

        self.conversation_contexts[chat_id]["files"].append(file_info)

    # Command handlers
    async def _handle_summarize_command(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """Handle /summarize command."""
        response_text = (
            "📝 **Summarize Command**\n\n"
            "To summarize content, you can:\n\n"
            "1. **Send text directly** - I'll summarize it\n"
            "2. **Upload a file** - I'll summarize its contents\n"
            "3. **Reply with text** - Forward a message to summarize\n\n"
            "Example: `/summarize This is a long text that needs to be summarized into key points for easier understanding.`"
        )
        return await self._send_response(response_text, update, context)

    async def _handle_analyze_command(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """Handle /analyze command."""
        response_text = (
            "🔍 **Analyze Command**\n\n"
            "I can analyze content for:\n\n"
            "• 📊 Readability and clarity\n"
            "• 🎤 Voice optimization\n"
            "• 💭 Sentiment and tone\n"
            "• 📋 Structure and organization\n\n"
            "Just send me text or upload a file and I'll analyze it for you!"
        )
        return await self._send_response(response_text, update, context)

    async def _handle_plan_command(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """Handle /plan command."""
        response_text = (
            "📋 **Plan Command**\n\n"
            "I can help you plan:\n\n"
            "• 🎯 Projects and tasks\n"
            "• 📅 Workflows and processes\n"
            "• 🗂️ Step-by-step instructions\n"
            "• ⏰ Time estimates and priorities\n\n"
            "Example: `/plan Create a REST API for user authentication`"
        )
        return await self._send_response(response_text, update, context)

    async def _handle_help_command(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """Handle /help command."""
        response_text = (
            "🤖 **Helper Agent Bot Help**\n\n"
            "**📝 Available Commands:**\n"
            "• `/summarize` - Get help with summarization\n"
            "• `/analyze` - Learn about content analysis\n"
            "• `/plan` - Discover task planning\n"
            "• `/help` - Show this help message\n\n"
            "**📄 File Support:**\n"
            "• CSV files - Data analysis and insights\n"
            "• Text files - Summarization and analysis\n"
            "• Documents - Content processing\n\n"
            "**💬 Natural Language:**\n"
            "Just send me text like:\n"
            "• \"Summarize this article...\"\n"
            "• \"Analyze this content...\"\n"
            "• \"Help me plan...\"\n\n"
            "I'll understand and help you! 🚀"
        )
        return await self._send_response(response_text, update, context)

    async def _handle_unknown_command(
        self,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """Handle unknown commands."""
        response_text = (
            "❓ I didn't recognize that command.\n\n"
            "Use `/help` to see available commands,\n"
            "or just send me text to get started! 🚀"
        )
        return await self._send_response(response_text, update, context)

    async def _generate_generic_response(
        self,
        text: str,
        message_data: Dict[str, Any],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """Generate a generic response to text."""
        # Simple acknowledgment
        response_text = f"👍 Got it! You said: \"{text[:100]}{'...' if len(text) > 100 else ''}\"\n\n"
        response_text += (
            "How can I help you with this?\n\n"
            "I can:\n"
            "• 📝 Summarize it\n"
            "• 🔍 Analyze it\n"
            "• 📋 Plan next steps\n"
            "• 🤖 Process with Claude Code SDK\n\n"
            "Just let me know what you need! 💬"
        )

        return await self._send_response(response_text, update, context)

    def add_custom_processor(self, message_type: str, processor: Callable):
        """Add a custom message processor."""
        self.message_processors[message_type] = processor

    def get_conversation_stats(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a conversation."""
        context = self.conversation_contexts.get(chat_id)
        if not context:
            return None

        return {
            "chat_id": chat_id,
            "message_count": context["message_count"],
            "started_at": context["started_at"],
            "last_message_time": context["last_message_time"],
            "topics_discussed": len(context["topics_discussed"]),
            "files_shared": len(context["files_shared"])
        }
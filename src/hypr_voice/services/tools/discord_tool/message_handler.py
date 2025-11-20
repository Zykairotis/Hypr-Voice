"""
Discord Message Handler for Helper Agent

This module provides comprehensive message handling for Discord Bot integration,
enabling intelligent processing of user messages, commands, and file uploads.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
import discord
from discord.ext import commands

try:
    from ...helper_agent import HelperAgent
except ImportError:
    HelperAgent = None

logger = logging.getLogger(__name__)


class DiscordMessageHandler:
    """
    Comprehensive message handler for Discord Bot integration.

    Handles:
    - Text messages and commands
    - File uploads and processing
    - Context-aware responses
    - Helper Agent integration
    """

    def __init__(self, discord_client: 'DiscordClient', helper_agent: Optional[HelperAgent] = None):
        """
        Initialize Discord message handler.

        Args:
            discord_client: Initialized Discord client
            helper_agent: Optional Helper Agent instance
        """
        self.discord_client = discord_client
        self.helper_agent = helper_agent
        self.conversation_contexts: Dict[str, Dict[str, Any]] = {}
        self.message_processors: Dict[str, Callable] = {}
        self.response_queue = asyncio.Queue()

        # Message processing configuration
        self.max_message_length = 2000  # Discord limit
        self.max_context_messages = 10
        self.response_timeout = 30  # seconds

        # Initialize message processors
        self._initialize_processors()

    def _initialize_processors(self):
        """Initialize message processors for different content types."""
        self.message_processors = {
            'text': self._process_text_message,
            'command': self._process_command,
            'file': self._process_file_upload,
            'image': self._process_image_upload,
            'mention': self._process_mention,
            'reaction': self._process_reaction
        }

    async def handle_message(self, message: discord.Message) -> Optional[Dict[str, Any]]:
        """
        Handle incoming Discord message.

        Args:
            message: Discord message object

        Returns:
            Response dictionary or None if no response needed
        """
        try:
            # Skip bot messages
            if message.author.bot:
                return None

            # Get or create conversation context
            context = self._get_conversation_context(message)

            # Determine message type
            message_type = self._determine_message_type(message)

            # Process message based on type
            processor = self.message_processors.get(message_type, self._process_default)
            response = await processor(message, context)

            # Update conversation context
            self._update_conversation_context(message, context)

            # Log interaction
            logger.debug(f"Processed {message_type} message from {message.author.name} in {message.channel.name}")

            return response

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return await self._create_error_response("An error occurred while processing your message.")

    async def _process_text_message(self, message: discord.Message, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process regular text messages."""
        try:
            content = message.content.strip()
            if not content:
                return None

            # Check if this is a question or request
            is_question = self._is_question(content)
            is_request = self._is_request(content)

            if is_question or is_request:
                # Process with Helper Agent if available
                if self.helper_agent:
                    response = await self._process_with_helper_agent(content, context)
                else:
                    response = await self._generate_simple_response(content, context)

                return response

            # Add to conversation context
            context['messages'].append({
                'type': 'user',
                'content': content,
                'timestamp': message.created_at
            })

            return None  # No response needed for casual messages

        except Exception as e:
            logger.error(f"Error processing text message: {e}")
            return await self._create_error_response("Failed to process text message.")

    async def _process_command(self, message: discord.Message, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process Discord bot commands."""
        try:
            content = message.content.strip()
            if not content.startswith('!'):
                return None

            # Parse command
            parts = content[1:].split()
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            # Handle different commands
            if command == 'summarize':
                return await self._handle_summarize_command(args, message, context)
            elif command == 'analyze':
                return await self._handle_analyze_command(args, message, context)
            elif command == 'help':
                return await self._handle_help_command(message, context)
            elif command == 'voice':
                return await self._handle_voice_command(args, message, context)
            elif command == 'clear':
                return await self._handle_clear_command(message, context)
            else:
                return await self._create_response(
                    f"Unknown command: `{command}`. Type `!help` for available commands.",
                    message.channel.id
                )

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return await self._create_error_response("Failed to process command.")

    async def _process_file_upload(self, message: discord.Message, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process file uploads."""
        try:
            if not message.attachments:
                return None

            # Process first attachment
            attachment = message.attachments[0]

            # Check file size
            if attachment.size > self.discord_client.max_file_size_mb * 1024 * 1024:
                return await self._create_error_response(
                    f"File size exceeds {self.discord_client.max_file_size_mb}MB limit."
                )

            # Check file type
            if not self._is_allowed_file_type(attachment.filename):
                return await self._create_error_response(
                    "File type not supported. Please upload text, CSV, JSON, or markdown files."
                )

            # Download and process file
            file_content = await attachment.read()
            file_path = f"/tmp/discord_{attachment.filename}"

            with open(file_path, 'wb') as f:
                f.write(file_content)

            # Process file with Helper Agent if available
            if self.helper_agent:
                from .file_manager import DiscordFileManager
                file_manager = DiscordFileManager(self.discord_client.bot)
                analysis = await file_manager.analyze_file(file_path, attachment.filename)

                return await self._create_embed_response(
                    title=f"📄 File Analysis: {attachment.filename}",
                    description=analysis.get('summary', 'File processed successfully.'),
                    fields=[
                        ("File Type", attachment.content_type or "Unknown"),
                        ("Size", f"{attachment.size / 1024:.1f} KB"),
                        ("Lines", str(analysis.get('lines', 'N/A'))),
                        ("Characters", str(analysis.get('characters', 'N/A')))
                    ],
                    channel_id=message.channel.id
                )
            else:
                return await self._create_response(
                    f"File `{attachment.filename}` uploaded successfully. File analysis requires Helper Agent.",
                    message.channel.id
                )

        except Exception as e:
            logger.error(f"Error processing file upload: {e}")
            return await self._create_error_response("Failed to process file upload.")

    async def _process_image_upload(self, message: discord.Message, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process image uploads."""
        try:
            if not message.attachments:
                return None

            attachment = message.attachments[0]
            if not attachment.content_type or not attachment.content_type.startswith('image/'):
                return None

            return await self._create_embed_response(
                title="🖼️ Image Received",
                description="Image uploaded successfully. Image analysis not yet implemented.",
                fields=[
                    ("Filename", attachment.filename),
                    ("Size", f"{attachment.size / 1024:.1f} KB"),
                    ("URL", attachment.url)
                ],
                image_url=attachment.url,
                channel_id=message.channel.id
            )

        except Exception as e:
            logger.error(f"Error processing image upload: {e}")
            return await self._create_error_response("Failed to process image.")

    async def _process_mention(self, message: discord.Message, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process bot mentions."""
        try:
            if self.discord_client.bot.user not in message.mentions:
                return None

            # Extract message content without mention
            content = message.content.replace(f'<@!{self.discord_client.bot.user.id}>', '').strip()

            if not content:
                return await self._create_response(
                    "You mentioned me! How can I help you? Type `!help` for available commands.",
                    message.channel.id
                )

            # Process as regular text message
            return await self._process_text_message(message, context)

        except Exception as e:
            logger.error(f"Error processing mention: {e}")
            return None

    async def _process_reaction(self, message: discord.Message, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process message reactions."""
        # Currently just log reactions
        for reaction in message.reactions:
            logger.debug(f"Reaction {reaction.emoji} with {reaction.count} count")
        return None

    async def _process_default(self, message: discord.Message, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Default message processor."""
        return None

    async def _handle_summarize_command(self, args: List[str], message: discord.Message, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle !summarize command."""
        if not self.helper_agent:
            return await self._create_error_response("Summarization requires Helper Agent.")

        # Check if there's text to summarize
        if args:
            text = ' '.join(args)
        else:
            # Look for previous messages to summarize
            if len(context['messages']) > 1:
                text = ' '.join([msg['content'] for msg in context['messages'][-5:]])
            else:
                return await self._create_error_response("No text to summarize. Provide text after the command.")

        # Use Helper Agent summarization tools
        try:
            from ..tools.summarization import SummarizationTools
            summarizer = SummarizationTools(self.helper_agent.sglang_client, self.helper_agent.prompts)

            result = await summarizer.summarize_text(
                text=text,
                max_length=500,
                focus="key_points",
                style="voice_optimized"
            )

            if 'error' in result:
                return await self._create_error_response(f"Summarization failed: {result['error']}")

            return await self._create_embed_response(
                title="📝 Summary",
                description=result['summary'],
                fields=[
                    ("Original Length", str(result['original_length'])),
                    ("Summary Length", str(result['summary_length'])),
                    ("Compression", f"{result['compression_ratio']:.1%}")
                ],
                channel_id=message.channel.id
            )

        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            return await self._create_error_response("Failed to generate summary.")

    async def _handle_analyze_command(self, args: List[str], message: discord.Message, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle !analyze command."""
        # Check if there's a file attachment
        if not message.attachments:
            return await self._create_error_response("Please attach a file to analyze.")

        return await self._process_file_upload(message, context)

    async def _handle_help_command(self, message: discord.Message, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle !help command."""
        help_text = """
        **🤖 Helper Agent Bot Commands**

        **Text Processing:**
        • `!summarize <text>` - Summarize text content
        • `!analyze` - Analyze attached files

        **Voice Features:**
        • `!voice optimize <text>` - Optimize text for voice
        • `!voice script <topic>` - Generate voice script

        **Utility:**
        • `!help` - Show this help message
        • `!clear` - Clear conversation context

        **File Support:**
        • Text files (.txt, .md)
        • CSV files (.csv)
        • JSON files (.json)
        • Images (basic recognition)

        Simply mention the bot (@Helper Agent) to ask questions!
        """

        return await self._create_embed_response(
            title="Helper Agent Bot - Help",
            description=help_text,
            channel_id=message.channel.id,
            color=discord.Color.blue()
        )

    async def _handle_voice_command(self, args: List[str], message: discord.Message, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle !voice command."""
        if not args:
            return await self._create_error_response("Usage: `!voice <optimize|script> <text/topic>`")

        subcommand = args[0].lower()
        content = ' '.join(args[1:]) if len(args) > 1 else ""

        if subcommand == "optimize" and content:
            # Optimize text for voice
            optimized = self._optimize_for_voice(content)
            return await self._create_embed_response(
                title="🗣️ Voice Optimization",
                description="Text optimized for voice output:",
                fields=[("Original", content), ("Optimized", optimized)],
                channel_id=message.channel.id
            )
        elif subcommand == "script" and content:
            # Generate voice script
            script = self._generate_voice_script(content)
            return await self._create_embed_response(
                title="📜 Voice Script",
                description=f"Voice script for: {content}",
                fields=[("Script", script)],
                channel_id=message.channel.id
            )
        else:
            return await self._create_error_response("Invalid voice command. Usage: `!voice <optimize|script> <text/topic>`")

    async def _handle_clear_command(self, message: discord.Message, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle !clear command."""
        context_key = str(message.channel.id)
        if context_key in self.conversation_contexts:
            del self.conversation_contexts[context_key]

        return await self._create_response("✅ Conversation context cleared.", message.channel.id)

    def _get_conversation_context(self, message: discord.Message) -> Dict[str, Any]:
        """Get or create conversation context for a channel."""
        context_key = str(message.channel.id)

        if context_key not in self.conversation_contexts:
            self.conversation_contexts[context_key] = {
                'channel_id': message.channel.id,
                'guild_id': message.guild.id if message.guild else None,
                'user_id': message.author.id,
                'messages': [],
                'last_activity': datetime.utcnow(),
                'preferences': {}
            }

        return self.conversation_contexts[context_key]

    def _update_conversation_context(self, message: discord.Message, context: Dict[str, Any]):
        """Update conversation context with new message."""
        context['last_activity'] = datetime.utcnow()

        # Keep only recent messages
        if len(context['messages']) > self.max_context_messages:
            context['messages'] = context['messages'][-self.max_context_messages:]

    def _determine_message_type(self, message: discord.Message) -> str:
        """Determine the type of message."""
        if message.content.startswith('!'):
            return 'command'
        elif message.attachments:
            attachment = message.attachments[0]
            if attachment.content_type and attachment.content_type.startswith('image/'):
                return 'image'
            else:
                return 'file'
        elif self.discord_client.bot.user in message.mentions:
            return 'mention'
        elif message.reactions:
            return 'reaction'
        else:
            return 'text'

    def _is_question(self, text: str) -> bool:
        """Check if text is a question."""
        question_indicators = ['?', 'what', 'how', 'why', 'when', 'where', 'who', 'can', 'could', 'would', 'should']
        return any(indicator in text.lower() for indicator in question_indicators)

    def _is_request(self, text: str) -> bool:
        """Check if text is a request."""
        request_indicators = ['please', 'help', 'need', 'want', 'can you', 'could you', 'would you']
        return any(indicator in text.lower() for indicator in request_indicators)

    def _is_allowed_file_type(self, filename: str) -> bool:
        """Check if file type is allowed."""
        allowed_extensions = {'.txt', '.md', '.csv', '.json', '.yaml', '.yml', '.xml', '.log'}
        return any(filename.lower().endswith(ext) for ext in allowed_extensions)

    def _optimize_for_voice(self, text: str) -> str:
        """Optimize text for voice output."""
        # Simple voice optimization rules
        text = text.replace('e.g.', 'for example')
        text = text.replace('i.e.', 'that is')
        text = text.replace('etc.', 'et cetera')
        text = text.replace('&', 'and')
        text = text.replace('%', 'percent')
        text = text.replace('$', 'dollars')
        text = text.replace('#', 'number')

        # Add pauses for commas and periods
        text = text.replace(',', ', <pause>')
        text = text.replace('.', '. <pause>')

        return text

    def _generate_voice_script(self, topic: str) -> str:
        """Generate a simple voice script for a topic."""
        return f"""
        Welcome to this voice session about {topic}.

        Today, we'll explore the key aspects of {topic} and provide you with valuable insights.

        Let's begin with an introduction to {topic}...

        This is a basic script template. More sophisticated script generation can be added with additional development.
        """

    async def _process_with_helper_agent(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message using Helper Agent."""
        if not self.helper_agent:
            return await self._create_simple_response(content)

        try:
            # Create a formatted prompt with context
            context_messages = context.get('messages', [])
            context_text = '\n'.join([f"{msg['type']}: {msg['content']}" for msg in context_messages[-3:]])

            prompt = f"""
            Discord User Message: {content}

            Recent Context:
            {context_text}

            Please provide a helpful response that:
            1. Answers the user's question or addresses their request
            2. Is concise and conversational
            3. Is optimized for Discord chat format
            4. Includes relevant emojis where appropriate
            """

            # Process with Helper Agent
            response = await self.helper_agent.process_request(prompt)

            return await self._create_response(response, context['channel_id'])

        except Exception as e:
            logger.error(f"Error processing with Helper Agent: {e}")
            return await self._create_simple_response(content)

    async def _generate_simple_response(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a simple response without Helper Agent."""
        # Simple response logic
        if self._is_question(content):
            response = f"""🤔 That's an interesting question!

            I'm a basic Discord bot helper. To provide more sophisticated responses, I need the Helper Agent system to be fully configured.

            For now, I can help with:
            • File analysis and summarization
            • Basic text processing
            • Voice optimization
            • Conversation context management

            Try `!help` to see available commands!"""
        else:
            response = "👋 Thanks for your message! Type `!help` to see what I can do for you."

        return await self._create_response(response, context['channel_id'])

    async def _create_response(self, text: str, channel_id: int) -> Dict[str, Any]:
        """Create a simple text response."""
        return {
            'type': 'text',
            'channel_id': channel_id,
            'content': text,
            'timestamp': datetime.utcnow()
        }

    async def _create_embed_response(
        self,
        title: str,
        description: str,
        fields: Optional[List[tuple]] = None,
        channel_id: int = None,
        color: discord.Color = discord.Color.green(),
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an embed response."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )

        if fields:
            for name, value in fields:
                embed.add_field(name=name, value=value, inline=False)

        if image_url:
            embed.set_image(url=image_url)

        embed.set_footer(text="Helper Agent Bot")

        return {
            'type': 'embed',
            'channel_id': channel_id,
            'embed': embed,
            'timestamp': datetime.utcnow()
        }

    async def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response."""
        embed = discord.Embed(
            title="❌ Error",
            description=error_message,
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )

        return {
            'type': 'error',
            'embed': embed,
            'timestamp': datetime.utcnow()
        }

    async def _create_simple_response(self, content: str) -> Dict[str, Any]:
        """Create a simple response."""
        response = f"""🤖 **Helper Agent Response**

        {content}

        *Note: Advanced features require Helper Agent system integration.*
        """
        return {
            'type': 'text',
            'content': response,
            'timestamp': datetime.utcnow()
        }

    def get_conversation_history(self, channel_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a channel."""
        context_key = str(channel_id)
        context = self.conversation_contexts.get(context_key, {})
        return context.get('messages', [])[-limit:]

    def clear_conversation_context(self, channel_id: int):
        """Clear conversation context for a channel."""
        context_key = str(channel_id)
        if context_key in self.conversation_contexts:
            del self.conversation_contexts[context_key]

    def get_active_conversations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active conversation contexts."""
        active_conversations = {}
        for key, context in self.conversation_contexts.items():
            if datetime.utcnow() - context['last_activity'] < timedelta(hours=1):
                active_conversations[key] = context
        return active_conversations
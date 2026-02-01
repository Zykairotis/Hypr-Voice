# Bot Integrations Guide

## Overview

Hypr-Voice provides integration with popular chat platforms including Discord and Telegram. These integrations allow you to create voice-enabled AI assistants that can transcribe voice messages, process them with AI, and respond with text or synthesized speech.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Bot Integration Layer                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Bot Skills Layer                        │   │
│  │  - Discord Skills                                    │   │
│  │  - Telegram Skills                                   │   │
│  │  - Unified Bot Skills                                │   │
│  └─────────────┬────────────────────────────────────────┘   │
│                │                                             │
│         ┌──────┴──────┐                                     │
│         │ Bot Clients │                                     │
│         ├─────────────┤                                     │
│         │ Discord     │                                     │
│         │ Telegram    │                                     │
│         └──────┬──────┘                                     │
│                │                                             │
│  ┌─────────────┴────────────────────────────────────────┐   │
│  │              Core Services                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │   │
│  │  │   TTS    │ │  STT     │ │   AI     │ │             │   │
│  │  └──────────┘ └──────────┘ └──────────┘             │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Discord Integration

### Configuration

```bash
# Required: Discord Bot Token
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Get your bot token from:
# https://discord.com/developers/applications
```

### Getting Discord Bot Token

1. Visit https://discord.com/developers/applications
2. Create a new application
3. Go to "Bot" section
4. Click "Add Bot"
5. Copy the bot token
6. Enable necessary intents:
   - Message Content Intent
   - Server Members Intent
   - Guild Messages Intent

### Basic Discord Bot

```python
from hypr_voice.services.tools.discord_tool import DiscordClient

async def basic_discord_bot():
    # Initialize Discord client
    discord = DiscordClient(
        bot_token=os.getenv("DISCORD_BOT_TOKEN"),
        command_prefix="!"
    )

    # Initialize bot
    await discord.initialize()

    # Start bot (runs indefinitely)
    await discord.start()
```

### Sending Messages

```python
async def send_discord_message():
    discord = DiscordClient()
    await discord.initialize()

    # Send text message
    result = await discord.send_message(
        channel_id=123456789,
        text="Hello from Hypr-Voice!",
        embed=None  # Optional Discord embed
    )

    print(f"Message sent: {result['message_id']}")

    # Send with embed
    from discord import Embed
    embed = Embed(
        title="Voice Assistant",
        description="AI-powered voice transcription",
        color=0x00ff00
    )

    await discord.send_message(
        channel_id=123456789,
        text="Here's your transcription",
        embed=embed
    )
```

### Sending Files

```python
async def send_discord_file():
    discord = DiscordClient()
    await discord.initialize()

    # Send file
    result = await discord.send_file(
        channel_id=123456789,
        file_path="/path/to/audio.mp3",
        content="Here's the synthesized response"
    )

    print(f"File sent: {result['file_name']}")
```

### Reading Channel History

```python
async def read_discord_history():
    discord = DiscordClient()
    await discord.initialize()

    # Get channel history
    messages = await discord.get_channel_history(
        channel_id=123456789,
        limit=100  # Last 100 messages
    )

    for msg in messages:
        print(f"{msg['author']}: {msg['content']}")
```

### Discord Skills

```python
from hypr_voice.services.tools.claude_skills import DiscordSkills

async def discord_with_skills():
    discord = DiscordClient()
    await discord.initialize()

    skills = DiscordSkills(discord)

    # Transcribe voice message
    transcription = await skills.transcribe_voice_message(
        channel_id=123456789,
        message_id=987654321
    )

    # Process with AI
    response = await skills.process_with_ai(
        transcription['text']
    )

    # Synthesize response
    audio_path = await skills.synthesize_response(
        response['text']
    )

    # Send response
    await skills.send_voice_response(
        channel_id=123456789,
        audio_path=audio_path,
        text=response['text']
    )
```

## Telegram Integration

### Configuration

```bash
# Required: Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Get your bot token from BotFather:
# 1. Open Telegram and search for @BotFather
# 2. Send /newbot
# 3. Follow instructions to create bot
# 4. Copy the bot token
```

### Basic Telegram Bot

```python
from hypr_voice.services.tools.telegram_tool import TelegramClient

async def basic_telegram_bot():
    # Initialize Telegram client
    telegram = TelegramClient(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN")
    )

    # Initialize bot
    await telegram.initialize()

    # Start bot (runs indefinitely)
    await telegram.start()

    # Or use webhook
    await telegram.start(
        webhook_url="https://your-domain.com/webhook",
        port=8443
    )
```

### Sending Messages

```python
async def send_telegram_message():
    telegram = TelegramClient()
    await telegram.initialize()

    # Send text message
    result = await telegram.send_message(
        chat_id=123456789,  # User ID or group ID
        text="Hello from Hypr-Voice!",
        parse_mode="HTML"  # or "Markdown"
    )

    print(f"Message sent: {result['message_id']}")

    # Send with HTML formatting
    await telegram.send_message(
        chat_id=123456789,
        text="<b>Bold text</b> and <i>italic text</i>",
        parse_mode="HTML"
    )
```

### Sending Files

```python
async def send_telegram_file():
    telegram = TelegramClient()
    await telegram.initialize()

    # Send document
    result = await telegram.send_file(
        chat_id=123456789,
        file_path="/path/to/document.pdf",
        caption="Here's your document"
    )

    print(f"File sent: {result['file_name']}")
```

### Reading Chat History

```python
async def read_telegram_history():
    telegram = TelegramClient()
    await telegram.initialize()

    # Get chat history
    messages = await telegram.get_chat_history(
        chat_id=123456789,
        limit=100,
        offset=0
    )

    for msg in messages:
        print(f"{msg['from_user']}: {msg['text']}")
```

### Telegram Skills

```python
from hypr_voice.services.tools.claude_skills import TelegramSkills

async def telegram_with_skills():
    telegram = TelegramClient()
    await telegram.initialize()

    skills = TelegramSkills(telegram)

    # Transcribe voice message
    transcription = await skills.transcribe_voice_message(
        chat_id=123456789,
        message_id=987654321
    )

    # Process with AI
    response = await skills.process_with_ai(
        transcription['text']
    )

    # Synthesize response
    audio_path = await skills.synthesize_response(
        response['text']
    )

    # Send response
    await skills.send_voice_response(
        chat_id=123456789,
        audio_path=audio_path,
        caption=response['text']
    )
```

## Unified Bot Skills

### Configuration

```python
from hypr_voice.services.tools.claude_skills import UnifiedBotSkills

async def unified_bot_example():
    # Works with both Discord and Telegram
    skills = UnifiedBotSkills(
        discord_client=discord_client,
        telegram_client=telegram_client
    )

    # Platform-agnostic methods
    response = await skills.process_message(
        platform="discord",  # or "telegram"
        message_id=123456789,
        channel_id=123456789,
        text="Hello, bot!"
    )
```

### Voice Message Processing Pipeline

```python
async def voice_pipeline_discord():
    discord = DiscordClient()
    await discord.initialize()

    skills = DiscordSkills(discord)

    # Complete pipeline
    result = await skills.process_voice_message(
        channel_id=123456789,
        message_id=987654321,
        # Pipeline:
        # 1. Download audio
        # 2. Transcribe with Wispr Flow
        # 3. Process with Claude AI
        # 4. Synthesize with TTS
        # 5. Send response
    )

    print(f"Response: {result['text']}")
    print(f"Audio: {result['audio_path']}")
```

### Custom Commands

```python
from hypr_voice.services.tools.discord_tool import DiscordClient
from discord.ext import commands

async def custom_discord_commands():
    discord = DiscordClient(command_prefix="!")
    await discord.initialize()

    @discord.bot.command(name='transcribe')
    async def transcribe_command(ctx):
        """Transcribe voice message"""
        if ctx.message.attachments:
            # Download and transcribe
            from hypr_voice.services.tools.claude_skills import DiscordSkills
            skills = DiscordSkills(discord)

            transcription = await skills.transcribe_voice_message(
                ctx.channel.id,
                ctx.message.id
            )

            await ctx.send(f"Transcription: {transcription['text']}")

    @discord.bot.command(name='ask')
    async def ask_command(ctx, *, question):
        """Ask AI a question"""
        from hypr_voice.services.tools.claude_skills import DiscordSkills
        skills = DiscordSkills(discord)

        response = await skills.process_with_ai(question)
        await ctx.send(response['text'])

    await discord.start()
```

## Bot Integration Configuration

### Bot Integration Config

```python
from hypr_voice.services.tools.bot_integration_config import BotIntegrationConfig

config = BotIntegrationConfig(
    # Discord
    discord_token=os.getenv("DISCORD_BOT_TOKEN"),
    discord_command_prefix="!",
    discord_max_file_size_mb=8,

    # Telegram
    telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
    telegram_max_file_size_mb=20,

    # AI Processing
    enable_tts=True,
    tts_provider="kokoro",
    enable_stt=True,
    stt_provider="wispr_flow",

    # Claude AI
    claude_api_key=os.getenv("ANTHROPIC_API_KEY"),
    claude_model="claude-3-5-sonnet-20241022"
)
```

## Advanced Features

### File Management

```python
from hypr_voice.services.tools.discord_tool import FileManager

async def file_management_discord():
    discord = DiscordClient()
    await discord.initialize()

    file_manager = FileManager(discord)

    # Download file
    file_path = await file_manager.download_attachment(
        url="https://cdn.discordapp.com/attachments/...",
        destination="/tmp/downloaded_file.mp3"
    )

    # Upload file
    result = await file_manager.upload_file(
        channel_id=123456789,
        file_path="/tmp/audio.mp3",
        content="Here's your audio"
    )
```

### Authentication Management

```python
from hypr_voice.services.tools.discord_tool import AuthManager

async def auth_management():
    auth_manager = AuthManager()

    # Add user
    auth_manager.add_user(
        user_id=123456789,
        username="user123",
        permissions=["transcribe", "synthesize"]
    )

    # Check permissions
    if auth_manager.has_permission(123456789, "transcribe"):
        # Allow transcription
        pass

    # Remove user
    auth_manager.remove_user(123456789)
```

### Message Handling

```python
from hypr_voice.services.tools.discord_tool import MessageHandler

async def custom_message_handler():
    discord = DiscordClient()
    await discord.initialize()

    handler = MessageHandler(discord)

    # Register custom handler
    @handler.register()
    async def handle_voice_message(message):
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.startswith("audio/"):
                    # Process voice message
                    result = await process_voice(attachment)
                    return result

    # Start processing
    await handler.start()
```

## Integration Examples

### Discord Voice Assistant

```python
async def discord_voice_assistant():
    from hypr_voice.services.tools.discord_tool import DiscordClient
    from hypr_voice.services.tools.claude_skills import DiscordSkills

    # Setup
    discord = DiscordClient()
    await discord.initialize()

    skills = DiscordSkills(discord)

    # Event handler for voice messages
    @discord.bot.event
    async def on_message(message):
        if message.author.bot:
            return

        # Check for voice attachment
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.startswith("audio/"):
                    # Process voice message
                    result = await skills.process_voice_message(
                        message.channel.id,
                        message.id
                    )

                    # Send response
                    await skills.send_voice_response(
                        message.channel.id,
                        result['audio_path'],
                        result['text']
                    )

    await discord.start()
```

### Telegram Voice Assistant

```python
async def telegram_voice_assistant():
    from hypr_voice.services.tools.telegram_tool import TelegramClient
    from hypr_voice.services.tools.claude_skills import TelegramSkills

    # Setup
    telegram = TelegramClient()
    await telegram.initialize()

    skills = TelegramSkills(telegram)

    # Register voice handler
    @telegram.application.add_handler(
        MessageHandler(filters.VOICE, skills.handle_voice_message)
    )

    await telegram.start()
```

### Multi-Platform Bot

```python
async def multi_platform_bot():
    from hypr_voice.services.tools.discord_tool import DiscordClient
    from hypr_voice.services.tools.telegram_tool import TelegramClient
    from hypr_voice.services.tools.claude_skills import UnifiedBotSkills

    # Setup both platforms
    discord = DiscordClient()
    await discord.initialize()

    telegram = TelegramClient()
    await telegram.initialize()

    skills = UnifiedBotSkills(
        discord_client=discord,
        telegram_client=telegram
    )

    # Handle Discord messages
    @discord.bot.event
    async def on_message(message):
        if not message.author.bot:
            await skills.process_message(
                platform="discord",
                message_id=message.id,
                channel_id=message.channel.id,
                text=message.content
            )

    # Handle Telegram messages
    @telegram.application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, skills.handle_telegram_message)
    )

    # Start both bots
    await asyncio.gather(
        discord.start(),
        telegram.start()
    )
```

## Troubleshooting

### Discord Bot Not Responding

**Error**: Bot doesn't respond to commands

**Solution**:
```bash
# Check bot token
echo $DISCORD_BOT_TOKEN

# Verify bot is online
# Check Discord developer portal

# Check bot permissions
# Ensure bot has:
# - Read Messages
# - Send Messages
# - Read Message History
# - Attach Files
```

### Telegram Bot Not Working

**Error**: Bot doesn't receive updates

**Solution**:
```bash
# Check bot token
echo $TELEGRAM_BOT_TOKEN

# Test bot manually
curl https://api.telegram.org/bot<TOKEN>/getMe

# Check if webhook is set
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

### File Upload Failed

**Error**: File size exceeds limit

**Solution**:
```python
# Discord: 8MB limit (default)
# Telegram: 20MB limit (default)

# Compress file before sending
from pydub import AudioSegment

def compress_audio(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="mp3", bitrate="64k")
```

### Rate Limiting

**Error**: Rate limit exceeded

**Solution**:
```python
import asyncio

# Implement rate limiting
class RateLimiter:
    def __init__(self, calls_per_minute=30):
        self.calls_per_minute = calls_per_minute
        self.calls = []

    async def wait_if_needed(self):
        now = time.time()
        self.calls = [c for c in self.calls if now - c < 60]

        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0])
            await asyncio.sleep(sleep_time)

        self.calls.append(now)
```

## Best Practices

### 1. Handle Errors Gracefully

```python
try:
    result = await skills.process_voice_message(...)
except Exception as e:
    logger.error(f"Processing failed: {e}")
    await message.channel.send(
        "Sorry, I couldn't process that message. Please try again."
    )
```

### 2. Validate Input

```python
def validate_message(message):
    if not message.content:
        return False
    if len(message.content) > 4000:
        return False
    return True
```

### 3. Use Async Properly

```python
# Good
await asyncio.gather(
    task1(),
    task2(),
    task3()
)

# Bad (sequential)
await task1()
await task2()
await task3()
```

### 4. Monitor Performance

```python
import time

start = time.time()
result = await process_message(...)
duration = time.time() - start

logger.info(f"Processed in {duration:.2f}s")
```

### 5. Implement Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(text):
    return process_with_ai(text)
```

## API Reference

### DiscordClient

**Constructor Parameters**:
- `bot_token (str, optional)`: Discord bot token
- `command_prefix (str)`: Command prefix (default: "!")

**Methods**:
- `async initialize()`: Initialize bot
- `async start()`: Start bot
- `async stop()`: Stop bot
- `async send_message(channel_id, text, embed, file_path)`: Send message
- `async send_file(channel_id, file_path, content)`: Send file
- `async get_channel_history(channel_id, limit, before)`: Get history
- `async get_channel_info(channel_id)`: Get channel info
- `async get_guild_channels(guild_id)`: Get guild channels

### TelegramClient

**Constructor Parameters**:
- `bot_token (str, optional)`: Telegram bot token

**Methods**:
- `async initialize()`: Initialize bot
- `async start(webhook_url, port)`: Start bot
- `async stop()`: Stop bot
- `async send_message(chat_id, text, parse_mode, ...)`: Send message
- `async send_file(chat_id, file_path, caption)`: Send file
- `async get_chat_history(chat_id, limit, offset)`: Get history
- `async get_chat_info(chat_id)`: Get chat info

### DiscordSkills / TelegramSkills

**Methods**:
- `async transcribe_voice_message(...)`: Transcribe voice
- `async process_with_ai(text)`: Process with AI
- `async synthesize_response(text)`: Synthesize speech
- `async send_voice_response(...)`: Send voice response

## Related Documentation

- [Claude Integration](./claude-integration.md)
- [TTS Integration](./tts-integration.md)
- [Wispr Flow API](../api/wispr-flow-api.md)
- [Architecture Overview](./ARCHITECTURE.md)

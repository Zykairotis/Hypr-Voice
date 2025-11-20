# Telegram and Discord Bot Integration for Hypr-Voice

This comprehensive integration enables Claude Code SDK to interact with Telegram and Discord platforms through the Helper Agent system, allowing for cross-platform messaging, file processing, and intelligent response generation.

## Overview

The bot integration system provides:

- **Cross-Platform Messaging**: Send and receive messages on both Telegram and Discord
- **File Processing**: Upload, download, and analyze files (CSV, text, documents, images)
- **User Management**: Authentication, authorization, and permission management
- **Voice Optimization**: Text optimization for voice agent applications
- **Claude Code SDK Integration**: Unified interface for Claude to interact with both platforms
- **Security**: Rate limiting, user validation, and secure token management

## Architecture

```
Hypr-Voice Helper Agent System
├── services/tools/
│   ├── telegram_tool/           # Telegram Bot API integration
│   │   ├── telegram_client.py   # Main Telegram client
│   │   ├── message_handler.py   # Message processing
│   │   ├── file_manager.py      # File operations
│   │   └── auth_manager.py      # Authentication & security
│   ├── discord_tool/            # Discord Bot API integration
│   │   ├── discord_client.py    # Main Discord client
│   │   ├── message_handler.py   # Message processing
│   │   ├── file_manager.py      # File operations
│   │   └── auth_manager.py      # Authentication & security
│   ├── claude_skills/           # Claude Code SDK skills
│   │   ├── telegram_skills.py   # Telegram-specific skills
│   │   ├── discord_skills.py    # Discord-specific skills
│   │   └── unified_bot_skills.py # Cross-platform skills
│   └── bot_integration_config.py # Unified configuration
```

## Setup Instructions

### 1. Environment Configuration

Create or update your `.env` file with the following variables:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_ENABLED=true
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook  # Optional
TELEGRAM_WEBHOOK_PORT=8443  # Optional

# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_ENABLED=true
DISCORD_COMMAND_PREFIX=!
DISCORD_OWNER_IDS=123456789,987654321  # Optional: Owner user IDs

# General Bot Configuration
BOT_LOG_LEVEL=INFO
BOT_TEMP_DIR=/tmp/bot_files
HELPER_AGENT_ENABLED=true
CLEANUP_INTERVAL_HOURS=24
ENABLE_VOICE_FEATURES=true
ENABLE_FILE_PROCESSING=true
ENABLE_SUMMARIZATION=true

# Rate Limiting
TELEGRAM_RATE_LIMIT=30  # requests per minute
DISCORD_RATE_LIMIT=30   # requests per minute
```

### 2. Bot Creation

#### Telegram Bot Setup

1. **Create Bot with BotFather**:
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` command
   - Follow prompts to create your bot
   - Save the bot token provided

2. **Configure Bot**:
   - Set bot description and about text
   - Configure privacy settings (recommended: enabled)
   - Enable inline mode if needed
   - Set commands list

#### Discord Bot Setup

1. **Create Discord Application**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Give your application a name
   - Create the application

2. **Create Bot**:
   - Go to "Bot" tab
   - Click "Add Bot"
   - Customize bot username and avatar
   - Copy the bot token

3. **Configure Bot Permissions**:
   - Enable "Message Content Intent"
   - Enable "Server Members Intent"
   - Set required permissions:
     - Send Messages
     - Read Message History
     - Attach Files
     - Embed Links
     - Use External Emojis

4. **Invite Bot to Server**:
   - Go to "OAuth2" → "URL Generator"
   - Select bot scope
   - Select required permissions
   - Copy generated URL and invite bot to your server

### 3. Installation

1. **Install Dependencies**:
   ```bash
   cd /home/mewtwo/Zykairotis/Hypr-Voice
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create Configuration File**:
   ```bash
   mkdir -p config
   cp config/bot_integration.yaml.example config/bot_integration.yaml
   ```

3. **Update Configuration**:
   Edit `config/bot_integration.yaml` with your specific settings.

### 4. Running the Integration

#### Method 1: Using the Bot Integration Manager

```python
import asyncio
from src.Hypr.Voice.Agent.services.tools.bot_integration_config import create_bot_integration_manager

async def main():
    async with await create_bot_integration_manager() as manager:
        # Bot is now running
        print("Bot integration started successfully!")

        # Keep running
        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
```

#### Method 2: Using Claude Skills

```python
import asyncio
from src.Hypr.Voice.Agent.services.tools.claude_skills.unified_bot_skills import UnifiedBotSkills
from src.Hypr.Voice.Agent.services.tools.bot_integration_config import create_bot_integration_manager

async def main():
    # Initialize bot manager
    manager = await create_bot_integration_manager()
    await manager.start()

    # Initialize unified skills
    skills = UnifiedBotSkills(manager)

    # Send a message to Telegram
    result = await skills.execute_skill(
        "send_message",
        platform="telegram",
        chat_id=123456789,
        text="Hello from Claude Code SDK!"
    )
    print(f"Telegram result: {result}")

    # Send a message to Discord
    result = await skills.execute_skill(
        "send_message",
        platform="discord",
        chat_id=987654321,
        text="Hello from Claude Code SDK!"
    )
    print(f"Discord result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Claude Code SDK Usage

### Available Skills

#### Unified Skills (Cross-Platform)

1. **send_message**: Send messages to Telegram or Discord
2. **get_chat_history**: Retrieve message history
3. **send_file**: Upload files to chats/channels
4. **analyze_file**: Process and analyze uploaded files
5. **search_messages**: Search through message history
6. **cross_platform_search**: Search across multiple platforms
7. **broadcast_message**: Send messages to multiple platforms
8. **voice_optimization**: Optimize text for voice output

#### Platform-Specific Skills

**Telegram Skills**:
- `send_telegram_message`
- `get_telegram_chat_history`
- `send_telegram_file`
- `analyze_telegram_file`
- `manage_telegram_users`
- `telegram_bot_status`

**Discord Skills**:
- `send_discord_message`
- `get_discord_channel_history`
- `send_discord_file`
- `analyze_discord_file`
- `manage_discord_permissions`
- `list_discord_channels`
- `create_discord_embed`

### Usage Examples

#### Example 1: Send Message to Multiple Platforms

```python
# Using unified skills
result = await skills.execute_skill(
    "broadcast_message",
    message="Important announcement from Hypr-Voice!",
    platforms=["telegram", "discord"],
    chat_ids={
        "telegram": [123456789, 987654321],
        "discord": [111111111, 222222222]
    }
)
```

#### Example 2: Analyze Uploaded CSV File

```python
# Telegram file analysis
result = await skills.execute_skill(
    "analyze_file",
    platform="telegram",
    file_path="/tmp/telegram_file.csv",
    analysis_type="summary"
)

# Discord file analysis
result = await skills.execute_skill(
    "analyze_file",
    platform="discord",
    file_path="/tmp/discord_file.csv",
    analysis_type="structure"
)
```

#### Example 3: Search Messages

```python
# Search in Telegram
result = await skills.execute_skill(
    "search_messages",
    platform="telegram",
    chat_id=123456789,
    query="voice assistant",
    limit=20
)

# Cross-platform search
result = await skills.execute_skill(
    "cross_platform_search",
    query="machine learning",
    platforms=["telegram", "discord"],
    chat_ids={
        "telegram": 123456789,
        "discord": 111111111
    }
)
```

#### Example 4: Voice Optimization

```python
# Optimize text for voice
result = await skills.execute_skill(
    "voice_optimization",
    text="The AI model processes e.g. text and i.e. audio data with 99% accuracy.",
    optimization_type="pronunciation"
)

# Result will be: "The AI model processes for example text and that is audio data with ninety-nine percent accuracy."
```

## Configuration Options

### Complete Configuration File (config/bot_integration.yaml)

```yaml
# Telegram Configuration
telegram:
  bot_token: ${TELEGRAM_BOT_TOKEN}
  enabled: true
  max_file_size_mb: 20
  rate_limit_per_minute: 30
  authorized_users: []
  authorized_chats: []
  webhook_url: null
  webhook_port: 8443
  use_webhook: false

# Discord Configuration
discord:
  bot_token: ${DISCORD_BOT_TOKEN}
  enabled: true
  command_prefix: "!"
  max_file_size_mb: 8
  rate_limit_per_minute: 30
  owner_ids: []
  allowed_guilds: []
  require_guild_membership: true
  default_permission_level: "user"

# General Configuration
helper_agent_enabled: true
log_level: "INFO"
temp_directory: "/tmp/bot_files"
cleanup_interval_hours: 24
max_concurrent_users: 100
enable_voice_features: true
enable_file_processing: true
enable_summarization: true
```

## Security Considerations

### 1. Token Security
- Store bot tokens securely in environment variables
- Never commit tokens to version control
- Use `.env` files for local development
- Use secret management systems in production

### 2. User Authentication
- Only authorized users can interact with bots
- Configurable permission levels (user, moderator, admin, owner)
- Rate limiting prevents abuse
- Session management for user tracking

### 3. File Security
- File type validation
- File size limits
- Temporary file cleanup
- Virus scanning (can be added)

### 4. Privacy
- Message content is processed locally
- No data shared with third parties
- Configurable data retention policies
- User consent for data processing

## Monitoring and Logging

### 1. Bot Status Monitoring
```python
# Get overall status
status = await skills.execute_skill("get_platform_status")
print(f"Telegram status: {status['platforms']['telegram']}")
print(f"Discord status: {status['platforms']['discord']}")
```

### 2. Statistics and Metrics
- Message counts per platform
- File processing statistics
- User activity metrics
- Error tracking and reporting

### 3. Audit Logging
- All user actions logged
- Authentication events tracked
- File access recorded
- Permission changes documented

## Troubleshooting

### Common Issues

1. **Bot Token Invalid**
   - Verify token is correct
   - Check bot is created and active
   - Ensure token has required permissions

2. **Webhook Not Working**
   - Verify HTTPS certificate
   - Check firewall settings
   - Ensure port is accessible

3. **Discord Intents Missing**
   - Enable privileged intents in Discord Developer Portal
   - Update bot permissions
   - Re-invite bot to server

4. **File Upload Failing**
   - Check file size limits
   - Verify file type is supported
   - Ensure sufficient disk space

5. **Rate Limiting Issues**
   - Adjust rate limits in configuration
   - Implement user-specific limits
   - Add caching for repeated requests

### Debug Mode

Enable debug logging:

```bash
export BOT_LOG_LEVEL=DEBUG
```

Check logs for detailed error information.

## Advanced Features

### 1. Custom Commands
Add custom commands to message handlers:

```python
# Telegram custom command
async def custom_telegram_command(update, context):
    await update.message.reply_text("Custom response!")

# Discord custom command
@bot.command()
async def custom_discord_command(ctx):
    await ctx.send("Custom response!")
```

### 2. Webhook Integration
Set up webhooks for real-time message processing:

```python
# Configure webhook
await telegram_client.start(
    webhook_url="https://your-domain.com/webhook",
    port=8443
)
```

### 3. Database Integration
Store messages and user data in database:

```python
# Add database models for persistent storage
# Integrate with existing SQLAlchemy setup
```

### 4. AI Model Integration
Connect with custom AI models for enhanced processing:

```python
# Use custom voice models
# Integrate with Whisper for speech-to-text
# Add TTS for voice responses
```

## API Reference

### TelegramClient Methods
- `send_message(chat_id, text, **kwargs)`
- `send_file(chat_id, file_path, **kwargs)`
- `get_chat_history(chat_id, limit, offset)`
- `get_chat_info(chat_id)`

### DiscordClient Methods
- `send_message(channel_id, text, **kwargs)`
- `send_file(channel_id, file_path, **kwargs)`
- `get_channel_history(channel_id, limit, before)`
- `get_channel_info(channel_id)`
- `get_guild_channels(guild_id)`

### UnifiedBotSkills Methods
- `execute_skill(skill_name, **kwargs)`
- `get_available_skills()`
- `broadcast_message(message, platforms, chat_ids)`

## Support and Contributing

For support:
1. Check this documentation
2. Review logs for error details
3. Create issues in the project repository
4. Join the Discord community for discussions

To contribute:
1. Fork the repository
2. Create feature branches
3. Add tests for new functionality
4. Submit pull requests with documentation

## License

This integration is part of the Hypr-Voice project. See the main project license for details.
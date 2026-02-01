# Features Overview

Hypr-Voice is a powerful multi-agent voice orchestration system with Claude AI integration. This guide explains all the features available to you.

## Core Features

### 🎤 Voice Transcription (Speech-to-Text)

**Powered by Whisper** - State-of-the-art speech recognition

**Capabilities:**
- Real-time speech-to-text transcription
- Support for multiple languages and accents
- Custom vocabulary for technical terms
- Automatic punctuation and formatting
- Streaming transcription for long recordings

**Two Modes:**

1. **LOCAL Mode** (Default)
   - Uses hybrid Whisper server running locally
   - No API costs
   - Works offline after initial model download
   - Enhanced with custom vocabulary

2. **FLOW Mode** (Optional)
   - Uses Wispr Flow cloud API
   - Faster transcription speed
   - Better accuracy with personalized context
   - Requires internet connection

**Performance Features:**
- Opus audio compression (10x smaller files)
- Automatic chunking for long recordings
- Streaming chunking (processes while recording)
- Optimized chunk overlap for seamless transcription

### 🗣️ Text-to-Speech (Voice Synthesis)

**Multiple TTS Providers:**

1. **Deepgram** (Recommended)
   - Ultra-low latency (<500ms to first audio)
   - Natural sounding voices
   - Streaming support
   - Voice: "aura-luna-en" (default)

2. **ElevenLabs**
   - Highest quality voices
   - Emotional expression
   - Multiple voice options
   - Voice cloning available

3. **Kokoro-ONNX**
   - Local text-to-speech
   - No API costs
   - Fast inference
   - Multiple voice models

**Streaming TTS Features:**
- Pre-buffering for instant playback
- Minimum character threshold
- Maximum latency control
- Idle timeout management
- Automatic flush on completion

### 🤖 Multi-Agent AI System

**Specialized Agents:**

1. **Code Agent** (`code-worker`)
   - Code analysis and generation
   - Debugging and refactoring
   - Test writing and code review
   - Best practices enforcement

2. **Research Agent** (`research-worker`)
   - Information gathering
   - Documentation search
   - Pattern analysis
   - Report generation

3. **Shell Agent** (`shell-worker`)
   - System operations
   - File management
   - Service administration
   - Command automation

4. **Voice Agent** (`voice-worker`)
   - Natural conversation
   - Context-aware responses
   - Memory management
   - Multi-turn dialogue

5. **Enhanced Context Agent**
   - Window awareness (active application)
   - Clipboard integration
   - Workspace monitoring
   - Context-specific assistance

### 🧠 Context Awareness

**Hyprland Integration:**
- Detects active window title and class
- Understands current workspace
- Monitors clipboard content
- Provides contextual assistance

**Example Scenarios:**
- Coding: "Add error handling to this function"
- Terminal: "What does this command do?"
- Browser: "Summarize this article"
- File Manager: "Find all Python files in this directory"

### 🔌 Agent Tools

**File Operations:**
- Read - Read file contents
- Write - Create new files
- Edit - Edit existing files
- Glob - Find files by pattern
- Grep - Search file contents

**System Operations:**
- Bash - Execute shell commands
- LSP - Code intelligence features

**Web Access:**
- Tavily Search - Web search capabilities
- Context7 - Documentation lookup

## Web UI Features

### Dashboard Interface

**Panels:**

1. **Whisper Panel**
   - Voice recording controls
   - Real-time transcription display
   - Audio waveform visualization
   - Recording history
   - Vocabulary management

2. **Agent Panel**
   - AI chat interface
   - Message history
   - Agent selection
   - Tool usage display
   - Response streaming

3. **Orchestrator Panel**
   - Active agent sessions
   - Session management
   - Agent performance metrics
   - Conversation history

4. **Skills Library**
   - Browse available skills
   - Enable/disable skills
   - Skill documentation
   - Custom skill creation

5. **Vocabulary Dashboard**
   - Custom word list
   - Import/export vocabulary
   - Word frequency tracking
   - Domain-specific terms

6. **TTS Control Panel**
   - Voice selection
   - Speed/pitch controls
   - Volume adjustment
   - Test TTS functionality

7. **MCP Dashboard**
   - Protocol integrations
   - Connection status
   - Tool availability
   - Configuration management

8. **Analytics Dashboard**
   - Usage statistics
   - Performance metrics
   - Error tracking
   - Resource monitoring

### Real-time Features

**WebSocket Connections:**
- Live transcription streaming
- Real-time agent responses
- Instant status updates
- Event notifications

**Status Indicators:**
- Whisper server status
- Orchestrator status
- Agent availability
- Connection health

### Audio Mixer

**Features:**
- Microphone level adjustment
- Speaker volume control
- Audio device selection
- Noise reduction settings
- Audio visualization

## Command-Line Features

### Push-to-Talk

**F10 Keybinding:**
- Press F10 to start recording
- Release F10 to stop and process
- Audio feedback sounds
- Status notifications

**Configuration:**
```bash
# Configure in Hyprland
~/.config/hypr/hyprvoice.conf
```

### Voice Recording Script

**Script:** `./scripts/hypr-voice-record.sh`

**Features:**
- Manual voice recording
- Automatic transcription
- Direct text queries
- Duration settings
- Output format options

**Usage:**
```bash
# Record with default settings
./scripts/hypr-voice-record.sh

# Record for specific duration
./scripts/hypr-voice-record.sh --duration 30

# Send text query directly
./scripts/hypr-voice-record.sh --text "Your query here"
```

## Configuration Features

### Environment Variables

**Voice Settings:**
- `MODE` - LOCAL or FLOW transcription
- `WISPR_FLOW_USE_OPUS` - Enable Opus compression
- `WISPR_FLOW_CHUNK_SECONDS` - Chunk size for long audio
- `FLOW_STREAMING_MODE` - Enable streaming processing

**TTS Settings:**
- `HYPR_VOICE_TTS_STREAMING` - Enable streaming TTS
- `HYPR_VOICE_TTS_PREBUFFER_MS` - Pre-buffer duration
- `HYPR_VOICE_TTS_MIN_CHARS` - Minimum characters for TTS
- `HYPR_VOICE_TTS_MAX_LATENCY` - Maximum latency target

**Agent Settings:**
- `HYPR_AGENT_TIMEOUT` - Agent timeout in seconds
- `HYPR_VOICE_MAX_TURNS` - Maximum conversation turns
- `ENHANCED_AGENT_MAX_TURNS` - Enhanced agent turns

**Observability:**
- `CLAUDE_HOOKS_ENABLED` - Enable event tracking
- `HYPR_VOICE_TRACE` - Enable detailed logging
- `HYPR_VOICE_FLOW_TRACE` - Trace transcription flow

### Configuration Files

**Whisper Configuration:** `config/hypr_voice/whisper/config.yaml`
```yaml
model_size: "base"
language: "auto"
vocabulary_path: "custom-vocabulary.txt"
```

**Audio Profile:** `config/hypr_voice/whisper/audio-profile.yaml`
```yaml
audio_source: "@DEFAULT_SOURCE@"
sample_rate: 16000
channels: 1
```

**Claude SDK:** `config/hypr_voice/claude-sdk.yaml`
```yaml
model: "claude-sonnet-4-5"
max_tokens: 4096
temperature: 0.7
```

## Advanced Features

### Streaming Chunking

**For Long Recordings (60s+):**
- Processes audio chunks while recording
- Reduces wait time by 85%
- Automatic overlap handling
- Seamless transcription merging

### Custom Vocabulary

**Enhance Transcription Accuracy:**
- Add technical terms
- Include names and acronyms
- Domain-specific language
- Pronunciation hints

**Manage via Web UI:**
- Vocabulary Dashboard panel
- Import word lists
- Export current vocabulary
- Track word usage

### MCP Integration

**Model Context Protocol:**
- Extensible tool system
- Third-party integrations
- Custom tool development
- Tool marketplace

### Observability Hooks

**Event Tracking:**
- Transcription events
- Agent lifecycle
- Tool usage
- Performance metrics

**View in Web UI:**
- Analytics Dashboard
- Real-time event feed
- Historical data
- Export capabilities

## Performance Features

### Optimizations

**Audio Processing:**
- Opus compression (24k bitrate)
- Automatic chunking
- Streaming mode
- Efficient encoding

**AI Processing:**
- Agent pooling
- Connection reuse
- Request batching
- Response streaming

**Caching:**
- Transcription cache
- Agent session persistence
- Configuration caching
- Model warm-up

### Monitoring

**System Metrics:**
- CPU usage
- Memory consumption
- Disk I/O
- Network activity

**Application Metrics:**
- Transcription speed
- Agent response time
- TTS latency
- Error rates

## Security Features

### API Key Management

**Best Practices:**
- Store in `.env` file (never commit)
- Rotate keys regularly
- Use separate keys for dev/prod
- Monitor usage and quotas

### Permissions

**System Access:**
- File operations (user directory)
- Shell commands (sudo awareness)
- Network access (API endpoints)
- Audio device access

### Data Privacy

**Local Processing:**
- Whisper LOCAL mode processes locally
- No audio sent to cloud (LOCAL mode)
- Session isolation
- No data retention (optional)

## Integration Features

### Hyprland Integration

**Window Management:**
- Active window detection
- Workspace awareness
- Title/class extraction
- Context-aware assistance

### Clipboard Integration

**Universal Clipboard:**
- Cross-device clipboard sync
- Clipboard monitoring
- Content analysis
- Smart paste

### Bot Integration

**Supported Platforms:**
- Telegram Bot
- Discord Bot

**Configuration:** `config/bot_integration.yaml.example`

## Feature Comparison

| Feature | LOCAL Mode | FLOW Mode |
|---------|-----------|-----------|
| Transcription | ✓ | ✓ |
| API Costs | Free | Paid |
| Internet Required | No | Yes |
| Speed | Good | Excellent |
| Custom Vocabulary | ✓ | ✓ |
| Personalization | No | Yes |
| Accuracy | Good | Excellent |

## Coming Soon

**Planned Features:**
- Mobile app (iOS/Android)
- Voice activity detection (VAD)
- Multi-language support in transcription
- Custom voice cloning
- Voice command recognition
- Meeting transcription mode
- Translation features

For more information on using specific features, see:
- [Web UI Guide](./web-ui-guide.md)
- [CLI Guide](./cli-guide.md)
- [Use Cases](./use-cases.md)

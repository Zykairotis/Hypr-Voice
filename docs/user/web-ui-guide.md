# Web UI Guide

The Hypr-Voice Web UI provides a beautiful, intuitive interface for interacting with all system features. This guide will help you navigate and use the interface effectively.

## Accessing the Web UI

### Start the Web UI

```bash
# Start all services (including Web UI)
./scripts/start_everything.sh start
```

### Open in Browser

Navigate to:

```
http://localhost:8933
```

**Note:** The Web UI runs on port 8933 by default.

## Dashboard Overview

The dashboard is organized into multiple panels, each dedicated to a specific feature. Navigate between panels using the dock at the bottom of the screen.

### Status Bar (Top)

The status bar shows the health of all services:

- **Whisper Status** - Speech-to-text service (🟢 Online / 🔴 Offline / 🟡 Error)
- **Agent Status** - AI agent service (🟢 Online / 🔴 Offline / 🟡 Error)
- **Orchestrator Status** - Agent orchestration service (🟢 Online / 🔴 Offline / 🟡 Error)

### Navigation Dock (Bottom)

Quick access to all panels:
- 🎤 Whisper
- 🤖 Agent
- 🎛️ Orchestrator
- 📚 Skills
- 📖 Vocabulary
- 🔊 TTS
- 🔌 MCP
- 📊 Analytics

## Whisper Panel (Voice Transcription)

### Overview

The Whisper panel handles all voice recording and speech-to-text transcription.

### Recording Controls

**Start Recording**
1. Click the **"Start Recording"** button
2. Speak clearly into your microphone
3. The button changes to **"Stop Recording"**
4. Click again to stop

**Visual Feedback:**
- Recording indicator (red dot) appears
- Audio waveform shows in real-time
- Timer displays recording duration
- Microphone level meter shows input strength

**Keyboard Shortcuts:**
- Press **Space** to toggle recording (when focused)
- Press **Escape** to cancel recording

### Transcription Display

After stopping recording:
1. Transcription appears in the text area
2. Confidence score displayed (percentage)
3. Processing time shown
4. Option to retry if confidence is low

**Actions:**
- **Copy** - Copy transcription to clipboard
- **Edit** - Edit the transcribed text before sending
- **Send to Agent** - Send directly to AI agent
- **Save** - Save transcription to file

### Recording History

View past recordings:
- Date and timestamp
- Transcription text
- Audio file link
- Duration
- Confidence score

**Actions:**
- Click to view details
- Re-send to agent
- Delete recording
- Export as text/audio

### Microphone Settings

**Device Selection:**
- Choose from available microphones
- Test microphone levels
- Adjust input gain
- Enable noise reduction

**Advanced Settings:**
- Sample rate (default: 16000 Hz)
- Channel count (mono/stereo)
- Bit depth (16-bit/24-bit)

## Agent Panel (AI Assistant)

### Overview

The Agent panel is your main interface for interacting with AI agents.

### Chat Interface

**Sending Messages:**
1. Type your message in the input field
2. Click **"Send"** or press **Enter**
3. The agent processes your request
4. Response appears in the chat history

**Message Types:**
- **User** (blue) - Your messages
- **Assistant** (green) - AI responses
- **System** (gray) - System notifications
- **Error** (red) - Error messages

### Conversation Features

**Context Awareness:**
- Active window shown above chat
- Clipboard content available
- Workspace context included
- Previous messages remembered

**Tool Usage:**
- Shows which tools the agent used
- Displays tool results inline
- Indicates file operations
- Shows command execution

### Agent Selection

**Available Agents:**
- **Code Worker** - Programming tasks
- **Research Worker** - Information gathering
- **Shell Worker** - System operations
- **Voice Worker** - General conversation
- **Enhanced Context** - Context-aware assistance

**Switching Agents:**
- Manual: Select from dropdown
- Auto: Agent routes automatically based on query

### Response Options

**For Each Response:**
- **Copy** - Copy response text
- **Regenerate** - Get a new response
- **Speak** - Read aloud using TTS
- **Rate** - Rate response quality (helps improve)

**TTS Controls:**
- Play/pause audio
- Adjust playback speed
- Volume control
- Voice selection

### Conversation History

**View Past Conversations:**
- Search by date/content
- Filter by agent type
- Export conversation
- Delete conversation

**Actions:**
- Click to load conversation
- Continue from where you left off
- Branch new conversation from history

## Orchestrator Panel (Agent Management)

### Overview

Manage and monitor AI agent sessions.

### Active Sessions

**Session List:**
- Session ID
- Agent type
- Start time
- Status (active/idle/error)
- Message count

**Session Actions:**
- **View** - See session details
- **Pause** - Pause session
- **Resume** - Resume paused session
- **Terminate** - End session

### Session Details

**Information Displayed:**
- Session metadata
- Conversation history
- Tools used
- Performance metrics
- Error logs

### Create New Session

**Options:**
- Select agent type
- Set session name
- Configure timeout
- Enable/disable features

### Performance Metrics

**Real-time Monitoring:**
- Response time
- Token usage
- Tool calls
- Error rate
- Memory usage

## Skills Library Panel

### Overview

Browse and manage agent skills (capabilities/tools).

### Available Skills

**Skill Categories:**
- **File Operations** - Read, Write, Edit, Glob, Grep
- **System** - Bash commands, process management
- **Web** - Search, documentation lookup
- **Code** - LSP, code intelligence
- **Communication** - Email, messaging

**Skill Information:**
- Name and description
- Parameters required
- Usage examples
- Permissions needed

### Managing Skills

**Actions:**
- **Enable** - Allow agent to use skill
- **Disable** - Prevent agent from using skill
- **Configure** - Set skill parameters
- **Test** - Try out skill

### Custom Skills

**Create Skill:**
1. Click **"New Skill"**
2. Enter skill details
3. Define parameters
4. Write documentation
5. Save and enable

## Vocabulary Dashboard

### Overview

Manage custom vocabulary for improved transcription accuracy.

### Word List

**Current Vocabulary:**
- Word/phrase
- Pronunciation hint
- Frequency count
- Last used date

**Adding Words:**
1. Click **"Add Word"**
2. Enter word/phrase
3. Add pronunciation hint (optional)
4. Save

**Import/Export:**
- Import from text file (one word per line)
- Export current vocabulary
- Download as CSV
- Backup vocabulary

### Vocabulary Statistics

**Analytics:**
- Total words
- Most used words
- Recent additions
- Accuracy improvement

## TTS Control Panel

### Overview

Configure text-to-speech settings.

### Voice Settings

**Provider Selection:**
- Deepgram (default)
- ElevenLabs
- Kokoro-ONNX

**Voice Selection:**
- Choose from available voices
- Preview voice samples
- Set as default

### Voice Parameters

**Adjustments:**
- **Speed** - Playback speed (0.5x to 2.0x)
- **Pitch** - Voice pitch adjustment
- **Volume** - Output volume
- **Style** - Speaking style (if supported)

### Test TTS

**Testing:**
1. Enter test text
2. Click **"Test"**
3. Listen to output
4. Adjust settings as needed

### Advanced Settings

**Options:**
- Pre-buffer duration (ms)
- Minimum characters
- Maximum latency
- Idle timeout

## MCP Dashboard

### Overview

Manage Model Context Protocol integrations.

### Connected Services

**Service List:**
- Service name
- Connection status
- Available tools
- Last activity

**Connection Actions:**
- **Connect** - Establish connection
- **Disconnect** - Close connection
- **Configure** - Edit settings
- **Test** - Verify connection

### Tool Registry

**Available Tools:**
- Tool name
- Provider service
- Description
- Status

### MCP Configuration

**Settings:**
- Server URLs
- Authentication tokens
- Timeout values
- Retry policies

## Analytics Dashboard

### Overview

Monitor system performance and usage statistics.

### Usage Statistics

**Metrics Displayed:**
- Total queries
- Transcription count
- Agent sessions
- TTS requests
- Tool usage

**Time Periods:**
- Last hour
- Last 24 hours
- Last week
- Last month
- Custom range

### Performance Metrics

**Key Metrics:**
- Average response time
- Transcription accuracy
- TTS latency
- Agent throughput
- Error rate

**Visualizations:**
- Line charts for trends
- Bar charts for comparisons
- Pie charts for distribution
- Heat maps for patterns

### Error Tracking

**Error Log:**
- Error type
- Timestamp
- Context
- Stack trace (if applicable)

**Actions:**
- Filter by error type
- Export error log
- Clear errors

## Audio Mixer Panel

### Overview

Control audio input and output settings.

### Input Controls

**Microphone:**
- Level slider
- Mute/unmute toggle
- Device selection
- Boost control

### Output Controls

**Speaker:**
- Volume slider
- Mute/unmute toggle
- Device selection
- Balance control

### Audio Visualizer

**Real-time Display:**
- Input waveform
- Output waveform
- Frequency spectrum
- Level meters

## Tips and Tricks

### Productivity Tips

**Keyboard Shortcuts:**
- `Ctrl+K` - Focus search
- `Ctrl+N` - New conversation
- `Ctrl+H` - Open history
- `Escape` - Close modal/panel

**Workflow Tips:**
- Keep frequently used agents pinned
- Use keyboard shortcuts for common actions
- Save important conversations
- Set up custom vocabulary for your domain

### Best Practices

**For Better Transcription:**
- Speak clearly and at moderate pace
- Minimize background noise
- Use quality microphone
- Add technical terms to vocabulary

**For Better AI Responses:**
- Provide context in your queries
- Be specific about what you want
- Use appropriate agent for task
- Give feedback on responses

## Troubleshooting

### Common Issues

**Web UI Won't Load:**
```bash
# Check if service is running
ps aux | grep next

# Restart Web UI
cd web-ui && npm start

# Check logs
tail -f /tmp/hypr-voice-ui.log
```

**Can't Connect to Services:**
- Verify all services are running
- Check firewall settings
- Ensure correct ports
- Check browser console for errors

**Recording Not Working:**
- Test microphone in system settings
- Check microphone permissions
- Verify audio device in Mixer panel
- Try different browser

**Transcription Fails:**
- Check Whisper server status
- Verify audio input levels
- Check for error messages
- Try shorter recording

## Browser Compatibility

**Supported Browsers:**
- Chrome/Chromium 90+
- Firefox 88+
- Edge 90+
- Safari 14+

**Recommended:**
- Chrome/Chromium for best performance
- Enable hardware acceleration
- Allow microphone access
- Allow WebSocket connections

## Accessibility

**Features:**
- Keyboard navigation
- Screen reader support
- High contrast mode
- Adjustable text size
- Color blind friendly palette

For more information:
- [Features Overview](./features.md)
- [CLI Guide](./cli-guide.md)
- [Troubleshooting](./troubleshooting.md)

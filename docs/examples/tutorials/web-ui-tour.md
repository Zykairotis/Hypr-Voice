# Tutorial: Web UI Tour

Learn how to use the Hypr-Voice web interface.

## Table of Contents

- [Overview](#overview)
- [Step 1: Starting the Web UI](#step-1-starting-the-web-ui)
- [Step 2: Dashboard Overview](#step-2-dashboard-overview)
- [Step 3: Creating Agents](#step-3-creating-agents)
- [Step 4: Managing Agents](#step-4-managing-agents)
- [Step 5: Voice Features](#step-5-voice-features)
- [Step 6: Settings](#step-6-settings)
- [Keyboard Shortcuts](#keyboard-shortcuts)

---

## Overview

The Hypr-Voice web UI provides a graphical interface for managing agents, monitoring transcription, and configuring settings.

### Features

- **Agent Management** - Create, configure, and monitor agents
- **Real-time Transcription** - View live speech-to-text
- **Voice Output** - Test TTS voices and settings
- **Configuration** - Adjust settings without editing files
- **Monitoring** - View agent status and logs

---

## Step 1: Starting the Web UI

### Start the Backend Services

```bash
# Start the orchestrator
cd /home/mewtwo/Zykairotis/Hypr-Voice
python -m hypr_voice.orchestrator.orchestrator

# In another terminal, start the web server
python -m hypr_voice.web.server
```

### Access the Web UI

```
Open your browser and navigate to:
http://localhost:8934
```

### First Time Setup

1. **Login Page** - Enter your credentials (if configured)
2. **Dashboard** - Overview of system status
3. **Quick Setup** - Configure basic settings

---

## Step 2: Dashboard Overview

### Main Dashboard

The dashboard provides an at-a-glance view of your Hypr-Voice system:

```
┌─────────────────────────────────────────────────────┐
│  Hypr-Voice Dashboard                                │
├─────────────────────────────────────────────────────┤
│                                                       │
│  System Status: 🟢 Online                            │
│  Active Agents: 3                                    │
│  CPU Usage: 25%                                      │
│  Memory: 1.2 GB / 8 GB                               │
│                                                       │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │  Agents      │  │  Activity    │                 │
│  │  ───────     │  │  ───────     │                 │
│  │  • agent-1   │  │  • Transcr.. │                 │
│  │  • agent-2   │  │  • TTS gen.. │                 │
│  │  • agent-3   │  │  • Agent c.. │                 │
│  └──────────────┘  └──────────────┘                 │
│                                                       │
│  [Create Agent]  [Settings]  [Logs]                  │
└─────────────────────────────────────────────────────┘
```

### Dashboard Sections

| Section | Description |
|---------|-------------|
| **System Status** | Overall system health |
| **Active Agents** | List of running agents |
| **Activity Feed** | Recent system events |
| **Quick Actions** | Common tasks |

---

## Step 3: Creating Agents

### Agent Creation Wizard

1. Click **"Create Agent"** on the dashboard
2. Follow the wizard steps:

#### Step 1: Basic Information

```
Name: [my-agent                                    ]
Description: [My first agent                        ]
Working Directory: [/tmp/agents/my-agent            ]
```

#### Step 2: Select Skills

```
Available Skills:              Selected Skills:
☑ file_operations          →   ☑ file_operations
☐ bash_execution               ☐ voice_synthesis
☐ voice_synthesis              ☐ web_search
☐ hierarchical_agents
☐ web_search
```

#### Step 3: Configure AI

```
Model: [claude-3-5-sonnet-20241022 ▼]
Max Tokens: [4096]
Temperature: [0.7]
Timeout: [300] seconds
```

#### Step 4: Voice Settings (Optional)

```
Enable Voice: ☑
Provider: [kokoro ▼]
Voice: [af_bella ▼]
```

#### Step 5: Review

```
Summary:
• Name: my-agent
• Skills: file_operations, voice_synthesis
• Model: claude-3-5-sonnet-20241022
• Voice: kokoro (af_bella)

[Cancel]  [Create Agent]
```

---

## Step 4: Managing Agents

### Agent List

View all created agents:

```
┌─────────────────────────────────────────────────────┐
│  Agents                                             │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌───────────────────────────────────────────────┐  │
│  │ 🟢 my-agent                    [Edit] [Delete] │  │
│  │    Status: Running                            │  │
│  │    Skills: file_operations, voice_synthesis    │  │
│  │    Created: 2 hours ago                       │  │
│  └───────────────────────────────────────────────┘  │
│                                                       │
│  ┌───────────────────────────────────────────────┐  │
│  │ ⚪ research-agent               [Edit] [Delete] │  │
│  │    Status: Stopped                            │  │
│  │    Skills: file_operations, web_search        │  │
│  │    Created: 1 day ago                         │  │
│  └───────────────────────────────────────────────┘  │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### Agent Details

Click on an agent to view details:

```
┌─────────────────────────────────────────────────────┐
│  Agent: my-agent                                    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Status: 🟢 Running                                  │
│  PID: 12345                                          │
│  Uptime: 2 hours 15 minutes                          │
│                                                       │
│  Configuration:                                      │
│  • Model: claude-3-5-sonnet-20241022                │
│  • Max Tokens: 4096                                  │
│  • Temperature: 0.7                                  │
│  • Skills: file_operations, voice_synthesis          │
│                                                       │
│  Activity Log:                                       │
│  [14:30:22] Instruction received                     │
│  [14:30:25] Processing...                            │
│  [14:30:28] Task completed successfully              │
│                                                       │
│  [Send Instruction]  [Stop]  [Restart]               │
└─────────────────────────────────────────────────────┘
```

### Send Instruction

Interact with agents via the web UI:

```
┌─────────────────────────────────────────────────────┐
│  Send Instruction                                    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Enter your instruction:                             │
│  ┌─────────────────────────────────────────────┐    │
│  │ Create a file called hello.txt with 'Hello   │    │
│  │ World' inside it                             │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ☑ Speak response                                    │
│  ☑ Show detailed output                              │
│                                                       │
│  [Send] [Clear]                                      │
│                                                       │
└─────────────────────────────────────────────────────┘
```

---

## Step 5: Voice Features

### Transcription Panel

Real-time speech-to-text:

```
┌─────────────────────────────────────────────────────┐
│  Live Transcription                                  │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Mode: [FLOW ▼]                                      │
│                                                       │
│  [🎤 Start Recording]  [⏹️ Stop]  [📋 Copy]        │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │ > This is a test of the speech to text      │    │
│  │ > transcription system using Whisper        │    │
│  │ > and it works really well for technical    │    │
│  │ > terms like Kubernetes and Docker          │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  Vocabulary: [development ▼]                          │
│  Language: [English ▼]                                │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### TTS Testing

Test text-to-speech voices:

```
┌─────────────────────────────────────────────────────┐
│  Text-to-Speech                                      │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Provider: [kokoro ▼]                                │
│  Voice: [af_bella ▼]                                 │
│                                                       │
│  Enter text to speak:                                │
│  ┌─────────────────────────────────────────────┐    │
│  │ Hello! This is a test of the text to       │    │
│  │ speech system.                              │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  Speed: [1.0x] ━━━━●━━━━                              │
│  Pitch: [1.0] ━━━━●━━━━                              │
│                                                       │
│  [🔊 Generate]  [⬇️ Download]  [📋 Copy Code]        │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### Voice Presets

Quick voice configurations:

```
┌─────────────────────────────────────────────────────┐
│  Voice Presets                                       │
├─────────────────────────────────────────────────────┤
│                                                       │
│  [👔 Professional]  [😊 Friendly]  [💻 Technical]    │
│  [📖 Narrator]                                       │
│                                                       │
│  Professional:                                       │
│  • Provider: kokoro                                  │
│  • Voice: af_bella                                   │
│  • Speed: 1.0x                                       │
│                                                       │
│  [Create Custom Preset]                              │
│                                                       │
└─────────────────────────────────────────────────────┘
```

---

## Step 6: Settings

### Configuration Panel

Access settings from the dashboard:

```
┌─────────────────────────────────────────────────────┐
│  Settings                                           │
├─────────────────────────────────────────────────────┤
│                                                       │
│  [General]  [Voice]  [Whisper]  [Agents]  [System]  │
│                                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                       │
│  General Settings                                    │
│                                                       │
│  Theme: [☑ Light]  [☐ Dark]                          │
│  Language: [English ▼]                               │
│  Timezone: [UTC ▼]                                   │
│                                                       │
│  Logging                                             │
│  ☑ Enable debug logging                              │
│  ☑ Save logs to file                                 │
│  Log directory: [/tmp/agents/logs]                   │
│                                                       │
│  Notifications                                       │
│  ☑ Enable desktop notifications                      │
│  ☑ Notify on agent completion                        │
│  ☐ Notify on errors                                  │
│                                                       │
│  [Save Changes]  [Reset to Defaults]                 │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### Voice Settings

```
┌─────────────────────────────────────────────────────┐
│  Voice Settings                                      │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Default Provider: [kokoro ▼]                        │
│  Fallback Provider: [deepgram ▼]                     │
│                                                       │
│  Kokoro Configuration                                │
│  ☑ Enabled                                           │
│  Default Voice: [af_bella ▼]                         │
│  Sample Rate: [24000 ▼] Hz                           │
│  Phonemizer: [espeak ▼]                              │
│                                                       │
│  Deepgram Configuration                              │
│  ☑ Enabled                                           │
│  API Key: [••••••••••••]                             │
│  Default Voice: [asteria ▼]                          │
│  Sample Rate: [24000 ▼] Hz                           │
│                                                       │
│  ElevenLabs Configuration                            │
│  ☑ Enabled                                           │
│  API Key: [••••••••••••]                             │
│  Default Voice: [rachel ▼]                           │
│  Model: [eleven_multilingual_v2 ▼]                   │
│                                                       │
│  [Test All Providers]  [Save Changes]                │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### Whisper Settings

```
┌─────────────────────────────────────────────────────┐
│  Whisper Settings                                    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Transcription Mode: [FLOW ▼]                        │
│                                                       │
│  Wispr Flow Configuration                            │
│  ☑ Enabled                                           │
│  JWT Token: [••••••••••••]                            │
│  API Key: [••••••••••••]                              │
│  User UUID: [••••••••••••]                            │
│                                                       │
│  Performance Options                                 │
│  ☑ Use Opus encoding                                 │
│  Opus Bitrate: [24k ▼]                               │
│  ☑ Auto-chunking                                     │
│  Chunk Size: [30 ▼] seconds                          │
│  ☑ Streaming mode (60s+ recordings)                  │
│                                                       │
│  Local Server Configuration                          │
│  ☑ Enabled                                           │
│  Model: [small.en ▼]                                 │
│  Device: [cuda ▼]                                    │
│  Port: [9099]                                        │
│                                                       │
│  [Test Connection]  [Save Changes]                   │
│                                                       │
└─────────────────────────────────────────────────────┘
```

---

## Keyboard Shortcuts

### Global Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl + N` | Create new agent |
| `Ctrl + S` | Save settings |
| `Ctrl + R` | Refresh dashboard |
| `Ctrl + L` | Open logs |
| `Esc` | Close modal |

### Agent Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl + I` | Send instruction |
| `Ctrl + T` | Stop agent |
| `Ctrl + E` | Edit agent |
| `Ctrl + D` | Delete agent |

### Voice Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl + Space` | Start/Stop recording |
| `Ctrl + V` | Test TTS |
| `Ctrl + C` | Copy transcription |

---

## Tips and Tricks

### Quick Agent Creation

1. Press `Ctrl + N` to create agent
2. Use templates for common agent types
3. Clone existing agents to copy settings

### Efficient Monitoring

1. Pin important agents to top of list
2. Use agent groups to organize
3. Set up notifications for completion

### Voice Workflow

1. Use preset voices for consistency
2. Test voices before long sessions
3. Adjust speed/pitch for clarity

---

## Next Steps

- [Basic Usage Examples](../basic-usage.md) - More examples
- [Configuration Reference](../../development/configuration-reference.md) - Detailed config
- [Agent Configuration](../../development/agent-config.md) - Agent settings

---

## See Also

- [First Agent Tutorial](first-agent.md)
- [TTS Setup Tutorial](tts-setup.md)
- [Whisper Setup Tutorial](whisper-setup.md)

# 🎨 Hypr-Voice Web UI Guide

Complete guide for the Hypr-Voice Web UI - a modern glassmorphic interface for managing voice transcription and AI agents.

## 📍 Overview

The Hypr-Voice Web UI provides a beautiful, intuitive interface to configure and monitor:
- **Hypr-Whisper** - Voice transcription system
- **Hypr-Voice Agent** - Multi-agent AI orchestration

Built with Next.js 14, TypeScript, shadcn/ui, and a custom dark AMOLED glassmorphic theme.

## 🎯 Key Features

### Visual Design
- **Pure Black AMOLED Background** (#000000) - Perfect for OLED displays
- **Glassmorphic Cards** - Transparent panels with backdrop blur
- **Purple Accent Theme** - Beautiful purple gradients with glow effects
- **Smooth Animations** - Polished transitions and hover effects
- **Responsive Layout** - Works on desktop and mobile devices

### Functionality
- **Real-Time Monitoring** - Live server status updates every 2-5 seconds
- **Configuration Management** - Save settings to YAML config files
- **Audio Device Selection** - Choose microphone/input sources
- **Model Configuration** - Select Whisper models and parameters
- **Vocabulary Management** - Add custom technical terms
- **Agent Control** - Create and manage Claude SDK agents
- **Voice Synthesis** - Configure TTS providers and voices
- **MCP Server Management** - Enable/disable integrations
- **Skills Configuration** - Control agent capabilities

## 📂 Project Location

```
/home/mewtwo/Zykairotis/Hypr-Voice/web-ui/
```

## 🚀 Quick Start

### One-Command Launch
```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui
./start-ui.sh
```

This starts both frontend (port 3000) and backend (port 8080).

### Access Points
- **Web UI:** http://localhost:3000
- **Backend API:** http://localhost:8080
- **API Documentation:** http://localhost:8080/docs

## 📱 User Interface

### Main Dashboard

The dashboard has two main tabs:

#### 1. Hypr-Whisper Tab
Manages voice transcription configuration:

**Server Status Card**
- Connection status (online/offline/error)
- Active clients count
- Server uptime
- Request count and latency
- WebSocket and REST API endpoints

**Configuration Tabs:**

**Audio Tab:**
- Input device selection with refresh
- Sample rate slider (8000-48000 Hz)
- Channels (Mono/Stereo)
- Buffer size configuration
- Save recordings toggle
- Auto cleanup toggle

**Model Tab:**
- Whisper model selection (tiny to large-v3-turbo)
- Device selection (CUDA/CPU)
- Compute type (INT8, FP16, FP32)
- Language selection
- Translation toggle
- Performance settings (workers, threads)
- VAD configuration with sensitivity sliders

**Vocabulary Tab:**
- Master enable/disable toggle
- Custom words input with live add/remove
- Category vocabularies (Technical, Programming, SysAdmin)
- Statistics display
- Words counter

#### 2. Hypr-Voice Agent Tab
Manages AI agent system:

**Agent Status Card**
- Server connection status
- Active/total agents count
- CPU and memory usage
- API and WebSocket endpoints

**Configuration Tabs:**

**Agents Tab:**
- Create new agents with custom names
- Agent list with status badges
- Start/pause/delete controls
- Chat interface buttons

**Voice Tab:**
- Provider selection (Kokoro/ElevenLabs/Deepgram)
- Voice selection per provider
- Preset selection (Professional/Friendly/Technical/Narrator)
- Speed and pitch sliders
- Auto fallback configuration
- Test voice button

**MCP Tab:**
- Available MCP servers list
- Enable/disable toggles per server
- Server status indicators
- Start/stop controls
- Statistics (running/stopped/errors)

**Skills Tab:**
- Categorized skills (Core/Voice/Advanced)
- Enable/disable toggles
- Skill descriptions
- Active skills counter

### UI Components

**Status Indicators:**
- 🟢 Green - Online/Running
- ⚫ Gray - Offline/Stopped
- 🔴 Red - Error

**Interactive Elements:**
- Buttons with hover glow effects
- Sliders with real-time value display
- Switches with smooth transitions
- Cards with glass-hover effects
- Dropdowns with glassmorphic styling

## 🔧 Configuration Management

### How It Works

1. **Frontend** (Next.js) displays UI
2. **User** makes changes in UI
3. **Frontend** sends changes to Backend Bridge
4. **Backend Bridge** (FastAPI) updates YAML config files
5. **Servers** (Whisper/Agent) use updated configs

### Configuration Files

The backend bridge manages these files:

**Whisper:**
- `src/Hypr-Whisper/config/config.yaml` - Main server config
- `src/Hypr-Whisper/config/audio-profile.yaml` - Audio settings
- `src/Hypr-Whisper/config/vocabulary.yaml` - Vocabulary data

**Agent:**
- `config/hypr_voice/config.yaml` - Agent system config

### API Endpoints

**Whisper Management:**
```
GET  /api/whisper/status        - Server status
GET  /api/audio/devices         - List audio devices
GET  /api/config/audio          - Get audio config
POST /api/config/audio          - Update audio config
GET  /api/config/model          - Get model config
POST /api/config/model          - Update model config
GET  /api/config/vocabulary     - Get vocabulary config
POST /api/config/vocabulary     - Update vocabulary config
```

**Agent Management:**
```
GET  /api/agent/status          - Agent status
POST /api/config/voice          - Update voice config
```

## 🎨 Customization

### Theme Colors

Edit `web-ui/app/globals.css`:

```css
.dark {
  --background: oklch(0 0 0);        /* Pure black */
  --primary: oklch(0.65 0.25 270);   /* Purple accent */
  --border: oklch(1 0 0 / 8%);       /* Subtle borders */
}
```

### Glass Effects

Utility classes available:
- `.glass` - Standard glassmorphic background
- `.glass-hover` - Hover effect
- `.glow` - Accent glow
- `.glow-hover` - Glow on hover

### Adding Components

```bash
cd web-ui
npx shadcn@latest add [component-name]
```

## 🐛 Troubleshooting

### Common Issues

**1. "Cannot connect to server"**
- Ensure Whisper server is running on port 9090
- Ensure Agent server is running on port 8922
- Check firewall settings

**2. "Configuration not saving"**
- Verify write permissions on config directories
- Check backend bridge logs
- Ensure backend is running

**3. "UI looks broken"**
- Clear Next.js cache: `rm -rf .next`
- Reinstall dependencies: `npm install`
- Check browser console (F12) for errors

**4. "Port already in use"**
- Kill process: `lsof -ti:3000 | xargs kill -9`
- Or use different port: `PORT=3001 npm run dev`

### Logs

**Frontend logs:**
```bash
# In terminal running npm run dev
```

**Backend logs:**
```bash
# In terminal running bridge.py
```

**Server logs:**
```bash
# Whisper
tail -f /tmp/whisper-live-hypr-voice.log

# Agent
tail -f var/hypr_voice/logs/raw/*.log
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Web Browser                        │
│              (http://localhost:3000)                 │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┴──────────────┐
        │                          │
┌───────▼────────┐      ┌──────────▼────────┐
│  Next.js       │      │  FastAPI Bridge   │
│  Frontend      │◄────►│  (Port 8080)      │
│  (Port 3000)   │      │                   │
└────────────────┘      └──────┬────────────┘
                               │
                   ┌───────────┴───────────┐
                   │                       │
         ┌─────────▼──────┐    ┌──────────▼───────┐
         │ Hypr-Whisper   │    │  Hypr-Voice      │
         │ (Port 9090)    │    │  Agent           │
         │                │    │  (Port 8922)     │
         └────────────────┘    └──────────────────┘
```

## 🔐 Security

### CORS Configuration

The backend bridge allows these origins by default:
- `http://localhost:3000`
- `http://localhost:3001`

To add more origins, edit `api/bridge.py`:
```python
allow_origins=["http://localhost:3000", "your-domain.com"]
```

### Authentication

Currently, the UI has no authentication. To add auth:

1. Implement JWT tokens in backend
2. Add login page to frontend
3. Store tokens in localStorage/cookies
4. Add auth middleware to protected routes

## 🚀 Production Deployment

### Build Frontend
```bash
cd web-ui
npm run build
npm start
# Runs on port 3000
```

### Production Backend
```bash
cd web-ui/api
source venv/bin/activate
uvicorn bridge:app --host 0.0.0.0 --port 8080 --workers 4
```

### Using PM2
```bash
# Install PM2
npm install -g pm2

# Start frontend
pm2 start npm --name "hypr-ui-frontend" -- start

# Start backend
pm2 start "uvicorn bridge:app --host 0.0.0.0 --port 8080" --name "hypr-ui-backend" --interpreter python3
```

### Using Docker
See `web-ui/Dockerfile` (to be created)

### Using Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

## 📚 Additional Resources

- [README.md](../web-ui/README.md) - Complete documentation
- [GETTING_STARTED.md](../web-ui/GETTING_STARTED.md) - Quick start guide
- [shadcn/ui docs](https://ui.shadcn.com/) - Component library
- [Next.js docs](https://nextjs.org/docs) - Framework documentation
- [FastAPI docs](https://fastapi.tiangolo.com/) - Backend framework

## 🤝 Contributing

To contribute to the Web UI:

1. Make changes in `web-ui/` directory
2. Test thoroughly
3. Update documentation
4. Submit pull request

## 📄 License

Same as main Hypr-Voice project (MIT)

---

**Built with ❤️ for the Hypr-Voice ecosystem**


# Hypr-Voice Web UI - Quick Start Guide

**Last Updated:** November 1, 2025

## 🚀 Quick Start

### Start Everything (Recommended)

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui
./start-ui.sh
```

**What This Does:**
- ✅ Starts Frontend (Next.js) on port **8933**
- ✅ Starts Backend (FastAPI bridge) on port **8934**
- ✅ Opens browser automatically

**Access Points:**
- 🌐 **Web UI:** http://localhost:8933
- 🔧 **API Docs:** http://localhost:8934/docs
- ❤️ **Health Check:** http://localhost:8934/health

---

## 📋 Prerequisites

### 1. Dependencies Installed

```bash
# Frontend dependencies
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui
npm install

# Backend dependencies
cd api
source /home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/activate
pip install -r requirements.txt
```

### 2. Services Running (Optional but Recommended)

```bash
# Whisper server (STT)
cd /home/mewtwo/Zykairotis/Hypr-Voice
./scripts/start_hybrid_server.sh
# Runs on port 9099

# Agent server (Optional)
cd /home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Voice/Agent
./start_system.sh
# Runs on port 9093
```

---

## 🎯 Common Tasks

### Start Frontend Only

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui
npm run dev
```

Open http://localhost:8933

**Note:** Backend features will show "Backend Offline" but UI will work with defaults.

### Start Backend Only

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui/api
source /home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/activate
python bridge.py
```

Runs on http://localhost:8934

### Build for Production

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui
npm run build
npm start
```

### Stop All Services

```bash
# Press Ctrl+C in the start-ui.sh terminal
# Or kill processes manually:
pkill -f "next dev"
pkill -f "bridge.py"
```

---

## 🔍 Check Status

### Frontend

```bash
curl http://localhost:8933
# Should return HTML
```

### Backend

```bash
curl http://localhost:8934/health
# Should return: {"status":"ok","service":"Hypr-Voice Web UI Bridge"}
```

### All Services

```bash
# Check what's running on which ports
lsof -i :8933  # Frontend
lsof -i :8934  # Backend
lsof -i :9099  # Whisper server
lsof -i :9093  # Orchestrator
```

---

## 🛠️ Troubleshooting

### Port Already in Use

```bash
# Find and kill process on port 8933
lsof -ti:8933 | xargs kill -9

# Find and kill process on port 8934
lsof -ti:8934 | xargs kill -9
```

### Console Errors About Backend

**If you see warnings like:**
```
[WARN] Backend not available on port 8934...
```

**Solution:**
```bash
cd web-ui && ./start-ui.sh
```

The UI will work with defaults, but backend provides real data.

### Module Not Found

```bash
# Reinstall dependencies
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui
rm -rf node_modules package-lock.json
npm install
```

### Python Virtual Environment Issues

```bash
# Recreate venv
cd /home/mewtwo/Zykairotis/Hypr-Voice
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 Project Structure

```
web-ui/
├── app/                    # Next.js app directory (pages)
├── components/             # React components
│   ├── agent/             # Agent management components
│   ├── whisper/           # Whisper config components
│   ├── context/           # Context dashboard
│   └── ui/                # shadcn/ui components
├── api/                   # Backend bridge (FastAPI)
│   ├── bridge.py         # Main FastAPI app
│   └── requirements.txt  # Python dependencies
├── lib/                   # Utilities and helpers
├── public/                # Static assets
├── start-ui.sh           # Main startup script
├── package.json          # NPM dependencies & scripts
└── next.config.js        # Next.js configuration
```

---

## 🎨 Features

### Available Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Main dashboard overview |
| Whisper Config | `/whisper` | Configure Whisper STT |
| Agent Manager | `/agent` | Manage AI agents |
| Context | `/context` | Live context monitoring |
| Vocabulary | `/vocabulary` | Custom vocabulary |
| TTS | `/tts` | Text-to-speech settings |

### Components

- **Context Panel** - Real-time context from Hyprland
- **Audio Config** - Microphone and recording settings
- **Model Config** - Whisper model configuration
- **Vocabulary Config** - Custom vocabulary management
- **Agent Manager** - Create and manage agents
- **Voice Config** - TTS provider settings

---

## 🔗 Integration Points

### Backend Bridge (Port 8934)

Acts as a proxy between the frontend and services:

```
Frontend (8933) → Backend Bridge (8934) → Whisper (9099)
                                        → Orchestrator (9093)
```

### APIs Connected

- **Whisper Server (9099):** Speech-to-text transcription
- **Orchestrator (9093):** Multi-agent orchestration
- **Context Manager:** Live window and clipboard monitoring
- **Vocabulary System:** Custom word correction

---

## 📱 Development Tips

### Hot Reload

Next.js supports hot reload - save any file and see changes instantly.

### Debugging

```bash
# Start with verbose logging
cd web-ui
npm run dev -- --verbose

# Backend logs
cd web-ui/api
python bridge.py --log-level debug
```

### Browser Console

Open DevTools (F12) to see:
- Component state
- API calls
- Error messages
- Network requests

### API Testing

Use the FastAPI docs: http://localhost:8934/docs
- Try out endpoints
- See request/response schemas
- Test authentication

---

## 🎯 Common Workflows

### 1. Configure Whisper

1. Start services: `./start-ui.sh`
2. Go to: http://localhost:8933/whisper
3. Select audio device
4. Configure model settings
5. Save configuration

### 2. Create an Agent

1. Start services: `./start-ui.sh`
2. Go to: http://localhost:8933/agent
3. Enter agent name
4. Click "Create"
5. Manage from dashboard

### 3. Monitor Context

1. Start services: `./start-ui.sh`
2. Go to: http://localhost:8933/context
3. See live updates:
   - Active window
   - Recent commands
   - Clipboard history
   - Git status

### 4. Configure Vocabulary

1. Start services: `./start-ui.sh`
2. Go to: http://localhost:8933/vocabulary
3. Add custom words
4. Enable/disable categories
5. Save configuration

---

## 🚨 Error Handling

The UI gracefully handles backend unavailability:

- ✅ Shows "Backend Offline" status
- ✅ Displays helpful instructions
- ✅ Uses default/mock data
- ✅ Minimal console warnings
- ✅ No functionality breaks

**See:** `BACKEND_ERROR_HANDLING.md` for details

---

## 📦 NPM Scripts

```json
{
  "dev": "next dev -p 8933",           // Start dev server
  "build": "next build",                // Build for production
  "start": "next start -p 8933",       // Start production server
  "lint": "eslint",                     // Run linter
  "start:ui": "./start-ui.sh",         // Start frontend + backend
  "backend": "cd api && python bridge.py" // Start backend only
}
```

---

## 🔐 Environment Variables

Create `.env.local` in `/web-ui`:

```bash
# Optional: API Keys
ELEVENLABS_API_KEY=your_key_here
DEEPGRAM_API_KEY=your_key_here

# Optional: Custom ports
NEXT_PUBLIC_BACKEND_URL=http://localhost:8934
NEXT_PUBLIC_WHISPER_URL=http://localhost:9099
NEXT_PUBLIC_AGENT_URL=http://localhost:9093
```

---

## 📚 Additional Documentation

- **Backend Error Handling:** `BACKEND_ERROR_HANDLING.md`
- **API Reference:** http://localhost:8934/docs
- **Component Guide:** Check individual component files
- **Main Project:** `/home/mewtwo/Zykairotis/Hypr-Voice/README.md`

---

## 🤝 Getting Help

### Check Logs

```bash
# Frontend logs (terminal running npm run dev)
# Backend logs (terminal running bridge.py)
# Browser console (F12 → Console tab)
```

### Common Issues

1. **Port conflicts** → Kill processes, restart
2. **Module errors** → Reinstall dependencies
3. **Backend offline** → Run `./start-ui.sh`
4. **No audio devices** → Check PulseAudio/PipeWire
5. **Whisper errors** → Start Whisper server first

---

## 🎉 Quick Reference

| Action | Command |
|--------|---------|
| Start everything | `./start-ui.sh` |
| Start frontend | `npm run dev` |
| Start backend | `cd api && python bridge.py` |
| Build production | `npm run build` |
| Check health | `curl localhost:8934/health` |
| View logs | Check terminal + browser console |
| Stop services | `Ctrl+C` in terminal |

---

**Ready to go!** 🚀

Run `./start-ui.sh` and open http://localhost:8933

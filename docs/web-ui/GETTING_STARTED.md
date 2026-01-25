# 🚀 Getting Started with Hypr-Voice Web UI

A quick guide to get up and running with the Hypr-Voice Web UI.

## 📋 Prerequisites

Before you start, ensure you have:

- ✅ **Node.js 18+** and npm installed
- ✅ **Python 3.10+** installed
- ✅ **Hypr-Whisper** server running (default: `http://localhost:9099`)
- ✅ **Hypr-Voice Orchestrator** server running (default: `http://localhost:9093`)

## ⚡ Quick Start (Easiest Method)

### One-Command Start

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui
./start-ui.sh
```

This single command will:
1. ✨ Set up the backend Python environment
2. 📦 Install all required dependencies
3. 🚀 Start the backend bridge (port 8080)
4. 🎨 Start the frontend (port 3000)

**Access the UI at:** [http://localhost:3000](http://localhost:3000)

Press `Ctrl+C` to stop all services.

---

## 🔧 Manual Setup (For Development)

If you prefer to run services separately or need more control:

### Step 1: Install Frontend Dependencies

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui
npm install
```

### Step 2: Install Backend Dependencies

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Start Services

**Terminal 1 - Backend Bridge:**
```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui/api
source venv/bin/activate
python bridge.py
# Running on http://localhost:8080
```

**Terminal 2 - Frontend:**
```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui
npm run dev
# Running on http://localhost:3000
```

---

## 🎯 First Steps

Once the UI is running, you'll see the main dashboard with two tabs:

### 1️⃣ Hypr-Whisper Tab
Configure your voice transcription system:

**Server Status** (shows connection status)
- Check if Whisper server is online
- View active clients and uptime

**Audio Configuration**
- Select your microphone/audio input device
- Configure sample rate (16000 Hz recommended)
- Set channels (Mono for voice)
- Adjust buffer size for latency

**Model Configuration**
- Choose Whisper model (large-v3-turbo recommended)
- Select device (CUDA for GPU, CPU otherwise)
- Configure Voice Activity Detection (VAD)
- Set language preferences

**Vocabulary Management**
- Add custom technical terms
- Enable/disable vocabulary categories
- Manage context-specific vocabularies

### 2️⃣ Hypr-Voice Agent Tab
Manage your AI agent system:

**Agent Manager**
- Create new Claude SDK agents
- Start/stop/pause agents
- View agent status

**Voice Synthesis**
- Choose TTS provider (Kokoro/ElevenLabs/Deepgram)
- Select voice and preset
- Adjust speed and pitch
- Test voice output

**MCP Servers**
- Enable/disable MCP integrations
- Filesystem, GitHub, Git, Database servers
- Monitor server status

**Skills Configuration**
- Enable agent capabilities
- File operations, bash execution
- Voice synthesis, hierarchical agents

---

## 🎨 UI Features

### Glass Effect
The UI features a beautiful glassmorphic design:
- Transparent panels with backdrop blur
- Subtle glow effects on interactive elements
- Pure black AMOLED background
- Purple accent colors

### Real-Time Updates
- Status monitors update every 2-5 seconds
- Live server status indicators
- Automatic reconnection on network issues

### Responsive Design
- Works on desktop and mobile
- Adaptive layouts for different screen sizes
- Touch-friendly controls

---

## 🔍 Troubleshooting

### Backend Connection Failed
**Symptom:** "Whisper/Agent Status: offline"

**Solutions:**
1. Ensure Whisper server is running:
   ```bash
   # Check if server is running
   curl http://localhost:9099/health
   ```

2. Ensure Agent server is running:
   ```bash
   # Check if server is running
   curl http://localhost:9093/agents
   ```

3. Start servers if needed:
   ```bash
   # Whisper server
   cd /home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper
   ./scripts/start_hybrid_server.sh start
   
   # Agent server
    ./scripts/hypr_voice/start_system.sh
   ```

### Port Already in Use
**Symptom:** "EADDRINUSE: address already in use :::3000"

**Solution:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use a different port
PORT=3001 npm run dev
```

### Configuration Not Saving
**Symptom:** Changes don't persist

**Solutions:**
1. Check file permissions:
   ```bash
   # Ensure you can write to config directories
   ls -la ../src/Hypr-Whisper/config/
    ls -la ../config/hypr_voice/
   ```

2. Verify backend bridge is running
3. Check browser console for errors (F12)

### Styling Broken
**Symptom:** UI looks broken or unstyled

**Solutions:**
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Restart dev server
npm run dev
```

---

## 📚 Next Steps

1. **Configure Audio Input**
   - Go to Whisper > Audio tab
   - Select your microphone
   - Click "Save Audio Configuration"

2. **Test Voice Transcription**
   - Ensure F9 keybind is configured
   - Press and hold F9
   - Speak into microphone
   - Release F9 to transcribe

3. **Create an Agent**
   - Go to Agent > Agents tab
   - Enter agent name
   - Click "Create"

4. **Configure Voice Synthesis**
   - Go to Agent > Voice tab
   - Select provider and voice
   - Click "Test Voice"

---

## 🆘 Getting Help

- 📖 **Full Documentation:** [README.md](./README.md)
- 🐛 **Issues:** Report bugs on GitHub
- 💬 **Community:** Join Discord server
- 📧 **Contact:** See main project docs

---

## 🎉 You're All Set!

The Hypr-Voice Web UI is now ready to use. Enjoy managing your voice transcription and AI agent system with a beautiful, modern interface!

**Happy voice controlling! 🎤✨**

# 🎨 Hypr-Voice Web UI

A modern, glassmorphic web interface for managing **Hypr-Voice** and **Hypr-Whisper** configurations with a dark AMOLED theme.

![License](https://img.shields.io/badge/license-MIT-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![shadcn/ui](https://img.shields.io/badge/shadcn%2Fui-latest-purple)

## ✨ Features

### 🎤 Hypr-Whisper Management
- **Audio Configuration**
  - Select input devices (microphone, PulseAudio sources)
  - Configure sample rate, channels, and buffer size
  - Toggle recording save and auto-cleanup
  
- **Model Configuration**
  - Choose Whisper model (tiny to large-v3-turbo)
  - Device selection (CUDA/CPU)
  - Compute type optimization (INT8, FP16, FP32)
  - Voice Activity Detection (VAD) settings
  - Language selection and translation options
  
- **Vocabulary Management**
  - Add custom technical terms
  - Enable/disable vocabulary categories
  - Real-time vocabulary statistics
  
- **Server Monitoring**
  - Live server status
  - Active client count
  - Request metrics and latency

### 🤖 Hypr-Voice Agent Management
- **Agent Control**
  - Create and manage Claude SDK agents
  - Start/stop/pause agents
  - Monitor agent status
  
- **Voice Synthesis**
  - Configure TTS providers (Kokoro, ElevenLabs, Deepgram)
  - Select voices and presets
  - Adjust speed and pitch
  - Test voice synthesis
  
- **MCP Servers**
  - Enable/disable MCP servers
  - Filesystem, GitHub, Git, Database integrations
  - Server status monitoring
  
- **Skills Configuration**
  - Enable/disable agent skills
  - Core, Voice, and Advanced skills
  - File operations, bash execution, web search

### 🎨 Design Features
- **Glassmorphic UI** with backdrop blur effects
- **Dark AMOLED Theme** (pure #000000 black)
- **Purple accent** colors with glow effects
- **Responsive layout** for desktop and mobile
- **Real-time updates** via WebSocket (context proxy on `/ws/context` → upstream `ws://localhost:9091` by default)
- **Smooth animations** and transitions

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- Hypr-Whisper server running on port 9090
- Hypr-Voice Agent server running on port 8922

### Installation

1. **Install Frontend Dependencies**
```bash
cd web-ui
npm install
```

2. **Install Backend Bridge Dependencies**
```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the UI

**Option 1: Development Mode (Recommended)**

Terminal 1 - Start the Backend Bridge:
```bash
cd web-ui/api
./start.sh
# Or manually:
# source venv/bin/activate
# python bridge.py
```

Terminal 2 - Start the Frontend:
```bash
cd web-ui
npm run dev
```

**Option 2: Production Build**
```bash
cd web-ui
npm run build
npm start
```

Access the UI at: **http://localhost:8933**

**Option 3: Quick Start Script (Easiest)**
```bash
cd web-ui
./start-ui.sh
```

This starts both frontend and backend automatically!

## 📚 Documentation

**📖 [Documentation Index](DOCUMENTATION_INDEX.md) - Complete documentation overview**

### Quick Links
- **[Complete Fix Summary](COMPLETE_FIX_SUMMARY.md)** - ⭐ Start here for overview
- **[Quick Start Guide](QUICK_START.md)** - Get up and running quickly
- **[Backend Error Handling](BACKEND_ERROR_HANDLING.md)** - Technical details on graceful error handling
- **[Console Error Fix Summary](CONSOLE_ERROR_FIX_SUMMARY.md)** - Quick summary of recent fixes
- **[Changelog](CHANGELOG.md)** - Detailed change history

## 📁 Project Structure

```
web-ui/
├── app/
│   ├── globals.css          # Global styles with glassmorphic theme
│   ├── layout.tsx            # Root layout with dark mode
│   └── page.tsx              # Main dashboard
├── components/
│   ├── ui/                   # shadcn/ui components
│   ├── layout/
│   │   └── status-bar.tsx    # Bottom status bar
│   ├── whisper/
│   │   ├── whisper-panel.tsx # Main Whisper panel
│   │   ├── audio-config.tsx  # Audio settings
│   │   ├── model-config.tsx  # Model settings
│   │   ├── vocabulary-config.tsx # Vocabulary management
│   │   └── server-status.tsx # Server monitoring
│   └── agent/
│       ├── agent-panel.tsx   # Main Agent panel
│       ├── agent-manager.tsx # Agent CRUD operations
│       ├── voice-config.tsx  # TTS configuration
│       ├── mcp-servers.tsx   # MCP server management
│       └── skills-config.tsx # Skills configuration
├── api/
│   ├── bridge.py             # FastAPI backend bridge
│   ├── requirements.txt      # Python dependencies
│   └── start.sh              # Backend start script
├── lib/
│   └── utils.ts              # Utility functions
└── public/                   # Static assets
```

## 🎨 Theme Customization

The UI uses a custom dark AMOLED theme with glassmorphism. To customize:

### Colors
Edit `app/globals.css`:
```css
.dark {
  --background: oklch(0 0 0);      /* Pure black */
  --primary: oklch(0.65 0.25 270); /* Purple accent */
  --border: oklch(1 0 0 / 8%);     /* Subtle borders */
}
```

### Glass Effects
The theme provides utility classes:
- `.glass` - Standard glassmorphic background
- `.glass-hover` - Hover effect for glass elements
- `.glow` - Accent glow effect
- `.glow-hover` - Hover glow effect

## 🔌 API Endpoints

The backend bridge provides these endpoints:

### Whisper Server
- `GET /api/whisper/status` - Server status
- `GET /api/audio/devices` - List audio devices
- `GET /api/config/audio` - Get audio config
- `POST /api/config/audio` - Update audio config
- `GET /api/config/model` - Get model config
- `POST /api/config/model` - Update model config
- `GET /api/config/vocabulary` - Get vocabulary config
- `POST /api/config/vocabulary` - Update vocabulary config

### Agent Server
- `GET /api/agent/status` - Agent status
- `POST /api/config/voice` - Update voice config

API Documentation: **http://localhost:8934/docs**

## 🛠️ Development

### Adding New Components
```bash
npx shadcn@latest add [component-name]
```

### Running Tests
```bash
npm run test
```

### Building for Production
```bash
npm run build
```

### Code Formatting
```bash
npm run lint
```

## 📊 Features Roadmap

- [x] Glassmorphic dark AMOLED theme
- [x] Hypr-Whisper configuration
- [x] Hypr-Voice Agent management
- [x] Voice synthesis configuration
- [x] MCP server management
- [x] Skills configuration
- [ ] WebSocket real-time updates
- [ ] Advanced audio visualization
- [ ] Agent conversation history
- [ ] Configuration import/export
- [ ] Multi-language support
- [ ] Mobile app (React Native)

## 🐛 Troubleshooting

### Frontend won't start
```bash
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend bridge errors
```bash
cd api
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Configuration not saving
- Ensure you have write permissions to config directories
- Check that Whisper/Agent servers are running
- Verify API bridge is running on port 8934

### Console errors about backend
- See [Console Error Fix Summary](CONSOLE_ERROR_FIX_SUMMARY.md)
- Run `./start-ui.sh` to start both frontend and backend
- UI will work with defaults if backend is offline

### Styling issues
- Clear browser cache
- Check that `globals.css` is properly imported
- Verify Tailwind CSS is configured

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](../LICENSE) file for details

## 🙏 Acknowledgments

- [Next.js](https://nextjs.org/) - React framework
- [shadcn/ui](https://ui.shadcn.com/) - Component library
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Lucide Icons](https://lucide.dev/) - Icon library

## 📞 Support

For issues and questions:
- Check the [main project documentation](../docs/README.md)
- Open an issue on GitHub
- Join our community Discord

---

**Built with ❤️ for the Hypr-Voice project**

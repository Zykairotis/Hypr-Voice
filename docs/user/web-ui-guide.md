# 🎤 Hypr-Voice Web UI

A modern, minimalistic web interface for managing Hypr-Voice configuration and monitoring with a purple/black theme.

## ✨ Features

### 🎯 **Core Capabilities**
- **Real-time Monitoring Dashboard** - Live audio levels, system metrics, and service status
- **Configuration Management** - Edit YAML/JSON configuration files with live validation
- **Model Control** - Switch between Whisper models and processing devices
- **Mode Switching** - Configure F9 (Raw) and F10 (Enhanced) modes
- **MCP Tools Management** - Configure Model Context Protocol tools and servers

### 🎨 **Modern UI Features**
- **Purple/Black Theme** - Sophisticated dark theme with purple accents
- **Glassmorphism Effects** - Modern frosted glass visual effects
- **Responsive Design** - Works seamlessly on desktop and mobile
- **Real-time Updates** - WebSocket-powered live monitoring
- **Smooth Animations** - Micro-interactions and transitions

### 🛠️ **Configuration Management**
- **Audio Settings** - Device selection, quality parameters, recording options
- **Application Profiles** - Per-application behavior and LLM settings
- **LLM Providers** - Multi-provider configuration with fallback support
- **MCP Configuration** - Server management and tool permissions
- **Import/Export** - Backup and restore configuration files

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** with virtual environment
- **Node.js 16+** and npm
- **Hypr-Voice** core system installed

### Installation

1. **Clone and Setup**
   ```bash
   cd /path/to/Hypr-Voice-main/hypr-voice
   ```

2. **Start the Web UI**
   ```bash
   ./scripts/start_web_ui.sh
   ```

3. **Access the Interface**
   - **Web UI**: http://localhost:3001
   - **API Server**: http://localhost:9091
   - **Existing Whisper API**: http://localhost:9880
   - **Existing SG-Lang API**: http://localhost:30000

### Manual Setup

If you prefer to start services manually:

1. **Start Backend Server**
   ```bash
   # Activate virtual environment
   source venv/bin/activate

   # Install dependencies
   pip install fastapi uvicorn psutil websockets

   # Start web server
   python web_server.py
   ```

2. **Start Frontend** (in another terminal)
   ```bash
   cd web_ui

   # Install dependencies
   npm install

   # Start development server
   npm run dev
   ```

## 📖 Interface Overview

### 🏠 **Dashboard**
- System status overview with real-time indicators
- Audio input visualization with level meters
- Service health monitoring (Whisper, SG-Lang)
- Quick access controls for mode switching
- Recent activity and system metrics

### ⚙️ **Configuration Panel**
- **Audio Settings** - Microphone configuration, quality settings
- **Application Profiles** - Per-app behavior customization
- **LLM Providers** - AI service configuration and management
- **MCP Tools** - Model Context Protocol server setup
- **Clipboard Profiles** - Paste behavior per application

### 🎛️ **Model Control**
- Whisper model selection (tiny → large)
- Processing device management (CPU/CUDA)
- Service start/stop/restart controls
- Performance monitoring

### 🔄 **Mode Switching**
- **F9 Raw Mode** - Fast transcription, no AI processing
- **F10 Enhanced Mode** - AI-enhanced with context awareness
- Real-time recording control
- Mode-specific configuration

### 🛠️ **MCP Tools**
- Server management (enable/disable/configure)
- Tool permission and auto-approval settings
- Environment variable configuration
- Real-time server status

## 🎨 Theme Customization

The interface uses a sophisticated purple/black theme with CSS variables:

```css
:root {
  --hypr-primary: #8B5CF6;
  --hypr-primary-dark: #7C3AED;
  --hypr-background: #0A0A0A;
  --hypr-surface: #2A2A2A;
  --hypr-text: #FFFFFF;
  /* ... more variables */
}
```

### Customization Options
- Modify CSS variables in `src/utils/theme.ts`
- Adjust glassmorphism effects
- Customize color schemes
- Modify animations and transitions

## 🔧 Technical Architecture

### Backend (FastAPI)
- **web_server.py** - Main API server with WebSocket support
- **RESTful endpoints** for configuration management
- **Real-time monitoring** via WebSocket connections
- **File system integration** for YAML/JSON configs

### Frontend (React + TypeScript)
- **Modern components** with Ant Design UI library
- **Type-safe development** with TypeScript definitions
- **Real-time updates** via WebSocket client
- **Responsive design** with mobile support

### Key Technologies
- **FastAPI** - High-performance Python web framework
- **React 18** - Modern UI development
- **TypeScript** - Type-safe JavaScript
- **Ant Design** - Component library
- **WebSocket** - Real-time communication

## 📁 Project Structure

```
hypr-voice/
├── web_server.py              # FastAPI backend server
├── web_ui/                    # React frontend application
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── Dashboard/     # Main dashboard components
│   │   │   ├── Configuration/ # Configuration editors
│   │   │   ├── ModelControl/  # Model management
│   │   │   ├── ModeSwitch/    # F9/F10 mode switching
│   │   │   └── McpTools/      # MCP tools management
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API service layer
│   │   ├── types/            # TypeScript definitions
│   │   └── utils/            # Utility functions
│   ├── static/               # Built static files
│   │   ├── css/             # Stylesheets
│   │   ├── js/              # JavaScript bundles
│   │   └── index.html       # Main HTML file
│   ├── package.json         # Node.js dependencies
│   └── vite.config.ts       # Vite build configuration
└── scripts/
    └── start_web_ui.sh       # Startup script
```

## 🔌 API Endpoints

### System Status
- `GET /api/status` - Get current system status
- `GET /api/audio/devices` - List available audio devices
- `GET /api/models` - Get available Whisper models

### Configuration
- `GET /api/config/{type}` - Load configuration by type
- `POST /api/config/{type}` - Save configuration
- `POST /api/config/{type}/validate` - Validate configuration

### Service Control
- `POST /api/model/switch` - Switch Whisper model
- `POST /api/service/control` - Start/stop/restart services

### WebSocket
- `WS /ws/monitor` - Real-time monitoring updates

## 🎯 Configuration Types

- **audio** - Audio device and quality settings
- **app_profiles** - Application-specific behavior
- **llm_providers** - AI service configuration
- **mcp** - Model Context Protocol servers
- **clipboard_profiles** - Paste behavior settings

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Kill processes on ports 9091 and 3000 (web UI services only)
   # NOTE: Do NOT kill existing services on ports 9880 and 30000
   lsof -ti:9091 | xargs kill -9
   lsof -ti:3000 | xargs kill -9
   ```

2. **Dependencies not found**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt

   # Install Node.js dependencies
   cd web_ui && npm install
   ```

3. **WebSocket connection failed**
   - Check if backend server is running on port 9090
   - Verify firewall settings
   - Check browser console for errors

4. **Configuration not saving**
   - Verify file permissions
   - Check backend logs for errors
   - Ensure YAML/JSON syntax is valid

### Getting Help

- Check the browser console for JavaScript errors
- Review backend server logs
- Verify all services are running
- Check network connectivity

## 🤝 Contributing

1. **Development Setup**
   ```bash
   cd hypr-voice/web_ui
   npm install
   npm run dev
   ```

2. **Building for Production**
   ```bash
   npm run build
   ```

3. **Code Style**
   - Use TypeScript for type safety
   - Follow React best practices
   - Maintain consistent naming conventions
   - Add proper error handling

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ant Design** - Excellent UI component library
- **FastAPI** - Modern Python web framework
- **React** - Powerful UI development library
- **Vite** - Fast build tool and dev server
- **Hypr-Voice** - Core voice input system

---

**🎉 Ready to get started?**

1. Run `./scripts/start_web_ui.sh`
2. Open http://localhost:3000
3. Configure your Hypr-Voice system visually!

**Need help?** Check the documentation or open an issue on GitHub.
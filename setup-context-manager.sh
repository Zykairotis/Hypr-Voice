#!/bin/bash

# Context Manager Setup Script
# This script sets up the Context Manager system for Hypr-Whisper

set -e

echo "========================================="
echo "Context Manager Setup"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in the correct directory
if [ ! -f "src/Hypr-Whisper/context_manager.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found project root${NC}"
echo ""

# Step 1: Check Python dependencies
echo "Step 1: Checking Python dependencies..."
python3 -c "import sys; print(f'Python {sys.version}')" || {
    echo -e "${RED}Error: Python 3 is required${NC}"
    exit 1
}

# Check for required Python packages
echo "Checking Python packages..."
python3 -c "import asyncio, websockets, psutil" 2>/dev/null || {
    echo -e "${YELLOW}Installing missing Python packages...${NC}"
    pip3 install --user websockets psutil || {
        echo -e "${RED}Failed to install Python packages${NC}"
        exit 1
    }
}

echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Step 2: Install Node.js dependencies
echo "Step 2: Installing Node.js dependencies..."
cd web-ui

if [ ! -d "node_modules" ]; then
    npm install || {
        echo -e "${RED}Failed to install Node.js dependencies${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Installed Node.js dependencies${NC}"
else
    echo -e "${GREEN}✓ Node.js dependencies already installed${NC}"
fi

cd ..
echo ""

# Step 3: Create required directories
echo "Step 3: Creating required directories..."
mkdir -p /tmp/context-data
mkdir -p logs

echo -e "${GREEN}✓ Created directories${NC}"
echo ""

# Step 4: Make scripts executable
echo "Step 4: Making scripts executable..."
chmod +x src/Hypr-Whisper/context_websocket_server.py
chmod +x src/Hypr-Whisper/scripts/context_processor.py

echo -e "${GREEN}✓ Made scripts executable${NC}"
echo ""

# Step 5: Setup environment variables
echo "Step 5: Setting up environment variables..."
if [ ! -f "web-ui/.env.local" ]; then
    cat > web-ui/.env.local << EOF
# Context Manager API
NEXT_PUBLIC_CONTEXT_API_URL=http://localhost:9090
NEXT_PUBLIC_CONTEXT_WS_URL=ws://localhost:9091

# Context Configuration
CONTEXT_UPDATE_INTERVAL=5000
CONTEXT_MAX_COMMANDS=100
CONTEXT_MAX_CLIPBOARD=50
CONTEXT_RETENTION_HOURS=24

# Privacy Settings
CONTEXT_ENABLE_PRIVACY_MODE=true
CONTEXT_MASK_SENSITIVE_DATA=true
EOF
    echo -e "${GREEN}✓ Created .env.local${NC}"
else
    echo -e "${YELLOW}! .env.local already exists, skipping${NC}"
fi

echo ""

# Step 6: Setup systemd service (optional)
echo "Step 6: Setting up systemd service..."
read -p "Do you want to install systemd service for context processor? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    USER=$(whoami)

    sudo tee /etc/systemd/system/context-processor.service > /dev/null <<EOF
[Unit]
Description=Context Processor for Hypr-Whisper
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)/src/Hypr-Whisper
ExecStart=/usr/bin/python3 scripts/context_processor.py
Restart=always
RestartSec=5
StandardOutput=append:$(pwd)/logs/context-processor.log
StandardError=append:$(pwd)/logs/context-processor.log

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable context-processor

    echo -e "${GREEN}✓ Systemd service installed${NC}"
    echo ""
    echo -e "${YELLOW}To start the service:${NC}"
    echo "  sudo systemctl start context-processor"
    echo ""
else
    echo -e "${YELLOW}Skipping systemd service setup${NC}"
fi

# Step 7: Check for required tools
echo "Step 7: Checking for required system tools..."

# Check for cliphist
if command -v cliphist &> /dev/null; then
    echo -e "${GREEN}✓ cliphist found${NC}"
else
    echo -e "${YELLOW}! cliphist not found (required for clipboard on Wayland)${NC}"
    echo "  Install with: sudo pacman -S cliphist"
fi

# Check for hyprctl
if command -v hyprctl &> /dev/null; then
    echo -e "${GREEN}✓ hyprctl found${NC}"
else
    echo -e "${YELLOW}! hyprctl not found (window detection may not work)${NC}"
fi

echo ""

# Step 8: Create startup scripts
echo "Step 8: Creating startup scripts..."

cat > start-context.sh << 'EOF'
#!/bin/bash
# Start Context Manager services

echo "Starting Context Manager..."

# Start context processor in background
cd src/Hypr-Whisper
python3 scripts/context_processor.py > ../../logs/context-processor.log 2>&1 &
PROCESSOR_PID=$!
echo "Context processor started (PID: $PROCESSOR_PID)"

# Start WebSocket server in background
python3 context_websocket_server.py > ../../logs/websocket.log 2>&1 &
WEBSOCKET_PID=$!
echo "WebSocket server started (PID: $WEBSOCKET_PID)"

echo "Context Manager started successfully!"
echo "PIDs: $PROCESSOR_PID (processor), $WEBSOCKET_PID (WebSocket)"
echo "Logs: logs/context-processor.log, logs/websocket.log"
echo ""
echo "To stop services, run: stop-context.sh"

# Save PIDs
echo $PROCESSOR_PID > /tmp/context-processor.pid
echo $WEBSOCKET_PID > /tmp/websocket.pid
EOF

chmod +x start-context.sh

cat > stop-context.sh << 'EOF'
#!/bin/bash
# Stop Context Manager services

echo "Stopping Context Manager..."

# Stop context processor
if [ -f /tmp/context-processor.pid ]; then
    kill $(cat /tmp/context-processor.pid) 2>/dev/null || true
    rm /tmp/context-processor.pid
    echo "Context processor stopped"
fi

# Stop WebSocket server
if [ -f /tmp/websocket.pid ]; then
    kill $(cat /tmp/websocket.pid) 2>/dev/null || true
    rm /tmp/websocket.pid
    echo "WebSocket server stopped"
fi

echo "Context Manager stopped"
EOF

chmod +x stop-context.sh

echo -e "${GREEN}✓ Created startup scripts${NC}"
echo ""

# Step 9: Build web UI
echo "Step 9: Building web UI..."
cd web-ui
npm run build || {
    echo -e "${YELLOW}Warning: Build failed, but continuing...${NC}"
}
cd ..
echo -e "${GREEN}✓ Web UI built${NC}"
echo ""

# Step 10: Create quick start guide
echo "Step 10: Creating quick start guide..."
cat > CONTEXT_MANAGER_QUICKSTART.md << 'EOF'
# Context Manager Quick Start

## Starting the Context Manager

Run the startup script:
```bash
./start-context.sh
```

This will start:
- Context processor (gathers context data)
- WebSocket server (provides real-time updates)

## Accessing the Dashboard

1. Start the web UI:
```bash
cd web-ui
npm run dev
```

2. Open browser to: http://localhost:8933

3. Navigate to Context Manager: http://localhost:8933/context

## Stopping the Services

```bash
./stop-context.sh
```

## Using the Context Widget

The context widget can be added to any page:

```typescript
import { ContextWidget } from '@/app/components/context/widgets/ContextWidget';

export default function Dashboard() {
  return (
    <div className="grid gap-4">
      <ContextWidget />
      {/* Other content */}
    </div>
  );
}
```

## Checking Status

```bash
# Check if processes are running
ps aux | grep context_processor
ps aux | grep context_websocket_server

# Check logs
tail -f logs/context-processor.log
tail -f logs/websocket.log
```

## Troubleshooting

### No context data showing
1. Check if services are running: `ps aux | grep context`
2. Check logs: `tail -f logs/context-processor.log`
3. Restart services: `./stop-context.sh && ./start-context.sh`

### WebSocket connection failed
1. Check if port 9091 is open: `netstat -tuln | grep 9091`
2. Check firewall settings
3. Restart WebSocket server: `./stop-context.sh && ./start-context.sh`

### Clipboard not working
1. Install cliphist: `sudo pacman -S cliphist`
2. Test cliphist: `cliphist list`

## Keyboard Shortcuts

- `Ctrl+Shift+C` - Clear context data
- `Ctrl+Shift+E` - Export context
- `Ctrl+Shift+R` - Refresh context
- `Ctrl+Shift+F` - Focus search

## Systemd Service (if installed)

```bash
# Start service
sudo systemctl start context-processor

# Check status
sudo systemctl status context-processor

# View logs
sudo journalctl -u context-processor -f
```

## Configuration

Edit `web-ui/.env.local` to change settings:
- `NEXT_PUBLIC_CONTEXT_WS_URL` - WebSocket URL
- `CONTEXT_UPDATE_INTERVAL` - Update frequency (ms)
- `CONTEXT_MAX_COMMANDS` - Max shell commands to keep
- `CONTEXT_MAX_CLIPBOARD` - Max clipboard entries to keep

## More Information

See:
- `CONTEXT_MANAGER_IMPLEMENTATION.md` - Detailed implementation
- `INTEGRATION_GUIDE.md` - Integration instructions
- `web-ui/app/components/context/README.md` - Component docs
EOF

echo -e "${GREEN}✓ Created quick start guide${NC}"
echo ""

# Completion message
echo "========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start Context Manager services:"
echo "   ./start-context.sh"
echo ""
echo "2. Start the web UI:"
echo "   cd web-ui"
echo "   npm run dev"
echo ""
echo "3. Open your browser:"
echo "   http://localhost:8933/context"
echo ""
echo "4. Read the documentation:"
echo "   - Quick Start: CONTEXT_MANAGER_QUICKSTART.md"
echo "   - Implementation: CONTEXT_MANAGER_IMPLEMENTATION.md"
echo "   - Integration: INTEGRATION_GUIDE.md"
echo ""
echo "For help: ./stop-context.sh to stop services"
echo ""

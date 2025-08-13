#!/bin/bash

# Hypr-Voice Setup Script
# Automated setup for Hypr-Voice on Arch Linux with Hyprland

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Hypr-Voice Setup ===${NC}"
echo

# Check if running on Arch Linux
if [ ! -f /etc/arch-release ]; then
    echo -e "${YELLOW}Warning: This script is designed for Arch Linux${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for Hyprland
if ! command -v hyprctl &> /dev/null; then
    echo -e "${YELLOW}Warning: Hyprland not detected${NC}"
    echo "Hypr-Voice works best with Hyprland window manager"
fi

echo -e "${GREEN}[1/7] Installing system dependencies...${NC}"
# Install system packages
sudo pacman -S --needed --noconfirm \
    python python-pip python-virtualenv \
    wl-clipboard libnotify wtype \
    sox ffmpeg portaudio \
    redis || true

echo -e "${GREEN}[2/7] Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

echo -e "${GREEN}[3/7] Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}[4/7] Setting up Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Pull default models
echo "Pulling Ollama models (this may take a while)..."
ollama pull llama3.1 || true
ollama pull codellama || true
echo "Models pulled successfully"

echo -e "${GREEN}[5/7] Creating directories...${NC}"
mkdir -p logs
mkdir -p models
mkdir -p data
mkdir -p config

echo -e "${GREEN}[6/7] Setting up environment configuration...${NC}"
if [ ! -f .env ]; then
    cat > .env << EOF
# Hypr-Voice Environment Configuration

# Whisper Settings
WHISPER_MODEL=small
WHISPER_SERVER_URL=http://localhost:9880
WHISPER_DEVICE=cuda  # Options: cuda, cpu
WHISPER_COMPUTE_TYPE=float16  # Options: float16, int8, float32

# LLM API Keys (optional - for cloud providers)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
XAI_API_KEY=

# Cognee Memory Configuration
EMBEDDING_PROVIDER=voyage
EMBEDDING_MODEL=voyage-code-3
EMBEDDING_API_KEY=
LANCEDB_API=
CHUNK_SIZE=1024
CHUNK_OVERLAP=128

# Paths
LOG_DIR=./logs
MODEL_DIR=./models
DATA_DIR=./data

# Debug
DEBUG=false
LOG_LEVEL=INFO
EOF
    echo ".env file created - Please add your API keys if using cloud providers"
else
    echo ".env file already exists"
fi

echo -e "${GREEN}[7/7] Setting up systemd services (optional)...${NC}"
cat > hypr-voice-whisper.service << EOF
[Unit]
Description=Hypr-Voice Whisper Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/whisper_server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

cat > hypr-voice-client.service << EOF
[Unit]
Description=Hypr-Voice Client
After=network.target hypr-voice-whisper.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DISPLAY=:0"
Environment="WAYLAND_DISPLAY=wayland-0"
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/hypr_voice_client.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

echo
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo
echo "To install systemd services (auto-start on boot):"
echo "  sudo cp hypr-voice-*.service /etc/systemd/user/"
echo "  systemctl --user daemon-reload"
echo "  systemctl --user enable hypr-voice-whisper"
echo "  systemctl --user enable hypr-voice-client"
echo
echo "To start Hypr-Voice manually:"
echo "  1. Start Redis: sudo systemctl start redis"
echo "  2. Start Ollama: ollama serve"
echo "  3. Start Whisper Server: source venv/bin/activate && python whisper_server.py"
echo "  4. Start Client: source venv/bin/activate && python hypr_voice_client.py"
echo
echo "Add to your Hyprland config (~/.config/hypr/hyprland.conf):"
echo "  bind = SUPER, V, exec, pkill -SIGUSR1 -f hypr_voice_client.py"
echo
echo -e "${GREEN}Enjoy Hypr-Voice!${NC}"

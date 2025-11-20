#!/bin/bash

# Install Voice Services Dependencies
# This script installs the required packages for all voice providers

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="/home/mewtwo/Zykairotis/Hypr-Voice/.venv"

echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}        Voice Services Installation Script${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo

# Check virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}Virtual environment not found at $VENV_PATH${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}→ Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Install ElevenLabs SDK
echo -e "${CYAN}→ Installing ElevenLabs SDK...${NC}"
pip install elevenlabs==1.9.0

# Install Deepgram SDK
echo -e "${CYAN}→ Installing Deepgram SDK...${NC}"
pip install deepgram-sdk==3.8.0

# Install Gemini dependencies for screen analysis
echo -e "${CYAN}→ Installing Gemini Live dependencies...${NC}"
pip install google-generativeai==0.8.3
pip install pillow==10.4.0
pip install mss==9.0.2

# Check installations
echo
echo -e "${CYAN}Checking installations...${NC}"

# Check ElevenLabs
if python -c "import elevenlabs" 2>/dev/null; then
    echo -e "${GREEN}✓ ElevenLabs SDK installed successfully${NC}"
else
    echo -e "${YELLOW}⚠ ElevenLabs SDK not installed${NC}"
fi

# Check Deepgram
if python -c "import deepgram" 2>/dev/null; then
    echo -e "${GREEN}✓ Deepgram SDK installed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Deepgram SDK not installed${NC}"
fi

# Check Gemini
if python -c "import google.generativeai" 2>/dev/null; then
    echo -e "${GREEN}✓ Google Generative AI installed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Google Generative AI not installed${NC}"
fi

# Check PIL
if python -c "from PIL import Image" 2>/dev/null; then
    echo -e "${GREEN}✓ Pillow installed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Pillow not installed${NC}"
fi

# Check mss
if python -c "import mss" 2>/dev/null; then
    echo -e "${GREEN}✓ MSS (screenshot) installed successfully${NC}"
else
    echo -e "${YELLOW}⚠ MSS not installed${NC}"
fi

# Create cache directories
echo
echo -e "${CYAN}→ Creating cache directories...${NC}"
mkdir -p /tmp/kokoro_cache
mkdir -p /tmp/elevenlabs_cache
mkdir -p /tmp/deepgram_cache
mkdir -p /tmp/voice_cache
echo -e "${GREEN}✓ Cache directories created${NC}"

# Test voice providers
echo
echo -e "${CYAN}Testing voice providers...${NC}"
python -c "
import sys
sys.path.append('$AGENT_DIR')

from services.voice import VoiceManager, VoiceProvider

manager = VoiceManager()
providers = manager.list_providers()

for provider in providers:
    status = '✓' if provider['available'] else '✗'
    print(f\"{status} {provider['name']}: {'Available' if provider['available'] else 'Not configured'}\")
" 2>/dev/null || echo -e "${YELLOW}Could not test providers (services may need configuration)${NC}"

echo
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        Installation Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo
echo -e "${CYAN}Next steps:${NC}"
echo -e "1. Add your API keys to ${YELLOW}.env${NC}:"
echo -e "   - ${YELLOW}ELEVENLABS_API_KEY${NC} - Get from https://elevenlabs.io"
echo -e "   - ${YELLOW}DEEPGRAM_API_KEY${NC} - Get from https://deepgram.com"
echo -e "   - ${YELLOW}GEMINI_API_KEY${NC} - Get from https://makersuite.google.com/app/apikey"
echo
echo -e "2. Test voice synthesis:"
echo -e "   ${YELLOW}python -c \"from services.voice import VoiceManager; import asyncio; asyncio.run(VoiceManager().synthesize('Hello world'))\"${NC}"
echo
echo -e "3. Available providers:"
echo -e "   - ${GREEN}Kokoro${NC}: Local, free, no API key required"
echo -e "   - ${CYAN}ElevenLabs${NC}: Premium quality, requires API key"
echo -e "   - ${CYAN}Deepgram${NC}: Fast & natural, requires API key"
echo

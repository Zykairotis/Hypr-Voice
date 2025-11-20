#!/bin/bash

# Install Claude SDK and set up integration
# This script installs the Claude Code SDK and configures the integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/.venv"
HYPR_VOICE_SRC="$PROJECT_ROOT/src/hypr_voice"
HYPR_VOICE_STATE_DIR="$PROJECT_ROOT/var/hypr_voice"
HYPR_VOICE_REQUIREMENTS="$PROJECT_ROOT/requirements/hypr_voice.txt"

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}        Claude Code SDK Installation Script${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}✗ Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}Please run the main installation script first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}→ Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Install Claude SDK
echo -e "${BLUE}→ Installing Claude Agent SDK...${NC}"
pip install claude-agent-sdk==0.2.1

# Check if installation was successful
if python -c "import claude_agent_sdk" 2>/dev/null; then
    echo -e "${GREEN}✓ Claude Agent SDK installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install Claude Agent SDK${NC}"
    exit 1
fi

# Install additional requirements for the Hypr Voice package
echo -e "${BLUE}→ Installing Hypr Voice requirements...${NC}"
if [ -f "$HYPR_VOICE_REQUIREMENTS" ]; then
    pip install -r "$HYPR_VOICE_REQUIREMENTS"
else
    echo -e "${YELLOW}⚠️ Requirements file not found at $HYPR_VOICE_REQUIREMENTS${NC}"
fi

# Create necessary directories under var/
echo -e "${BLUE}→ Creating runtime directories...${NC}"
mkdir -p "$HYPR_VOICE_STATE_DIR/logs/raw"
mkdir -p "$HYPR_VOICE_STATE_DIR/audio_output/raw_agent"
mkdir -p "$HYPR_VOICE_STATE_DIR/tts_output/claude"
mkdir -p "$HYPR_VOICE_STATE_DIR/cli_tts_output/history"
mkdir -p "$HYPR_VOICE_STATE_DIR/data"
mkdir -p "$HYPR_VOICE_STATE_DIR/sessions"

# Set executable permissions on helper scripts
echo -e "${BLUE}→ Setting permissions...${NC}"
chmod +x "$PROJECT_ROOT/scripts/hypr_voice/claude-tts" 2>/dev/null || true

# Test imports
echo -e "${BLUE}→ Testing imports...${NC}"
python -c "
import sys
from pathlib import Path
sys.path.append(str(Path('$PROJECT_ROOT') / 'src'))
try:
    from hypr_voice.services.tools.claude_code_integration import ClaudeCodeAgent, HyprlandMonitor
    print('✓ Claude Code integration module loaded successfully')
except ImportError as e:
    print(f'✗ Failed to import Claude Code integration: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All imports successful${NC}"
else
    echo -e "${RED}✗ Import test failed${NC}"
    exit 1
fi

# Create a test script
echo -e "${BLUE}→ Creating test script...${NC}"
cat > "$PROJECT_ROOT/test_claude_integration.py" << 'EOF'
#!/usr/bin/env python3
"""Test Claude SDK Integration"""

import asyncio
import sys
from pathlib import Path

# Add project src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from hypr_voice.services.tools.claude_code_integration import HyprlandMonitor

async def test_hyprland_detection():
    """Test Hyprland window detection"""
    monitor = HyprlandMonitor()
    
    print("Testing Hyprland window detection...")
    window = await monitor.get_active_window()
    
    if window:
        print(f"✓ Active window detected:")
        print(f"  Class: {window.get('class', 'N/A')}")
        print(f"  Title: {window.get('title', 'N/A')}")
    else:
        print("✗ No active window detected (is Hyprland running?)")
    
    print("\nTesting client list...")
    clients = await monitor.get_all_clients()
    
    if clients:
        print(f"✓ Found {len(clients)} windows:")
        for client in clients[:3]:  # Show first 3
            print(f"  - {client.get('class', 'N/A')}: {client.get('title', 'N/A')}")
    else:
        print("✗ No clients found")

if __name__ == "__main__":
    asyncio.run(test_hyprland_detection())
EOF

chmod +x "$PROJECT_ROOT/test_claude_integration.py"

echo
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        Installation Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Test Hyprland detection: ${YELLOW}python test_claude_integration.py${NC}"
echo -e "  2. Start the Agent system: ${YELLOW}./scripts/hypr_voice/start_system.sh${NC}"
echo -e "  3. Start Hypr-Whisper: ${YELLOW}./scripts/start_hybrid_server.sh${NC}"
echo
echo -e "${BLUE}Configuration files:${NC}"
echo -e "  - Agent config: ${YELLOW}config/hypr_voice/config.yaml${NC}"
echo -e "  - Claude SDK: ${YELLOW}config/hypr_voice/claude-sdk.yaml${NC}"
echo -e "  - Vocabulary: ${YELLOW}src/Hypr-Whisper/config/vocabulary.yaml${NC}"
echo
echo -e "${GREEN}The system is now configured to:${NC}"
echo -e "  • Use Claude Code SDK instead of API"
echo -e "  • Monitor Hyprland windows every 150ms"
echo -e "  • Switch vocabulary based on active application"
echo -e "  • Provide context-aware AI responses"
echo

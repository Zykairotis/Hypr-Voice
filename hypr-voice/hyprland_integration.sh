#!/bin/bash
# Hyprland integration for Hypr-Voice
# Add keybinds and setup push-to-talk functionality

HYPR_VOICE_DIR="$(dirname "$(readlink -f "$0")")"
HYPR_VOICE_CMD="python3 $HYPR_VOICE_DIR/hypr_voice.py"
RECORD_CMD="$HYPR_VOICE_DIR/record_audio.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Hypr-Voice Hyprland Integration${NC}"

# Check if Hyprland is running
if ! pgrep -x "Hyprland" > /dev/null; then
    echo -e "${RED}Error: Hyprland is not running${NC}"
    exit 1
fi

# Create record script
cat > "$RECORD_CMD" << 'EOF'
#!/bin/bash
# Record audio for Hypr-Voice

AUDIO_DIR="/tmp/hypr-voice"
mkdir -p "$AUDIO_DIR"

# Generate unique filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
AUDIO_FILE="$AUDIO_DIR/recording_${TIMESTAMP}.wav"

# Check if already recording
if pgrep -f "arecord.*hypr-voice" > /dev/null; then
    # Stop recording
    pkill -f "arecord.*hypr-voice"
    sleep 0.5
    
    # Find the latest recording
    LATEST=$(ls -t "$AUDIO_DIR"/recording_*.wav 2>/dev/null | head -1)
    
    if [ -f "$LATEST" ]; then
        # Process the recording
        python3 "$(dirname "$0")/hypr_voice.py" -f "$LATEST"
        
        # Clean up old recordings (keep last 10)
        ls -t "$AUDIO_DIR"/recording_*.wav 2>/dev/null | tail -n +11 | xargs -r rm
    fi
else
    # Start recording
    notify-send "Hypr-Voice" "Recording started..." -u low
    arecord -f cd -t wav "$AUDIO_FILE" &
fi
EOF

chmod +x "$RECORD_CMD"

# Add Hyprland keybinds
echo -e "${YELLOW}Adding Hyprland keybinds...${NC}"

# Check if config exists
HYPR_CONFIG="$HOME/.config/hypr/hyprland.conf"
if [ ! -f "$HYPR_CONFIG" ]; then
    echo -e "${RED}Error: Hyprland config not found at $HYPR_CONFIG${NC}"
    exit 1
fi

# Backup config
cp "$HYPR_CONFIG" "$HYPR_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"

# Check if keybinds already exist
if grep -q "Hypr-Voice" "$HYPR_CONFIG"; then
    echo -e "${YELLOW}Hypr-Voice keybinds already configured${NC}"
else
    # Add keybinds to config
    cat >> "$HYPR_CONFIG" << EOF

# Hypr-Voice Keybinds
bind = SUPER, V, exec, $RECORD_CMD # Push-to-talk recording
bind = SUPER SHIFT, V, exec, $HYPR_VOICE_CMD -r # Real-time mode
bind = SUPER ALT, V, exec, killall -9 python3 arecord 2>/dev/null # Stop all

EOF
    echo -e "${GREEN}Keybinds added to Hyprland config${NC}"
fi

# Create systemd service (optional)
SERVICE_FILE="$HOME/.config/systemd/user/hypr-voice.service"
mkdir -p "$(dirname "$SERVICE_FILE")"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Hypr-Voice - Voice input for Hyprland
After=graphical-session.target

[Service]
Type=simple
ExecStart=$HYPR_VOICE_CMD -p
Restart=on-failure
RestartSec=5
Environment="DISPLAY=:0"
Environment="WAYLAND_DISPLAY=wayland-1"

[Install]
WantedBy=default.target
EOF

echo -e "${GREEN}Systemd service created at $SERVICE_FILE${NC}"

# Reload Hyprland config
echo -e "${YELLOW}Reloading Hyprland configuration...${NC}"
hyprctl reload

echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Keybinds:"
echo "  SUPER + V        : Push-to-talk recording (press to start, press again to stop)"
echo "  SUPER + SHIFT + V: Real-time transcription mode"
echo "  SUPER + ALT + V  : Stop all Hypr-Voice processes"
echo ""
echo "To start the service automatically:"
echo "  systemctl --user enable hypr-voice.service"
echo "  systemctl --user start hypr-voice.service"
echo ""
echo "Manual usage:"
echo "  $HYPR_VOICE_CMD -f <audio_file>  # Transcribe audio file"
echo "  $HYPR_VOICE_CMD -r                # Real-time mode"
echo "  $HYPR_VOICE_CMD -p                # Push-to-talk mode"

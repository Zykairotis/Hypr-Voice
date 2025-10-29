#!/bin/bash
# Audio Setup Helper for Hypr-Voice WhisperLive

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHISPER_ROOT="$(dirname "$SCRIPT_DIR")"
DEFAULT_PROFILE="$WHISPER_ROOT/config/audio-profile.yaml"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🎤 Hypr-Voice Audio Configuration Helper${NC}"
echo ""

# Function to list all audio sources
list_sources() {
    echo -e "${GREEN}📋 Available PulseAudio Sources:${NC}"
    echo ""
    pactl list sources short
    echo ""
}

# Function to list all sinks (for monitors)
list_sinks() {
    echo -e "${GREEN}📋 Available PulseAudio Sinks (Outputs):${NC}"
    echo ""
    pactl list sinks short
    echo ""
    echo -e "${YELLOW}Tip: Monitors capture what's playing on outputs${NC}"
    echo ""
}

# Function to test recording
test_recording() {
    local source="${1:-@DEFAULT_SOURCE@}"
    local duration="${2:-5}"
    local output_file="/tmp/audio-test-$(date +%s).wav"
    
    echo -e "${GREEN}🎙️  Testing audio recording...${NC}"
    echo -e "Source: $source"
    echo -e "Duration: ${duration}s"
    echo -e "Output: $output_file"
    echo ""
    echo -e "${YELLOW}Recording in 3 seconds...${NC}"
    sleep 3
    
    parecord --channels=1 --rate=16000 --format=s16le --device="$source" "$output_file" &
    local pid=$!
    
    echo -e "${GREEN}Recording...${NC}"
    sleep "$duration"
    
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    
    echo ""
    if [ -f "$output_file" ]; then
        local size=$(du -h "$output_file" | cut -f1)
        echo -e "${GREEN}✅ Recording saved: $output_file ($size)${NC}"
        echo -e "Play it with: paplay $output_file"
    else
        echo -e "${RED}❌ Recording failed${NC}"
    fi
    echo ""
}

# Function to show current audio setup
show_current() {
    echo -e "${GREEN}📊 Current Audio Configuration:${NC}"
    echo ""
    echo -e "Default Source: $(pactl get-default-source)"
    echo -e "Default Sink:   $(pactl get-default-sink)"
    echo ""
}

# Function to set audio device from profile
apply_profile() {
    local profile_file="${1:-$DEFAULT_PROFILE}"
    
    if [ ! -f "$profile_file" ]; then
        echo -e "${RED}❌ Profile not found: $profile_file${NC}"
        return 1
    fi
    
    echo -e "${GREEN}📝 Reading audio profile...${NC}"
    
    # Requires Python with PyYAML
    local device=$(python3 -c "
import yaml
with open('$profile_file', 'r') as f:
    config = yaml.safe_load(f)
    print(config['pulseaudio']['default_source'])
" 2>/dev/null)
    
    if [ -n "$device" ]; then
        echo -e "Setting default source to: $device"
        pactl set-default-source "$device"
        echo -e "${GREEN}✅ Audio profile applied${NC}"
        echo ""
        show_current
    else
        echo -e "${RED}❌ Could not read device from profile${NC}"
    fi
}

# Main menu
case "${1:-menu}" in
    list|ls)
        list_sources
        list_sinks
        ;;
    test)
        show_current
        test_recording "${2:-@DEFAULT_SOURCE@}" "${3:-5}"
        ;;
    apply)
        apply_profile "${2:-audio-profile.yaml}"
        ;;
    current|status)
        show_current
        ;;
    *)
        echo "Usage: $0 {list|test|apply|current}"
        echo ""
        echo "Commands:"
        echo "  list              - List all available audio sources and sinks"
        echo "  test [source] [s] - Test recording (default: 5 seconds from default source)"
        echo "  apply [profile]   - Apply audio profile (default: audio-profile.yaml)"
        echo "  current           - Show current audio configuration"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 test"
        echo "  $0 test alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor 10"
        echo "  $0 apply audio-profile.yaml"
        ;;
esac

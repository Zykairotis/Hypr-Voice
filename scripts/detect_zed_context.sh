#!/bin/bash
# Zed Context Detection Script for Hyprland
# Detects whether Zed Editor is in terminal or editor context based on window title

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if jq is available
check_dependencies() {
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Error: jq is required but not installed${NC}"
        echo "Install with: sudo pacman -S jq"
        exit 1
    fi

    if ! command -v hyprctl &> /dev/null; then
        echo -e "${RED}Error: hyprctl not found. Are you running Hyprland?${NC}"
        exit 1
    fi
}

# Function to get current window information
get_window_info() {
    local window_info=$(hyprctl activewindow -j 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to get window information${NC}"
        exit 1
    fi

    echo "$window_info"
}

# Function to detect Zed context
detect_zed_context() {
    local class="$1"
    local title="$2"

    # Check if this is Zed at all
    if [[ "$class" != "dev.zed.Zed" ]]; then
        echo "other"
        return
    fi

    # Terminal context detection patterns
    local terminal_patterns=(
        ".*@.*:.*"        # user@host:path format
        "^Terminal"       # Generic terminal title
        "^(bash|zsh|fish)" # Shell names at start
        ".*\\$"           # Shell prompt ending with $
        "^~\\$"           # Home directory prompt
        "^/.*\\$"         # Full path prompt
        ".*\\[.*\\].*\\$"  # Prompt with brackets
        ".*%$"            # Fish shell prompt
    )

    # Editor context detection patterns
    local editor_patterns=(
        "^(.+) — (.+)$"   # filename — project format
        "\\.[a-z]+$"      # File extensions
        "^[^@]*\$"        # No @ symbol (not terminal)
        "^[^—]*\$"        # No em dash (not project format)
        "^[^\\\$]*\$"     # No $ prompt (not terminal)
    )

    # Check terminal patterns
    for pattern in "${terminal_patterns[@]}"; do
        if [[ "$title" =~ $pattern ]]; then
            echo "terminal"
            return
        fi
    done

    # Check editor patterns
    for pattern in "${editor_patterns[@]}"; do
        if [[ "$title" =~ $pattern ]]; then
            echo "editor"
            return
        fi
    done

    # If no specific pattern matches, check generic indicators
    if [[ "$title" == *"Terminal"* ]] || [[ "$title" == *"@"* ]]; then
        echo "terminal"
    elif [[ "$title" == *" — "* ]] || [[ "$title" =~ \.[a-z]+$ ]]; then
        echo "editor"
    else
        echo "unknown"
    fi
}

# Function to display detailed information
show_detailed_info() {
    local window_info="$1"
    local class=$(echo "$window_info" | jq -r '.class // "unknown"')
    local title=$(echo "$window_info" | jq -r '.title // "unknown"')
    local initial_class=$(echo "$window_info" | jq -r '.initialClass // "unknown"')
    local initial_title=$(echo "$window_info" | jq -r '.initialTitle // "unknown"')
    local pid=$(echo "$window_info" | jq -r '.pid // "unknown"')
    local workspace=$(echo "$window_info" | jq -r '.workspace.name // "unknown"')
    local xwayland=$(echo "$window_info" | jq -r '.xwayland // "unknown"')

    echo -e "${BLUE}=== Window Information ===${NC}"
    echo -e "Class: ${GREEN}$class${NC}"
    echo -e "Title: ${GREEN}$title${NC}"
    echo -e "Initial Class: ${YELLOW}$initial_class${NC}"
    echo -e "Initial Title: ${YELLOW}$initial_title${NC}"
    echo -e "PID: $pid"
    echo -e "Workspace: $workspace"
    echo -e "XWayland: $xwayland"
    echo ""
}

# Function to monitor focus changes in real-time
monitor_focus() {
    echo -e "${BLUE}Monitoring Zed context changes...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""

    local last_context=""
    local last_title=""

    while true; do
        local window_info=$(get_window_info)
        local class=$(echo "$window_info" | jq -r '.class // "unknown"')
        local title=$(echo "$window_info" | jq -r '.title // "unknown"')
        local context=$(detect_zed_context "$class" "$title")

        # Only display when context changes
        if [[ "$class" == "dev.zed.Zed" && ("$context" != "$last_context" || "$title" != "$last_title") ]]; then
            local timestamp=$(date '+%H:%M:%S')
            echo -e "[${timestamp}] ${GREEN}Zed Context: ${context}${NC} | Title: $title"
            last_context="$context"
            last_title="$title"
        fi

        sleep 0.5
    done
}

# Function to test with sample titles
test_patterns() {
    echo -e "${BLUE}Testing pattern detection with sample titles:${NC}"
    echo ""

    local test_titles=(
        "settings.nix — nixcfg"
        "user@hostname:~/project"
        "bash — nixcfg"
        "main.py"
        "zsh — myproject"
        "Terminal"
        "user@dev-machine:/var/log"
        "config.json"
        "~$"
        "/home/user/projects$"
        "[user@host] ~/projects$"
        "fish ~/development/project"
    )

    for title in "${test_titles[@]}"; do
        local context=$(detect_zed_context "dev.zed.Zed" "$title")
        local color=""
        case "$context" in
            "terminal") color="$YELLOW" ;;
            "editor") color="$GREEN" ;;
            "unknown") color="$RED" ;;
            *) color="$NC" ;;
        esac
        echo -e "\"${title}\" → ${color}${context}${NC}"
    done
}

# Main function
main() {
    # Parse command line arguments
    case "${1:-detect}" in
        "detect"|"d")
            check_dependencies
            window_info=$(get_window_info)
            class=$(echo "$window_info" | jq -r '.class // "unknown"')
            title=$(echo "$window_info" | jq -r '.title // "unknown"')
            context=$(detect_zed_context "$class" "$title")

            if [[ "$class" == "dev.zed.Zed" ]]; then
                color=""
                case "$context" in
                    "terminal") color="$YELLOW" ;;
                    "editor") color="$GREEN" ;;
                    "unknown") color="$RED" ;;
                    *) color="$NC" ;;
                esac
                echo -e "Current Zed Context: ${color}${context}${NC}"
                show_detailed_info "$window_info"
            else
                echo -e "${YELLOW}Not running Zed Editor${NC}"
                echo "Current window class: $class"
                echo "Current window title: $title"
            fi
            ;;

        "monitor"|"m")
            check_dependencies
            monitor_focus
            ;;

        "test"|"t")
            test_patterns
            ;;

        "help"|"h"|"-h"|"--help")
            echo "Zed Context Detection Script"
            echo ""
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  detect, d      Detect current Zed context (default)"
            echo "  monitor, m     Monitor focus changes in real-time"
            echo "  test, t        Test pattern detection with sample titles"
            echo "  help, h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                # Detect current context"
            echo "  $0 monitor        # Monitor focus changes"
            echo "  $0 test           # Test patterns"
            ;;

        *)
            echo -e "${RED}Unknown command: $1${NC}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
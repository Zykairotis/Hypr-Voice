#!/bin/bash

echo "🎯 Real-time Window Title Monitor"
echo "=================================="
echo "This will show you exactly how window titles change when you click different areas"
echo ""
echo "Instructions:"
echo "1. Open VS Code or any app with different areas (editor, terminal, etc.)"
echo "2. Click between different areas"
echo "3. Watch how the title changes instantly"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Monitor window title changes in real-time
last_title=""

while true; do
    current_title=$(hyprctl activewindow -j | jq -r '.title // "Unknown"')
    current_class=$(hyprctl activewindow -j | jq -r '.class // "Unknown"')

    if [[ "$current_title" != "$last_title" ]]; then
        echo "🔄 Title changed:"
        echo "   Class: $current_class"
        echo "   Title: $current_title"
        echo "   Time: $(date '+%H:%M:%S.%3N')"
        echo ""
        last_title="$current_title"
    fi

    sleep 0.05  # Check every 50ms for responsive detection
done
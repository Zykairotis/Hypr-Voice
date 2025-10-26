#!/bin/bash

echo "🧪 Universal Paste Test"
echo "======================="

TEST_TEXT="Test at $(date +%H:%M:%S)"
echo "📋 Text: $TEST_TEXT"
echo "⏰ 3 seconds to switch windows..."

echo "$TEST_TEXT" | wl-copy

for i in 3 2 1; do
    echo "⏳ $i"
    sleep 1
done

echo "🎯 Pasting..."
wtype "$TEST_TEXT" && echo "✅ Success!" || echo "❌ Failed"
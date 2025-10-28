#!/usr/bin/env python3
"""
Final test for WhisperLive server with GPU
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def test_whisper_live():
    try:
        from whisper_live.client import TranscriptionClient

        print("🧪 Testing WhisperLive Server")
        print("=" * 40)
        print("🔗 Connecting to ws://localhost:9090")
        print("📤 This will trigger model download and GPU usage")

        # Create client with large model (will download if needed)
        client = TranscriptionClient(
            host="localhost",
            port=9090,
            lang="en",
            translate=False,
            model="large-v3",  # Start with standard large model
            use_vad=True,
        )

        print("✅ Client created")
        print("⏳ Connecting to trigger model loading...")
        print("   Monitor nvidia-smi in another terminal to see VRAM usage")
        print("   Press Ctrl+C to stop")

        # Connect to trigger model loading
        client()

    except Exception as e:
        print(f"❌ Error: {e}")
        if "already in use" in str(e):
            print("💡 Port 9090 is in use, server should be running")
        return False

    return True

def main():
    try:
        success = asyncio.run(test_whisper_live())
        if success:
            print("\n🎉 Connection test completed!")
            print("💡 Check nvidia-smi to see if model loaded in VRAM")
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
    except Exception as e:
        print(f"\n❌ Test error: {e}")

if __name__ == "__main__":
    main()
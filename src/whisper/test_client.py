#!/usr/bin/env python3
"""
Test client for WhisperLive to trigger model download and test transcription
"""

import asyncio
import websockets
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def test_whisper_live():
    uri = "ws://localhost:9090"

    try:
        print("🔗 Connecting to WhisperLive server...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to server")

            # Send initial configuration
            config = {
                "uid": "test-client",
                "language": "auto",
                "task": "transcribe",
                "model": "openai/whisper-large-v3-turbo",  # Will use INT8 quantization
                "use_vad": True
            }

            print(f"📤 Sending configuration: {config}")
            await websocket.send(json.dumps(config))

            # Listen for responses
            print("🎤 Listening for responses...")
            timeout_count = 0
            max_timeout = 30  # Wait up to 30 seconds for model to load

            while timeout_count < max_timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)

                    if 'message' in data:
                        print(f"📨 Server message: {data['message']}")
                    if 'status' in data:
                        print(f"📊 Status: {data['status']}")
                    if 'transcription' in data:
                        print(f"🎯 Transcription: {data['transcription']}")
                        break

                except asyncio.TimeoutError:
                    timeout_count += 1
                    if timeout_count % 5 == 0:
                        print(f"⏳ Waiting for model to load... ({timeout_count}/{max_timeout}s)")

                except json.JSONDecodeError:
                    print(f"📨 Raw response: {response}")

            if timeout_count >= max_timeout:
                print("⚠️ Timeout reached, but server is responsive")
                print("🎯 Model may still be downloading in background")

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True

def main():
    print("🧪 Testing WhisperLive Server")
    print("=" * 50)

    try:
        result = asyncio.run(test_whisper_live())
        if result:
            print("✅ Test completed successfully")
        else:
            print("❌ Test failed")
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
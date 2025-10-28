#!/usr/bin/env python3
"""
Test client for WhisperLive with large-v3-turbo model
"""

import sys
import asyncio
import websockets
import json
import time
import subprocess
from pathlib import Path

async def test_whisper_live():
    """Test WhisperLive with large-v3-turbo"""

    server_url = "ws://localhost:9090"

    print(f"🎤 Testing WhisperLive with large-v3-turbo")
    print(f"🔗 Server: {server_url}")

    try:
        async with websockets.connect(server_url) as websocket:
            print("✅ Connected to WhisperLive server")

            # Configure client for large-v3-turbo
            config = {
                "type": "recognize",
                "language": "auto",
                "task": "transcribe",
                "model": "large-v3-turbo",
                "initial_prompt": "",
                "temperature": 0.0,
                "max_tokens": None,
                "use_vad": True,
                "vad_threshold": 0.5,
                "single_segment": False
            }

            # Send configuration
            await websocket.send(json.dumps(config))
            print("📤 Sent configuration for large-v3-turbo")

            # Listen for responses
            timeout = 30
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)

                    if data.get("type") == "recognition_event":
                        if "results" in data and data["results"]:
                            transcript = data["results"][0].get("transcript", "")
                            if transcript.strip():
                                print(f"📝 Transcript: {transcript}")
                                return True
                        elif "message" in data:
                            print(f"ℹ️ Server message: {data['message']}")

                except asyncio.TimeoutError:
                    print(f"⏳ Waiting for response... ({int(time.time() - start_time)}s)")
                    continue
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break

            print("⏰ Test completed (timeout reached)")
            return False

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def check_vram():
    """Check VRAM usage before and after model loading"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True
        )
        used, total = map(int, result.stdout.strip().split(", "))
        print(f"📊 VRAM: {used} MB / {total} MB ({used/total*100:.1f}%)")
        return used, total
    except:
        print("📊 VRAM: Unable to query GPU")
        return None, None

async def main():
    print("🎯 Large-v3-turbo Model Test")
    print("=" * 50)

    # Check initial VRAM
    print("🔍 Checking initial VRAM usage...")
    initial_vram, total_vram = check_vram()

    # Test WhisperLive
    success = await test_whisper_live()

    # Check final VRAM
    print("\n🔍 Checking final VRAM usage...")
    final_vram, _ = check_vram()

    if initial_vram and final_vram:
        vram_diff = final_vram - initial_vram
        print(f"📈 VRAM change: {vram_diff:+d} MB")

        if vram_diff > 100:  # Significant VRAM increase suggests model loaded
            print("✅ Model appears to be loaded in GPU")
        else:
            print("⚠️ Model may not be loaded in GPU")

    print("\n🎉 Test completed!")
    if success:
        print("✅ WhisperLive with large-v3-turbo is working")
    else:
        print("❌ WhisperLive test failed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
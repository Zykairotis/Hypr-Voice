#!/usr/bin/env python3
"""
Script to trigger WhisperLive model download and verify VRAM usage
"""

import sys
import time
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def check_gpu_usage():
    """Check current GPU VRAM usage"""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            return int(result.stdout.strip())
    except:
        pass
    return 0

def test_model_loading():
    """Test if model gets loaded when client connects"""
    print("🎯 Triggering WhisperLive Model Download Test")
    print("=" * 50)

    # Check initial VRAM usage
    initial_vram = check_gpu_usage()
    print(f"📊 Initial VRAM usage: {initial_vram} MB")

    try:
        from whisper_live.client import TranscriptionClient

        print("🔗 Creating WhisperLive client...")
        client = TranscriptionClient(
            host="localhost",
            port=9090,
            lang="en",
            translate=False,
            model="large-v3",  # Use correct model name
            use_vad=False,  # Disable VAD for simpler test
        )

        print("✅ Client created")
        print("⏳ Connecting to trigger model download...")
        print("   (This should download large-v3 model if not cached)")
        print("   Watch your network activity and VRAM usage...")

        # Record start time
        start_time = time.time()
        start_vram = check_gpu_usage()

        # Try to connect (this should trigger model loading)
        try:
            # We'll run this for a limited time to see if model loads
            print("🎤 Attempting to connect and initialize model...")
            print("   (Will timeout after 60 seconds)")

            # Use timeout to prevent hanging
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Model loading timeout")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)  # 60 second timeout

            # This will try to connect and load the model
            client()

        except TimeoutError:
            print("⏰ Timeout reached - checking if model started loading...")
        except KeyboardInterrupt:
            print("\n⏹️ Interrupted by user")
        except Exception as e:
            if "connect" in str(e).lower() or "server" in str(e).lower():
                print(f"❌ Connection error: {e}")
                return False
            else:
                print(f"📥 Model activity detected: {e}")

        finally:
            signal.alarm(0)  # Cancel timeout

        # Check VRAM after connection attempt
        end_vram = check_gpu_usage()
        vram_increase = end_vram - start_vram

        print(f"\n📊 VRAM Usage Analysis:")
        print(f"   Before: {start_vram} MB")
        print(f"   After:  {end_vram} MB")
        print(f"   Increase: {vram_increase} MB")

        if vram_increase > 500:  # Large model should use at least 500MB VRAM
            print("✅ SUCCESS: Model appears to be loaded in VRAM!")
            return True
        elif vram_increase > 100:
            print("🔄 Some activity detected - model may be loading...")
            return True
        else:
            print("❌ No significant VRAM increase - model not loaded")
            return False

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    try:
        success = test_model_loading()

        if success:
            print("\n🎉 Model loading test indicates activity!")
            print("💡 Check nvidia-smi to confirm VRAM usage")
            print("🌐 Monitor network for download activity")
        else:
            print("\n⚠️ Model loading may not have started")
            print("💡 Check server logs and network connection")

    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
    except Exception as e:
        print(f"\n❌ Test error: {e}")

if __name__ == "__main__":
    main()
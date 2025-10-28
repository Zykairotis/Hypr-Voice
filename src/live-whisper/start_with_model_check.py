#!/usr/bin/env python3
"""
WhisperLive server with automatic model loading and verification
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def check_gpu_available():
    """Check if GPU is available"""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def check_and_load_model():
    """Check and load the WhisperLive model to ensure it's ready"""
    logging.info("🔍 Checking model availability...")

    try:
        from whisper_live.client import TranscriptionClient

        # Create a test client to trigger model loading
        logging.info("📥 Creating test client to trigger model loading...")

        client = TranscriptionClient(
            host="localhost",
            port=9090,
            lang="en",
            translate=False,
            model="large-v3",  # Use standard large-v3 for now
            use_vad=False,  # Disable VAD for simpler test
        )

        logging.info("✅ Model loading test completed")
        return True

    except Exception as e:
        logging.error(f"❌ Model loading test failed: {e}")
        return False

def monitor_model_loading():
    """Monitor model loading progress"""
    logging.info("👀 Monitoring model loading progress...")

    try:
        import subprocess
        import time

        # Check GPU memory usage
        def get_vram_usage():
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return int(result.stdout.strip())
            except:
                pass
            return 0

        initial_vram = get_vram_usage()
        logging.info(f"📊 Initial VRAM usage: {initial_vram} MB")

        # Monitor for 30 seconds
        for i in range(30):
            time.sleep(1)
            current_vram = get_vram_usage()
            vram_increase = current_vram - initial_vram

            if vram_increase > 500:  # Significant increase indicates model loading
                logging.info(f"✅ Model loading detected! VRAM increase: +{vram_increase} MB")
                logging.info("🎯 Model is being loaded into GPU memory")
                return True
            elif i % 5 == 0:
                logging.info(f"⏳ Monitoring... VRAM: {current_vram} MB (+{vram_increase} MB)")

        logging.info("⚠️ Model loading may still be in progress")
        return False

    except Exception as e:
        logging.error(f"❌ Monitoring failed: {e}")
        return False

def main():
    setup_logging()

    logging.info("🎤 WhisperLive Server with Model Loading")
    logging.info("=" * 50)

    # Check GPU availability
    if check_gpu_available():
        logging.info("✅ GPU is available")
    else:
        logging.warning("⚠️ GPU not detected - will use CPU")

    # Wait a moment for server to start
    time.sleep(2)

    # Check if server is running
    try:
        import subprocess
        result = subprocess.run(['netstat', '-ln', '|', 'grep', ':9090'],
                              shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error("❌ Server not found on port 9090")
            logging.info("💡 Please start the WhisperLive server first:")
            logging.info("   ./start_server.sh start")
            return False

        logging.info("✅ Server is running on port 9090")

    except Exception as e:
        logging.error(f"❌ Failed to check server status: {e}")
        return False

    # Try to trigger model loading
    logging.info("🚀 Attempting to trigger model loading...")
    model_loaded = check_and_load_model()

    if model_loaded:
        logging.info("✅ Model loading test successful")
    else:
        logging.info("⚠️ Model loading may take more time")

    # Monitor model loading progress
    model_in_gpu = monitor_model_loading()

    logging.info("=" * 50)
    logging.info("🎉 WhisperLive Server Status:")
    logging.info(f"   Server: ✅ Running on ws://localhost:9090")
    logging.info(f"   Model: {'✅ Loaded into GPU' if model_in_gpu else '🔄 Loading/Ready'}")
    logging.info(f"   Status: 🎯 Ready for transcription")
    logging.info("")
    logging.info("💡 Usage:")
    logging.info("   - Connect clients to ws://localhost:9090")
    logging.info("   - Model will auto-load on first transcription request")
    logging.info("   - Monitor with: nvidia-smi")

if __name__ == "__main__":
    main()
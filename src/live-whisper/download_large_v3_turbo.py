#!/usr/bin/env python3
"""
Download and configure large-v3-turbo model for WhisperLive
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def download_large_v3_turbo():
    """Download large-v3-turbo model from HuggingFace"""
    print("📥 Downloading large-v3-turbo model from HuggingFace...")

    try:
        from huggingface_hub import snapshot_download

        # Create model directory
        model_dir = Path("/tmp/whisper-models/large-v3-turbo")
        model_dir.mkdir(parents=True, exist_ok=True)

        # Download model
        model_path = snapshot_download(
            repo_id="openai/whisper-large-v3-turbo",
            cache_dir="/tmp/whisper-models",
            local_files_only=False,
            resume_download=True
        )

        print(f"✅ Model downloaded to: {model_path}")

        # Create a symlink for easier access
        symlink_path = Path("/tmp/whisper-models/large-v3-turbo")
        if symlink_path.exists():
            symlink_path.unlink()

        symlink_path.symlink_to(model_path, target_is_directory=True)
        print(f"🔗 Created symlink: {symlink_path} -> {model_path}")

        # List model files
        print(f"📁 Model files:")
        for item in sorted(model_path.iterdir()):
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f"   - {item.name} ({size_mb:.1f} MB)")

        return str(model_path)

    except ImportError:
        print("❌ huggingface_hub not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
        return download_large_v3_turbo()
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def update_config(model_path):
    """Update WhisperLive configuration to use large-v3-turbo"""
    print("🔧 Updating configuration...")

    config_file = Path("config.yaml")
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return False

    # Read current config
    with open(config_file, 'r') as f:
        content = f.read()

    # Update model path to use local model
    content = content.replace(
        'model: "openai/whisper-large-v3-turbo"',
        f'model: "{model_path}"'
    )

    # Write updated config
    with open(config_file, 'w') as f:
        f.write(content)

    print(f"✅ Updated config.yaml with model path: {model_path}")
    return True

def restart_server():
    """Restart WhisperLive server with new configuration"""
    print("🔄 Restarting server...")

    # Kill existing server
    try:
        subprocess.run(["pkill", "-f", "start_whisper_live.py"], check=False)
        subprocess.run(["pkill", "-f", "run_server.py"], check=False)
        print("🛑 Stopped existing server")
    except:
        pass

    # Wait a moment
    import time
    time.sleep(2)

    # Start new server
    print("🚀 Starting server with large-v3-turbo...")
    server_process = subprocess.Popen([
        sys.executable, "start_whisper_live.py", "--config", "config.yaml"
    ])

    return server_process.pid

def main():
    print("🎯 Large-v3-turbo Setup for WhisperLive")
    print("=" * 50)

    # Step 1: Download model
    model_path = download_large_v3_turbo()
    if not model_path:
        print("❌ Failed to download model")
        return False

    # Step 2: Update configuration
    if not update_config(model_path):
        print("❌ Failed to update configuration")
        return False

    # Step 3: Restart server
    server_pid = restart_server()

    print("\n🎉 Setup completed!")
    print(f"📂 Model path: {model_path}")
    print(f"🔧 Config updated: config.yaml")
    print(f"🚀 Server PID: {server_pid}")
    print("\n💡 Next steps:")
    print("   1. Wait for server to start")
    print("   2. Monitor VRAM usage with: nvidia-smi")
    print("   3. Test with: python test_real_client.py")

    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Setup interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        sys.exit(1)
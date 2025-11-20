#!/usr/bin/env python3
"""
Voice Configuration Tool
Configure and test voices for specific use cases
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
def load_env():
    try:
        env_path = Path('/home/mewtwo/Zykairotis/Hypr-Voice/.env')
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#') and '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        return True
    except:
        return False

# Voice presets for different use cases
VOICE_PRESETS = {
    "professional": {
        "voice": "athena",
        "description": "Professional British voice for business content",
        "settings": {
            "speaking_rate": 1.0,
            "pitch": 0.0,
            "volume": 1.0
        }
    },
    "customer_service": {
        "voice": "helena",
        "description": "Caring American voice for customer support",
        "settings": {
            "speaking_rate": 0.9,
            "pitch": 1.0,
            "volume": 0.9
        }
    },
    "energetic": {
        "voice": "stella",
        "description": "Energetic voice for marketing and sales",
        "settings": {
            "speaking_rate": 1.2,
            "pitch": 2.0,
            "volume": 1.1
        }
    },
    "calm": {
        "voice": "luna",
        "description": "Gentle voice for relaxation and education",
        "settings": {
            "speaking_rate": 0.8,
            "pitch": 1.5,
            "volume": 0.8
        }
    },
    "authoritative": {
        "voice": "zeus",
        "description": "Deep male voice for announcements",
        "settings": {
            "speaking_rate": 0.95,
            "pitch": -2.0,
            "volume": 1.0
        }
    }
}

async def test_voice_preset(preset_name, test_text=None):
    """Test a specific voice preset"""

    if preset_name not in VOICE_PRESETS:
        print(f"❌ Preset '{preset_name}' not found")
        print("Available presets:", list(VOICE_PRESETS.keys()))
        return False

    preset = VOICE_PRESETS[preset_name]
    voice = preset["voice"]
    settings = preset["settings"]

    # Use default test text if none provided
    if not test_text:
        test_text = f"This is the {preset_name} preset using {preset['description'].lower()}."

    print(f"🎤 Testing {preset_name.upper()} preset")
    print(f"📋 Voice: {voice} - {preset['description']}")
    print(f"⚙️  Settings: {settings}")
    print(f"📝 Text: {test_text}")

    try:
        # Use CLI tool with voice
        import subprocess

        cmd = [
            'python', 'deepgram_clp.py',
            test_text,
            '--voice', voice
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Preset test successful!")
            # Extract output file path from CLI output
            for line in result.stdout.split('\n'):
                if 'Output:' in line:
                    output_file = line.split('Output:')[-1].strip()
                    print(f"📁 Audio: {output_file}")
                    break
            return True
        else:
            print(f"❌ Preset test failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error testing preset: {e}")
        return False

def show_presets():
    """Display all available presets"""
    print("🎨 Available Voice Presets")
    print("=" * 50)

    for name, preset in VOICE_PRESETS.items():
        print(f"\n📌 {name.upper()}")
        print(f"   Voice: {preset['voice']}")
        print(f"   Description: {preset['description']}")
        print(f"   Settings: {preset['settings']}")

def create_custom_preset():
    """Interactive custom preset creation"""
    print("🎛️  Create Custom Voice Preset")
    print("=" * 30)

    # Available voices
    voices = [
        "asteria", "luna", "stella", "athena", "hera", "thalia",
        "andromeda", "helena", "orion", "apollo", "arcas",
        "aries", "zeus", "orpheus", "nestor"
    ]

    print("\nAvailable voices:")
    for i, voice in enumerate(voices, 1):
        print(f"   {i:2d}. {voice}")

    try:
        # Get user input
        voice_num = int(input(f"\nSelect voice (1-{len(voices)}): "))
        if 1 <= voice_num <= len(voices):
            selected_voice = voices[voice_num - 1]
        else:
            print("❌ Invalid selection")
            return

        # Get settings
        rate = float(input("Speaking rate (0.5-2.0, 1.0=normal): ") or 1.0)
        pitch = float(input("Pitch adjustment (-10 to +10, 0=natural): ") or 0.0)
        volume = float(input("Volume (0.0-2.0, 1.0=normal): ") or 1.0)

        # Display configuration
        print(f"\n🎛️  Your Custom Preset:")
        print(f"   Voice: {selected_voice}")
        print(f"   Rate: {rate}")
        print(f"   Pitch: {pitch}")
        print(f"   Volume: {volume}")

        # Test the preset
        test_text = input("\nEnter test text (or press Enter for default): ").strip()
        if not test_text:
            test_text = "This is your custom voice preset in action."

        # Create temporary config file
        config_data = f"""
voice: {selected_voice}
speaking_rate: {rate}
pitch: {pitch}
volume: {volume}
"""

        with open('/tmp/custom_preset.txt', 'w') as f:
            f.write(config_data)

        print(f"\n✅ Custom preset saved to /tmp/custom_preset.txt")
        print("🎤 Testing your preset...")

        # Test with CLI
        import subprocess
        cmd = ['python', 'deepgram_clp.py', test_text, '--voice', selected_voice]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Custom preset test successful!")
        else:
            print("❌ Custom preset test failed")
            print(result.stderr)

    except (ValueError, KeyboardInterrupt):
        print("\n❌ Invalid input or cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main configuration tool"""
    import argparse

    parser = argparse.ArgumentParser(description="Voice Configuration Tool")
    parser.add_argument('--preset', '-p',
                       help='Test specific preset (professional, customer_service, energetic, calm, authoritative)')
    parser.add_argument('--text', '-t',
                       help='Custom text to test with')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List all available presets')
    parser.add_argument('--custom', '-c', action='store_true',
                       help='Create custom preset')

    args = parser.parse_args()

    # Load environment
    load_env()

    print("🎛️  Deepgram Voice Configuration Tool")
    print("=" * 40)

    if args.list:
        show_presets()
    elif args.custom:
        create_custom_preset()
    elif args.preset:
        asyncio.run(test_voice_preset(args.preset, args.text))
    else:
        # Show help and available options
        print("\n📋 Available Commands:")
        print("   --list, -l              List all voice presets")
        print("   --preset NAME, -p NAME   Test specific preset")
        print("   --custom, -c           Create custom preset")
        print("   --text TEXT, -t TEXT   Custom text for testing")
        print("\n🎯 Example Usage:")
        print("   python configure_voice.py --list")
        print("   python configure_voice.py --preset professional")
        print("   python configure_voice.py --preset energetic --text 'Special offer!'")
        print("   python configure_voice.py --custom")

        # Show quick demo of available presets
        print(f"\n🎨 Available Presets: {', '.join(VOICE_PRESETS.keys())}")

if __name__ == "__main__":
    main()
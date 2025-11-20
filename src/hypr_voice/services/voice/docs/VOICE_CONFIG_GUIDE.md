# Voice Configuration Guide

## 🎯 Voice Selection by Use Case

### **Business & Professional**
- **Customer Service**: `asteria`, `helena`, `orpheus`
- **Corporate Presentations**: `athena`, `zeus`, `orpheus`
- **Training Videos**: `luna`, `arcas`, `apollo`
- **News & Information**: `athena`, `orpheus`, `arcas`

### **Entertainment & Creative**
- **Storytelling**: `athena`, `luna`, `arcas`
- **Audiobooks**: `athena`, `helena`, `orpheus`
- **Games & Animation**: `stella`, `thalia`, `aries`
- **Marketing**: `stella`, `thalia`, `asteria`

### **Accessibility & Education**
- **Screen Reading**: `luna`, `arcas`, `apollo`
- **E-Learning**: `helena`, `apollo`, `arcas`
- **Language Learning**: `athena`, `nestor`, `orpheus`
- **Children Content**: `luna`, `andromeda`, `apollo`

### **Personal Assistant**
- **General Assistant**: `luna`, `orion`, `apollo`
- **Productivity**: `asteria`, `arcas`, `orpheus`
- **Smart Home**: `helena`, `apollo`, `andromeda`

## 🔧 Configuration Methods

### **Method 1: CLI Tool (Easiest)**
```bash
# Basic usage
python deepgram_clp.py "Your text here" --voice asteria

# Save to specific file
python deepgram_clp.py "Your text" --voice luna --output custom.wav

# Spanish content
python deepgram_clp.py "Hola, cómo estás?" --voice nestor
```

### **Method 2: Python Configuration**
```python
from deepgram import DeepgramWebSocketTTS, DeepgramWebSocketConfig

# Basic configuration
config = DeepgramWebSocketConfig(
    default_voice="asteria",
    auto_play=True
)

# Advanced configuration
config = DeepgramWebSocketConfig(
    default_voice="luna",
    sample_rate=24000,           # Audio quality (16000-48000)
    speaking_rate=1.2,           # Speed (0.5-2.0, 1.0=normal)
    pitch=2.0,                    # Pitch adjustment (-20 to +20)
    volume=0.9,                   # Volume (0.0-2.0, 1.0=normal)
    auto_play=True,
    enable_logging=True
)

tts = DeepgramWebSocketTTS(config)
```

### **Method 3: Voice Manager Integration**
```python
from voice_manager import VoiceManager, VoiceProvider

# Create manager with specific voice config
from deepgram import DeepgramWebSocketConfig

deepgram_config = DeepgramWebSocketConfig(
    default_voice="athena",
    auto_play=True
)

manager = VoiceManager()
await manager.synthesize(
    "Your text",
    provider=VoiceProvider.DEEPGRAM_WEBSOCKET,
    voice="athena"
)
```

## 🎚️ Voice Customization Parameters

### **Speaking Rate**
- `0.5` - Very slow (dramatic effect)
- `0.8` - Slow (easy listening)
- `1.0` - Normal speed (default)
- `1.2` - Fast (energetic)
- `1.5` - Very fast (urgent)
- `2.0` - Extremely fast

### **Pitch Adjustment**
- `-10` to `-5` - Very low pitch
- `-3` to `-1` - Low pitch
- `0` - Natural pitch (default)
- `+1` to `+3` - High pitch
- `+5` to `+10` - Very high pitch

### **Volume Control**
- `0.3` - Very quiet
- `0.5` - Quiet
- `0.8` - Normal (slightly quiet)
- `1.0` - Normal volume (default)
- `1.2` - Loud
- `1.5` - Very loud

## 📝 Practical Examples

### **Example 1: Customer Service Bot**
```python
config = DeepgramWebSocketConfig(
    default_voice="helena",      # Caring voice
    speaking_rate=0.9,           # Slightly slower
    pitch=1.0,                   # Natural pitch
    volume=0.9                   # Comfortable volume
)
```

### **Example 2: News Reader**
```python
config = DeepgramWebSocketConfig(
    default_voice="athena",      # Professional British
    speaking_rate=1.1,           # Normal pace
    pitch=0.0,                   # Natural
    volume=1.0                   # Clear volume
)
```

### **Example 3: Children's Story**
```python
config = DeepgramWebSocketConfig(
    default_voice="luna",        # Gentle voice
    speaking_rate=0.8,           # Slower for kids
    pitch=2.0,                   # Higher pitch
    volume=0.8                   # Comfortable volume
)
```

### **Example 4: Fitness App**
```python
config = DeepgramWebSocketConfig(
    default_voice="stella",      # Energetic voice
    speaking_rate=1.2,           # Faster pace
    pitch=1.5,                   # Upbeat
    volume=1.1                   # Motivating
)
```

## 🌍 Language & Accent Configuration

### **American English**
- `asteria`, `luna`, `stella`, `hera`, `thalia`, `andromeda`, `helena`
- `orion`, `apollo`, `arcas`, `aries`, `zeus`, `orpheus`

### **British English**
- `athena` (only British voice currently)

### **Spanish**
- `nestor` (professional Spanish)

## 🔍 Voice Testing Script

### **Test Different Voices**
```bash
# Professional use
python deepgram_clp.py "Welcome to our customer service. How can I assist you today?" --voice helena

# Energetic marketing
python deepgram_clp.py "Don't miss our amazing sale! Get 50% off today only!" --voice stella

# Calm educational
python deepgram_clp.py "In this lesson, we will explore the fascinating world of science." --voice luna

# Authoritative announcement
python deepgram_clp.py "Attention passengers, please remain seated until the aircraft has come to a complete stop." --voice zeus
```

### **Compare Voices Side by Side**
```bash
# Same text, different voices
python deepgram_clp.py "This is a test of voice comparison." --voice asteria --output test_asteria.wav
python deepgram_clp.py "This is a test of voice comparison." --voice luna --output test_luna.wav
python deepgram_clp.py "This is a test of voice comparison." --voice orion --output test_orion.wav
```

## 🎯 Voice Selection Recommendations

| **Use Case** | **Recommended Voice** | **Why** |
|--------------|----------------------|---------|
| **Corporate presentations** | `athena`, `orpheus` | Professional, clear |
| **Customer support** | `helena`, `luna` | Caring, friendly |
| **E-learning** | `arcas`, `apollo` | Natural, easy to follow |
| **Marketing** | `stella`, `thalia` | Energetic, engaging |
| **News reading** | `athena`, `orpheus` | Authoritative, clear |
| **Entertainment** | `aries`, `stella` | Dynamic, lively |
| **Accessibility** | `luna`, `apollo` | Gentle, comfortable |
| **Spanish content** | `nestor` | Professional Spanish |

## 🚀 Quick Testing Commands

```bash
# Test all recommended voices
python deepgram_clp.py "This is a professional announcement" --voice athena
python deepgram_clp.py "Thank you for calling customer service" --voice helena
python deepgram_clp.py "Welcome to our learning platform" --voice arcas
python deepgram_clp.py "Check out our amazing deals!" --voice stella
python deepgram_clp.py "Here are today's headlines" --voice opheus
python deepgram_clp.py "Let's begin our adventure" --voice luna
python deepgram_clp.py "Hola, bienvenidos" --voice nestor
```

## 💡 Pro Tips

1. **Test before deploying**: Always test your voice choice with actual content
2. **Consider context**: Match voice characteristics to your content type
3. **Audio quality**: Use higher sample rates (24000+) for better quality
4. **Pacing matters**: Adjust speaking rate based on content complexity
5. **Volume consistency**: Keep volume consistent across different voices
6. **File naming**: Use descriptive names for generated audio files

## 🔧 Advanced Configuration

### **Custom Voice Presets**
```python
# Create custom presets for different scenarios
VOICE_PRESETS = {
    "calm_reading": {
        "voice": "luna",
        "rate": 0.9,
        "pitch": 1.0,
        "volume": 0.8
    },
    "energetic_sales": {
        "voice": "stella",
        "rate": 1.2,
        "pitch": 2.0,
        "volume": 1.1
    },
    "professional_announcement": {
        "voice": "athena",
        "rate": 1.0,
        "pitch": 0.0,
        "volume": 1.0
    }
}
```

You now have **15 professional voices** and multiple ways to configure them for your specific needs! 🎤
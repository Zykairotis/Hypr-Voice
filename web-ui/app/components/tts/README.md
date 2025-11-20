# TTS Control Panel

A comprehensive, professional-grade Text-to-Speech (TTS) control panel for the Hypr-Voice application. This module provides a complete interface for managing TTS synthesis, voice configuration, audio playback, and agent integration.

## 🎯 Features

### 1. **TTS Provider Selection**
- Support for **Kokoro** (Local/Free), **Deepgram** (Cloud), and **ElevenLabs** (Cloud/Premium)
- Real-time provider status monitoring
- Provider comparison and detailed information
- Automatic fallback configuration
- Cost and latency indicators

### 2. **Voice Selection Interface**
- Browse voices organized by provider
- Voice preview functionality
- Voice categorization (male, female, accent, age)
- Search and filter capabilities
- Favorite voices system
- Voice comparison tool with custom text

### 3. **Text-to-Speech Controls**
- Rich text input with sample texts
- Single and batch synthesis modes
- Real-time synthesis progress
- Audio parameter controls (speed, pitch, volume)
- Emotion and style settings
- Multiple output formats (MP3, WAV, OGG, FLAC)
- Synthesize history and job queue

### 4. **Advanced Audio Player**
- Web Audio API integration
- Real-time visualization (waveform & spectrum)
- Full playback controls (play, pause, stop, seek)
- Variable speed playback (0.5x - 2.0x)
- Volume control with mute
- Loop and shuffle modes
- Audio sharing and downloading

### 5. **TTS Agent Integration**
- Per-agent TTS configuration
- Auto-synthesize toggle
- Custom voice settings per agent
- Agent configuration export/import
- Voice testing per agent
- Real-time status monitoring

### 6. **Audio Management**
- Complete audio library with metadata
- Search and filter capabilities
- Favorite system with ratings
- File size and duration tracking
- Batch operations
- Export library to JSON
- Clear cache functionality

### 7. **Live TTS Streaming**
- Real-time streaming synthesis
- WebSocket integration
- Chunked audio delivery
- Live progress monitoring
- Event logging
- Session history
- Stream status indicators

### 8. **Advanced Settings**
- **Audio Settings**: Sample rate, bit rate, format, normalization
- **Playback Settings**: Auto-play, fade in/out, crossfade
- **Synthesis Settings**: Chunk size, queue size, concurrency
- **Provider Configuration**: API keys, endpoints, models
- **UI Customization**: Theme, visualization, animations
- **Keyboard Shortcuts**: Customizable hotkeys
- **Cache Management**: Size, TTL, location

## 📁 Component Structure

```
web-ui/app/components/tts/
├── index.ts                          # Main exports
├── tts-control-panel.tsx             # Main container component
├── tts-provider-selector.tsx         # Provider selection and comparison
├── tts-voice-selector.tsx            # Voice browsing and selection
├── tts-synthesizer.tsx               # Text input and synthesis
├── tts-audio-player.tsx              # Audio playback with visualization
├── tts-agent-integration.tsx         # Agent configuration
├── tts-audio-library.tsx             # Audio library management
├── tts-live-stream.tsx               # Real-time streaming
├── tts-advanced-settings.tsx         # System configuration
└── README.md                         # This file
```

## 🚀 Quick Start

### Importing the Control Panel

```tsx
import { TTSControlPanel } from "@/components/tts";

export default function MyPage() {
  return (
    <TTSControlPanel
      onStatusChange={(status) => console.log("TTS Status:", status)}
    />
  );
}
```

### Using Individual Components

```tsx
import {
  TTSProviderSelector,
  TTSSynthesizer,
  TTSAudioPlayer,
} from "@/components/tts";

export default function CustomTTSPage() {
  const [provider, setProvider] = useState("kokoro");
  const [voice, setVoice] = useState("af_bella");

  return (
    <div className="space-y-6">
      <TTSProviderSelector
        selectedProvider={provider}
        onProviderChange={setProvider}
      />
      <TTSSynthesizer
        provider={provider}
        voice={voice}
        onProviderChange={setProvider}
        onVoiceChange={setVoice}
      />
      <TTSAudioPlayer />
    </div>
  );
}
```

## 🎨 Design Patterns

### Glass Morphism UI
All components use a consistent **glass morphism** design with:
- Translucent backgrounds with backdrop blur
- Gradient borders and highlights
- Smooth animations and transitions
- Dark/light theme support
- Professional color schemes

### State Management
Components use React hooks for local state:
```tsx
const [voices, setVoices] = useState<Voice[]>([]);
const [selectedVoice, setSelectedVoice] = useState<string>("");
```

### Persistence
Settings and data are saved to localStorage:
```tsx
const saveSettings = (settings: TTSSettings) => {
  localStorage.setItem("tts-settings", JSON.stringify(settings));
};
```

### Error Handling
Consistent error handling with toast notifications:
```tsx
try {
  await synthesize(text);
  toast.success("Synthesis completed!");
} catch (error) {
  toast.error(`Synthesis failed: ${error.message}`);
}
```

## 🔌 API Integration

### TTS Synthesis Endpoint
```typescript
POST /api/tts/synthesize
{
  text: string;
  provider: string;
  voice: string;
  speed?: number;
  pitch?: number;
  volume?: number;
  emotion?: string;
  style?: string;
  outputFormat?: string;
  returnUrl?: boolean;
}
```

### Voice List Endpoint
```typescript
GET /api/tts/voices/:provider
// Returns: { voices: Voice[] }
```

### Provider Status Endpoint
```typescript
GET /api/tts/provider/:id/status
// Returns: { status: "available" | "unavailable" }
```

### WebSocket Streaming
```typescript
ws://localhost:8934/api/tts/stream

// Message format:
{
  type: "started" | "progress" | "chunk" | "completed" | "error";
  status: "pending" | "processing" | "success" | "failed";
  message: string;
  data?: any;
}
```

## 🎹 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Enter` | Synthesize text |
| `Space` | Play/Pause |
| `Ctrl + Space` | Pause |
| `Escape` | Stop |

## 🎨 Customization

### Theme Support
Components adapt to the application's theme system:
```tsx
<div className="glass border-border/50">
  <Card className="glass-hover" />
</div>
```

### Custom Colors
Provider-specific color schemes:
```tsx
const providerColors = {
  kokoro: "from-blue-500 to-cyan-500",
  deepgram: "from-purple-500 to-indigo-500",
  elevenlabs: "from-orange-500 to-red-500",
};
```

## 📊 Features Comparison

| Feature | Kokoro | Deepgram | ElevenLabs |
|---------|--------|----------|------------|
| **Type** | Local | Cloud | Cloud |
| **Cost** | Free | Paid | Paid |
| **Latency** | Very Low | Low | Medium |
| **Voice Cloning** | ✓ | ✗ | ✓ |
| **Emotion Control** | ✓ | ✓ | ✓ |
| **Streaming** | ✓ | ✓ | ✓ |
| **Languages** | EN, JA | EN, ES, FR, DE | EN, ES, FR, DE, IT |

## 🔧 Configuration

### Provider Setup

#### Kokoro (Local)
```yaml
kokoro:
  enabled: true
  url: "http://localhost:8880"
  workers: 2
```

#### Deepgram (Cloud)
```yaml
deepgram:
  enabled: true
  api_key: "YOUR_API_KEY"
  endpoint: "https://api.deepgram.com"
```

#### ElevenLabs (Cloud)
```yaml
elevenlabs:
  enabled: true
  api_key: "YOUR_API_KEY"
  model: "eleven_turbo_v2_5"
```

### Audio Settings
```typescript
{
  sampleRate: 48000,  // 22050, 44100, 48000, 96000
  bitRate: 128,       // 64, 128, 192, 256, 320
  format: "mp3",      // mp3, wav, ogg, flac
  normalize: true,
  noiseReduction: false
}
```

## 🧪 Testing

### Component Testing
```tsx
import { render, screen } from "@testing-library/react";
import { TTSControlPanel } from "@/components/tts";

test("renders TTS control panel", () => {
  render(<TTSControlPanel />);
  expect(screen.getByText("TTS Control Panel")).toBeInTheDocument();
});
```

### Voice Testing
```tsx
const testVoice = async (provider: string, voice: string) => {
  const response = await fetch("http://localhost:8934/api/tts/synthesize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: "This is a test voice",
      provider,
      voice,
      preview: true
    }),
  });
  return response.json();
};
```

## 📈 Performance

### Optimization Tips
1. **Chunking**: Large texts are automatically split
2. **Caching**: Enable cache for faster repeated playback
3. **Concurrency**: Configure max concurrent syntheses
4. **WebSocket**: Use streaming for better perceived latency

### Monitoring
- Synthesis progress tracking
- Queue size monitoring
- Error rate tracking
- Memory usage alerts

## 🔐 Security

### API Key Management
- Store API keys securely
- Never expose in client code
- Use environment variables
- Rotate keys regularly

### File Handling
- Validate audio file types
- Sanitize filenames
- Limit file sizes
- Secure upload/download

## 🤝 Contributing

When adding new features:

1. **Follow existing patterns**: Use the same component structure
2. **Add TypeScript types**: Define proper interfaces
3. **Include error handling**: Use try/catch and toast notifications
4. **Write documentation**: Update this README
5. **Test thoroughly**: Verify all states and edge cases

### Component Template
```tsx
interface ComponentNameProps {
  // Define props
}

export default function ComponentName({ ...props }: ComponentNameProps) {
  const [state, setState] = useState();

  return (
    <Card className="glass border-border/50">
      {/* Component UI */}
    </Card>
  );
}
```

## 📝 License

This TTS Control Panel is part of the Hypr-Voice project. See the main project license for details.

## 🆘 Support

For issues or questions:
1. Check the [GitHub Issues](https://github.com/your-org/hypr-voice/issues)
2. Review the documentation
3. Contact the development team

## 🎯 Roadmap

### Upcoming Features
- [ ] Voice training/customization
- [ ] Real-time voice mixing
- [ ] Advanced audio effects
- [ ] Multi-language support
- [ ] Voice marketplace
- [ ] AI voice generation
- [ ] Collaborative voice editing
- [ ] Advanced analytics dashboard

### Version History
- **v1.0.0**: Initial release with core features
- **v1.1.0**: Added live streaming support
- **v1.2.0**: Agent integration enhancements
- **v2.0.0**: Professional UI overhaul
- **v2.1.0**: Advanced audio player

---

Built with ❤️ for the Hypr-Voice project

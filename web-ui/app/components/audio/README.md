# Audio/Visualization Mixer Components

A comprehensive audio monitoring and mixing solution with real-time visualizations, built with Web Audio API and Canvas.

## Features

### 1. Audio Level Monitor (`AudioLevelMonitor.tsx`)
- Real-time RMS and peak level visualization
- Decibel scale display (-60 dB to 0 dB)
- Horizontal and vertical orientations
- Color-coded levels (green/yellow/red)
- Adjustable sizes (sm/md/lg)

### 2. Audio Waveform Display (`visualization/AudioWaveformDisplay.tsx`)
- Real-time waveform visualization
- Oscilloscope mode with grid
- Customizable colors and themes
- Adjustable width and height
- Grid overlay for reference

### 3. Spectrum Analyzer (`visualization/SpectrumAnalyzer.tsx`)
- Real-time frequency spectrum analysis
- FFT-based visualization
- Gradient color support
- Configurable bar count (64 bars default)
- Peak detection indicators

### 4. LED VU Meter (`visualization/LEDVUMeter.tsx`)
- 20-segment LED-style VU meter
- Color-coded segments (green/yellow/red)
- Horizontal and vertical layouts
- Percentage display
- Active segment highlighting

### 5. 3D Audio Visualization (`visualization/ThreeDAudioVisualization.tsx`)
- Interactive 3D audio visualization
- Rotating spectrum visualization
- Radial bar chart display
- Customizable colors
- Real-time animation

### 6. Recording Controls (`controls/AudioRecordingControls.tsx`)
- Record/Pause/Stop buttons
- Format selection (WAV/MP3/FLAC)
- Sample rate and bitrate controls
- Channel selection (Mono/Stereo)
- Auto-gain control (AGC)
- Recording length limiters
- Download functionality

### 7. Playback Mixer (`controls/AudioPlaybackMixer.tsx`)
- Multi-channel support
- Per-channel volume control
- Mute/Solo functionality
- Color-coded channels
- Add/remove channels
- Individual channel controls

### 8. Audio Effects (`effects/AudioEffects.tsx`)
- Noise reduction (0-100%)
- Echo cancellation toggle
- Audio normalization
- Dynamic range compression
  - Threshold control (-40 to 0 dB)
  - Ratio control (1:1 to 20:1)
  - Attack time (0-100 ms)
  - Release time (10-1000 ms)

### 9. Device Manager (`monitoring/AudioDeviceManager.tsx`)
- Input/output device enumeration
- Device testing functionality
- Sample rate configuration (22.05-96 kHz)
- Buffer size optimization (128-2048 samples)
- Input/Output gain controls
- Real-time device status

### 10. Audio Monitoring (`monitoring/AudioMonitoring.tsx`)
- Latency monitoring
- Quality score calculation
- Sample rate and buffer display
- Connection status indicators
- Dropout detection
- Device connection status

### 11. Main Dashboard (`AudioMixerDashboard.tsx`)
- Tabbed interface
- Multiple visualization modes
- Integrated controls
- Real-time audio processing
- Keyboard shortcuts support

## Audio Worklet Processors (`/public/audio-worklets.js`)

### 1. AudioLevelWorkletProcessor
- Real-time level detection
- RMS and peak calculation
- Low-latency processing
- Message-based communication

### 2. AudioFrequencyProcessor
- Frequency domain analysis
- FFT data processing
- Real-time spectrum generation

### 3. NoiseReductionProcessor
- Noise profile tracking
- Adjustable reduction amount
- Real-time noise suppression

### 4. AudioCompressorProcessor
- Dynamic range compression
- Threshold and ratio controls
- Attack and release times
- Gain reduction

### 5. AudioNormalizerProcessor
- Peak detection
- Automatic gain control
- Smooth envelope following

## Keyboard Shortcuts (`hooks/useKeyboardShortcuts.ts`)

- `Ctrl+R` - Record/Pause
- `Ctrl+S` - Stop
- `Ctrl+M` - Mute/Unmute
- `Ctrl+Space` - Play/Pause
- `Escape` - Stop All
- `1-6` - Switch between tabs
- `F1` - Help
- `F11` - Fullscreen

## Usage

### Basic Setup

```tsx
import { AudioMixerDashboard } from '@/components/audio/AudioMixerDashboard';

export default function Page() {
  return <AudioMixerDashboard />;
}
```

### Individual Components

```tsx
import { AudioLevelMonitor } from '@/components/audio/AudioLevelMonitor';
import { AudioWaveformDisplay } from '@/components/audio/visualization/AudioWaveformDisplay';

function MyComponent() {
  const [audioLevel, setAudioLevel] = useState({
    rms: 0,
    peak: 0,
    db: -60,
  });

  return (
    <div>
      <AudioLevelMonitor
        level={audioLevel}
        isActive={true}
        orientation="vertical"
        size="lg"
      />
      <AudioWaveformDisplay
        buffer={audioBuffer}
        isRecording={true}
        width={800}
        height={200}
      />
    </div>
  );
}
```

## Technical Details

### Web Audio API Integration
- Uses AudioContext for audio processing
- AnalyserNode for real-time visualization
- MediaStreamAudioSourceNode for microphone input
- Custom AudioWorklet processors for low-latency

### Canvas Rendering
- High-DPI canvas support
- Real-time animation with requestAnimationFrame
- Optimized rendering for smooth 60fps
- Responsive design

### Device Management
- navigator.mediaDevices.enumerateDevices()
- Real-time device detection
- Permission handling
- Device testing capabilities

### Recording Capabilities
- MediaRecorder API integration
- Multiple format support (WAV/MP3/FLAC)
- Configurable quality settings
- File download functionality

## Browser Compatibility

- Chrome/Edge 66+ (full support)
- Firefox 60+ (limited AudioWorklet support)
- Safari 14.1+ (basic support)

## Performance Considerations

- Worklet processors run in separate thread
- Canvas rendering optimized for 60fps
- Efficient memory usage with typed arrays
- Configurable buffer sizes for latency control
- Automatic cleanup on component unmount

## Future Enhancements

- Audio file import/export
- Multi-track editing
- Real-time effects processing
- MIDI controller support
- VST plugin integration
- Cloud recording storage
- Collaborative mixing sessions

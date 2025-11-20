# Audio/Visualization Mixer - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ installed
- Modern web browser (Chrome 66+, Edge 79+, Firefox 60+, Safari 14.1+)
- Microphone access

### Installation

1. **Start the Development Server**
   ```bash
   cd /home/mewtwo/Zykairotis/Hypr-Voice/web-ui
   npm run dev
   ```

2. **Access the Audio Mixer**
   ```
   http://localhost:8933/audio-mixer
   ```

3. **Grant Permissions**
   - Click "Allow" when prompted for microphone access
   - If denied, click the lock icon in the address bar to grant permissions

### 🎮 Quick Tour

#### 1. Monitor Tab
- View real-time audio input levels
- See RMS and peak measurements
- Control recording (Ctrl+R to record, Ctrl+S to stop)
- Check audio quality metrics

#### 2. Waveform Tab
- See live audio waveform
- Oscilloscope-style display
- Grid overlay for reference

#### 3. Spectrum Tab
- View frequency spectrum analysis
- See audio frequencies in real-time
- Identify different sound components

#### 4. 3D Visual Tab
- Watch interactive 3D visualization
- Radial spectrum display
- Animated rotating bars

#### 5. Mixer Tab
- Add playback channels
- Control volume, mute, and solo
- Apply audio effects
- Mix multiple audio sources

#### 6. Settings Tab
- Select audio devices
- Configure sample rate (22.05kHz - 96kHz)
- Adjust buffer size
- Test input/output devices

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+R` | Record/Pause |
| `Ctrl+S` | Stop |
| `Escape` | Emergency Stop |
| `1-6` | Switch Tabs |
| `F1` | Help |
| `F11` | Fullscreen |

## 🎛️ Controls Guide

### Recording
1. Click the **red record button** or press `Ctrl+R`
2. Recording starts - the button turns yellow
3. Click **pause** to pause recording
4. Click **stop** or press `Ctrl+S` to end
5. Click **download** to save the recording

### Mixer Channels
1. Click **"Add Channel"** to create a new channel
2. Drag volume slider to adjust level (0-150%)
3. Click **mute** to silence channel
4. Click **solo** to hear only that channel
5. Click **play** to test the channel
6. Click **X** to remove channel

### Audio Effects
1. Go to **Mixer Tab**
2. Scroll to **Audio Effects** section
3. Adjust **Noise Reduction** (0-100%)
4. Toggle **Echo Cancellation**
5. Toggle **Normalization**
6. Configure **Compression**:
   - Threshold: -40 to 0 dB
   - Ratio: 1:1 to 20:1
   - Attack: 0-100 ms
   - Release: 10-1000 ms

### Device Settings
1. Go to **Settings Tab**
2. Click **"Refresh"** to scan devices
3. Select **Input Device** (microphone)
4. Select **Output Device** (speaker/headphones)
5. Click **"Test Input"** or **"Test Output"**
6. Adjust **Sample Rate** and **Buffer Size**
7. Set **Input/Output Gain** (0-150%)

## 🎨 Visualizations

### Level Meters
- **Green**: Healthy level (-60 to -18 dB)
- **Yellow**: Warning level (-18 to -6 dB)
- **Red**: Critical level (-6 to 0 dB)
- **Red Flash**: Peak detected

### LED VU Meter
- 20 segments light up based on audio level
- Color changes from green → yellow → red
- Shows percentage of full scale

### Waveform Display
- Real-time audio waveform
- Grid lines for reference
- Center line = zero crossing

### Spectrum Analyzer
- 64 frequency bars
- Low frequencies on left
- High frequencies on right
- Gradient coloring

### 3D Visualization
- Radial bar chart
- Bars rotate around center
- Height = frequency magnitude

## 📊 Understanding the Metrics

### Audio Levels
- **RMS**: Root Mean Square (average level)
- **Peak**: Maximum instantaneous level
- **dB**: Decibels (logarithmic scale)

### Quality Metrics
- **Latency**: Delay from input to output
  - <10ms: Excellent
  - 10-30ms: Good
  - >30ms: May notice delay
- **Quality Score**: Overall audio quality (0-100%)

### Monitoring Stats
- **Sample Rate**: Samples per second (22.05kHz, 44.1kHz, 48kHz, 96kHz)
- **Buffer Size**: Audio buffer in samples
  - Smaller = lower latency, more CPU
  - Larger = higher latency, less CPU
- **Dropouts**: Audio interruptions (should be 0)

## 🔧 Troubleshooting

### No Audio
1. Check microphone permissions (browser lock icon)
2. Verify microphone is not muted
3. Try refreshing the page
4. Check device selection in Settings

### High Latency
1. Reduce buffer size in Settings
2. Close other audio applications
3. Use Chrome/Edge for best performance

### Poor Quality
1. Increase sample rate (48kHz or higher)
2. Check input gain levels
3. Enable noise reduction/echo cancellation

### Visualizations Not Working
1. Ensure AudioWorklet is supported
2. Try refreshing the page
3. Check browser compatibility

### Device Not Detected
1. Click "Refresh" button
2. Grant device permissions
3. Restart browser if necessary

## 🎯 Best Practices

### Recording
- Use 44.1kHz or 48kHz for general recording
- Keep levels in yellow range for best quality
- Use compression for consistent levels
- Enable normalization for loudness

### Monitoring
- Keep latency under 10ms for live work
- Monitor quality score (aim for 90%+)
- Watch for dropouts
- Use proper gain staging

### Mixing
- Start with levels at 80%
- Use solo to isolate channels
- Color-code channels for organization
- Save preset configurations

## 📱 Mobile Support

The mixer works on mobile devices with some limitations:
- **iOS Safari**: Basic functionality, some visual effects reduced
- **Android Chrome**: Full support, recommended browser
- **Responsive**: UI adapts to screen size
- **Touch**: Tap controls instead of drag sliders

## 🌐 Browser Performance

| Feature | Chrome | Edge | Firefox | Safari |
|---------|--------|------|---------|--------|
| Audio Worklet | ✅ | ✅ | ⚠️ | ⚠️ |
| Real-time FFT | ✅ | ✅ | ✅ | ✅ |
| Canvas 2D | ✅ | ✅ | ✅ | ✅ |
| Device Access | ✅ | ✅ | ✅ | ✅ |
| MediaRecorder | ✅ | ✅ | ✅ | ⚠️ |

✅ Full Support | ⚠️ Limited Support

## 🎓 Advanced Tips

### Low Latency Setup
1. Use ASIO drivers (Windows) or Core Audio (Mac)
2. Set buffer size to 128-256 samples
3. Close unnecessary applications
4. Use wired connections
5. Disable audio enhancements

### Professional Recording
1. Use 48kHz or 96kHz sample rate
2. Keep peak levels below -6dB
3. Use compression with 4:1 ratio
4. Enable normalization for final output
5. Record in WAV format for best quality

### Mixing Mastery
1. Group similar channels
2. Use EQ to separate frequencies
3. Apply compression for punch
4. Use reverb/delay for space
5. Reference with commercial tracks

## 💡 Customization

### Colors
Modify CSS variables in `styles.css`:
```css
:root {
  --audio-level-healthy: #22c55e;
  --audio-level-warning: #f59e0b;
  --audio-level-critical: #ef4444;
}
```

### Visualization Themes
Create custom themes by modifying component props:
```tsx
<AudioWaveformDisplay
  color="#8b5cf6"
  backgroundColor="#000000"
  showGrid={true}
/>
```

### Buffer Settings
Adjust for your use case:
- **Live Performance**: 128 samples (5ms latency)
- **Podcast/Streaming**: 256-512 samples (10-20ms)
- **General Recording**: 1024 samples (20-40ms)

## 📞 Support

For issues or questions:
1. Check browser console for errors
2. Verify microphone permissions
3. Try different browser
4. Check network connection
5. Review audio device settings

## 🎉 Next Steps

After getting familiar with the basics:
1. Experiment with effects settings
2. Try different visualization modes
3. Record and mix multiple channels
4. Adjust quality settings for your use case
5. Create custom channel setups

---

**Happy Mixing!** 🎵

Access the mixer at: `http://localhost:8933/audio-mixer`

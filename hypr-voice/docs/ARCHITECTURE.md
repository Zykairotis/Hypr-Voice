# Hypr-Voice Architecture Deep Dive

## Core Data Flow
```python
async def process_audio():
    # Capture from sounddevice InputStream
    audio = self.stream.read()
    
    # Convert to Whisper-compatible format
    processed_audio = self._convert_audio(audio)
    
    # WebSocket stream to Whisper server
    async with websockets.connect(WHISPER_URL) as ws:
        await ws.send(processed_audio)
        transcript = await ws.recv()
    
    # Apply context-aware processing
    return await self.context_engine.enhance(transcript)
```

## Key Integration Points
1. **Hyprland IPC** - Uses hyprctl to get window context
2. **Redis** - Backend for Cognee memory system
3. **LanceDB** - Vector storage for semantic context
# Hypr-Voice API Reference

## Core Modules

### `hypr_voice.py`
```python
class HyprVoice:
    def start_recording(self, device: str = "default") -> None:
        """
        Start audio recording from specified device
        
        Args:
            device: Audio device name or index
        """
        
    def process_audio_chunk(self, chunk: np.ndarray) -> str:
        """
        Process raw audio data to text
        
        Args:
            chunk: Numpy array of audio samples
        Returns:
            Transcribed text
        """
```

### `context_engine_cognee.py`
```python
class CogneeContextEngine:
    async def set_active_application(self, app_name: str) -> None:
        """
        Set active application context
        
        Args:
            app_name: Application identifier
        """
    
    async def enhance_text(
        self, 
        text: str,
        temperature: float = 0.7
    ) -> EnhancedText:
        """
        Enhance raw text with contextual awareness
        
        Args:
            text: Input text
            temperature: LLM creativity (0.0-1.0)
        Returns:
            EnhancedText object with:
            - processed_content
            - suggestions
            - context_tags
        """
```

### `whisper_server.py`
```python
class WhisperASR:
    def transcribe(
        self,
        audio: bytes,
        language: str = "en",
        beam_size: int = 5
    ) -> TranscriptionResult:
        """
        Transcribe audio bytes to text
        
        Args:
            audio: Raw audio bytes
            language: ISO 639-1 language code
            beam_size: Decoder beam width
        Returns:
            TranscriptionResult with:
            - text
            - confidence
            - language
        """
```

## Web API Endpoints

### POST /transcribe
```json
{
  "audio": "base64_encoded_audio",
  "language": "en",
  "options": {
    "temperature": 0.0,
    "beam_size": 5
  }
}
```

### WS /ws/transcribe
```json
{
  "action": "start|stop|config",
  "params": {
    "sample_rate": 16000,
    "channels": 1
  }
}
```

## Configuration API

### Audio Config (audio_config.yaml)
```yaml
input:
  primary:
    name: "pulse"
  quality:
    sample_rate: 48000
    dtype: float32
```

### App Profiles (app_profiles.yaml)
```yaml
terminal:
  llm:
    model: "codellama"
    max_tokens: 1024
  context:
    - command_syntax
    - shell_abbreviations
# Adding Features Guide

This guide walks through the process of adding new features to Hypr-Voice, from planning to implementation.

## Table of Contents

1. [Feature Development Workflow](#feature-development-workflow)
2. [Planning Phase](#planning-phase)
3. [Design Phase](#design-phase)
4. [Implementation Phase](#implementation-phase)
5. [Testing Phase](#testing-phase)
6. [Documentation Phase](#documentation-phase)
7. [Examples](#examples)
8. [Best Practices](#best-practices)

## Feature Development Workflow

### Overview

```
Planning → Design → Implementation → Testing → Documentation → Review → Merge
```

### 1. Planning Phase

**Before Writing Code**:
1. Understand the problem
2. Define success criteria
3. Identify dependencies
4. Estimate effort
5. Get stakeholder feedback

### 2. Design Phase

**Create Design Document** (for complex features):
- Feature overview
- Architecture diagram
- API changes
- Data model changes
- Migration strategy
- Testing strategy

### 3. Implementation Phase

Follow Test-Driven Development (TDD):
1. Write failing tests
2. Implement feature
3. Make tests pass
4. Refactor code

### 4. Testing Phase

- Unit tests for new code
- Integration tests for interactions
- Manual testing for UI changes
- Performance testing if applicable

### 5. Documentation Phase

- Update API docs
- Add usage examples
- Update README if needed
- Create migration guide for breaking changes

### 6. Review & Merge

- Self-review code
- Create pull request
- Address feedback
- Merge when approved

## Planning Phase

### Feature Proposal Template

```markdown
## Feature: [Brief Title]

### Problem Statement
What problem does this solve? Why do we need it?

### Proposed Solution
High-level description of the solution.

### Success Criteria
- [ ] Specific, measurable criteria
- [ ] Performance requirements
- [ ] User experience goals

### Alternatives Considered
What other approaches were considered? Why rejected?

### Dependencies
- Technical dependencies
- Other features
- External services

### Estimated Effort
- Planning: X hours
- Implementation: Y hours
- Testing: Z hours
- Documentation: W hours

### Risks & Mitigations
What could go wrong? How to mitigate?
```

### Example Feature Proposal

```markdown
## Feature: Custom Voice Training for TTS

### Problem Statement
Users want to use custom voices for TTS synthesis, not just
pre-built provider voices.

### Proposed Solution
Implement voice training pipeline that allows users to:
1. Upload audio samples
2. Train custom voice model
3. Use trained voice for synthesis

### Success Criteria
- [ ] Support for 30+ audio samples
- [ ] Training completes within 2 hours
- [ ] Voice quality comparable to providers
- [ ] API for managing custom voices

### Alternatives Considered
- Use fine-tuning API from providers (expensive, slow)
- Build custom training pipeline (complex, but faster/cheaper)
- Voice conversion (lower quality)

### Dependencies
- GPU infrastructure for training
- Storage for audio samples and models
- Training queue management

### Estimated Effort
- Planning: 8 hours
- Implementation: 40 hours
- Testing: 16 hours
- Documentation: 8 hours
**Total**: 72 hours

### Risks & Mitigations
- **Risk**: Poor voice quality
  **Mitigation**: Extensive testing with various voices

- **Risk**: Long training times
  **Mitigation**: Progress tracking, cancellation support
```

## Design Phase

### Architecture Design

**For complex features**, create architecture diagrams:

```
User Request
    ↓
API Layer (new endpoints)
    ↓
Service Layer (new service)
    ↓
Infrastructure (storage, compute)
```

### API Design

**REST API Example**:

```python
# New endpoint in server.py
from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/api/voices/custom", tags=["custom-voices"])

@router.post("/train")
async def train_custom_voice(
    name: str,
    samples: List[UploadFile] = File(...)
):
    """
    Train custom voice from audio samples.

    Args:
        name: Voice name
        samples: Audio samples (WAV format, 30+ files)

    Returns:
        Training job ID
    """
    job_id = await voice_trainer.start_training(name, samples)
    return {"job_id": job_id, "status": "started"}

@router.get("/status/{job_id}")
async def get_training_status(job_id: str):
    """Get training job status."""
    status = await voice_trainer.get_status(job_id)
    return status

@router.get("/voices")
async def list_custom_voices():
    """List all custom voices."""
    voices = await voice_manager.list_voices()
    return {"voices": voices}
```

**WebSocket API Example**:

```python
@router.websocket("/ws/voice-training")
async def websocket_training(websocket: WebSocket):
    """
    WebSocket endpoint for real-time training updates.

    Messages:
    - {"type": "progress", "value": 0-100}
    - {"type": "complete", "voice_id": "..."}
    - {"type": "error", "message": "..."}
    """
    await websocket.accept()
    job_id = await websocket.receive_text()

    async for update in voice_trainer.stream_updates(job_id):
        await websocket.send_json(update)

    await websocket.close()
```

### Data Model Design

```python
# New data models in models.py
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class TrainingJob(BaseModel):
    """Voice training job."""

    job_id: str = Field(..., description="Unique job ID")
    name: str = Field(..., description="Voice name")
    status: Literal["pending", "training", "completed", "failed"] = "pending"
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123",
                "name": "My Custom Voice",
                "status": "training",
                "progress": 45.5,
                "created_at": "2025-01-26T10:00:00Z"
            }
        }

class CustomVoice(BaseModel):
    """Custom voice model."""

    voice_id: str = Field(..., description="Unique voice ID")
    name: str = Field(..., description="Voice name")
    model_path: str = Field(..., description="Path to trained model")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sample_count: int = Field(..., description="Number of training samples")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
```

### Configuration Design

```python
# Add to config/defaults.py
class VoiceTrainingConfig(BaseConfig):
    """Configuration for voice training."""

    # Training parameters
    min_samples: int = 30
    max_samples: int = 100
    sample_duration: int = 10  # seconds
    training_epochs: int = 1000

    # Infrastructure
    gpu_required: bool = True
    max_concurrent_jobs: int = 2

    # Storage
    samples_dir: str = "runtime/voice_samples"
    models_dir: str = "runtime/custom_models"
```

## Implementation Phase

### Test-Driven Development (TDD)

**Step 1: Write Failing Tests**

```python
# tests/test_voice_training.py
import pytest
from hypr_voice.services.voice_training import VoiceTrainer

@pytest.mark.asyncio
async def test_train_custom_voice():
    """Test basic voice training."""
    trainer = VoiceTrainer()

    # Create mock samples
    samples = create_mock_audio_samples(count=30)

    # Start training
    job_id = await trainer.start_training("test_voice", samples)

    # Assertions
    assert job_id is not None
    job_status = await trainer.get_status(job_id)
    assert job_status.status == "training"

@pytest.mark.asyncio
async def test_insufficient_samples():
    """Test that training fails with insufficient samples."""
    trainer = VoiceTrainer()
    samples = create_mock_audio_samples(count=5)

    with pytest.raises(ValueError, match="at least 30 samples"):
        await trainer.start_training("test_voice", samples)

@pytest.mark.asyncio
async def test_training_progress():
    """Test training progress updates."""
    trainer = VoiceTrainer()
    samples = create_mock_audio_samples(count=30)

    job_id = await trainer.start_training("test_voice", samples)

    # Stream progress
    progress_updates = []
    async for update in trainer.stream_updates(job_id):
        progress_updates.append(update)
        if update["progress"] >= 100:
            break

    assert len(progress_updates) > 0
    assert progress_updates[-1]["status"] == "completed"
```

**Step 2: Implement Feature**

```python
# services/voice_training.py
from pathlib import Path
from typing import List, AsyncIterator
import asyncio

class VoiceTrainer:
    """Train custom TTS voices."""

    def __init__(self, config: VoiceTrainingConfig):
        self.config = config
        self.jobs: Dict[str, TrainingJob] = {}

    async def start_training(
        self,
        name: str,
        samples: List[Path]
    ) -> str:
        """
        Start voice training job.

        Args:
            name: Voice name
            samples: List of audio sample paths

        Returns:
            Job ID

        Raises:
            ValueError: If insufficient samples
        """
        # Validate
        if len(samples) < self.config.min_samples:
            raise ValueError(
                f"Need at least {self.config.min_samples} samples, "
                f"got {len(samples)}"
            )

        # Create job
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        self.jobs[job_id] = TrainingJob(
            job_id=job_id,
            name=name,
            status="pending"
        )

        # Start training in background
        asyncio.create_task(self._train_voice(job_id, samples))

        return job_id

    async def _train_voice(
        self,
        job_id: str,
        samples: List[Path]
    ):
        """Train voice model (background task)."""
        job = self.jobs[job_id]
        job.status = "training"

        try:
            # Preprocess samples
            await self._preprocess_samples(job_id, samples)

            # Train model
            for epoch in range(self.config.training_epochs):
                # Training logic here
                job.progress = (epoch / self.config.training_epochs) * 100

                # Update status
                await asyncio.sleep(0.1)  # Simulate training

            job.status = "completed"
            job.completed_at = datetime.utcnow()

        except Exception as e:
            job.status = "failed"
            job.error = str(e)

    async def stream_updates(
        self,
        job_id: str
    ) -> AsyncIterator[dict]:
        """Stream training progress updates."""
        while True:
            job = self.jobs.get(job_id)
            if not job:
                yield {"type": "error", "message": "Job not found"}
                break

            yield {
                "type": "progress",
                "status": job.status,
                "progress": job.progress
            }

            if job.status in ["completed", "failed"]:
                break

            await asyncio.sleep(1)
```

**Step 3: Make Tests Pass**

```bash
# Run tests
pytest tests/test_voice_training.py -v

# Debug failures
pytest tests/test_voice_training.py::test_train_custom_voice -vv
```

### Service Integration

```python
# Integrate with existing TTS service
from hypr_voice.services.voice import TTSProvider, UniversalTTS

class CustomTTSProvider(TTSProvider):
    """Custom voice provider."""

    CUSTOM = "custom"

# Update UniversalTTS to support custom voices
class UniversalTTS:
    async def speak(
        self,
        text: str,
        voice: str = None,
        provider: TTSProvider = None
    ) -> dict:
        if provider == CustomTTSProvider.CUSTOM:
            return await self._speak_custom(text, voice)
        # ... existing logic
```

### Orchestrator Integration

```python
# Update orchestrator to use custom voices
class VoiceOrchestrator:
    def __init__(self, config: VoiceOrchestratorConfig):
        # ... existing init
        self.voice_trainer = VoiceTrainer(config.training)

    async def train_custom_voice(
        self,
        name: str,
        samples: List[Path]
    ) -> str:
        """Train custom voice."""
        return await self.voice_trainer.start_training(name, samples)
```

## Testing Phase

### Unit Tests

```python
# Test individual components
@pytest.mark.asyncio
async def test_voice_trainer_validation():
    """Test input validation."""
    trainer = VoiceTrainer(config)

    # Test insufficient samples
    with pytest.raises(ValueError):
        await trainer.start_training("test", samples=[])

    # Test invalid audio format
    with pytest.raises(ValueError):
        invalid_sample = Path("test.txt")
        await trainer.start_training("test", samples=[invalid_sample])
```

### Integration Tests

```python
# Test service integration
@pytest.mark.asyncio
async def test_custom_voice_synthesis():
    """Test end-to-end custom voice synthesis."""
    # Train voice
    trainer = VoiceTrainer()
    samples = create_mock_audio_samples(count=30)
    job_id = await trainer.start_training("test", samples)

    # Wait for completion
    await wait_for_training(job_id)

    # Use voice for synthesis
    tts = UniversalTTS()
    result = await tts.speak(
        "Hello world",
        voice="test",
        provider="custom"
    )

    assert result["success"]
    assert Path(result["audio_file"]).exists()
```

### Performance Tests

```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_training_performance():
    """Test training meets performance requirements."""
    import time

    trainer = VoiceTrainer()
    samples = create_mock_audio_samples(count=30)

    start = time.time()
    job_id = await trainer.start_training("test", samples)
    await wait_for_training(job_id)
    duration = time.time() - start

    # Should complete within 2 hours (7200 seconds)
    assert duration < 7200
```

## Documentation Phase

### API Documentation

```python
def train_custom_voice(
    self,
    name: str,
    samples: List[UploadFile]
) -> dict:
    """
    Train custom TTS voice from audio samples.

    Requires 30-100 audio samples in WAV format. Each sample
    should be 5-15 seconds of clear speech.

    Args:
        name: Unique name for the voice (max 50 chars)
        samples: List of audio files (WAV, 16kHz, mono)

    Returns:
        dict:
            - job_id (str): Training job ID
            - status (str): Initial status ("pending")
            - estimated_time (int): Estimated minutes

    Raises:
        ValueError: If validation fails
        ResourceError: If GPU unavailable

    Example:
        >>> samples = [Path("sample1.wav"), Path("sample2.wav")]
        >>> job = await trainer.train_custom_voice("MyVoice", samples)
        >>> print(job['job_id'])
        'job_abc123'
    """
```

### Usage Examples

```python
# docs/examples/custom_voice_training.md
# Example: Training Custom Voice

import asyncio
from hypr_voice.services.voice_training import VoiceTrainer

async def main():
    """Train custom voice example."""
    # Initialize trainer
    trainer = VoiceTrainer()

    # Load samples
    samples = [
        Path("samples/sample_001.wav"),
        Path("samples/sample_002.wav"),
        # ... 30+ samples
    ]

    # Start training
    job = await trainer.start_training("MyVoice", samples)
    print(f"Training started: {job['job_id']}")

    # Monitor progress
    async for update in trainer.stream_updates(job['job_id']):
        print(f"Progress: {update['progress']}%")

        if update['status'] == 'completed':
            print("Training complete!")
            break

    # Use voice
    from hypr_voice.services.voice import UniversalTTS
    tts = UniversalTTS()
    result = await tts.speak(
        "Hello, this is my custom voice!",
        voice="MyVoice",
        provider="custom"
    )
    print(f"Audio: {result['audio_file']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Migration Guide

```markdown
# Migration Guide: Custom Voices

## Breaking Changes
- Voice ID format changed from `voice_name` to `custom:voice_name`

## Migration Steps

### 1. Update Voice References
```python
# Before
result = await tts.speak("Hello", voice="my_voice")

# After
result = await tts.speak("Hello", voice="my_voice", provider="custom")
```

### 2. Update Configuration
```yaml
# config.yaml
voice:
  # Add custom provider
  providers:
    - kokoro
    - deepgram
    - custom  # New
```

### 3. Database Migration
```sql
-- Migrate existing custom voices
UPDATE voices SET provider = 'custom' WHERE is_custom = true;
```
```

## Examples

### Example 1: Add New TTS Provider

```python
# 1. Create provider implementation
# services/voice/providers/new_provider.py

class NewTTSProvider:
    """New TTS provider implementation."""

    async def synthesize(
        self,
        text: str,
        voice: str,
        options: dict
    ) -> dict:
        """Synthesize speech."""
        # Implementation
        pass

# 2. Register provider
# services/voice/__init__.py

class TTSProvider(Enum):
    KOKORO = "kokoro"
    DEEPGRAM = "deepgram"
    NEW_PROVIDER = "new_provider"  # Add here

# 3. Update UniversalTTS
# services/voice/tts_manager.py

class UniversalTTS:
    async def speak(self, text: str, voice: str = None, provider: str = None):
        if provider == TTSProvider.NEW_PROVIDER.value:
            return await self._speak_new_provider(text, voice)

# 4. Add tests
# tests/test_new_provider.py

@pytest.mark.asyncio
async def test_new_provider():
    tts = UniversalTTS()
    result = await tts.speak("Test", provider="new_provider")
    assert result["success"]
```

### Example 2: Add WebSocket Event

```python
# 1. Define event type
# ipc/websocket.py

class WebSocketEvent:
    """WebSocket event types."""

    # Existing events
    QUERY = "query"
    RESPONSE = "response"

    # New event
    VOICE_TRAINING_PROGRESS = "voice_training_progress"

# 2. Add handler
# ipc/websocket.py

class OrchestratorWebSocket:
    async def handle_voice_training_progress(self, data: dict):
        """Handle voice training progress event."""
        job_id = data.get("job_id")
        progress = data.get("progress")

        # Broadcast to clients
        await self.broadcast({
            "type": WebSocketEvent.VOICE_TRAINING_PROGRESS,
            "job_id": job_id,
            "progress": progress
        })

# 3. Update server
# server.py

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    async for message in websocket.iter_json():
        if message["type"] == "voice_training_progress":
            await ws_server.handle_voice_training_progress(message)
```

### Example 3: Add CLI Command

```python
# 1. Create CLI command
# cli/voice_training.py

import click
from hypr_voice.services.voice_training import VoiceTrainer

@click.group()
def voice():
    """Voice training commands."""
    pass

@voice.command()
@click.argument("name")
@click.argument("samples_dir", type=click.Path(exists=True))
async def train(name: str, samples_dir: str):
    """Train custom voice."""
    trainer = VoiceTrainer()
    samples = list(Path(samples_dir).glob("*.wav"))

    if len(samples) < 30:
        click.echo(f"Need 30+ samples, got {len(samples)}")
        return

    click.echo(f"Training voice '{name}' with {len(samples)} samples...")
    job_id = await trainer.start_training(name, samples)

    click.echo(f"Training started: {job_id}")

    # Monitor progress
    async for update in trainer.stream_updates(job_id):
        click.echo(f"Progress: {update['progress']}%")
        if update['status'] == 'completed':
            click.echo("Training complete!")
            break

# 2. Register in main CLI
# cli/__init__.py

from .voice_training import voice

cli.add_command(voice)
```

## Best Practices

### DO's

1. **Plan Before Coding**
   - Write design doc for complex features
   - Get feedback on design
   - Break into small tasks

2. **Test-Driven Development**
   - Write tests first
   - Test edge cases
   - Mock external dependencies

3. **Incremental Implementation**
   - Start with MVP
   - Add features incrementally
   - Refactor as needed

4. **Document as You Go**
   - Write docstrings
   - Update API docs
   - Add examples

5. **Consider Performance**
   - Profile bottlenecks
   - Add caching where appropriate
   - Use async/await for I/O

### DON'Ts

1. **Don't Skip Testing**
   - Always write tests
   - Aim for >80% coverage
   - Test error paths

2. **Don't Break Backward Compatibility**
   - Use deprecation warnings
   - Provide migration path
   - Update major version for breaking changes

3. **Don't Ignore Security**
   - Validate inputs
   - Sanitize outputs
   - Never log secrets

4. **Don't Over-Engineer**
   - Keep it simple
   - Avoid premature optimization
   - YAGNI (You Aren't Gonna Need It)

5. **Don't Forget Error Handling**
   - Handle exceptions gracefully
   - Provide helpful error messages
   - Log errors appropriately

## Next Steps

- Read [Debugging Guide](debugging.md)
- Learn [Testing Guide](testing.md)
- Review [Contributing Guidelines](contributing.md)

## Resources

- [Feature Template](../../.github/ISSUE_TEMPLATE/feature_request.md)
- [API Design Best Practices](https://github.com/interagent/http-api-design)
- [Testing Best Practices](testing.md)

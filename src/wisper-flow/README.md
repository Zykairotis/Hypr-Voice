# 🚀 Wispr Fast - Ultra-Fast Voice Transcription

A standalone, high-performance transcription toolkit optimized for WisprFlow. Features auto-chunking and parallel processing for blazingly fast results even on long audio files.

## ✨ Features
- **Parallel Processing**: Transcribes long files in parallel chunks, reducing wait time by up to 3x.
- **Auto-Chunking**: Seamlessly handles audio files longer than 30 seconds.
- **Opus Compression**: Reduces network bandwidth usage and latency by over 90x.
- **Direct API Access**: Minimizes overhead by connecting directly to Baseten model chains.

---

## 🛠️ Parameters & API

### `transcribe_file(file_path, language='en')`
The primary high-level function for all transcription needs.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `file_path` | `str` | Absolute or relative path to the audio file (.wav, .mp3, etc.) |
| `language` | `str` | ISO language code (default: `'en'`) |

**Returns**: A `dict` containing:
- `status`: `'success'` or `'error'`
- `asr_text`: The full transcribed text
- `method`: `'direct'` or `'parallel-chunked'`
- `detected_language`: The language used for transcription

---

## 🚀 Quick Start

### 1. Install Dependencies
Ensure you have `ffmpeg` installed on your system.
```bash
pip install -r requirements.txt
```

### 2. Command Line Usage
```bash
python transcribe.py path/to/your/audio.wav
```

### 3. Use in your Project
```python
from wispr_fast.transcribe import transcribe_file

result = transcribe_file("my_audio.wav")
if result['status'] == 'success':
    print(f"Transcript: {result['asr_text']}")
```

---

## 📊 Benchmark Tool
Use `benchmark.py` to test performance against your own dataset:
```bash
python benchmark.py path/to/audio_folder
```
This will generate `benchmark_results_v4.md` with detailed latency metrics.

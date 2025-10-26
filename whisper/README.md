# Whisper Real-time Transcription Server & Client

This directory contains a high-performance, real-time audio transcription service using `faster-whisper`. It consists of a FastAPI server and a Python client that can stream audio from a microphone or transcribe local audio and video files.

## Features

*   **Real-time Transcription**: Stream audio from a microphone and receive transcriptions with low latency via WebSockets.
*   **File Transcription**: Transcribe audio files (`.wav`, `.mp3`, etc.) and video files (`.mp4`, `.mkv`, etc.).
*   **Session Management**: The server can handle multiple transcription sessions simultaneously.
*   **Hardware Acceleration**: Supports both CPU and GPU (CUDA) for transcription.
*   **Configurable Models**: Easily switch between different Whisper model sizes (`tiny`, `base`, `small`, `medium`, `large`).
*   **Client Utilities**: Includes helpers to list and test audio input devices.

## Setup

1.  **Install FFmpeg**: This is required for video file processing.
    *   **Ubuntu/Debian**: `sudo apt update && sudo apt install ffmpeg`
    *   **macOS**: `brew install ffmpeg`
    *   **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your system's PATH.

2.  **Install Dependencies**: It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Key Dependencies**:
    *   `fastapi`: For the web server.
    *   `uvicorn`: For running the FastAPI server.
    *   `faster-whisper`: The core transcription engine.
    *   `torch`: Required by `faster-whisper`. Install the appropriate version for your CUDA setup if you have a GPU.
    *   `websockets`: For real-time communication.
    *   `requests`: For the client to communicate with the server's REST API.
    *   `sounddevice`: For microphone input on the client.
    *   `numpy`: For audio data manipulation.
    *   `soundfile`: For reading audio files.
    *   `ffmpeg-python`: For processing video files.

## How to Use

### 1. Running the Transcription Server

The server listens for requests from the client. You can start it with various options.

**Basic command:**
```bash
python whisper/server.py
```

**To use a specific model and run on GPU (recommended for performance):**
```bash
python whisper/server.py --model medium --device cuda --compute-type float16
```

**Server Arguments:**
*   `--host`: Host to bind to (default: `0.0.0.0`).
*   `--port`: Port to listen on (default: `9880`).
*   `--model`: Whisper model size (`tiny`, `base`, `small`, `medium`, `large`). Default: `base`.
*   `--device`: Device to use (`cpu`, `cuda`, `auto`). Default: `auto`.
*   `--compute-type`: Type of computation (`int8`, `float16`, `float32`). Default: `int8`.
*   `--clean-output`: Enable clean output mode (only transcription text).

### 2. Using the Client

The client can be used to list devices, transcribe files, or stream from your microphone.

**List available audio devices:**
This is useful to find the `DEVICE_ID` for streaming.
```bash
python whisper/client.py --list-devices
```

**Transcribe an audio or video file:**
The client will create a session, upload the file, and print the final transcription.
```bash
python whisper/client.py --file /path/to/your/video.mp4
```

**Stream from your microphone:**
Use the `DEVICE_ID` from the `list-devices` command.
```bash
python whisper/client.py --stream --device 1
```
Press `Ctrl+C` to stop streaming.

## Suggested Improvements

1.  **Containerization**: Create a `Dockerfile` for the server to simplify deployment and ensure a consistent environment. This would be especially useful for managing CUDA dependencies.

2.  **Configuration Management**: For the server, switch from command-line arguments to a configuration file (e.g., `config.yaml` or `.env`) to make it easier to manage a variety of settings, especially for production deployments.

3.  **Security**: The server is currently open. Implement API key authentication (`X-API-Key` header) to secure the endpoints and control access. The code already contains a placeholder for this (`AUTH_ENABLED`).

4.  **Client-Side VAD (Voice Activity Detection)**: The client currently streams all audio. Implementing VAD on the client would prevent sending silence to the server, saving bandwidth and reducing server load.

5.  **Connection Robustness**: Enhance the client with automatic reconnection logic for the WebSocket connection. This would make the streaming more resilient to network interruptions.

6.  **Dependency Management**: Create two separate `requirements.txt` files (`requirements-server.txt`, `requirements-client.txt`) to distinguish between the dependencies needed for the server and the client.

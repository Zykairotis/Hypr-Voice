#!/usr/bin/env python3
"""
Simple audio transcription script for Whisper API.
Transcribes an audio file and prints the result.
"""

import sys
import os
from client import WhisperClient

def transcribe_audio_file(file_path, server_url="http://localhost:9880"):
    """Transcribe a single audio file."""
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return None

    print(f"Transcribing: {file_path}")
    client = WhisperClient(server_url)

    # Create session and transcribe
    client.create_session()
    client.transcribe_file(file_path)

    # Wait for transcription to complete
    result = client.get_final_transcription(wait=True, inactivity_timeout=60)

    if result and result.get("text"):
        return result["text"]
    else:
        print("Transcription failed or no text found.")
        return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python audio-trans-file.py <audio_file>")
        print("Example: python audio-trans-file.py Recording1.mp3")
        sys.exit(1)

    audio_file = sys.argv[1]
    transcription = transcribe_audio_file(audio_file)

    if transcription:
        print(f"\nTranscription:\n{transcription}")

if __name__ == "__main__":
    main()
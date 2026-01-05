#!/usr/bin/env python3
"""
Test Deepgram Flux STT - Ultra-low latency speech-to-text
Flux uses /v2/listen endpoint with ~260ms end-of-turn detection
"""

import asyncio
import json
import os
import time
import subprocess
import websockets

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
AUDIO_FILE = "harvard.wav"
CHUNK_SIZE_MS = 80
SAMPLE_RATE = 16000


def convert_to_flux_format(input_file: str) -> bytes:
    """Convert audio to Flux-compatible format: 16kHz, mono, 16-bit PCM"""
    print(f"🔄 Converting {input_file} to 16kHz mono PCM...")
    
    cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-ar", str(SAMPLE_RATE), "-ac", "1",
        "-f", "s16le", "-acodec", "pcm_s16le",
        "-loglevel", "error", "pipe:1"
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print(f"❌ FFmpeg error: {result.stderr.decode()}")
        return b""
    
    audio_data = result.stdout
    duration = len(audio_data) / (SAMPLE_RATE * 2)
    print(f"✅ Converted: {len(audio_data)} bytes ({duration:.2f}s)")
    return audio_data


async def transcribe_with_flux(audio_file: str):
    """Transcribe audio using Deepgram Flux via WebSocket"""
    
    if not DEEPGRAM_API_KEY:
        print("❌ DEEPGRAM_API_KEY not set!")
        return
    
    audio_data = convert_to_flux_format(audio_file)
    if not audio_data:
        return
    
    # Chunk size in bytes for 80ms at 16kHz mono 16-bit
    bytes_per_chunk = int(SAMPLE_RATE * 2 * CHUNK_SIZE_MS / 1000)
    chunks = [audio_data[i:i+bytes_per_chunk] for i in range(0, len(audio_data), bytes_per_chunk)]
    print(f"📦 {len(chunks)} chunks of {bytes_per_chunk} bytes ({CHUNK_SIZE_MS}ms each)")
    
    url = f"wss://api.deepgram.com/v2/listen?model=flux-general-en&encoding=linear16&sample_rate={SAMPLE_RATE}"
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
    
    print(f"\n🚀 Connecting to Flux...")
    
    start_time = time.time()
    first_transcript_time = None
    transcripts = []
    final_transcript = ""
    
    try:
        async with websockets.connect(url, extra_headers=headers) as ws:
            print(f"✅ Connected in {(time.time() - start_time)*1000:.0f}ms")
            
            async def receive():
                nonlocal first_transcript_time, final_transcript
                try:
                    async for message in ws:
                        data = json.loads(message)
                        msg_type = data.get("type", "")
                        
                        if msg_type == "TurnInfo":
                            transcript = data.get("transcript", "")
                            event = data.get("event", "")
                            eot_conf = data.get("end_of_turn_confidence", 0)
                            
                            if transcript:
                                if first_transcript_time is None:
                                    first_transcript_time = time.time()
                                    ttft = (first_transcript_time - start_time) * 1000
                                    print(f"⚡ First transcript at {ttft:.0f}ms")
                                
                                # Show interim results with EOT confidence
                                print(f"🔄 [{eot_conf:.1%}] {transcript}")
                                final_transcript = transcript
                            
                            if event == "EndOfTurn":
                                print(f"🔚 Turn complete!")
                                transcripts.append(final_transcript)
                                final_transcript = ""
                        
                        elif msg_type == "EagerEndOfTurn":
                            print(f"⚡ Eager EOT - LLM can start responding!")
                        
                except asyncio.CancelledError:
                    pass
            
            receiver = asyncio.create_task(receive())
            
            # Send chunks at real-time pace
            send_start = time.time()
            for i, chunk in enumerate(chunks):
                await ws.send(chunk)
                # Real-time pacing (80ms per chunk)
                elapsed = time.time() - send_start
                expected = (i + 1) * CHUNK_SIZE_MS / 1000
                if expected > elapsed:
                    await asyncio.sleep(expected - elapsed)
            
            send_time = time.time() - send_start
            print(f"\n📤 Sent {len(chunks)} chunks in {send_time:.2f}s (real-time)")
            
            await ws.send(json.dumps({"type": "CloseStream"}))
            await asyncio.sleep(2)
            receiver.cancel()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Add any remaining transcript
    if final_transcript:
        transcripts.append(final_transcript)
    
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"⏱️  Total: {total_time:.2f}s | Audio: 18.36s")
    if first_transcript_time:
        print(f"⚡ Time to first transcript: {(first_transcript_time - start_time)*1000:.0f}ms")
    print(f"📝 {' '.join(transcripts)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import sys
    asyncio.run(transcribe_with_flux(sys.argv[1] if len(sys.argv) > 1 else AUDIO_FILE))

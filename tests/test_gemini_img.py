#!/usr/bin/env python3
"""Test Gemini image-to-text with valid image."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from google import genai
from google.genai import types
from PIL import Image


async def main():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    print(f"API Key: {api_key[:20]}...")

    client = genai.Client(api_key=api_key)

    # Use valid image
    test_img = Path("/home/mewtwo/Media/Images/landscape.png")
    print(f"Testing with: {test_img.name} ({test_img.stat().st_size} bytes)")

    # Open and verify image
    pil_img = Image.open(test_img)
    print(f"Image size: {pil_img.size}, mode: {pil_img.mode}")

    print("\n--- Test 1: Describe image ---")

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=["Describe this image in detail. What do you see?", pil_img],
        config=types.GenerateContentConfig(temperature=0.7)
    )

    print(f"\nResponse:\n{response.text}")

    if hasattr(response, "usage_metadata") and response.usage_metadata:
        metadata = response.usage_metadata
        pt = getattr(metadata, "prompt_token_count", 0)
        ct = getattr(metadata, "candidates_token_count", 0)
        tt = getattr(metadata, "total_token_count", 0)
        print(f"\nUsage: prompt={pt}, completion={ct}, total={tt}")

    print("\n--- Test 2: Extract text (if any) ---")

    response2 = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=["Extract any text visible in this image. If no text, say 'No text visible'.", pil_img],
        config=types.GenerateContentConfig(temperature=0.3)
    )

    print(f"\nResponse:\n{response2.text}")

    print("\n--- Test 3: Streaming analysis ---")

    stream = await asyncio.to_thread(
        client.models.generate_content_stream,
        model="gemini-2.5-flash",
        contents=["What are the main colors and visual elements in this image?", pil_img],
        config=types.GenerateContentConfig(temperature=0.5)
    )

    print("\nStreaming response:")
    for chunk in stream:
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()

if __name__ == "__main__":
    asyncio.run(main())

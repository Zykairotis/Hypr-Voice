#!/usr/bin/env python3
"""Simple standalone test for Gemini image-to-text."""

import asyncio
import os
import sys
from pathlib import Path

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Direct import without package init
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def main():
    """Test Gemini image-to-text directly."""
    print("="*60)
    print("GEMINI IMAGE-TO-TEXT TEST")
    print("="*60)

    # Check API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: No GEMINI_API_KEY found in environment!")
        return

    print(f"API Key: {api_key[:20]}...")

    # Import after dotenv loads
    from google import genai
    from google.genai import types
    from PIL import Image

    # Initialize client
    print("\nInitializing Gemini client...")
    client = genai.Client(api_key=api_key)

    # Find test image in user's media folder
    media_dir = Path("/home/mewtwo/Media/Images")
    if media_dir.exists():
        images = list(media_dir.glob("*.jpg")) + list(media_dir.glob("*.png")) + list(media_dir.glob("*.jpeg")) + list(media_dir.glob("*.webp"))
        if images:
            test_img = images[0]
            print(f"Using test image: {test_img.name}")
        else:
            print(f"No images found in {media_dir}")
            return
    else:
        print(f"Media directory not found: {media_dir}")
        return

    # Test 1: Direct API call with PIL Image
    print("\n" + "-"*60)
    print("TEST 1: Direct API call with PIL Image")
    print("-"*60)

    try:
        pil_img = Image.open(test_img)

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=["Describe this image in detail. What do you see?", pil_img],
            config=types.GenerateContentConfig(temperature=0.7)
        )

        print(f"\nResponse:\n{response.text}")

        # Usage metadata
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            metadata = response.usage_metadata
            print(f"\nUsage:")
            print(f"  Prompt tokens: {getattr(metadata, 'prompt_token_count', 0)}")
            print(f"  Completion tokens: {getattr(metadata, 'candidates_token_count', 0)}")
            print(f"  Total tokens: {getattr(metadata, 'total_token_count', 0)}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Streaming response
    print("\n" + "-"*60)
    print("TEST 2: Streaming response")
    print("-"*60)

    try:
        pil_img = Image.open(test_img)

        print("\nStreaming analysis...")
        stream = await asyncio.to_thread(
            client.models.generate_content_stream,
            model="gemini-2.5-flash",
            contents=["What text or symbols are visible in this image?", pil_img],
            config=types.GenerateContentConfig(temperature=0.5)
        )

        for chunk in stream:
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print()  # Newline

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: With bytes
    print("\n" + "-"*60)
    print("TEST 3: Using image bytes")
    print("-"*60)

    try:
        with open(test_img, "rb") as f:
            img_bytes = f.read()

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=[
                "Extract all text visible in this image. If no text, describe the main colors.",
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
            ],
            config=types.GenerateContentConfig(temperature=0.3)
        )

        print(f"\nResponse:\n{response.text}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

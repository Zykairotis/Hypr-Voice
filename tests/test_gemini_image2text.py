#!/usr/bin/env python3
"""Test Gemini image-to-text functionality."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load .env
load_dotenv(Path(__file__).parent.parent / ".env")

from hypr_voice.services.gemini_live.gemini_client import GeminiClient, GeminiConfig
from hypr_voice.services.gemini_live.integration import GeminiIntegration
from PIL import Image, ImageDraw, ImageFont


def create_test_image(path: Path, text: str = "Hello Gemini!") -> None:
    """Create a simple test image with text."""
    # Create a simple image with text
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)

    # Add some colored rectangles
    draw.rectangle([50, 50, 150, 100], fill='red')
    draw.rectangle([200, 50, 300, 100], fill='blue')
    draw.rectangle([125, 120, 225, 170], fill='green')

    # Add text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()

    draw.text((100, 10), text, fill='black', font=font)

    img.save(path)
    print(f"Created test image: {path}")


async def test_image_to_text_basic():
    """Test basic image-to-text with GeminiClient."""
    print("\n" + "="*60)
    print("TEST 1: Basic Image-to-Text with GeminiClient")
    print("="*60)

    # Check API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: No GEMINI_API_KEY found!")
        return False

    print(f"API Key found: {api_key[:20]}...")

    # Create test image
    test_img = Path("/tmp/test_gemini_image.png")
    create_test_image(test_img, "Hypr-Voice Test")

    try:
        config = GeminiConfig(api_key=api_key)
        client = GeminiClient(config)

        # Test 1: Generate content from image
        print("\n[Test 1.1] Analyzing image with basic prompt...")
        response = await client.generate_content(
            ["Describe this image in detail.", test_img],
            temperature=0.7
        )

        print(f"Response:\n{response['content']}")
        print(f"\nUsage: {response['usage']}")

        # Test 2: Stream content
        print("\n[Test 1.2] Streaming analysis...")
        async for chunk in client.stream_content(
            ["What text is visible in this image?", test_img],
            temperature=0.5
        ):
            if chunk['content']:
                print(chunk['content'], end='', flush=True)
        print()  # New line after streaming

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration_layer():
    """Test image-to-text with GeminiIntegration."""
    print("\n" + "="*60)
    print("TEST 2: Image-to-Text with GeminiIntegration")
    print("="*60)

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    test_img = Path("/tmp/test_gemini_image.png")

    try:
        integration = GeminiIntegration()

        # Test analyze_image
        print("\n[Test 2.1] Using analyze_image()...")
        result = await integration.analyze_image(
            test_img,
            prompt="Extract and list all text visible in this image."
        )
        print(f"Result: {result}")

        # Test streaming
        print("\n[Test 2.2] Streaming image analysis...")
        async for chunk in integration.stream_image_analysis(
            test_img,
            prompt="What colors and shapes do you see?"
        ):
            print(chunk, end='', flush=True)
        print()

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bytes_image():
    """Test with image as bytes."""
    print("\n" + "="*60)
    print("TEST 3: Image-to-Text with Bytes Input")
    print("="*60)

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    test_img = Path("/tmp/test_gemini_image.png")

    try:
        # Read image as bytes
        with open(test_img, "rb") as f:
            img_bytes = f.read()

        client = GeminiClient(GeminiConfig(api_key=api_key))

        print("\n[Test 3.1] Analyzing image bytes...")
        response = await client.generate_content(
            ["What does this image contain?", img_bytes],
            temperature=0.7
        )

        print(f"Response: {response['content']}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("GEMINI IMAGE-TO-TEXT TEST SUITE")
    print("="*60)

    results = []

    # Run tests
    results.append(("Basic Client", await test_image_to_text_basic()))
    results.append(("Integration Layer", await test_integration_layer()))
    results.append(("Bytes Input", await test_bytes_image()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")

    all_passed = all(r[1] for r in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

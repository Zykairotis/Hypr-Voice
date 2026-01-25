#!/usr/bin/env python3
"""
Image Generation API Client
A comprehensive Python client for the Cloudflare Workers AI image generation API
"""

import requests
import argparse
import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any


class ImageGenerationAPI:
    """Client for image generation API"""
    
    AVAILABLE_MODELS = [
        "@cf/leonardo/phoenix-1.0",           # Best for realism and quality
        "@cf/leonardo/lucid-origin",          # Sharp HD renders
        "@cf/stabilityai/stable-diffusion-xl-base-1.0",  # Reliable photorealism
        "@cf/black-forest-labs/flux-1-schnell",  # Fast and good quality
        "@cf/bytedance/stable-diffusion-xl-lightning",  # Fast SDXL
        "@cf/lykon/dreamshaper-8-lcm",        # Good balance (default)
        "@cf/runwayml/stable-diffusion-v1-5-img2img",
        "@cf/runwayml/stable-diffusion-v1-5-inpainting"
    ]
    
    def __init__(self, api_url: str, api_key: str):
        """
        Initialize the API client
        
        Args:
            api_url: Base URL of the API
            api_key: Authorization bearer token
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        num_steps: Optional[int] = None,
        guidance: Optional[float] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        nsfw: bool = False,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate an image from a text prompt
        
        Args:
            prompt: Text description of the image to generate
            model: Model to use (default: dreamshaper-8-lcm)
            num_steps: Number of inference steps (1-50, higher = better quality)
            guidance: How closely to follow prompt (2-10 for Phoenix, default varies)
            width: Image width in pixels
            height: Image height in pixels
            negative_prompt: Things to avoid in the image
            seed: Seed for reproducible generation
            nsfw: Allow NSFW content (note: platform filters still apply)
            output_path: Where to save the image (if None, returns bytes)
            
        Returns:
            Image data as bytes
        """
        # Build request payload
        payload: Dict[str, Any] = {"prompt": prompt}
        
        if model:
            if model not in self.AVAILABLE_MODELS:
                print(f"Warning: Model '{model}' not in known models list")
            payload["model"] = model
            
        if num_steps is not None:
            payload["num_steps"] = num_steps
        if guidance is not None:
            payload["guidance"] = guidance
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["seed"] = seed
        if nsfw:
            payload["nsfw"] = True
        
        # Make request
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            # Check if response is JSON (error)
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                error_data = response.json()
                raise Exception(f"API Error: {error_data}")
            
            response.raise_for_status()
            image_data = response.content
            
            # Save if output path provided
            if output_path:
                Path(output_path).write_bytes(image_data)
                print(f"✅ Image saved to: {output_path}")
            
            return image_data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    @classmethod
    def list_models(cls):
        """Print available models"""
        print("\n📋 Available Models:\n")
        for i, model in enumerate(cls.AVAILABLE_MODELS, 1):
            print(f"{i}. {model}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Cloudflare Workers AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python image_gen.py "a cute robot" -o robot.png
  
  # High quality with Phoenix model
  python image_gen.py "sunset over mountains" -m "@cf/leonardo/phoenix-1.0" -s 40 -g 7 -o sunset.png
  
  # Custom dimensions
  python image_gen.py "cityscape" -W 1920 -H 1080 -o city.png
  
  # With negative prompt
  python image_gen.py "portrait" -n "blurry, low quality" -o portrait.png
  
  # List available models
  python image_gen.py --list-models
        """
    )
    
    parser.add_argument('prompt', nargs='?', help='Text description of image to generate')
    parser.add_argument('-o', '--output', default='output.png', help='Output file path')
    parser.add_argument('-m', '--model', help='Model to use')
    parser.add_argument('-s', '--steps', type=int, help='Number of inference steps (1-50)')
    parser.add_argument('-g', '--guidance', type=float, help='Guidance scale (2-10)')
    parser.add_argument('-W', '--width', type=int, help='Image width')
    parser.add_argument('-H', '--height', type=int, help='Image height')
    parser.add_argument('-n', '--negative', help='Negative prompt')
    parser.add_argument('--seed', type=int, help='Seed for reproducibility')
    parser.add_argument('--nsfw', action='store_true', help='Allow NSFW (subject to platform filters)')
    parser.add_argument('--api-url', default='https://free-image-generation-api.parthsheth326.workers.dev', 
                        help='API endpoint URL')
    parser.add_argument('--api-key', default=None,
                        help='API authorization key (or set CFS_API_KEY)')
    parser.add_argument('--list-models', action='store_true', help='List available models')
    
    args = parser.parse_args()
    
    # Handle list models
    if args.list_models:
        ImageGenerationAPI.list_models()
        return
    
    # Require prompt
    if not args.prompt:
        parser.error("prompt is required (or use --list-models)")
    
    # Resolve API key securely
    api_key = args.api_key or os.getenv("CFS_API_KEY")
    if not api_key:
        parser.error("API key required (pass --api-key or set CFS_API_KEY)")
    
    # Create client
    client = ImageGenerationAPI(args.api_url, api_key)
    
    print(f"🎨 Generating image...")
    print(f"📝 Prompt: {args.prompt}")
    if args.model:
        print(f"🤖 Model: {args.model}")
    
    try:
        # Generate image
        client.generate(
            prompt=args.prompt,
            model=args.model,
            num_steps=args.steps,
            guidance=args.guidance,
            width=args.width,
            height=args.height,
            negative_prompt=args.negative,
            seed=args.seed,
            nsfw=args.nsfw,
            output_path=args.output
        )
        
        print(f"✨ Done!")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()



"""
-o, --output: Output file path
-m, --model: Model to use
-s, --steps: Number of inference steps (1-50)
-g, --guidance: Guidance scale (2-10)
-W, --width: Image width
-H, --height: Image height
-n, --negative: Negative prompt
--seed: Seed for reproducibility
--nsfw: Allow NSFW content
--api-url: Custom API URL
--api-key: Your API key
"""

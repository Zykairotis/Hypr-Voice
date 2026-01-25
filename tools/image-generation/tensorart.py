#!/usr/bin/env python3
"""
Tensor.Art API Client
Generate images using specific models from Tensor.Art
"""

import requests
import argparse
import json
import time
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import uuid


class TensorArtAPI:
    """Client for Tensor.Art TAMS API"""
    
    def __init__(self, api_token: str, api_url: str = "https://ap-east-1.tensorart.cloud"):
        """
        Initialize the API client
        
        Args:
            api_token: Your API token from Tensor.Art
            api_url: Base URL of the API (default: Asia-Pacific region)
        """
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
    
    def generate_image(
        self,
        prompt: str,
        model_id: str = "763947005736342551",  # Flux Pony-Real-F1D-alpha
        negative_prompt: str = "low quality, bad anatomy, blurry",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0,
        seed: int = -1,
        count: int = 1,
        clip_skip: int = 2,
        sampler_name: str = "dpmpp_2m_sde",
        scheduler: str = "karras"
    ) -> Dict[str, Any]:
        """
        Generate an image using Tensor.Art API
        
        Args:
            prompt: Text description of the image
            model_id: Model ID from Tensor.Art (default: Flux Pony-Real-F1D-alpha)
            negative_prompt: Things to avoid in the image
            width: Image width in pixels
            height: Image height in pixels
            steps: Number of inference steps (1-50)
            cfg_scale: Classifier-free guidance scale (1-20)
            seed: Random seed (-1 for random)
            count: Number of images to generate
            clip_skip: CLIP skip value
            sampler_name: Sampling method
            scheduler: Scheduler type
            
        Returns:
            Job response with job_id
        """
        request_id = str(uuid.uuid4()).replace('-', '')
        
        payload = {
            "request_id": request_id,
            "stages": [
                {
                    "type": "INPUT_INITIALIZE",
                    "inputInitialize": {
                        "seed": seed,
                        "count": count
                    }
                },
                {
                    "type": "DIFFUSION",
                    "diffusion": {
                        "width": width,
                        "height": height,
                        "prompts": [{"text": prompt}],
                        "negative_prompts": [{"text": negative_prompt}],
                        "steps": steps,
                        "sd_model": model_id,
                        "clip_skip": clip_skip,
                        "cfg_scale": cfg_scale,
                        "sampler_name": sampler_name,
                        "scheduler": scheduler
                    }
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/v1/jobs",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            # Print debug info on error
            if response.status_code != 200:
                print(f"\n🔍 Debug Info:")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                print(f"Request Payload: {json.dumps(payload, indent=2)}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create job: {e}")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a job
        
        Args:
            job_id: The job ID returned from generate_image
            
        Returns:
            Job status information
        """
        try:
            response = requests.get(
                f"{self.api_url}/v1/jobs/{job_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get job status: {e}")
    
    def wait_for_job(
        self,
        job_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wait for a job to complete
        
        Args:
            job_id: The job ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            Final job status
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            job_status = status.get('job', {}).get('status')
            
            if job_status == 'SUCCESS':
                return status
            elif job_status in ['FAILED', 'CANCELLED']:
                raise Exception(f"Job {job_status.lower()}: {status}")
            
            print(f"Status: {job_status}, waiting...")
            time.sleep(poll_interval)
        
        raise Exception(f"Job timed out after {timeout} seconds")
    
    def download_images(
        self,
        job_result: Dict[str, Any],
        output_dir: str = "."
    ) -> List[str]:
        """
        Download generated images from job result
        
        Args:
            job_result: Job status result containing image URLs
            output_dir: Directory to save images
            
        Returns:
            List of saved file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        job = job_result.get('job', {})
        successInfo = job.get('successInfo', {})
        images = successInfo.get('images', [])
        
        if not images:
            raise Exception("No images found in job result")
        
        for idx, image in enumerate(images):
            url = image.get('url')
            if not url:
                continue
            
            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                
                filename = f"tensorart_{job.get('id', 'unknown')}_{idx}.png"
                filepath = output_path / filename
                
                filepath.write_bytes(response.content)
                saved_files.append(str(filepath))
                print(f"✅ Saved: {filepath}")
                
            except Exception as e:
                print(f"❌ Failed to download image {idx}: {e}")
        
        return saved_files
    
    def generate_and_download(
        self,
        prompt: str,
        output_dir: str = ".",
        **kwargs
    ) -> List[str]:
        """
        Generate images and download them in one call
        
        Args:
            prompt: Text description
            output_dir: Where to save images
            **kwargs: Additional parameters for generate_image
            
        Returns:
            List of saved file paths
        """
        print(f"🎨 Generating image...")
        print(f"📝 Prompt: {prompt}")
        
        # Create job
        job_response = self.generate_image(prompt, **kwargs)
        job_id = job_response.get('job', {}).get('id')
        
        if not job_id:
            raise Exception(f"No job ID in response: {job_response}")
        
        print(f"✨ Job created: {job_id}")
        
        # Wait for completion
        result = self.wait_for_job(job_id)
        
        # Download images
        print("📥 Downloading images...")
        return self.download_images(result, output_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Tensor.Art API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python tensorart.py "anime girl" --token YOUR_TOKEN
  
  # With specific model
  python tensorart.py "landscape" --model 763947005736342551 --token YOUR_TOKEN
  
  # Custom parameters
  python tensorart.py "portrait" --steps 30 --cfg 8 --size 768 768 --token YOUR_TOKEN
  
  # Generate multiple images
  python tensorart.py "cat" --count 4 --token YOUR_TOKEN
        """
    )
    
    parser.add_argument('prompt', help='Text description of image to generate')
    parser.add_argument('--token', required=True, help='Tensor.Art API token')
    parser.add_argument('--model', default='763947005736342551', 
                        help='Model ID (default: Flux Pony-Real-F1D-alpha)')
    parser.add_argument('--negative', default='low quality, bad anatomy, blurry',
                        help='Negative prompt')
    parser.add_argument('--steps', type=int, default=20, help='Inference steps (1-50)')
    parser.add_argument('--cfg', type=float, default=7.0, 
                        help='CFG scale (1-20)')
    parser.add_argument('--size', type=int, nargs=2, default=[512, 512],
                        metavar=('WIDTH', 'HEIGHT'), help='Image dimensions')
    parser.add_argument('--seed', type=int, default=-1, help='Random seed (-1 for random)')
    parser.add_argument('--count', type=int, default=1, help='Number of images')
    parser.add_argument('--output', default='.', help='Output directory')
    parser.add_argument('--sampler', default='dpmpp_2m_sde',
                        help='Sampler name')
    parser.add_argument('--scheduler', default='karras', help='Scheduler type')
    parser.add_argument('--clip-skip', type=int, default=2, help='CLIP skip value')
    
    args = parser.parse_args()
    
    # Create client
    client = TensorArtAPI(api_token=args.token)
    
    try:
        # Generate and download
        files = client.generate_and_download(
            prompt=args.prompt,
            model_id=args.model,
            negative_prompt=args.negative,
            width=args.size[0],
            height=args.size[1],
            steps=args.steps,
            cfg_scale=args.cfg,
            seed=args.seed,
            count=args.count,
            clip_skip=args.clip_skip,
            sampler_name=args.sampler,
            scheduler=args.scheduler,
            output_dir=args.output
        )
        
        print(f"\n🎉 Done! Generated {len(files)} image(s)")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
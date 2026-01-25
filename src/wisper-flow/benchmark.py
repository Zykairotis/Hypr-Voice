#!/usr/bin/env python3
"""
Wispr Fast - ULTRAFAST Benchmark v6
===================================

Benchmark the new ULTRAFAST (in-memory soundfile) implementation.
"""

import csv
import os
import sys
import time
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# Configure logging without emojis for Unicode safety on Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("benchmark.log"), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Benchmark")

# Import from sibling module
sys.path.insert(0, str(Path(__file__).parent))
from transcribe import transcribe_file_async, get_audio_duration, TranscriptionContext

async def benchmark_file(file_path: str) -> dict:
    """Benchmark a single audio file with the async pipeline"""
    file_name = Path(file_path).name
    logger.info(f"BENCHMARKING: {file_name}")
    
    result = {
        'file': file_name,
        'duration_s': get_audio_duration(file_path),
        'time_ms': 0,
        'preprocess_ms': 0,
        'network_ms': 0,
        'status': '',
        'method': '',
        'chunks': 0,
        'text': '',
        'error': ''
    }
    
    t_start = time.time()
    try:
        resp = await transcribe_file_async(file_path)
        result['time_ms'] = (time.time() - t_start) * 1000
        result['status'] = resp.get('status', 'unknown')
        result['method'] = resp.get('method', 'unknown')
        result['preprocess_ms'] = resp.get('preprocess_ms', 0)
        result['network_ms'] = resp.get('network_ms', 0)
        result['chunks'] = resp.get('chunk_count', 1)
        
        if result['status'] == 'success':
            result['text'] = resp.get('asr_text', '')
            logger.info(f"  SUCCESS: {result['time_ms']:.0f}ms (preprocess: {result['preprocess_ms']:.0f}ms) [{result['method']}]")
        else:
            result['error'] = resp.get('error_message', 'API Error')
            logger.warning(f"  FAILED: {result['error']}")
    except Exception as e:
        result['status'] = 'exception'
        result['error'] = str(e)
        logger.error(f"  Exception: {e}")
            
    return result

async def run_benchmark(folder):
    audio_files = sorted(list(Path(folder).glob("*.wav")))
    logger.info(f"Starting ULTRAFAST Benchmark on {len(audio_files)} files")
    
    results = []
    for f in audio_files:
        results.append(await benchmark_file(str(f)))
    
    # Calculate totals
    total_duration = sum(r['duration_s'] for r in results)
    total_time = sum(r['time_ms'] for r in results)
    total_preprocess = sum(r['preprocess_ms'] for r in results)
    total_network = sum(r['network_ms'] for r in results)
    
    # Generate Report
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"# Wispr Fast - ULTRAFAST Benchmark v6\n\n"
    md += f"**Date:** {timestamp}\n\n"
    md += f"## Summary\n\n"
    md += f"- **Files:** {len(results)}\n"
    md += f"- **Total Audio Duration:** {total_duration:.1f}s\n"
    md += f"- **Total Processing Time:** {total_time:.0f}ms\n"
    md += f"- **Total Preprocess Time:** {total_preprocess:.0f}ms (was ~{len(results)*500}ms with FFmpeg)\n"
    md += f"- **Total Network Time:** {total_network:.0f}ms\n"
    md += f"- **Avg Preprocess:** {total_preprocess/len(results):.1f}ms per file\n\n"
    md += "## Results\n\n"
    md += "| File | Duration | Total (ms) | Preprocess | Network | Chunks | Transcript |\n"
    md += "|------|----------|------------|------------|---------|--------|------------|\n"
    for r in results:
        t_val = f"{r['time_ms']:.0f}" if r['time_ms'] > 0 else "FAIL"
        display_text = (r['text'][:40] + '...') if len(r['text']) > 40 else r['text']
        md += f"| {r['file'][:35]} | {r['duration_s']:.1f}s | {t_val} | {r['preprocess_ms']:.0f}ms | {r['network_ms']:.0f}ms | {r['chunks']} | {display_text} |\n"
    
    # Save with timestamp
    filename = f"benchmark_ultrafast_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(filename, "w", encoding='utf-8') as f:
        f.write(md)
        f.write("\n\n## Detailed Transcripts\n\n")
        for r in results:
            f.write(f"### {r['file']}\n")
            f.write(f"**Preprocess:** {r['preprocess_ms']:.0f}ms | **Network:** {r['network_ms']:.0f}ms | **Total:** {r['time_ms']:.0f}ms\n\n")
            f.write(f"{r['text']}\n\n")
            f.write("---\n\n")
    
    # Also save to standard location
    with open("benchmark_results.md", "w", encoding='utf-8') as f:
        f.write(md)
    
    logger.info(f"DONE. Report saved to {filename}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"ULTRAFAST BENCHMARK COMPLETE")
    print(f"{'='*60}")
    print(f"Files:            {len(results)}")
    print(f"Total Audio:      {total_duration:.1f}s")
    print(f"Total Time:       {total_time:.0f}ms")
    print(f"Avg Preprocess:   {total_preprocess/len(results):.1f}ms (was ~500ms with FFmpeg)")
    print(f"{'='*60}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python benchmark.py <test_folder>"); sys.exit(1)
    asyncio.run(run_benchmark(sys.argv[1]))

#!/usr/bin/env python3
"""
WhisperLive Startup Script for Hypr-Voice
Loads configuration and starts the WhisperLive server
"""

import os
import sys
import yaml
import logging
import argparse
from pathlib import Path

def setup_logging(log_level, log_file):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config(config_file):
    """Load configuration from YAML file"""
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_file}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing config file: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Start WhisperLive for Hypr-Voice")
    parser.add_argument("--config", "-c",
                       default="config.yaml",
                       help="Configuration file path")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show configuration without starting server")

    args = parser.parse_args()

    # Get script directory
    script_dir = Path(__file__).parent
    config_path = script_dir / args.config

    # Load configuration
    config = load_config(config_path)

    # Setup logging
    setup_logging(
        config['logging']['level'],
        config['logging']['file']
    )

    logger = logging.getLogger(__name__)

    if args.dry_run:
        print("🔍 Dry run - Configuration:")
        print(yaml.dump(config, default_flow_style=False))
        return

    logger.info("🎤 Starting WhisperLive for Hypr-Voice")
    logger.info(f"📋 Config: {config_path}")

    # Set environment variables
    os.environ["OMP_NUM_THREADS"] = str(config['performance']['omp_num_threads'])

    # Create cache directories
    os.makedirs(config['performance']['cache_path'], exist_ok=True)
    os.makedirs(config['model']['download_root'], exist_ok=True)

    # Import WhisperLive after environment setup
    try:
        from whisper_live.server import TranscriptionServer
        logger.info("✅ WhisperLive imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import WhisperLive: {e}")
        logger.error("Please install whisper-live: pip install whisper-live")
        sys.exit(1)

    # Create server instance
    server = TranscriptionServer()

    # Prepare server arguments
    server_kwargs = {
        'host': '0.0.0.0',
        'port': config['server']['port'],
        'backend': config['backend']['type'],
        'single_model': False,  # Allow model download per client for large-v3-turbo
        'max_clients': config['server']['max_clients'],
        'max_connection_time': config['server']['max_connection_time'],
        'cache_path': config['performance']['cache_path']
    }

    # Add model-specific paths if provided
    # Only use faster_whisper_custom_model_path for actual filesystem paths
    # HuggingFace repo IDs should be handled by client config
    if config['backend']['type'] == 'faster_whisper' and 'model_path' in config['backend']:
        model_path = config['backend']['model_path']
        # Check if it's a local filesystem path (not a HF repo ID)
        if os.path.isdir(model_path) or '/' not in model_path:
            server_kwargs['faster_whisper_custom_model_path'] = model_path
        # For HF repo IDs, we'll pass it via client config instead
    elif config['backend']['type'] == 'tensorrt' and 'model_path' in config['backend']:
        server_kwargs['whisper_tensorrt_path'] = config['backend']['model_path']
    
    # Store model preference for client connections
    server.model_preference = config['backend'].get('model_path')

    logger.info(f"🚀 Server configuration:")
    logger.info(f"   Host: 0.0.0.0:{config['server']['port']}")
    logger.info(f"   Backend: {config['backend']['type']}")
    logger.info(f"   Model: {config['backend'].get('model_path', 'Will download on first connection')}")
    logger.info(f"   Device: {config['backend']['device']}")
    logger.info(f"   Language: {config['backend']['language']}")

    if config['hypr_voice']['enabled']:
        logger.info("🔗 Hypr-Voice integration: ENABLED")

    try:
        # Start the server
        server.run(**server_kwargs)
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Background process for continuous context monitoring.
Runs independently to gather context data and provide it to the web UI.
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import psutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

class ContextProcessor:
    """Processes and aggregates context data."""

    def __init__(self, output_dir: str = '/tmp/context-data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.running = False

        # Import context manager
        try:
            from context_manager import get_context_manager
            self.context_manager = get_context_manager()
        except ImportError:
            logger.error("Context manager not available")
            self.context_manager = None

        self.last_shell_update = 0
        self.last_clipboard_update = 0
        self.last_window_update = 0

        # Stats tracking
        self.stats = {
            'shell_commands': 0,
            'clipboard_entries': 0,
            'window_changes': 0,
            'start_time': time.time()
        }

    async def process_shell_history(self):
        """Process shell history and extract keywords."""
        if not self.context_manager:
            return

        try:
            # Only update if data changed (check file modification time)
            history_files = [
                Path.home() / '.zsh_history',
                Path.home() / '.bash_history'
            ]

            latest_mtime = max([f.stat().st_mtime for f in history_files if f.exists()] + [0])

            if latest_mtime > self.last_shell_update:
                commands = self.context_manager.get_shell_history(100)
                logger.debug(f"Fetched {len(commands)} shell commands")

                # Save to disk for web UI
                self._save_data('shell_history.json', {
                    'commands': commands,
                    'timestamp': int(time.time()),
                    'count': len(commands)
                })

                self.last_shell_update = latest_mtime
                self.stats['shell_commands'] += len(commands)
        except Exception as e:
            logger.error(f"Error processing shell history: {e}")

    async def process_clipboard(self):
        """Process clipboard history."""
        if not self.context_manager:
            return

        try:
            # Check if cliphist is available
            import subprocess
            result = subprocess.run(
                ['cliphist', 'list'],
                capture_output=True,
                text=True,
                timeout=1
            )

            if result.returncode == 0:
                entries = self.context_manager.get_clipboard_history(50)
                logger.debug(f"Fetched {len(entries)} clipboard entries")

                # Save to disk for web UI
                self._save_data('clipboard_history.json', {
                    'entries': entries,
                    'timestamp': int(time.time()),
                    'count': len(entries)
                })

                self.last_clipboard_update = time.time()
                self.stats['clipboard_entries'] += len(entries)
        except Exception as e:
            logger.debug(f"Clipboard not available or error: {e}")

    async def process_window_info(self):
        """Process window information from active application."""
        if not self.context_manager:
            return

        try:
            # Try to get window info from Hyprland
            import subprocess
            result = subprocess.run(
                ['hyprctl', 'activewindow', '-j'],
                capture_output=True,
                text=True,
                timeout=1
            )

            if result.returncode == 0:
                window_info = json.loads(result.stdout)

                # Save to disk for web UI
                self._save_data('active_window.json', {
                    'window': window_info,
                    'timestamp': int(time.time())
                })

                self.last_window_update = time.time()
                self.stats['window_changes'] += 1

                # Update vocabulary with new window
                try:
                    from vocabulary_manager import get_vocabulary_manager
                    vocab_manager = get_vocabulary_manager()
                    if vocab_manager:
                        app_class = window_info.get('class', '')
                        app_title = window_info.get('title', '')
                        vocab_manager.update_vocabulary(app_class, app_title)
                except ImportError:
                    pass
        except Exception as e:
            logger.debug(f"Window info not available or error: {e}")

    async def process_comprehensive_context(self):
        """Process comprehensive context from all sources."""
        if not self.context_manager:
            return

        try:
            # Get window info for context
            window_info = None
            try:
                import subprocess
                result = subprocess.run(
                    ['hyprctl', 'activewindow', '-j'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    window_info = json.loads(result.stdout)
            except:
                pass

            # Get comprehensive context
            context_data = self.context_manager.get_comprehensive_context(window_info)

            # Save to disk for web UI
            self._save_data('comprehensive_context.json', {
                **context_data,
                'timestamp': int(time.time())
            })

            # Also save stats
            self._save_stats()

        except Exception as e:
            logger.error(f"Error processing comprehensive context: {e}")

    def _save_data(self, filename: str, data: Dict[str, Any]):
        """Save data to disk."""
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def _save_stats(self):
        """Save processing statistics."""
        runtime = time.time() - self.stats['start_time']

        self._save_data('processor_stats.json', {
            **self.stats,
            'runtime_seconds': runtime,
            'timestamp': int(time.time())
        })

    async def cleanup_old_files(self):
        """Clean up old data files."""
        try:
            # Remove files older than 1 hour
            cutoff = time.time() - 3600

            for filepath in self.output_dir.glob('*.json'):
                if filepath.stat().st_mtime < cutoff:
                    filepath.unlink()
                    logger.debug(f"Cleaned up old file: {filepath}")
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")

    async def run(self):
        """Run the context processor."""
        self.running = True
        logger.info("Starting Context Processor")

        try:
            while self.running:
                # Process all context sources
                await self.process_shell_history()
                await asyncio.sleep(1)

                await self.process_clipboard()
                await asyncio.sleep(1)

                await self.process_window_info()
                await asyncio.sleep(1)

                await self.process_comprehensive_context()

                # Wait before next cycle
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("Context processor cancelled")
        except Exception as e:
            logger.error(f"Error in processor loop: {e}")
        finally:
            self._save_stats()
            self.running = False
            logger.info("Context Processor stopped")

    def stop(self):
        """Stop the processor."""
        self.running = False


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/tmp/context-processor.log'),
            logging.StreamHandler()
        ]
    )

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create processor
    processor = ContextProcessor()

    # Run processor
    try:
        asyncio.run(processor.run())
    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down...")
    finally:
        processor.stop()


if __name__ == "__main__":
    main()

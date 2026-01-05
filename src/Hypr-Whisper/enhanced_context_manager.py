#!/usr/bin/env python3
"""
Enhanced Context Manager for Hypr-Voice
Integrates 5 data sources with ultra-fast vocabulary extraction
"""

import subprocess
import logging
import re
import json
import yaml
import time
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime

from ultrafast_vocabulary_extractor import (
    BatchVocabularyExtractor,
    get_vocabulary_extractor
)

logger = logging.getLogger(__name__)


class EnhancedContextManager:
    """
    Enhanced context manager with 5 data sources:
    1. Chat history (last 10 sessions)
    2. Clipboard history (10 entries)
    3. Window metadata (enhanced Hyprland integration)
    4. Shell history (last 40 commands)
    5. Custom dictionary (YAML)
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the enhanced context manager

        Args:
            config_path: Path to enhanced context configuration
        """
        self.config_dir = Path(config_path) if config_path else Path(__file__).parent / "config"

        # Load configuration
        self.config = self._load_config()

        # Initialize batch vocabulary extractor
        self.batch_extractor = BatchVocabularyExtractor(
            target_count=self.config.get('extractor', {}).get('target_vocabulary_size', 100),
            min_length=self.config.get('extractor', {}).get('min_word_length', 2)
        )

        # Cache for last extraction
        self._last_vocabulary: List[str] = []
        self._last_extraction_time: float = 0.0
        self._cache_ttl = 5.0  # Cache for 5 seconds

        logger.info("Enhanced Context Manager initialized")

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        config_file = self.config_dir / "context_enhanced.yaml"

        # Default configuration
        default_config = {
            'sources': {
                'chat_history': {
                    'enabled': True,
                    'max_sessions': 10,
                    'logs_dir': str(Path(__file__).parent.parent.parent / "logs"),
                    'extract_from': ['user']
                },
                'clipboard': {
                    'enabled': True,
                    'max_entries': 10,
                    'tool': 'cliphist'
                },
                'window': {
                    'enabled': True,
                    'backend': 'auto',
                    'monitor_events': False,
                    'extract_from_title': ['file_paths', 'git_branches', 'urls']
                },
                'shell': {
                    'enabled': True,
                    'command_count': 40,
                    'sources': ['zsh', 'bash']
                },
                'custom_dictionary': {
                    'enabled': True,
                    'path': 'config/custom_dictionary.yaml'
                }
            },
            'extractor': {
                'target_vocabulary_size': 100,
                'min_word_length': 2,
                'enable_compound_patterns': True,
                'cache_size': 1000
            },
            'performance': {
                'use_lru_cache': True,
                'parallel_extraction': False,
                'early_exit': True
            }
        }

        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = yaml.safe_load(f)
                    # Merge with defaults
                    default_config.update(user_config)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_file}: {e}")

        return default_config

    # ========== Data Source 1: Chat History ==========

    def get_chat_history(self, max_sessions: Optional[int] = None) -> List[str]:
        """
        Get chat history content from last N sessions

        Args:
            max_sessions: Maximum number of sessions to read

        Returns:
            List of transcribed text from chat sessions
        """
        if not self.config['sources']['chat_history']['enabled']:
            return []

        max_sessions = max_sessions or self.config['sources']['chat_history']['max_sessions']
        logs_dir = Path(self.config['sources']['chat_history']['logs_dir'])

        if not logs_dir.exists():
            logger.warning(f"Chat history directory not found: {logs_dir}")
            return []

        try:
            # Find all chat.json files, sort by modification time
            chat_files = sorted(
                logs_dir.glob("*/chat.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:max_sessions]

            all_content = []
            extract_from = set(self.config['sources']['chat_history']['extract_from'])

            for chat_file in chat_files:
                try:
                    with open(chat_file, 'r', errors='ignore') as f:
                        data = json.load(f)

                    # Extract content from messages
                    for message in data:
                        # Filter by message type
                        msg_type = message.get('type', '')
                        if msg_type in extract_from:
                            content = message.get('content', '')
                            if content and isinstance(content, str):
                                # Filter out command markers
                                content = re.sub(r'<command-name>.*?</command-name>', '', content)
                                content = re.sub(r'<command-args>.*?</command-args>', '', content)
                                content = re.sub(r'<local-command-stdout>.*?</local-command-stdout>', '', content)
                                if content.strip():
                                    all_content.append(content.strip())

                except Exception as e:
                    logger.debug(f"Error reading chat file {chat_file}: {e}")
                    continue

            logger.debug(f"Extracted content from {len(chat_files)} chat sessions")
            return all_content

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    # ========== Data Source 2: Clipboard History (Enhanced) ==========

    def get_clipboard_history(self, max_entries: Optional[int] = None) -> List[str]:
        """
        Get last N clipboard entries using cliphist or wl-paste

        Args:
            max_entries: Maximum number of clipboard entries

        Returns:
            List of clipboard entries
        """
        if not self.config['sources']['clipboard']['enabled']:
            return []

        max_entries = max_entries or self.config['sources']['clipboard']['max_entries']
        tool = self.config['sources']['clipboard']['tool']
        entries = []

        try:
            if tool == 'cliphist':
                result = subprocess.run(
                    ['cliphist', 'list'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[:max_entries]
                    for line in lines:
                        if '\t' in line:
                            entry = line.split('\t', 1)[1]
                        else:
                            entry = line
                        if entry:
                            entries.append(entry)

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.debug(f"cliphist not available or timed out: {e}")

        # Fallback: current clipboard only
        if not entries:
            try:
                result = subprocess.run(
                    ['wl-paste'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    entry = result.stdout.strip()
                    if entry:
                        entries.append(entry)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.debug("wl-paste not available")

        logger.debug(f"Retrieved {len(entries)} clipboard entries")
        return entries

    # ========== Data Source 3: Window Metadata (Enhanced) ==========

    def get_window_metadata(self) -> Dict:
        """
        Get enhanced window metadata using window_backends

        Returns:
            Dictionary with window information and extracted vocabulary
        """
        if not self.config['sources']['window']['enabled']:
            return {}

        try:
            # Import window backend detection
            from window_backends import detect_backend
            backend = detect_backend()
            window_info = backend.get_active_window()

            if not window_info:
                return {}

            # Extract vocabulary from window title
            title = window_info.get('title', '')
            extracted_vocab = set()

            if title:
                # Extract file paths
                file_patterns = re.findall(r'[\w\-]+\.\w+', title)
                extracted_vocab.update(file_patterns)

                # Extract paths
                path_patterns = re.findall(r'/[\w/\-\.]+', title)
                extracted_vocab.update(path_patterns)

                # Extract technical terms
                tech_terms = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)+|\w+_\w+|\w+-\w+', title)
                extracted_vocab.update(tech_terms)

                # Extract Git branches
                git_branches = re.findall(r'\((?:HEAD detached at|HEAD(?: ->)?|feature/|bugfix/|dev/)?([^)]+)\)', title)
                extracted_vocab.update(git_branches)

                # Extract URLs
                urls = re.findall(r'https?://[\w\-\.]+(?:/[\w\-\.]*)*', title)
                extracted_vocab.update(urls)

            return {
                'window_info': window_info,
                'extracted_vocabulary': list(extracted_vocab)
            }

        except Exception as e:
            logger.error(f"Error getting window metadata: {e}")
            return {}

    # ========== Data Source 4: Shell History (Maintained) ==========

    def get_shell_history(self, count: Optional[int] = None) -> List[str]:
        """
        Get last N shell commands from history file

        Args:
            count: Number of commands to retrieve

        Returns:
            List of recent commands
        """
        if not self.config['sources']['shell']['enabled']:
            return []

        count = count or self.config['sources']['shell']['command_count']

        history_files = []
        if 'zsh' in self.config['sources']['shell']['sources']:
            history_files.append(Path.home() / '.zsh_history')
        if 'bash' in self.config['sources']['shell']['sources']:
            history_files.append(Path.home() / '.bash_history')

        commands = []
        for history_file in history_files:
            if history_file.exists():
                try:
                    with open(history_file, 'r', errors='ignore') as f:
                        lines = f.readlines()
                        for line in lines[-count * 2:]:
                            if ':' in line and ';' in line:  # zsh format
                                parts = line.split(';', 1)
                                if len(parts) > 1:
                                    cmd = parts[1].strip()
                                    if cmd:
                                        commands.append(cmd)
                            else:
                                cmd = line.strip()
                                if cmd:
                                    commands.append(cmd)
                    break
                except Exception as e:
                    logger.error(f"Error reading shell history from {history_file}: {e}")
                    continue

        result = commands[-count:] if commands else []
        logger.debug(f"Retrieved {len(result)} shell commands")
        return result

    # ========== Data Source 5: Custom Dictionary (NEW) ==========

    def get_custom_dictionary(self) -> List[str]:
        """
        Load custom dictionary from YAML file

        Returns:
            List of custom vocabulary terms
        """
        if not self.config['sources']['custom_dictionary']['enabled']:
            return []

        dict_path = Path(self.config['sources']['custom_dictionary']['path'])

        # Try relative to config dir
        if not dict_path.is_absolute():
            dict_path = self.config_dir / dict_path

        if not dict_path.exists():
            logger.debug(f"Custom dictionary not found: {dict_path}")
            return []

        try:
            with open(dict_path, 'r') as f:
                data = yaml.safe_load(f)

            if not data:
                return []

            # Extract all terms from different sections
            terms = set()

            # Top-level lists
            for key in ['project_terms', 'domains', 'products', 'technical_terms']:
                if key in data:
                    if isinstance(data[key], list):
                        terms.update(data[key])
                    elif isinstance(data[key], dict):
                        for sublist in data[key].values():
                            if isinstance(sublist, list):
                                terms.update(sublist)

            logger.debug(f"Loaded {len(terms)} terms from custom dictionary")
            return list(terms)

        except Exception as e:
            logger.error(f"Error loading custom dictionary: {e}")
            return []

    # ========== Main Extraction Method ==========

    def extract_comprehensive_vocabulary(
        self,
        force_refresh: bool = False
    ) -> Dict[str, any]:
        """
        Extract vocabulary from all 5 data sources

        Args:
            force_refresh: Force refresh even if cache is valid

        Returns:
            Dictionary with vocabulary and metadata
        """
        # Check cache
        current_time = time.time()
        if not force_refresh and (current_time - self._last_extraction_time) < self._cache_ttl:
            logger.debug("Returning cached vocabulary")
            return {
                'vocabulary': self._last_vocabulary,
                'cached': True,
                'sources': {}
            }

        start_time = time.perf_counter()
        self.batch_extractor.reset()

        sources_metadata = {}

        # 1. Chat History
        if self.config['sources']['chat_history']['enabled']:
            chat_content = " ".join(self.get_chat_history())
            if chat_content:
                terms = self.batch_extractor.add_context('chat_history', chat_content)
                sources_metadata['chat_history'] = {
                    'sessions_processed': len(self.get_chat_history()),
                    'terms_extracted': len(terms)
                }

        # 2. Clipboard History
        if self.config['sources']['clipboard']['enabled']:
            clipboard_content = " ".join(self.get_clipboard_history())
            if clipboard_content:
                terms = self.batch_extractor.add_context('clipboard', clipboard_content)
                sources_metadata['clipboard'] = {
                    'entries_processed': len(self.get_clipboard_history()),
                    'terms_extracted': len(terms)
                }

        # 3. Window Metadata
        if self.config['sources']['window']['enabled']:
            window_data = self.get_window_metadata()
            if window_data and 'extracted_vocabulary' in window_data:
                window_vocab = " ".join(window_data['extracted_vocabulary'])
                if window_vocab:
                    terms = self.batch_extractor.add_context('window', window_vocab)
                    sources_metadata['window'] = {
                        'application': window_data.get('window_info', {}).get('class', ''),
                        'title': window_data.get('window_info', {}).get('title', '')[:50],
                        'terms_extracted': len(terms)
                    }

        # 4. Shell History
        if self.config['sources']['shell']['enabled']:
            shell_content = " ".join(self.get_shell_history())
            if shell_content:
                terms = self.batch_extractor.add_context('shell', shell_content)
                sources_metadata['shell'] = {
                    'commands_processed': len(self.get_shell_history()),
                    'terms_extracted': len(terms)
                }

        # 5. Custom Dictionary
        if self.config['sources']['custom_dictionary']['enabled']:
            custom_terms = self.get_custom_dictionary()
            if custom_terms:
                custom_content = " ".join(custom_terms)
                terms = self.batch_extractor.add_context('custom_dictionary', custom_content)
                sources_metadata['custom_dictionary'] = {
                    'terms_loaded': len(custom_terms),
                    'terms_extracted': len(terms)
                }

        # Get final vocabulary
        vocabulary = self.batch_extractor.get_vocabulary()

        # Update cache
        self._last_vocabulary = vocabulary
        self._last_extraction_time = current_time

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Comprehensive vocabulary extraction: {len(vocabulary)} terms "
            f"from {len(sources_metadata)} sources in {elapsed_ms:.2f}ms"
        )

        return {
            'vocabulary': vocabulary,
            'cached': False,
            'extraction_time_ms': elapsed_ms,
            'sources': sources_metadata,
            'stats': self.batch_extractor.get_stats()
        }

    def get_vocabulary_for_whisper(
        self,
        max_tokens: int = 200
    ) -> str:
        """
        Get vocabulary formatted for Whisper's initial_prompt

        Args:
            max_tokens: Maximum tokens ( Whisper max is 224)

        Returns:
            Comma-separated vocabulary string
        """
        result = self.extract_comprehensive_vocabulary()
        vocabulary = result['vocabulary']

        # Build comma-separated list (most effective format)
        # Conservative: 800 chars ≈ 200 tokens
        prompt_parts = []
        current_length = 0
        MAX_CHARS = 800

        for term in vocabulary:
            addition = f"{term}, "
            if current_length + len(addition) > MAX_CHARS:
                break
            prompt_parts.append(term)
            current_length += len(addition)

        prompt = ", ".join(prompt_parts)
        if prompt:
            prompt += "."

        logger.debug(
            f"Generated Whisper prompt: {len(prompt)} chars, "
            f"~{len(prompt)//4} tokens, {len(prompt_parts)} terms"
        )

        return prompt


# Singleton instance
_context_manager_instance: Optional[EnhancedContextManager] = None


def get_enhanced_context_manager(
    config_path: Optional[str] = None
) -> EnhancedContextManager:
    """
    Get or create the global enhanced context manager instance

    Args:
        config_path: Optional path to configuration file

    Returns:
        Enhanced context manager instance
    """
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = EnhancedContextManager(config_path)
    return _context_manager_instance

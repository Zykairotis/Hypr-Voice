#!/usr/bin/env python3
"""
Context Manager for Hypr-Voice vocabulary system.
Gathers contextual information from shell history and clipboard.
"""

import subprocess
import os
import logging
import re
import time
from pathlib import Path
from typing import List, Dict, Set

logger = logging.getLogger(__name__)
TRACE_ENABLED = os.getenv("HYPR_VOICE_TRACE", "0") == "1"
TRACE_SLOW_MS = float(os.getenv("HYPR_VOICE_TRACE_SLOW_MS", "0"))

class ContextManager:
    """Manages context gathering from various sources."""
    
    def __init__(self):
        self.last_shell_history = []
        self.last_clipboard_history = []
    
    def get_shell_history(self, count: int = 40) -> List[str]:
        """
        Get last N shell commands from history file.
        
        Args:
            count: Number of recent commands to retrieve
            
        Returns:
            List of recent commands
        """
        # Support both bash and zsh
        history_files = [
            Path.home() / '.zsh_history',
            Path.home() / '.bash_history'
        ]
        
        commands = []
        for history_file in history_files:
            if history_file.exists():
                try:
                    with open(history_file, 'r', errors='ignore') as f:
                        lines = f.readlines()
                        # Extract commands (handle zsh extended history format)
                        for line in lines[-count * 2:]:  # Read more to account for format overhead
                            # zsh extended history format: ": timestamp:duration;command"
                            if ':' in line and ';' in line:  # zsh format
                                parts = line.split(';', 1)
                                if len(parts) > 1:
                                    cmd = parts[1].strip()
                                    if cmd:
                                        commands.append(cmd)
                            else:
                                # bash format: just the command
                                cmd = line.strip()
                                if cmd:
                                    commands.append(cmd)
                    break  # Use first available history file
                except Exception as e:
                    logger.error(f"Error reading shell history from {history_file}: {e}")
                    continue
        
        # Return last N commands
        result = commands[-count:] if commands else []
        self.last_shell_history = result
        return result
    
    def get_clipboard_history(self, count: int = 5) -> List[str]:
        """
        Get last N clipboard entries using cliphist or wl-paste.
        
        Args:
            count: Number of recent clipboard entries to retrieve
            
        Returns:
            List of recent clipboard entries
        """
        entries = []
        
        try:
            # For Wayland/Hyprland, use cliphist if available
            start_time = time.perf_counter()
            result = subprocess.run(['cliphist', 'list'],
                                  capture_output=True, text=True, timeout=2)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            if TRACE_ENABLED or (TRACE_SLOW_MS > 0 and elapsed_ms >= TRACE_SLOW_MS):
                logger.info("[TRACE] cliphist rc=%s %.1fms", result.returncode, elapsed_ms)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[:count]
                for line in lines:
                    # cliphist format: "id\ttext"
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
                start_time = time.perf_counter()
                result = subprocess.run(['wl-paste'], 
                                      capture_output=True, text=True, timeout=1)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                if TRACE_ENABLED or (TRACE_SLOW_MS > 0 and elapsed_ms >= TRACE_SLOW_MS):
                    logger.info("[TRACE] wl-paste rc=%s %.1fms", result.returncode, elapsed_ms)
                if result.returncode == 0:
                    entry = result.stdout.strip()
                    if entry:
                        entries.append(entry)
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                logger.debug(f"wl-paste not available or timed out: {e}")
        
        self.last_clipboard_history = entries
        return entries
    
    def extract_vocabulary_from_context(self, 
                                       commands: List[str], 
                                       clipboard: List[str]) -> List[str]:
        """
        Extract relevant vocabulary words from commands and clipboard.
        Only letters allowed, no symbols, numbers, or common words.
        
        Args:
            commands: List of shell commands
            clipboard: List of clipboard entries
            
        Returns:
            List of extracted vocabulary words (clean, letters only)
        """
        # Common words to exclude
        COMMON_WORDS = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one',
            'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now',
            'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'run', 'top', 'use', 'way', 'she',
            'too', 'any', 'big', 'try', 'ask', 'own', 'say', 'let', 'put', 'end', 'why', 'try',
            'also', 'back', 'been', 'call', 'came', 'come', 'does', 'done', 'down', 'each', 'feel',
            'find', 'from', 'give', 'good', 'hand', 'have', 'here', 'high', 'into', 'just', 'kind',
            'know', 'last', 'left', 'life', 'like', 'line', 'live', 'long', 'look', 'made', 'make',
            'many', 'more', 'most', 'move', 'much', 'must', 'name', 'need', 'next', 'only', 'open',
            'over', 'part', 'place', 'read', 'right', 'said', 'same', 'seem', 'show', 'side', 'some',
            'such', 'take', 'tell', 'than', 'that', 'them', 'then', 'there', 'these', 'they', 'thing',
            'this', 'time', 'turn', 'very', 'want', 'well', 'went', 'were', 'what', 'when', 'where',
            'which', 'while', 'with', 'work', 'would', 'write', 'year', 'your', 'about', 'after',
            'again', 'being', 'below', 'could', 'every', 'first', 'found', 'great', 'house', 'large',
            'later', 'learn', 'never', 'other', 'people', 'person', 'point', 'right', 'small', 'still',
            'their', 'think', 'three', 'through', 'under', 'until', 'water', 'where', 'world', 'years'
        }
        
        vocab_words = set()
        
        # Helper function to split CamelCase
        def split_camelcase(word):
            """Split CamelCase into separate words"""
            import re
            # Insert space before uppercase letters
            spaced = re.sub(r'([A-Z])', r' \1', word)
            return spaced.split()
        
        # Extract from commands
        for cmd in commands:
            parts = cmd.split()
            for part in parts:
                # Clean the word: remove all non-letter characters
                clean_word = ''.join(c for c in part if c.isalpha())
                
                # Skip if too long (likely concatenated path)
                if len(clean_word) > 30:
                    continue
                
                # Only keep if:
                # - Between 6-30 characters
                # - All letters
                # - Not a common word
                # - Has at least one capital letter (technical terms, proper nouns)
                if (6 <= len(clean_word) <= 30 and 
                    clean_word.lower() not in COMMON_WORDS and
                    any(c.isupper() for c in clean_word)):
                    # Try to split CamelCase
                    parts = split_camelcase(clean_word)
                    for p in parts:
                        if 6 <= len(p) <= 30 and p.lower() not in COMMON_WORDS:
                            vocab_words.add(p)
        
        # Extract from clipboard
        for clip in clipboard:
            words = clip.split()
            for word in words:
                # Clean the word
                clean_word = ''.join(c for c in word if c.isalpha())
                
                # Skip if too long
                if len(clean_word) > 30:
                    continue
                
                # Same criteria
                if (6 <= len(clean_word) <= 30 and 
                    clean_word.lower() not in COMMON_WORDS and
                    any(c.isupper() for c in clean_word)):
                    # Try to split CamelCase
                    parts = split_camelcase(clean_word)
                    for p in parts:
                        if 6 <= len(p) <= 30 and p.lower() not in COMMON_WORDS:
                            vocab_words.add(p)
        
        return sorted(list(vocab_words))  # Return sorted for consistent display
    
    def extract_context_from_window(self, window_info: Dict) -> Dict[str, any]:
        """Extract context from a normalized window info dict (any backend)."""
        application = (
            window_info.get('class', '')
            or window_info.get('wm_class', '')
            or window_info.get('app_id', '')
        )

        context = {
            'application': application,
            'title': window_info.get('title', ''),
            'keywords': set(),
            'metadata': {}
        }

        # Extract keywords from window title
        title = window_info.get('title', '') or ''
        if title:
            # Extract file names, paths
            file_patterns = re.findall(r'[\w\-]+\.\w+', title)
            context['keywords'].update(file_patterns)

            # Extract paths
            path_patterns = re.findall(r'/[\w/\-\.]+', title)
            context['keywords'].update(path_patterns)

            # Extract technical terms (CamelCase, snake_case)
            tech_terms = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)+|\w+_\w+', title)
            context['keywords'].update(tech_terms)

        # Store window metadata (preserve legacy fields)
        context['metadata'] = {
            'class': window_info.get('class', ''),
            'initialClass': window_info.get('initialClass', ''),
            'initialTitle': window_info.get('initialTitle', ''),
            'backend': window_info.get('backend', ''),
            'app_id': window_info.get('app_id', ''),
            'wm_class': window_info.get('wm_class', ''),
            'pid': window_info.get('pid'),
            'workspace': window_info.get('workspace', ''),
        }

        if 'raw' in window_info:
            context['metadata']['raw'] = window_info.get('raw')

        return context

    def extract_context_from_hyprland(self, window_info: Dict) -> Dict[str, any]:
        """Backward-compatible wrapper for existing Hyprland callers."""
        return self.extract_context_from_window(window_info)
    
    def get_comprehensive_context(self, window_info: Dict = None) -> Dict[str, any]:
        """
        Get comprehensive context from all available sources.
        
        Context vs Vocabulary:
        - Vocabulary: Just the words/terms extracted (for transcription hints)
        - Context: Full metadata and information about the source (for understanding state)
        
        Args:
            window_info: Optional window information from Hyprland
            
        Returns:
            Dictionary containing:
              - vocabulary: List of extracted words (for Whisper)
              - context: Detailed metadata about sources
        """
        # Get shell history
        shell_commands = self.get_shell_history(40)
        
        # Get clipboard history
        clipboard_entries = self.get_clipboard_history(5)
        
        # Extract vocabulary from shell and clipboard (words only)
        vocab_words = self.extract_vocabulary_from_context(
            shell_commands, clipboard_entries
        )
        
        # Build context (detailed metadata about sources)
        context_metadata = {
            'shell': {
                'recent_commands': shell_commands,
                'command_count': len(shell_commands),
                'unique_commands': len(set([cmd.split()[0] for cmd in shell_commands if cmd.split()])),
                'timestamp': time.time()
            },
            'clipboard': {
                'recent_entries': clipboard_entries,
                'entry_count': len(clipboard_entries),
                'timestamp': time.time()
            }
        }
        
        # Add window context if available
        window_vocab = []
        if window_info:
            window_context = self.extract_context_from_window(window_info)
            window_vocab = list(window_context['keywords'])
            context_metadata['window'] = {
                'application': window_context['application'],
                'title': window_context['title'],
                'metadata': window_context['metadata'],
                'timestamp': time.time()
            }
        
        # Build comprehensive result
        result = {
            'vocabulary': vocab_words + window_vocab,  # Words only
            'context': context_metadata,  # Detailed metadata
        }
        
        return result


def get_context_manager():
    """Get the singleton context manager instance."""
    global _context_manager_instance
    if '_context_manager_instance' not in globals():
        _context_manager_instance = ContextManager()
    return _context_manager_instance

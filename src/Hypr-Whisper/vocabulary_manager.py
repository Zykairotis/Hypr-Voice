#!/usr/bin/env python3
"""
Vocabulary Manager for Hypr-Voice
Handles custom vocabulary enhancement for different applications.
"""

import os
import yaml
import json
import re
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher
from dataclasses import dataclass
from loguru import logger

try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    HAVE_PSUTIL = False
    logger.warning("psutil not available, application detection will be limited")

@dataclass
class VocabularyConfig:
    """Configuration for vocabulary enhancement."""
    name: str
    description: str
    keywords: Dict[str, List[str]]
    applications: Dict[str, List[str]]
    prompts: Dict[str, str]
    priority: int = 0

class VocabularyManager:
    """Manages custom vocabulary for different applications."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the vocabulary manager.

        Args:
            config_path: Path to vocabulary configuration directory
        """
        self.config_dir = Path(config_path) if config_path else Path(__file__).parent / "config"
        self.vocabularies: Dict[str, VocabularyConfig] = {}
        self.current_app: Optional[str] = None
        self.current_vocabulary: Optional[str] = None
        self.active_keywords: Set[str] = set()

        # Load configurations
        self.load_configurations()

        # Start application detection
        self._detection_task = None
        self._running = False

    def load_configurations(self):
        """Load vocabulary configurations from files."""
        # Load main vocabulary config
        main_config = self.config_dir / "vocabulary.yaml"
        if main_config.exists():
            with open(main_config, 'r') as f:
                self.main_config = yaml.safe_load(f)
        else:
            logger.warning(f"Main vocabulary config not found: {main_config}")
            self.main_config = {}

        # Load application-specific vocabularies
        vocab_dir = self.config_dir / "vocabularies"
        if vocab_dir.exists():
            for vocab_file in vocab_dir.glob("*.yaml"):
                try:
                    with open(vocab_file, 'r') as f:
                        config_data = yaml.safe_load(f)

                    vocab_config = VocabularyConfig(
                        name=config_data.get('name', vocab_file.stem),
                        description=config_data.get('description', ''),
                        keywords=config_data.get('keywords', {}),
                        applications=config_data.get('applications', {}),
                        prompts=config_data.get('prompts', {}),
                        priority=config_data.get('priority', 0)
                    )

                    self.vocabularies[vocab_file.stem] = vocab_config
                    logger.info(f"Loaded vocabulary: {vocab_config.name}")

                except Exception as e:
                    logger.error(f"Error loading vocabulary {vocab_file}: {e}")

        # Load global vocabulary
        if 'global' in self.main_config:
            global_vocab = VocabularyConfig(
                name="Global",
                description="Global vocabulary for all applications",
                keywords=self.main_config['global'],
                applications={},
                prompts={},
                priority=-1
            )
            self.vocabularies['global'] = global_vocab

    def detect_active_application(self) -> Optional[str]:
        """
        Detect the currently active application window.

        Returns:
            Window class name or None if detection fails
        """
        if not HAVE_PSUTIL:
            return None

        try:
            # Get active window information
            # This is a simplified implementation - you might need to adjust
            # based on your window manager (Hyprland, X11, etc.)

            # For Hyprland, we could use:
            # hyprctl activewindow -j | jq -r '.class'

            # For now, return None to use global vocabulary
            # You can implement specific detection logic here
            return None

        except Exception as e:
            logger.error(f"Error detecting active application: {e}")
            return None

    def match_vocabulary_to_application(self, app_name: str) -> Optional[str]:
        """
        Match application name to appropriate vocabulary.

        Args:
            app_name: Window class name

        Returns:
            Vocabulary name or None if no match
        """
        app_name_lower = app_name.lower()

        # Check direct matches in vocabulary configurations
        for vocab_name, vocab_config in self.vocabularies.items():
            if 'window_classes' in vocab_config.applications:
                for pattern in vocab_config.applications['window_classes']:
                    if pattern.lower() in app_name_lower:
                        return vocab_name

        # Check patterns in main config
        if 'applications' in self.main_config:
            for app_config in self.main_config['applications'].values():
                if 'window_class_patterns' in app_config:
                    for pattern in app_config['window_class_patterns']:
                        if pattern.lower() in app_name_lower:
                            # Find corresponding vocabulary
                            for vocab_name in app_config.keys():
                                if vocab_name in self.vocabularies:
                                    return vocab_name

        return None

    def update_vocabulary(self, app_name: Optional[str] = None):
        """
        Update active vocabulary based on current application.

        Args:
            app_name: Optional application name override
        """
        if app_name is None:
            app_name = self.detect_active_application()

        self.current_app = app_name

        # Find matching vocabulary
        vocab_name = None
        if app_name:
            vocab_name = self.match_vocabulary_to_application(app_name)

        # Fallback to global vocabulary
        if vocab_name is None:
            vocab_name = 'global'

        # Update if vocabulary changed
        if self.current_vocabulary != vocab_name:
            self.current_vocabulary = vocab_name
            self.active_keywords = self._get_active_keywords(vocab_name)
            logger.info(f"Switched to vocabulary: {vocab_name} (app: {app_name})")

    def _get_active_keywords(self, vocab_name: str) -> Set[str]:
        """
        Get all active keywords for a vocabulary.

        Args:
            vocab_name: Name of the vocabulary

        Returns:
            Set of keywords
        """
        keywords = set()

        # Add global keywords
        if 'global' in self.vocabularies:
            for category_words in self.vocabularies['global'].keywords.values():
                if isinstance(category_words, list):
                    keywords.update(category_words)
                elif isinstance(category_words, dict):
                    for words in category_words.values():
                        if isinstance(words, list):
                            keywords.update(words)

        # Add vocabulary-specific keywords
        if vocab_name in self.vocabularies and vocab_name != 'global':
            for category_words in self.vocabularies[vocab_name].keywords.values():
                if isinstance(category_words, list):
                    keywords.update(category_words)
                elif isinstance(category_words, dict):
                    for words in category_words.values():
                        if isinstance(words, list):
                            keywords.update(words)

        return keywords

    def get_enhanced_prompt(self, base_prompt: Optional[str] = None) -> str:
        """
        Generate enhanced prompt with vocabulary context.

        Args:
            base_prompt: Base prompt to enhance

        Returns:
            Enhanced prompt string
        """
        if not self.current_vocabulary or self.current_vocabulary not in self.vocabularies:
            return base_prompt or ""

        vocab_config = self.vocabularies[self.current_vocabulary]

        # Get vocabulary-specific prompt
        if 'initial' in vocab_config.prompts:
            vocab_prompt = vocab_config.prompts['initial']
        else:
            vocab_prompt = ""

        # Combine prompts
        if base_prompt and vocab_prompt:
            return f"{base_prompt}\n\n{vocab_prompt}"
        elif vocab_prompt:
            return vocab_prompt
        else:
            return base_prompt or ""

    def post_process_transcription(self, text: str) -> str:
        """
        Post-process transcription to correct vocabulary words.

        Args:
            text: Original transcription text

        Returns:
            Corrected transcription text
        """
        # First apply common corrections (multi-word fixes)
        if 'global' in self.main_config and 'common_corrections' in self.main_config['global']:
            for wrong, correct in self.main_config['global']['common_corrections'].items():
                text = text.replace(wrong, correct)
        
        if not self.active_keywords:
            return text

        words = text.split()
        corrected_words = []

        for word in words:
            # Remove punctuation for comparison
            clean_word = re.sub(r'[^\w]', '', word.lower())

            # Find best match in vocabulary
            best_match = self._find_best_vocabulary_match(clean_word)

            if best_match:
                # Preserve original capitalization and punctuation
                prefix = ''
                suffix = ''

                # Extract punctuation
                if word and not word[0].isalnum():
                    prefix = word[0]
                    word = word[1:]
                if word and not word[-1].isalnum():
                    suffix = word[-1]
                    word = word[:-1]

                # Apply correction - preserve vocabulary's capitalization by default
                if word.isupper():
                    corrected_word = best_match.upper()
                elif word and word[0].isupper():
                    corrected_word = best_match.capitalize()
                else:
                    # Keep vocabulary's original capitalization
                    corrected_word = best_match

                corrected_word = prefix + corrected_word + suffix
                corrected_words.append(corrected_word)
            else:
                corrected_words.append(word)

        return ' '.join(corrected_words)

    def _find_best_vocabulary_match(self, word: str) -> Optional[str]:
        """
        Find the best vocabulary match for a word.

        Args:
            word: Word to match

        Returns:
            Best matching vocabulary word or None
        """
        if not self.active_keywords:
            return None

        # Skip common words (stop words) and very short words
        common_words = {'i', 'me', 'my', 'we', 'you', 'he', 'she', 'it', 'they',
                       'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'with',
                       'to', 'from', 'for', 'in', 'on', 'at', 'by', 'of', 'as',
                       'is', 'am', 'are', 'was', 'were', 'been', 'be', 'have', 'has',
                       'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                       'may', 'might', 'must', 'can', 'use', 'using', 'used'}
        
        if word.lower() in common_words or len(word) < 3:
            return None

        # Direct match (case-insensitive)
        for kw in self.active_keywords:
            if kw.lower() == word.lower():
                return kw

        # Fuzzy matching with higher threshold
        best_match = None
        best_ratio = 0.85  # Higher minimum similarity ratio to avoid false matches

        for vocab_word in self.active_keywords:
            ratio = SequenceMatcher(None, word.lower(), vocab_word.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = vocab_word

        return best_match

    async def start_detection(self, update_interval: float = 0.5):
        """
        Start automatic application detection.

        Args:
            update_interval: Update interval in seconds
        """
        if self._running:
            return

        self._running = True
        self._detection_task = asyncio.create_task(self._detection_loop(update_interval))
        logger.info("Started automatic vocabulary detection")

    async def stop_detection(self):
        """Stop automatic application detection."""
        self._running = False
        if self._detection_task:
            self._detection_task.cancel()
            try:
                await self._detection_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped automatic vocabulary detection")

    async def _detection_loop(self, update_interval: float):
        """Main detection loop."""
        while self._running:
            try:
                self.update_vocabulary()
                await asyncio.sleep(update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                await asyncio.sleep(update_interval)

    def add_custom_words(self, vocabulary_name: str, words: List[str]):
        """
        Add custom words to a vocabulary.

        Args:
            vocabulary_name: Name of the vocabulary
            words: List of words to add
        """
        if vocabulary_name not in self.vocabularies:
            logger.error(f"Vocabulary not found: {vocabulary_name}")
            return

        # Add to custom words category
        if 'custom' not in self.vocabularies[vocabulary_name].keywords:
            self.vocabularies[vocabulary_name].keywords['custom'] = []

        self.vocabularies[vocabulary_name].keywords['custom'].extend(words)
        self.active_keywords.update(words)

        logger.info(f"Added {len(words)} custom words to {vocabulary_name}")

    def get_vocabulary_stats(self) -> Dict:
        """
        Get statistics about loaded vocabularies.

        Returns:
            Dictionary with vocabulary statistics
        """
        stats = {
            'total_vocabularies': len(self.vocabularies),
            'current_vocabulary': self.current_vocabulary,
            'current_application': self.current_app,
            'active_keywords': len(self.active_keywords),
            'vocabularies': {}
        }

        for name, vocab in self.vocabularies.items():
            total_keywords = sum(
                len(words) if isinstance(words, list) else
                sum(len(w) if isinstance(w, list) else 0 for w in words.values())
                for words in vocab.keywords.values()
            )
            stats['vocabularies'][name] = {
                'name': vocab.name,
                'description': vocab.description,
                'total_keywords': total_keywords
            }

        return stats

# Global instance
_vocabulary_manager: Optional[VocabularyManager] = None

def get_vocabulary_manager(config_path: Optional[str] = None) -> VocabularyManager:
    """Get or create the global vocabulary manager instance."""
    global _vocabulary_manager
    if _vocabulary_manager is None:
        _vocabulary_manager = VocabularyManager(config_path)
    return _vocabulary_manager
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

# Local imports
from window_backends import detect_backend
import hook_bus

# Import ContextManager (basic)
try:
    from context_manager import ContextManager
    HAVE_CONTEXT_MANAGER = True
except ImportError:
    HAVE_CONTEXT_MANAGER = False
    logger.warning("ContextManager not available, context extraction will be disabled")

# Import EnhancedContextManager (new ultra-fast system)
try:
    from enhanced_context_manager import EnhancedContextManager, get_enhanced_context_manager
    HAVE_ENHANCED_CONTEXT = True
    logger.info("Enhanced Context Manager available")
except ImportError:
    HAVE_ENHANCED_CONTEXT = False
    logger.info("Enhanced Context Manager not available, will use basic system")

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
        self.backend_overlays: Dict[str, Dict] = {}
        self.current_app: Optional[str] = None
        self.current_vocabulary: Optional[str] = None
        self.current_backend: Optional[str] = None
        self.active_keywords: Set[str] = set()

        # Check if enhanced system should be used
        use_enhanced = os.environ.get('HYPR_VOICE_ENHANCED_CONTEXT', '').lower() in ('true', '1', 'yes')

        # Initialize ContextManager (basic or enhanced)
        if use_enhanced and HAVE_ENHANCED_CONTEXT:
            try:
                self.context_manager = get_enhanced_context_manager(str(self.config_dir))
                self._use_enhanced = True
                logger.info("✅ Using Enhanced Context Manager (ultra-fast, 5 data sources)")
            except Exception as e:
                logger.warning(f"Failed to initialize enhanced context manager: {e}")
                if HAVE_CONTEXT_MANAGER:
                    self.context_manager = ContextManager()
                    self._use_enhanced = False
                else:
                    self.context_manager = None
                    self._use_enhanced = False
        elif HAVE_CONTEXT_MANAGER:
            self.context_manager = ContextManager()
            self._use_enhanced = False
            logger.info("Using Basic Context Manager (3 data sources)")
        else:
            self.context_manager = None
            self._use_enhanced = False

        # Load configurations
        self.load_configurations()

        # Detect backend once (cached in window_backends) and set baseline
        try:
            self.current_backend = detect_backend().name
            logger.info(f"Vocabulary manager detected backend: {self.current_backend}")
        except Exception as e:
            logger.warning(f"Could not detect backend for vocabulary overlays: {e}")
            self.current_backend = None

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

        # Load backend overlays (optional)
        overlays_file = self.config_dir / "backend_overlays.yaml"
        if overlays_file.exists():
            try:
                with open(overlays_file, 'r') as f:
                    data = yaml.safe_load(f) or {}
                self.backend_overlays = data.get('backends', {}) or {}
                logger.info(f"Loaded backend overlays for {len(self.backend_overlays)} backends")
            except Exception as e:
                logger.error(f"Error loading backend overlays: {e}")

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

    def match_vocabulary_to_application(self, app_name: str, app_title: str = "") -> Optional[str]:
        """
        Match application name to appropriate vocabulary using both class and title.

        Args:
            app_name: Window class name
            app_title: Window title (optional)

        Returns:
            Vocabulary name or None if no match
        """
        app_name_lower = app_name.lower()
        app_title_lower = app_title.lower()

        # Check direct matches in vocabulary configurations
        for vocab_name, vocab_config in self.vocabularies.items():
            if 'window_classes' in vocab_config.applications:
                for pattern in vocab_config.applications['window_classes']:
                    if pattern.lower() in app_name_lower:
                        return vocab_name

        # Check patterns in main config
        if 'applications' in self.main_config:
            for app_key, app_config in self.main_config['applications'].items():
                if 'window_class_patterns' in app_config:
                    for pattern in app_config['window_class_patterns']:
                        if pattern.lower() in app_name_lower:
                            return app_key

        return None

    def update_vocabulary(self, app_name: Optional[str] = None, app_title: Optional[str] = None, backend: Optional[str] = None):
        """
        Update active vocabulary based on current application.

        Args:
            app_name: Optional application name override
            app_title: Optional application title
            backend: Optional backend name (hyprland/gnome/kde/sway/x11/manual)
        """
        if app_name is None:
            app_name = self.detect_active_application()

        # Track backend changes
        if backend:
            if backend != self.current_backend:
                logger.info(f"Backend changed {self.current_backend} -> {backend}")
                self.current_backend = backend
                hook_bus.emit('backend_change', backend_name=backend)
        elif self.current_backend is None:
            try:
                self.current_backend = detect_backend().name
            except Exception:
                self.current_backend = None

        self.current_app = app_name

        # Find matching vocabulary
        vocab_name = None
        if app_name:
            vocab_name = self.match_vocabulary_to_application(app_name, app_title or "")

        # Fallback to global vocabulary
        if vocab_name is None:
            vocab_name = 'global'

        # Update if vocabulary changed
        if self.current_vocabulary != vocab_name or backend:
            self.current_vocabulary = vocab_name
            self.active_keywords = self._get_active_keywords(vocab_name)
            logger.info(f"Switched to vocabulary: {vocab_name} (app: {app_name}, backend: {self.current_backend})")
            hook_bus.emit('vocab_change', vocab_name=vocab_name, app_name=app_name, backend_name=self.current_backend)

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

        # Add context-aware keywords from shell history and clipboard
        if self.context_manager:
            try:
                if self._use_enhanced:
                    # Use enhanced context manager (ultra-fast, 5 data sources)
                    result = self.context_manager.extract_comprehensive_vocabulary()
                    enhanced_vocab = result.get('vocabulary', [])
                    keywords.update(enhanced_vocab)
                    logger.info(
                        f"Added {len(enhanced_vocab)} enhanced keywords "
                        f"from {len(result.get('sources', {}))} sources "
                        f"in {result.get('extraction_time_ms', 0):.2f}ms"
                    )
                else:
                    # Use basic context manager (original system)
                    commands = self.context_manager.get_shell_history(40)
                    clipboard = self.context_manager.get_clipboard_history(5)
                    context_vocab = self.context_manager.extract_vocabulary_from_context(
                        commands, clipboard
                    )
                    keywords.update(context_vocab)
                    logger.debug(f"Added {len(context_vocab)} basic context-aware keywords")
            except Exception as e:
                logger.error(f"Error getting context-aware keywords: {e}")

        # Add backend overlay keywords (if available)
        if self.current_backend and self.current_backend in self.backend_overlays:
            overlay = self.backend_overlays[self.current_backend]
            overlay_keywords = overlay.get('keywords', []) or []
            keywords.update(overlay_keywords)
            logger.debug(f"Added {len(overlay_keywords)} backend overlay keywords for {self.current_backend}")

        return keywords

    def get_initial_prompt(self, max_tokens: int = 200) -> str:
        """
        Build optimized initial_prompt for Whisper.
        Format: comma-separated list (most effective pattern per research).
        
        Args:
            max_tokens: Maximum tokens (default 200, max 224 for Whisper)
        
        Returns:
            String under 224 tokens with top vocabulary terms
        """
        if not self.active_keywords:
            return ""
        
        # Prioritize keywords (application-specific > context > global)
        prioritized = self._prioritize_keywords()
        
        # Build comma-separated list (proven most effective)
        # Conservative: 800 chars ≈ 200 tokens
        prompt_parts = []
        current_length = 0
        MAX_CHARS = 800
        
        for keyword in prioritized:
            # Add keyword if it fits
            addition = f"{keyword}, "
            if current_length + len(addition) > MAX_CHARS:
                break
            prompt_parts.append(keyword)
            current_length += len(addition)
        
        # Format as comma-separated list (research-proven best practice)
        prompt = ", ".join(prompt_parts)
        
        # Add period at end for proper formatting
        if prompt:
            prompt += "."
        
        logger.debug(f"Generated initial_prompt: {len(prompt)} chars, ~{len(prompt)//4} tokens, {len(prompt_parts)} terms")
        
        return prompt
    
    def get_contextual_prompt(
        self,
        previous_text: str = "",
        max_words: int = 30,
        include_vocabulary: bool = True
    ) -> str:
        """
        Build context-aware prompt for better recognition of ANY words (not just vocabulary).
        
        This method improves on get_initial_prompt() by:
        1. Including recent words from user's speech (continuity)
        2. Shorter prompts (less hallucination risk)
        3. Works for unknown words (not just pre-defined vocabulary)
        
        Research backing:
        - Short prompts (15-30 words) optimal for WER + F1
        - Recent context critical for coherence
        - Comma-separated format most effective
        
        Args:
            previous_text: Last confirmed transcription text
            max_words: Maximum words in prompt (default 30, optimal 15-30)
            include_vocabulary: Include custom vocabulary terms
        
        Returns:
            Context-aware prompt string
        """
        prompt_words = []
        
        # PART 1: Recent context (for coherence and unknown words)
        if previous_text:
            # Extract significant words from last sentence
            recent_words = previous_text.split()[-100:]  # Last 100 words
            
            # Filter for meaningful words (> 3 chars, alphanumeric)
            significant = [
                w for w in recent_words 
                if len(w) > 3 and w.isalpha() and w.lower() not in {
                    'that', 'this', 'with', 'from', 'have', 'been', 'were', 'would', 'could', 'should'
                }
            ]
            
            # Take last 5-8 significant words for immediate context
            recent_context = significant[-8:] if len(significant) >= 8 else significant[-5:]
            prompt_words.extend(recent_context)
        
        # PART 2: Custom vocabulary (if enabled and available)
        if include_vocabulary and self.active_keywords:
            # Prioritize vocabulary by:
            # 1. Length (longer = more specific)
            # 2. Application relevance
            vocab_sorted = sorted(
                self.active_keywords,
                key=lambda x: (len(x), x.lower()),
                reverse=True
            )
            
            # Add vocabulary terms until we hit max_words
            remaining_slots = max_words - len(prompt_words)
            vocab_to_add = vocab_sorted[:remaining_slots]
            prompt_words.extend(vocab_to_add)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_words = []
        for word in prompt_words:
            if word.lower() not in seen:
                seen.add(word.lower())
                unique_words.append(word)
        
        # Limit to max_words
        unique_words = unique_words[:max_words]
        
        # Format as comma-separated list (research-proven)
        prompt = ", ".join(unique_words)
        if prompt:
            prompt += "."
        
        logger.debug(
            f"Contextual prompt: {len(unique_words)} words, "
            f"{len(prompt)} chars ({len(prompt)//4} tokens approx), "
            f"context={len(recent_context if previous_text else [])} vocab={len(vocab_to_add) if include_vocabulary else 0}"
        )
        
        return prompt
    
    def _prioritize_keywords(self) -> List[str]:
        """
        Prioritize keywords by importance.
        Order: Application-specific > Context (shell/clipboard) > Global
        
        Returns:
            List of prioritized unique keywords
        """
        prioritized = []
        
        # 1. Application-specific vocabulary (highest priority)
        if self.current_vocabulary and self.current_vocabulary != 'global':
            app_keywords = self._get_app_specific_keywords()
            prioritized.extend(app_keywords[:20])  # Top 20 app terms
        
        # 2. Context keywords (shell history, clipboard)
        if self.context_manager:
            try:
                if self._use_enhanced:
                    # Enhanced manager: already extracted in _get_active_keywords
                    # Skip duplicate extraction
                    pass
                else:
                    # Basic manager: extract vocabulary
                    context_vocab = self.context_manager.get_shell_history(40)
                    context_keywords = self.context_manager.extract_vocabulary_from_context(
                        context_vocab,
                        self.context_manager.get_clipboard_history(5)
                    )
                    prioritized.extend(list(context_keywords)[:15])  # Top 15 context terms
            except Exception as e:
                logger.debug(f"Error getting context keywords: {e}")
        
        # 3. Global technical terms (lower priority)
        global_keywords = self._get_global_keywords()
        prioritized.extend(global_keywords[:15])  # Top 15 global terms
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for kw in prioritized:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)
        
        return unique
    
    def _get_app_specific_keywords(self) -> List[str]:
        """Extract keywords from current application vocabulary."""
        keywords = []
        
        if self.current_vocabulary in self.main_config.get('applications', {}):
            app_vocab = self.main_config['applications'][self.current_vocabulary].get('vocabulary', {})
            
            # Flatten all vocabulary categories
            for category_words in app_vocab.values():
                if isinstance(category_words, list):
                    keywords.extend(category_words)
        
        return keywords
    
    def _get_global_keywords(self) -> List[str]:
        """Extract global technical terms."""
        keywords = []
        
        if 'global' in self.main_config:
            global_vocab = self.main_config['global']
            
            # Extract technical terms
            if 'technical_terms' in global_vocab:
                keywords.extend(global_vocab['technical_terms'][:20])
            
            # Extract programming keywords
            if 'programming' in global_vocab:
                prog = global_vocab['programming']
                if 'keywords' in prog:
                    keywords.extend(prog['keywords'][:10])
        
        return keywords

    def get_enhanced_prompt(self, base_prompt: Optional[str] = None) -> str:
        """
        DEPRECATED: Use get_initial_prompt() instead.
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

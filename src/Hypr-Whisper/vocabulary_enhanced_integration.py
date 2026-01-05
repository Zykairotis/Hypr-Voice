#!/usr/bin/env python3
"""
Dynamic Integration Module for Enhanced Vocabulary System
Provides drop-in compatibility with existing vocabulary_manager.py
"""

import os
import logging
from typing import Optional, Set, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import enhanced context manager
try:
    from ultrafast_vocabulary_extractor import get_vocabulary_extractor
    from enhanced_context_manager import EnhancedContextManager, get_enhanced_context_manager
    ENHANCED_AVAILABLE = True
    logger.info("Enhanced vocabulary system available")
except ImportError as e:
    ENHANCED_AVAILABLE = False
    logger.warning(f"Enhanced vocabulary system not available: {e}")


class DynamicVocabularyManager:
    """
    Dynamic vocabulary manager that uses enhanced system when available
    Provides backward compatibility with existing vocabulary_manager.py
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize dynamic vocabulary manager

        Args:
            config_path: Optional path to configuration directory
        """
        self.config_path = config_path
        self._enhanced_manager = None
        self._use_enhanced = False

        # Check if we should use enhanced system
        self._init_enhanced_if_available()

    def _init_enhanced_if_available(self):
        """Initialize enhanced manager if available and enabled"""
        if not ENHANCED_AVAILABLE:
            logger.info("Enhanced system not available, using basic")
            return

        # Check environment variable or config
        use_enhanced = os.environ.get('HYPR_VOICE_ENHANCED_CONTEXT', '').lower() in ('true', '1', 'yes')

        if use_enhanced:
            try:
                self._enhanced_manager = get_enhanced_context_manager(self.config_path)
                self._use_enhanced = True
                logger.info("✅ Using Enhanced Context Manager with 5 data sources")
            except Exception as e:
                logger.warning(f"Failed to initialize enhanced manager: {e}")
                self._use_enhanced = False
        else:
            logger.info("Enhanced system available but not enabled (set HYPR_VOICE_ENHANCED_CONTEXT=true)")
            self._use_enhanced = False

    def get_enhanced_vocabulary(
        self,
        force_refresh: bool = False
    ) -> Dict[str, any]:
        """
        Get vocabulary using enhanced context manager

        Args:
            force_refresh: Force refresh even if cache is valid

        Returns:
            Dictionary with vocabulary and metadata
        """
        if not self._use_enhanced or not self._enhanced_manager:
            return {
                'vocabulary': [],
                'error': 'Enhanced manager not available',
                'using_enhanced': False
            }

        try:
            result = self._enhanced_manager.extract_comprehensive_vocabulary(
                force_refresh=force_refresh
            )

            # Add flag to indicate enhanced system was used
            result['using_enhanced'] = True
            result['system'] = 'enhanced'

            logger.info(
                f"Enhanced extraction: {len(result['vocabulary'])} terms "
                f"in {result.get('extraction_time_ms', 0):.2f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Error in enhanced extraction: {e}")
            return {
                'vocabulary': [],
                'error': str(e),
                'using_enhanced': False
            }

    def get_whisper_prompt(
        self,
        max_tokens: int = 200
    ) -> str:
        """
        Get vocabulary formatted for Whisper initial_prompt

        Args:
            max_tokens: Maximum tokens for Whisper

        Returns:
            Comma-separated vocabulary string
        """
        if self._use_enhanced and self._enhanced_manager:
            try:
                return self._enhanced_manager.get_vocabulary_for_whisper(max_tokens)
            except Exception as e:
                logger.error(f"Error getting Whisper prompt: {e}")

        # Fallback to empty string
        return ""

    def get_active_keywords(self) -> Set[str]:
        """
        Get active keywords from enhanced system

        Returns:
            Set of active keywords
        """
        result = self.get_enhanced_vocabulary()
        return set(result.get('vocabulary', []))

    def get_stats(self) -> Dict:
        """Get statistics about the vocabulary system"""
        stats = {
            'enhanced_available': ENHANCED_AVAILABLE,
            'using_enhanced': self._use_enhanced,
            'environment_enabled': os.environ.get('HYPR_VOICE_ENHANCED_CONTEXT', '').lower() in ('true', '1', 'yes')
        }

        if self._use_enhanced and self._enhanced_manager:
            # Get stats from enhanced manager
            result = self._enhanced_manager.extract_comprehensive_vocabulary()
            stats.update({
                'vocabulary_size': len(result['vocabulary']),
                'extraction_time_ms': result.get('extraction_time_ms', 0),
                'sources': list(result.get('sources', {}).keys()),
                'source_stats': result.get('stats', {})
            })

        return stats

    def is_using_enhanced(self) -> bool:
        """Check if enhanced system is being used"""
        return self._use_enhanced

    def enable_enhanced(self):
        """Enable enhanced vocabulary system"""
        if ENHANCED_AVAILABLE:
            self._use_enhanced = True
            if not self._enhanced_manager:
                self._enhanced_manager = get_enhanced_context_manager(self.config_path)
            logger.info("Enhanced vocabulary system enabled")
        else:
            logger.warning("Cannot enable enhanced system - not available")

    def disable_enhanced(self):
        """Disable enhanced vocabulary system"""
        self._use_enhanced = False
        logger.info("Enhanced vocabulary system disabled")


# Convenience function for easy import
def get_dynamic_manager(config_path: Optional[str] = None) -> DynamicVocabularyManager:
    """
    Get or create the dynamic vocabulary manager

    Args:
        config_path: Optional path to configuration directory

    Returns:
        Dynamic vocabulary manager instance
    """
    return DynamicVocabularyManager(config_path)


# Quick test function
def quick_test():
    """Quick test of the dynamic integration"""
    print("=" * 70)
    print("DYNAMIC VOCABULARY MANAGER - INTEGRATION TEST")
    print("=" * 70)
    print()

    # Initialize
    manager = get_dynamic_manager()

    # Check availability
    print("System Status:")
    print("-" * 70)
    print(f"  Enhanced available: {ENHANCED_AVAILABLE}")
    print(f"  Environment enabled: {os.environ.get('HYPR_VOICE_ENHANCED_CONTEXT', 'false')}")
    print(f"  Using enhanced: {manager.is_using_enhanced()}")
    print()

    if ENHANCED_AVAILABLE:
        # Enable enhanced
        print("Enabling enhanced system...")
        manager.enable_enhanced()
        print()

        # Get vocabulary
        print("Extracting vocabulary...")
        result = manager.get_enhanced_vocabulary(force_refresh=True)
        print()

        print("Results:")
        print("-" * 70)
        print(f"  Vocabulary size: {len(result['vocabulary'])}")
        print(f"  Extraction time: {result.get('extraction_time_ms', 0):.2f}ms")
        print(f"  Sources used: {', '.join(result.get('sources', {}).keys())}")
        print()

        # Show vocabulary
        vocab = result['vocabulary']
        print(f"Top 20 terms:")
        print(f"  {', '.join(vocab[:20])}")
        print()

        # Show Whisper prompt
        print("Whisper prompt (first 200 chars):")
        print("-" * 70)
        prompt = manager.get_whisper_prompt()
        print(prompt[:200] + "...")
        print()

        # Show stats
        stats = manager.get_stats()
        print("Statistics:")
        print("-" * 70)
        for key, value in stats.items():
            if key not in ['source_stats']:
                print(f"  {key}: {value}")
        print()

    else:
        print("❌ Enhanced system not available")
        print("   Check that ultrafast_vocabulary_extractor.py and")
        print("   enhanced_context_manager.py are in the same directory")
        print()

    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print()


if __name__ == "__main__":
    quick_test()
